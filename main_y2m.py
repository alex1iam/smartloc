import os
os.environ['SDL_AUDIODRIVER'] = 'alsa'
os.environ['PYGAME_DETECT_AVX2'] = '1'

import json
import re
import paho.mqtt.client as mqtt
from rapidfuzz import fuzz
import pygame
import configparser
import numpy as np
import threading
import queue
import vosk
import time
import atexit
import sys
import signal
import sounddevice as sd
import argparse
import logging
import subprocess

from commands import COMMANDS_ON_OFF, COMMANDS_LEVEL

logging.getLogger('vosk').setLevel(logging.ERROR)

# ==================== ГЛОБАЛЬНЫЕ ====================

running = True
model = None
mqtt_client = None
location_cache = {}
devices = {}
groups = {}
wake_list = []
USE_VOCABULARY = True
sound_initialized = False
MQTT_CONNECTED = False
INCLUDE_USB = True

LOG_BLOCKS = False
SHOW_MICS_LEVEL = False

mic_slots = []
mic_slots_lock = threading.Lock()

print_lock = threading.Lock()

def log(*args, **kwargs):
    kwargs.setdefault('flush', True)
    with print_lock:
        print(*args, **kwargs)

MIN_COMMAND_LENGTH = 2

DEDUP_WINDOW = 4.0
DEDUP_FUZZ = 85
last_command = {'cmd': '', 'time': 0.0}
dedup_lock = threading.Lock()

command_mode = False
command_timer = None
command_mode_lock = threading.Lock()

SAMPLERATE_VOSK = 16000

SEEED_KEYWORDS = ('MicArray', 'reSpeaker', 'XVF3800', 'Array')

SLOT_STALL_SEC = 10.0
_last_blocks = {}

ARECORD_RESTART_WARN_SEC = 30.0
ARECORD_MISSING_DEV_WAIT_SEC = 5.0

LEVEL_LOG_INTERVAL = 1.0
_last_level_log = {}

GAIN_TARGET = 12000
GAIN_MAX = 50
GAIN_MIN = 1
GAIN_SMOOTHING = 0.7
GAIN_SPEECH_THRESHOLD = 200

_subscribed_topics = []

device_states = {}
device_states_lock = threading.Lock()

LEVEL_INSTANCES = ('brightness', 'temperature', 'volume', 'humidity', 'position')

LEVEL_UP_WORDS = ('ярче', 'светлее', 'теплее', 'выше', 'громче', 'больше', 'сильнее')
LEVEL_DOWN_WORDS = ('тусклее', 'темнее', 'холоднее', 'ниже', 'тише', 'меньше', 'слабее')

# ==================== АВТООПРЕДЕЛЕНИЕ ====================

def detect_arecord_devices():
    try:
        out = subprocess.check_output(['arecord', '-l'], text=True, stderr=subprocess.DEVNULL)
    except Exception as e:
        log(f"⚠️ arecord -l: {e}")
        return []

    result = []
    for line in out.splitlines():
        m = re.search(r'card\s+(\d+):\s+(\S+)\s+\[([^\]]+)\],\s*device\s+(\d+):', line)
        if not m:
            continue
        card_num = int(m.group(1))
        card_id = m.group(2)
        card_desc = m.group(3)
        dev_num = int(m.group(4))
        hay = f"{card_id} {card_desc}".lower()
        is_seeed = any(k.lower() in hay for k in SEEED_KEYWORDS)
        if is_seeed:
            result.append({
                'dev': f'plughw:{card_num},{dev_num}',
                'fmt': 'S32_LE', 'channels': 4, 'rate': 16000, 'width': 4,
                'desc': f"seeed-4mic (arecord plughw:{card_num},{dev_num})",
                'is_seeed': True,
            })
        else:
            result.append({
                'dev': f'plughw:{card_num},{dev_num}',
                'fmt': 'S16_LE', 'channels': 1, 'rate': 16000, 'width': 2,
                'desc': f"arecord plughw:{card_num},{dev_num} ({card_desc})",
                'is_seeed': False,
            })
    return result


def detect_seeed_arecord_dev():
    for d in detect_arecord_devices():
        if d['is_seeed']:
            return d['dev']
    return None

# ==================== ПЕРЕСЭМПЛИНГ ====================

def resample_audio(audio_data, orig_sr, target_sr=16000):
    if orig_sr == target_sr or len(audio_data) == 0:
        return audio_data
    new_len = int(len(audio_data) * target_sr / orig_sr)
    if new_len <= 0:
        return audio_data
    indices = np.linspace(0, len(audio_data) - 1, new_len)
    idx_floor = np.clip(np.floor(indices).astype(np.int64), 0, len(audio_data) - 1)
    idx_ceil = np.clip(np.ceil(indices).astype(np.int64), 0, len(audio_data) - 1)
    weights = (indices - idx_floor).astype(np.float32)
    resampled = (1 - weights) * audio_data[idx_floor] + weights * audio_data[idx_ceil]
    return np.clip(resampled, -32768, 32767).astype(np.int16)

# ==================== DEVICE ====================

class Device:
    def __init__(self, device_id, name, room, mqtt_config, capabilities=None):
        self.device_id = device_id
        self.name = name
        self.room = room
        self.mqtt = mqtt_config
        self.capabilities = capabilities or []
        self.commands = {}
        self.level_specs = {}
        self.level_states = {}
        self._build_commands()

    def _build_commands(self):
        ranges = {}
        for cap in self.capabilities:
            if cap.get('type') == 'devices.capabilities.range':
                params = cap.get('parameters', {})
                inst = params.get('instance')
                rng = params.get('range', {})
                if inst and rng:
                    ranges[inst] = {
                        'min': rng.get('min', 0),
                        'max': rng.get('max', 100),
                        'step': rng.get('precision', 1),
                    }

        commands = {}
        for item in self.mqtt:
            instance = item.get('instance')
            topic = item.get('set')
            state_topic = item.get('state')
            if not topic:
                continue
            if instance == 'on':
                commands[topic] = COMMANDS_ON_OFF
            elif instance in LEVEL_INSTANCES:
                commands[topic] = COMMANDS_LEVEL
                spec = dict(ranges.get(instance, {
                    'min': 0, 'max': 100, 'step': 1,
                }))
                spec['instance'] = instance
                self.level_specs[topic] = spec
                if state_topic:
                    self.level_states[topic] = state_topic
        self.commands = commands

    def get_status_topics(self):
        return [i['state'] for i in self.mqtt if 'state' in i]

# ==================== ПАРСИНГ JS ====================

def parse_js_config(js_file):
    with open(js_file, 'r', encoding='utf-8') as f:
        content = f.read()

    match = re.search(r'module\.exports\s*=\s*({[\s\S]*?})\s*;?\s*$', content)
    if not match:
        match = re.search(r'module\.exports\s*=\s*({[\s\S]*})', content)
    if not match:
        raise ValueError("Не найден module.exports")

    js_code = match.group(1)
    js_code = re.sub(r'//.*?$', '', js_code, flags=re.MULTILINE)
    js_code = re.sub(r'/\*.*?\*/', '', js_code, flags=re.DOTALL)
    js_code = re.sub(r"'([^']*)'", r'"\1"', js_code)
    js_code = re.sub(r'([{,])\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', js_code)
    js_code = re.sub(r',\s*}', '}', js_code)
    js_code = re.sub(r',\s*]', ']', js_code)
    js_code = re.sub(r'\bundefined\b', 'null', js_code)

    try:
        return json.loads(js_code)
    except json.JSONDecodeError:
        py_code = js_code
        py_code = re.sub(r'\btrue\b', 'True', py_code)
        py_code = re.sub(r'\bfalse\b', 'False', py_code)
        py_code = re.sub(r'\bnull\b', 'None', py_code)
        safe_globals = {'__builtins__': None, 'True': True, 'False': False, 'None': None}
        return eval(py_code, safe_globals)


def load_devices_from_js(js_file):
    config = parse_js_config(js_file)
    result = {}
    for d in config.get('devices', []):
        dev = Device(
            d.get('id', ''),
            d.get('name', ''),
            d.get('room', ''),
            d.get('mqtt', []),
            d.get('capabilities', []),
        )
        result[dev.device_id] = dev
    return result

# ==================== СИГНАЛЫ ====================

def signal_handler(sig, frame):
    global running
    log("\nПолучен сигнал завершения...")
    running = False

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# ==================== НАСТРОЙКИ ====================

def load_config():
    global wake_list
    global DEDUP_WINDOW, DEDUP_FUZZ
    global SLOT_STALL_SEC, ARECORD_RESTART_WARN_SEC, ARECORD_MISSING_DEV_WAIT_SEC
    global LEVEL_LOG_INTERVAL
    global GAIN_TARGET, GAIN_MAX, GAIN_MIN, GAIN_SMOOTHING, GAIN_SPEECH_THRESHOLD

    config = configparser.ConfigParser()
    config.read('/opt/smartloc/settings.ini')

    wake_string = config.get('WAKE', 'wake_string', fallback='вика,века,виктор,лика,ника')
    wake_list = [w.strip().lower() for w in wake_string.split(',') if w.strip()]
    log(f"👋 Wake-слова: {wake_list}")

    config_js_path = config.get('DEVICES', 'config_path', fallback='/opt/yandex2mqtt/config.js')
    log(f"📁 Конфиг устройств: {config_js_path}")

    log_blocks_ini = False
    if config.has_section('LOG'):
        try:
            log_blocks_ini = config.getboolean('LOG', 'blocks', fallback=False)
        except ValueError:
            log_blocks_ini = False

    DEDUP_WINDOW = config.getfloat('TIMERS', 'dedup_window', fallback=4.0)
    DEDUP_FUZZ = config.getint('TIMERS', 'dedup_fuzz', fallback=85)
    SLOT_STALL_SEC = config.getfloat('TIMERS', 'slot_stall_sec', fallback=10.0)
    ARECORD_RESTART_WARN_SEC = config.getfloat('TIMERS', 'arecord_restart_warn_sec', fallback=30.0)
    ARECORD_MISSING_DEV_WAIT_SEC = config.getfloat('TIMERS', 'arecord_missing_dev_wait_sec', fallback=5.0)
    LEVEL_LOG_INTERVAL = config.getfloat('TIMERS', 'level_log_interval', fallback=1.0)

    GAIN_TARGET = config.getint('GAIN', 'target_amplitude', fallback=12000)
    GAIN_MAX = config.getint('GAIN', 'max_gain', fallback=50)
    GAIN_MIN = config.getint('GAIN', 'min_gain', fallback=1)
    GAIN_SMOOTHING = config.getfloat('GAIN', 'smoothing', fallback=0.7)
    GAIN_SPEECH_THRESHOLD = config.getint('GAIN', 'speech_threshold', fallback=200)

    return {
        'ip': config.get('MQTT', 'ip', fallback='localhost'),
        'port': config.getint('MQTT', 'port', fallback=1883),
        'wake_timer': config.getint('WAKE', 'wake_timer', fallback=10),
        'sim_wake': config.getint('DICT', 'sim_wake', fallback=75),
        'sim_name': config.getint('DICT', 'sim_name', fallback=70),
        'sim_location': config.getint('DICT', 'sim_location', fallback=70),
        'sim_action': config.getint('DICT', 'sim_action', fallback=70),
        'sim_group': config.getint('DICT', 'sim_group', fallback=85),
        'sound_wake': config.get('SOUNDS', 'sound_wake', fallback=''),
        'sound_command_done': config.get('SOUNDS', 'sound_command_done', fallback=''),
        'sound_command_end': config.get('SOUNDS', 'sound_command_end', fallback=''),
        'config_js_path': config_js_path,
        'log_blocks': log_blocks_ini,
    }

cfg = load_config()
IP = cfg['ip']
PORT = cfg['port']
WAKE_TIMER = cfg['wake_timer']
SIM_WAKE = cfg['sim_wake']
SIM_NAME = cfg['sim_name']
SIM_LOCATION = cfg['sim_location']
SIM_ACTION = cfg['sim_action']
SIM_GROUP = cfg['sim_group']
SOUND_WAKE = cfg['sound_wake']
SOUND_COMMAND_DONE = cfg['sound_command_done']
SOUND_COMMAND_END = cfg['sound_command_end']
CONFIG_JS_PATH = cfg['config_js_path']
LOG_BLOCKS = cfg.get('log_blocks', False)

# ==================== ВЫБОР МИКРОФОНОВ ====================

def detect_microphones(use_all=False, manual_indices=None):
    if manual_indices:
        result = []
        for item in manual_indices:
            if isinstance(item, str) and item.lower() == 'arecord':
                for d in detect_arecord_devices():
                    result.append(d)
                    log(f"   ✅ {d['desc']}")
                continue
            if isinstance(item, str) and item.lower() == 'seeed':
                for d in detect_arecord_devices():
                    if d['is_seeed']:
                        result.append(d)
                        log(f"   ✅ {d['desc']}")
                continue
            log(f"   ❌ '{item}' — поддерживается только 'arecord' или 'seeed'")
        return result

    result = []
    for d in detect_arecord_devices():
        result.append(d)
        log(f"   ✅ {d['desc']}")
    return result


def describe_mic(item):
    return item['desc']


def room_in_name(room, name):
    r = (room or '').lower()
    n = (name or '').lower()
    if not r:
        return True
    if r.endswith(('ая', 'яя')):
        stem = r[:-2]
    elif r.endswith(('а', 'я')):
        stem = r[:-1]
    else:
        stem = r
    return stem in n

# ==================== VOSK ====================

log("🔍 Загрузка Vosk модели...")
try:
    model = vosk.Model("/opt/model_stt/vosk-model-small-ru-0.22")
    log("✅ Модель загружена")
except Exception as e:
    log(f"❌ Ошибка: {e}")
    sys.exit(1)

# ==================== ЗВУК ====================

log("🔊 Инициализация звука...")
last_error = None
for device in ('plughw:0,0', 'default',
               'sysdefault:CARD=Headphones', 'hw:0,0'):
    try:
        try:
            pygame.mixer.quit()
        except Exception:
            pass
        os.environ['AUDIODEV'] = device
        os.environ['SDL_AUDIODRIVER'] = 'alsa'
        pygame.mixer.pre_init(frequency=22050, size=-16, channels=2)
        pygame.mixer.init()
        log(f"   ✅ Звук инициализирован: {device}")
        sound_initialized = True
        break
    except Exception as e:
        last_error = e
        log(f"   ❌ {device}: {e}")

if not sound_initialized:
    log(f"⚠️ Звук не инициализирован: {last_error}")


def play_sound(file_path):
    if not sound_initialized:
        return
    try:
        if file_path and os.path.exists(file_path):
            pygame.mixer.Sound(file_path).play()
    except Exception as e:
        logging.debug(f"play_sound: {e}")

# ==================== MQTT ====================

try:
    mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
except (AttributeError, TypeError):
    mqtt_client = mqtt.Client()


def on_connect(client, userdata, flags, rc, properties=None):
    global MQTT_CONNECTED
    MQTT_CONNECTED = True
    devs = userdata.get('devices', {}) if isinstance(userdata, dict) else {}
    for device in devs.values():
        for topic in device.get_status_topics():
            client.subscribe(topic)
            _subscribed_topics.append(topic)


def on_disconnect(client, userdata, flags=None, rc=None, properties=None):
    global MQTT_CONNECTED
    MQTT_CONNECTED = False
    log("⚠️ MQTT отключён")


def on_message(client, userdata, message, properties=None):
    topic = message.topic
    try:
        payload = message.payload.decode(errors='replace')
    except Exception:
        payload = ''
    with device_states_lock:
        device_states[topic] = payload


mqtt_client.user_data_set({'devices': devices})
mqtt_client.on_connect = on_connect
mqtt_client.on_disconnect = on_disconnect
mqtt_client.on_message = on_message

try:
    mqtt_client.connect(IP, int(PORT), 60)
    log(f"✅ MQTT: {IP}:{PORT}")
except Exception as e:
    log(f"❌ MQTT connect: {e}")


def publish_command(topic, value, description=""):
    if not mqtt_client:
        log(f"❌ MQTT клиент не инициализирован: {topic}={value}")
        return False
    try:
        result = mqtt_client.publish(topic, value)
        if result.rc != mqtt.MQTT_ERR_SUCCESS:
            log(f"❌ Ошибка публикации {topic}={value}: rc={result.rc}")
            return False
        log(f"✅ {description}{topic} = {value}")
        return True
    except Exception as e:
        log(f"❌ Публикация {topic}={value}: {e}")
        return False

# ==================== ВСПОМОГАТЕЛЬНЫЕ ====================

def get_location_variants(device):
    if device.device_id not in location_cache:
        variants = []
        if device.room:
            base = device.room.lower()
            variants.append(base)
            for suffix in ('е', 'и', 'у', 'ой', 'ей'):
                variants.append(base + suffix)
        location_cache[device.device_id] = variants
    return location_cache[device.device_id]


def build_vosk_vocabulary():
    vocabulary = set()
    for wake in wake_list:
        vocabulary.add(wake.lower())
    for device in devices.values():
        for cmd_options in device.commands.values():
            if not isinstance(cmd_options, dict):
                continue
            for synonyms_tuple in cmd_options.keys():
                for synonym in synonyms_tuple:
                    for word in synonym.lower().split():
                        w = word.strip('.,!?-()')
                        if len(w) > 1 and w.isalpha():
                            vocabulary.add(w)
        for word in device.name.lower().split():
            w = word.strip('.,!?-()')
            if len(w) > 1 and w.isalpha():
                vocabulary.add(w)
        if device.room:
            for word in device.room.lower().split():
                w = word.strip('.,!?-()')
                if len(w) > 1 and w.isalpha():
                    vocabulary.add(w)
    for group_name in groups.keys():
        for word in group_name.lower().split():
            w = word.strip('.,!?-()')
            if len(w) > 1 and w.isalpha():
                vocabulary.add(w)
    vocabulary.add("[unk]")
    result = sorted(vocabulary)
    log(f"📚 Собрано {len(result)} слов")
    for wake in wake_list:
        if wake.lower() not in result:
            vocabulary.add(wake.lower())
            result = sorted(vocabulary)
    return json.dumps(result, ensure_ascii=False)

# ==================== ЛОГИКА КОМАНД ====================

def is_wake_word(text):
    if not text or len(text.strip()) < 2:
        return False, None
    text = text.strip().lower()
    if text in wake_list:
        return True, "точное"
    for alias in wake_list:
        if text.startswith(alias):
            return True, "начало"
        if alias in text:
            return True, "вхождение"
    for alias in wake_list:
        if len(alias) >= 2:
            score = max(fuzz.ratio(alias, text),
                        fuzz.partial_ratio(alias, text),
                        fuzz.token_set_ratio(alias, text))
            if score >= SIM_WAKE:
                lr = min(len(alias), len(text)) / max(len(alias), len(text))
                if lr > 0.3:
                    return True, f"нечеткое ({score})"
    for word in text.split():
        if len(word) < 2:
            continue
        if word in wake_list:
            return True, "слово_точное"
        for alias in wake_list:
            if len(alias) >= 2:
                s = fuzz.ratio(alias, word)
                if s >= SIM_WAKE:
                    return True, f"слово_нечеткое ({s})"
    return False, None


def strip_wake_word(text):
    cmd = text.lower()
    found = False
    for alias in wake_list:
        if alias in cmd:
            cmd = cmd.replace(alias, ' ')
            found = True
    cmd = re.sub(r'\s+', ' ', cmd).strip(' .,!?-').strip()
    return cmd, found


def is_duplicate_command(cmd):
    if not cmd:
        return False
    now = time.time()
    with dedup_lock:
        prev = last_command['cmd']
        prev_time = last_command['time']
        if prev and now - prev_time < DEDUP_WINDOW:
            score = fuzz.token_set_ratio(prev, cmd)
            if score >= DEDUP_FUZZ:
                return True, prev, score
        last_command['cmd'] = cmd
        last_command['time'] = now
    return False, None, None


def resolve_level_value(cmd_lower, spec, current_value=None):
    """
    spec: {'min': 0, 'max': 100, 'step': 10, 'instance': 'brightness'}
    Возвращает строку-значение для publish или None.
    - число в команде → ограничить [min,max], округлить до step
    - 'UP'  → current + step (или 'UP', если current неизвестен)
    - 'DOWN'→ current - step (или 'DOWN')
    """
    lo = spec.get('min', 0)
    hi = spec.get('max', 100)
    step = spec.get('step', 1) or 1

    m = re.search(r'(\d{1,3})', cmd_lower)
    if m:
        v = int(m.group(1))
        v = max(lo, min(hi, v))
        if step > 0:
            v = lo + ((v - lo) // step) * step
        return str(v)

    if any(w in cmd_lower.split() for w in LEVEL_UP_WORDS):
        if current_value is not None:
            v = min(hi, current_value + step)
            return str(v)
        return 'UP'
    if any(w in cmd_lower.split() for w in LEVEL_DOWN_WORDS):
        if current_value is not None:
            v = max(lo, current_value - step)
            return str(v)
        return 'DOWN'

    return None


def find_device_in_command(cmd, device):
    cmd_lower = cmd.lower()
    device_name = device.name.lower()
    name_score = 100 if device_name in cmd_lower else fuzz.partial_ratio(device_name, cmd_lower)
    if name_score < SIM_NAME:
        return None, None
    for loc in get_location_variants(device):
        if loc in cmd_lower:
            return device.name, device.room.lower() if device.room else None
        if fuzz.partial_ratio(loc, cmd_lower) >= SIM_LOCATION:
            return device.name, device.room.lower() if device.room else None
    same = sum(1 for d in devices.values() if d.name.lower() == device_name)
    if same == 1:
        return device.name, None
    return None, None


def _current_level_value(device, cmd_topic):
    state_topic = device.level_states.get(cmd_topic)
    if not state_topic:
        return None
    with device_states_lock:
        raw = device_states.get(state_topic)
    if raw is None:
        return None
    try:
        return int(float(raw))
    except ValueError:
        return None


def execute_command(command):
    cmd_lower = command.lower().strip()
    if len(cmd_lower) < MIN_COMMAND_LENGTH:
        return None, None, None, None
    best_overall = None
    best_overall_score = 0
    for device in devices.values():
        dev_name, dev_location = find_device_in_command(cmd_lower, device)
        if not dev_name:
            continue
        best_score = 0
        best_result = None
        for cmd_topic, cmd_options in device.commands.items():
            if not isinstance(cmd_options, dict):
                continue
            for synonyms_tuple, action_value in cmd_options.items():
                for synonym in synonyms_tuple:
                    s = synonym.lower()
                    score = max(fuzz.ratio(s, cmd_lower),
                                fuzz.partial_ratio(s, cmd_lower),
                                fuzz.token_set_ratio(s, cmd_lower))
                    if score >= SIM_ACTION and score > best_score:
                        final_value = action_value
                        if cmd_topic in device.level_specs:
                            spec = device.level_specs[cmd_topic]
                            current = _current_level_value(device, cmd_topic)
                            new_val = resolve_level_value(cmd_lower, spec, current)
                            if new_val is not None:
                                final_value = new_val
                        best_score = score
                        best_result = (dev_name, dev_location, cmd_topic, final_value)
        if best_result and best_score > best_overall_score:
            best_overall_score = best_score
            best_overall = best_result
    return best_overall if best_overall else (None, None, None, None)


def find_action_in_command(cmd_lower):
    best_score = 0
    best = (None, None)
    for device in devices.values():
        for cmd_options in device.commands.values():
            if not isinstance(cmd_options, dict):
                continue
            for synonyms_tuple, action_value in cmd_options.items():
                for synonym in synonyms_tuple:
                    s = synonym.lower()
                    score = max(fuzz.ratio(s, cmd_lower),
                                fuzz.partial_ratio(s, cmd_lower),
                                fuzz.token_set_ratio(s, cmd_lower))
                    if score >= SIM_ACTION and score > best_score:
                        best_score = score
                        best = (action_value, synonym)
    return best


def execute_group_command(command):
    cmd_lower = command.lower().strip()
    if len(cmd_lower) < MIN_COMMAND_LENGTH:
        return False
    matched_group = None
    matched_score = 0
    for group_name, group_devices in groups.items():
        if not group_devices:
            continue
        score = fuzz.partial_ratio(group_name.lower(), cmd_lower)
        if score >= SIM_GROUP and score > matched_score:
            matched_score = score
            matched_group = (group_name, group_devices)
    if not matched_group:
        return False
    group_name, group_devices = matched_group
    action, matched_synonym = find_action_in_command(cmd_lower)
    if not action:
        return False
    log(f"🎯 {matched_synonym} {group_name}")
    success = False
    for device_id in group_devices:
        device = devices.get(device_id)
        if not device:
            continue
        for cmd_topic, cmd_options in device.commands.items():
            if not isinstance(cmd_options, dict):
                continue
            found = False
            for synonyms_tuple, action_value in cmd_options.items():
                if action_value == action:
                    final_value = action_value
                    if cmd_topic in device.level_specs:
                        spec = device.level_specs[cmd_topic]
                        current = _current_level_value(device, cmd_topic)
                        new_val = resolve_level_value(cmd_lower, spec, current)
                        if new_val is not None:
                            final_value = new_val
                    loc_str = ""
                    if device.room and not room_in_name(device.room, device.name):
                        loc_str = f" {device.room.upper()}"
                    if publish_command(cmd_topic, final_value, f"{device_id}{loc_str}: "):
                        success = True
                    found = True
                    break
            if found:
                break
    return success


def process_command(command):
    if len(command.strip()) < MIN_COMMAND_LENGTH:
        return
    log(f"🎯 ВЫПОЛНЕНА КОМАНДА: '{command}'")
    dev_name, location, topic, action = execute_command(command)
    if dev_name and topic and action:
        loc_str = ""
        if location and not room_in_name(location, dev_name):
            loc_str = f" {location.upper()}"
        if publish_command(topic, action, f"{dev_name}{loc_str}: "):
            play_sound(SOUND_COMMAND_DONE)
            return
        play_sound(SOUND_COMMAND_END)
        return
    if execute_group_command(command):
        play_sound(SOUND_COMMAND_DONE)
        return
    log("❌ Команда не распознана")
    play_sound(SOUND_COMMAND_END)


def reset_mode():
    global command_mode, command_timer
    with command_mode_lock:
        command_mode = False
        command_timer = None
    log("Режим команды отключен")


def process_text(text, mic_id=None):
    global command_mode, command_timer
    if not text:
        return

    src = f" [mic{mic_id}]" if mic_id is not None else ""
    log(f"\n📝 Vosk{src}: '{text}'")

    cmd, has_wake = strip_wake_word(text)
    wake_detected, wake_type = is_wake_word(text)

    if cmd and wake_detected:
        dup, prev, score = is_duplicate_command(cmd)
        if dup:
            log(f"   🔁 Дубликат команды от mic{mic_id} "
                f"(fuzz {score:.1f}, prev='{prev}'), игнорируем")
            return

    with command_mode_lock:
        if wake_detected:
            if command_timer:
                command_timer.cancel()
            log(f"  🎯 Wake: {wake_type}")
            play_sound(SOUND_WAKE)
            command_mode = True

            if cmd:
                log(f"Активация! Команда: '{cmd}'")
            else:
                log(f"Активация! Жду команду...")

            if len(cmd) >= MIN_COMMAND_LENGTH:
                process_command(cmd)
                if command_timer:
                    command_timer.cancel()
                command_mode = False
                command_timer = None
            else:
                command_timer = threading.Timer(WAKE_TIMER, reset_mode)
                command_timer.daemon = True
                command_timer.start()

        elif command_mode:
            log(f"  📝 Команда: '{text}'")
            if len(text) >= MIN_COMMAND_LENGTH:
                process_command(text)
            if command_timer:
                command_timer.cancel()
            command_mode = False
            command_timer = None

# ==================== ADAPTIVE GAIN ====================

class AdaptiveGain:
    def __init__(self, target_amplitude=None, max_gain=None, min_gain=None,
                 smoothing=None, speech_threshold=None):
        self.target_amplitude = target_amplitude if target_amplitude is not None else GAIN_TARGET
        self.max_gain = max_gain if max_gain is not None else GAIN_MAX
        self.min_gain = min_gain if min_gain is not None else GAIN_MIN
        self.current_gain = 3.0
        self.smoothing = smoothing if smoothing is not None else GAIN_SMOOTHING
        self.speech_threshold = speech_threshold if speech_threshold is not None else GAIN_SPEECH_THRESHOLD
        self.calibration_factor = 1.0
        self.is_calibrated = False

    def calibrate(self, audio_chunk):
        if len(audio_chunk) == 0:
            return
        af = audio_chunk.astype(np.float64)
        avg = np.mean(np.abs(af))
        if 0 < avg < 100:
            self.calibration_factor = 300.0 / (avg + 1.0)
            self.calibration_factor = np.clip(self.calibration_factor, 1.0, 10.0)
            self.is_calibrated = True

    def calculate_gain(self, audio_chunk):
        if len(audio_chunk) == 0:
            return max(1, int(self.current_gain * self.calibration_factor))
        if not self.is_calibrated:
            self.calibrate(audio_chunk)
        af = audio_chunk.astype(np.float64)
        avg = np.mean(np.abs(af))
        peak = min(float(np.max(np.abs(af))), 32767.0)
        if avg > self.speech_threshold:
            target = self.target_amplitude / (avg + 1.0)
            target = np.clip(target, float(self.min_gain), float(self.max_gain))
            self.current_gain = self.smoothing * self.current_gain + (1.0 - self.smoothing) * target
        else:
            self.current_gain = self.current_gain * 0.99 if self.current_gain > 3.0 else 3.0
        final = self.current_gain * self.calibration_factor
        if peak > 0:
            final = min(final, 30000.0 / (peak + 1.0))
        final = np.clip(final, float(self.min_gain), float(self.max_gain * 2))
        return max(1, int(final))

# ==================== WORKER ====================

def make_worker(slot_id, stop_event, rec, rec_rate):
    vosk_rate = SAMPLERATE_VOSK
    gain = AdaptiveGain()

    CHUNK_SEC = 1.0
    src_chunk = int(rec_rate * CHUNK_SEC)
    overlap = int(rec_rate * 0.01)

    buf_chunks = []
    buf_len = [0]

    def worker():
        nonlocal buf_chunks
        while running and not stop_event.is_set():
            with mic_slots_lock:
                if slot_id >= len(mic_slots):
                    return
                q = mic_slots[slot_id].get("queue")
                stats = mic_slots[slot_id].get("stats")

            if q is None:
                time.sleep(0.1)
                continue

            try:
                data = q.get(timeout=0.2)
            except queue.Empty:
                continue

            try:
                chunk = np.frombuffer(data, dtype=np.int16)

                g = gain.calculate_gain(chunk)
                amplified = np.clip(chunk.astype(np.float32) * g, -32768, 32767).astype(np.int16)
                buf_chunks.append(amplified)
                buf_len[0] += len(amplified)

                while buf_len[0] >= src_chunk:
                    buf = np.concatenate(buf_chunks)
                    piece = buf[:src_chunk]
                    rest = buf[src_chunk - overlap:] if overlap > 0 else buf[src_chunk:]
                    buf_chunks = [rest]
                    buf_len[0] = len(rest)

                    if rec_rate != vosk_rate:
                        piece16 = resample_audio(piece, rec_rate, vosk_rate)
                    else:
                        piece16 = piece

                    if SHOW_MICS_LEVEL and len(piece16) > 0:
                        now = time.time()
                        last = _last_level_log.get(slot_id, 0.0)
                        if now - last >= LEVEL_LOG_INTERVAL:
                            _last_level_log[slot_id] = now
                            arr = piece16.astype(np.float64)
                            peak = int(np.max(np.abs(arr))) if len(arr) else 0
                            rms = int(np.sqrt(np.mean(arr * arr))) if len(arr) else 0
                            pct = 100.0 * peak / 32767.0
                            bar_len = int(pct / 2)
                            bar = "#" * bar_len + "." * (50 - bar_len)
                            log(f"📈 [mic{slot_id}] peak={peak:5d} ({pct:5.1f}%) "
                                f"rms={rms:5d} |{bar}|")

                    if rec.AcceptWaveform(piece16.tobytes()):
                        result = json.loads(rec.Result())
                        text = result.get('text', '').strip().lower()
                        if text:
                            process_text(text, slot_id)

                if (LOG_BLOCKS and stats is not None
                        and stats["blocks"] % 500 == 0 and stats["blocks"] > 0):
                    elapsed = time.time() - stats["t_start"]
                    actual = stats["samples"] / rec_rate
                    lost_pct = max(0.0, (1.0 - actual / elapsed) * 100.0) if elapsed > 0 else 0.0
                    log(f"📊 [mic{slot_id}] blocks={stats['blocks']} "
                        f"audio={actual:.2f}s wall={elapsed:.2f}s lost≈{lost_pct:.1f}%")
            except Exception as e:
                log(f"❌ worker mic{slot_id}: {e}")
                import traceback
                traceback.print_exc()

    return worker

# ==================== УПРАВЛЕНИЕ СЛОТАМИ ====================

def start_arecord_slot(slot_id, spec, vocab_json):
    dev = spec['dev']
    fmt = spec['fmt']
    channels = spec['channels']
    rate = spec['rate']
    width = spec['width']

    frame_bytes = width * channels
    block_frames = 1024
    block_bytes = frame_bytes * block_frames

    with mic_slots_lock:
        while len(mic_slots) <= slot_id:
            mic_slots.append({})
        slot = mic_slots[slot_id]
        slot["slot"] = slot_id
        slot["dev_index"] = -1
        slot["dev_name"] = spec['desc']
        slot["rec_rate"] = rate
        slot["blocksize"] = block_frames
        slot["queue"] = queue.Queue(maxsize=200)
        slot["stop_event"] = threading.Event()
        slot["stats"] = {"blocks": 0, "samples": 0, "t_start": time.time()}
        slot["_is_seeed"] = spec['is_seeed']
        slot["_is_arecord"] = True
        slot["_arecord_dev"] = dev
        slot["_arecord_fmt"] = fmt
        slot["_arecord_channels"] = channels
        slot["_arecord_width"] = width
        slot["_vocab_json"] = vocab_json
        slot["proc"] = None

    if USE_VOCABULARY:
        rec = vosk.KaldiRecognizer(model, SAMPLERATE_VOSK, vocab_json)
    else:
        rec = vosk.KaldiRecognizer(model, SAMPLERATE_VOSK)
    rec.SetWords(True)

    with mic_slots_lock:
        mic_slots[slot_id]["rec"] = rec

    stop_event = mic_slots[slot_id]["stop_event"]

    log(
        f"\n🎤 [mic{slot_id}] {spec['desc']}\n"
        f"   {dev}, {fmt}, {channels}ch, {rate} Гц"
    )

    def reader():
        cmd = [
            "arecord", "-q", "-D", dev,
            "-f", fmt, "-r", str(rate),
            "-c", str(channels), "-t", "raw",
        ]
        last_warn = [0.0]
        last_err = [""]
        while running and not stop_event.is_set():
            try:
                proc = subprocess.Popen(
                    cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                )
            except Exception as e:
                log(f"❌ [mic{slot_id}] arecord: {e}")
                time.sleep(1)
                continue

            with mic_slots_lock:
                if slot_id < len(mic_slots):
                    mic_slots[slot_id]["proc"] = proc

            try:
                while running and not stop_event.is_set():
                    raw = proc.stdout.read(block_bytes)
                    if not raw:
                        break
                    n_frames = len(raw) // frame_bytes
                    if n_frames == 0:
                        continue
                    raw = raw[:n_frames * frame_bytes]
                    if width == 4:
                        arr = np.frombuffer(raw, dtype=np.int32).reshape(-1, channels)
                        mono = arr[:, 0]
                        pcm16 = np.clip(mono >> 16, -32768, 32767).astype(np.int16)
                    else:
                        arr = np.frombuffer(raw, dtype=np.int16).reshape(-1, channels)
                        mono = arr[:, 0]
                        pcm16 = mono.astype(np.int16)

                    with mic_slots_lock:
                        if slot_id >= len(mic_slots):
                            break
                        q = mic_slots[slot_id].get("queue")
                        stats = mic_slots[slot_id].get("stats")

                    if q is None:
                        break
                    try:
                        q.put_nowait(pcm16.tobytes())
                    except queue.Full:
                        pass
                    if stats is not None:
                        stats["blocks"] += 1
                        stats["samples"] += len(pcm16)
            finally:
                try:
                    proc.terminate()
                    proc.wait(timeout=1)
                except Exception:
                    try:
                        proc.kill()
                    except Exception:
                        pass
                try:
                    err = proc.stderr.read().decode(errors='replace').strip()
                except Exception:
                    err = ""

            rc = proc.returncode
            if err and err != last_err[0]:
                last_err[0] = err
                log(f"❌ [mic{slot_id}] arecord rc={rc}: {err}")

            with mic_slots_lock:
                if slot_id < len(mic_slots):
                    mic_slots[slot_id]["proc"] = None

            if running and not stop_event.is_set():
                current = [d for d in detect_arecord_devices() if d['dev'] == dev]
                if not current:
                    log(f"⚠️ [mic{slot_id}] {dev} пропал из arecord -l, ждём "
                        f"{ARECORD_MISSING_DEV_WAIT_SEC:.0f}с...")
                    time.sleep(ARECORD_MISSING_DEV_WAIT_SEC)
                    continue

                now = time.time()
                if now - last_warn[0] >= ARECORD_RESTART_WARN_SEC:
                    last_warn[0] = now
                    log(f"⚠️ [mic{slot_id}] arecord завершился (rc={rc}), перезапуск...")
                time.sleep(1)

    reader_thread = threading.Thread(target=reader, daemon=True,
                                     name=f"arecord-reader-{slot_id}")
    reader_thread.start()

    worker_thread = threading.Thread(
        target=make_worker(slot_id, stop_event, rec, rate),
        daemon=True, name=f"mic-worker-{slot_id}",
    )
    worker_thread.start()

    with mic_slots_lock:
        mic_slots[slot_id]["worker_thread"] = worker_thread
        mic_slots[slot_id]["reader_thread"] = reader_thread
        mic_slots[slot_id]["stream"] = "arecord"

    log(f"   ✅ [mic{slot_id}] arecord запущен")
    return True


def stop_mic_slot(slot_id):
    with mic_slots_lock:
        if slot_id >= len(mic_slots):
            return
        slot = mic_slots[slot_id]
        stop_event = slot.get("stop_event")
        proc = slot.get("proc")

    if stop_event:
        stop_event.set()

    if proc is not None:
        try:
            proc.terminate()
            proc.wait(timeout=1)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass

    with mic_slots_lock:
        if slot_id < len(mic_slots):
            mic_slots[slot_id]["stream"] = None
            mic_slots[slot_id]["worker_thread"] = None
            mic_slots[slot_id]["reader_thread"] = None
            mic_slots[slot_id]["proc"] = None


def restart_mic_slot(slot_id):
    with mic_slots_lock:
        if slot_id >= len(mic_slots):
            return False
        slot = mic_slots[slot_id]
        vocab_json = slot.get("_vocab_json")
        arecord_spec = {
            'dev': slot.get("_arecord_dev"),
            'fmt': slot.get("_arecord_fmt"),
            'channels': slot.get("_arecord_channels"),
            'rate': slot.get("rec_rate"),
            'width': slot.get("_arecord_width"),
            'desc': slot.get("dev_name"),
            'is_seeed': slot.get("_is_seeed", False),
        }

    stop_mic_slot(slot_id)
    time.sleep(0.5)

    current = [d for d in detect_arecord_devices() if d['dev'] == arecord_spec['dev']]
    if not current:
        log(f"🚨 [mic{slot_id}] {arecord_spec['dev']} пропал из arecord -l")
        return False

    log(f"🔄 [mic{slot_id}] перезапуск arecord {arecord_spec['dev']}")
    return start_arecord_slot(slot_id, arecord_spec, vocab_json)


def device_monitor():
    CHECK_INTERVAL = 5
    while running:
        for _ in range(CHECK_INTERVAL * 10):
            if not running:
                return
            time.sleep(0.1)

        with mic_slots_lock:
            slots_snapshot = list(enumerate(mic_slots))

        for slot_id, slot in slots_snapshot:
            if not slot:
                continue

            stats = slot.get("stats")
            stream_marker = slot.get("stream")

            if stats is not None and stream_marker is not None:
                now = time.time()
                prev_blocks, prev_time = _last_blocks.get(slot_id, (stats["blocks"], now))
                if stats["blocks"] == prev_blocks and now - prev_time >= SLOT_STALL_SEC:
                    log(f"🚨 [mic{slot_id}] blocks не растут {now - prev_time:.0f}с "
                        f"(blocks={stats['blocks']}) — перезапуск...")
                    _last_blocks[slot_id] = (stats["blocks"], now)
                    restart_mic_slot(slot_id)
                    continue
                else:
                    _last_blocks[slot_id] = (stats["blocks"], now)

            reader_thread = slot.get("reader_thread")
            if stream_marker is not None and (reader_thread is None or not reader_thread.is_alive()):
                log(f"🚨 [mic{slot_id}] arecord-reader умер — перезапуск...")
                restart_mic_slot(slot_id)

# ==================== ОСНОВНОЙ ЦИКЛ ====================

def voice_listener():
    global running

    try:
        log(
            "\n" + "=" * 60 + "\n"
            "🎙️ ИНИЦИАЛИЗАЦИЯ МИКРОФОНОВ\n"
            + "=" * 60
        )

        vocab_json = None
        if USE_VOCABULARY:
            log("\n🔧 Строим словарь Vosk...")
            vocab_json = build_vosk_vocabulary()
            log(f"📊 Словарь: {len(json.loads(vocab_json))} слов")

        slot_id = 0
        for item in mic_devices:
            if isinstance(item, dict):
                start_arecord_slot(slot_id, item, vocab_json)
                slot_id += 1
            else:
                log(f"⚠️ слот {item} (не dict) пропущен")
                slot_id += 1

        active = [s for s in mic_slots if s and s.get("stream") is not None]
        if not active:
            log("❌ Ни один микрофон не запустился")
            return

        if _subscribed_topics:
            lines = [f"\n📡 Подписка: {len(_subscribed_topics)} топиков"]
            for t in _subscribed_topics:
                lines.append(f"📡   {t}")
            log("\n".join(lines))

        monitor_thread = threading.Thread(target=device_monitor,
                                          daemon=True, name="device-monitor")
        monitor_thread.start()

        log(
            "\n" + "=" * 60 + "\n"
            f"🎙️ СЛУШАЮ С {len(active)} МИКРОФОНОВ\n"
            f"👋 Wake: {wake_list}\n"
            f"📱 Устройств: {len(devices)}\n"
            f"👥 Групп: {len(groups)}\n"
            f"🔁 Дедуп: {DEDUP_WINDOW}с, fuzz>={DEDUP_FUZZ} (только с wake)\n"
            f"🩺 Watchdog: blocks не растут {SLOT_STALL_SEC}с → рестарт\n"
            f"🔁 arecord restart warn: раз в {ARECORD_RESTART_WARN_SEC:.0f}с\n"
            + "=" * 60 + "\n"
        )

        while running:
            time.sleep(0.5)

    except Exception as e:
        log(f"❌ Ошибка voice_listener: {e}")
        import traceback
        traceback.print_exc()
    finally:
        stop_all_mics()


def stop_all_mics():
    with mic_slots_lock:
        count = len(mic_slots)
    for slot_id in range(count):
        stop_mic_slot(slot_id)
    try:
        sd.stop()
    except Exception:
        pass

# ==================== ОЧИСТКА ====================

def cleanup():
    global running, command_timer, model, mqtt_client

    running = False

    if command_timer:
        try:
            command_timer.cancel()
        except Exception:
            pass

    stop_all_mics()

    if sound_initialized:
        try:
            pygame.mixer.quit()
        except Exception:
            pass

    if mqtt_client:
        try:
            mqtt_client.loop_stop()
            mqtt_client.disconnect()
        except Exception:
            pass

    model = None
    log("\n✅ Завершено")

# ==================== АРГУМЕНТЫ ====================

def parse_arguments():
    global USE_VOCABULARY, INCLUDE_USB, LOG_BLOCKS, SHOW_MICS_LEVEL
    parser = argparse.ArgumentParser(
        description='Голосовой ассистент (arecord-путь для всех микрофонов)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Примеры:
  python3 main.py                      # АВТО: все capture-устройства через arecord
  python3 main.py --mics seeed         # только seeed (arecord)
  python3 main.py --mics arecord       # все через arecord
  python3 main.py --v                  # стандартный словарь Vosk
  python3 main.py --log-blocks         # статистика blocks
  python3 main.py --mics-level         # уровень звука в Vosk
        '''
    )
    parser.add_argument('--v', action='store_true',
                        help='Стандартный словарь Vosk')
    parser.add_argument('--all-mics', action='store_true',
                        help='Все входные устройства')
    parser.add_argument('--mics', type=str, default=None,
                        help='"seeed", "arecord" через запятую')
    parser.add_argument('--no-usb', action='store_true',
                        help='Не добавлять USB-микрофоны')
    parser.add_argument('--log-blocks', dest='log_blocks',
                        action='store_true', default=None,
                        help='Печатать статистику blocks/audio/wall/lost')
    parser.add_argument('--no-log-blocks', dest='log_blocks',
                        action='store_false',
                        help='Отключить статистику blocks')
    parser.add_argument('--mics-level', dest='mics_level',
                        action='store_true', default=False,
                        help='Показывать уровень звука, идущего в Vosk')
    args = parser.parse_args()

    USE_VOCABULARY = not args.v
    INCLUDE_USB = not args.no_usb
    SHOW_MICS_LEVEL = args.mics_level

    if args.log_blocks is not None:
        LOG_BLOCKS = args.log_blocks

    manual = None
    if args.mics:
        manual = []
        for x in args.mics.split(','):
            x = x.strip().lower()
            if not x:
                continue
            if x in ('seeed', 'arecord'):
                manual.append(x)
            else:
                log(f"❌ --mics: '{x}' — поддерживается только 'seeed'/'arecord'")
                sys.exit(1)

    mode = "СТАНДАРТНЫЙ СЛОВАРЬ" if args.v else "ОГРАНИЧЕННЫЙ СЛОВАРЬ"
    log(f"📚 Режим словаря: {mode}")
    log(f"📊 Лог blocks: {'ВКЛ' if LOG_BLOCKS else 'выкл'} "
        f"({'CLI' if args.log_blocks is not None else 'ini'})")
    log(f"📈 Уровень микрофонов: {'ВКЛ' if SHOW_MICS_LEVEL else 'выкл'}")
    if manual:
        log(f"🎯 Микрофоны (вручную): {manual}")
    else:
        log(f"🎯 Микрофоны: АВТО (все через arecord)")

    return manual, args.all_mics

# ==================== ЗАПУСК ====================

if __name__ == "__main__":
    manual_mics, use_all = parse_arguments()

    log("=" * 60)
    log("🚀 ЗАПУСК ГОЛОСОВОГО АССИСТЕНТА")
    log("=" * 60)

    try:
        devices = load_devices_from_js(CONFIG_JS_PATH)
        log(f"\n✅ Загружено {len(devices)} устройств")
    except Exception as e:
        log(f"❌ Ошибка загрузки устройств: {e}")
        sys.exit(1)

    mqtt_client.user_data_set({'devices': devices})

    try:
        from groups import groups as _groups
        groups = _groups
        log(f"✅ Загружено {len(groups)} групп")
    except ImportError:
        log("⚠️ groups.py не найден")
        groups = {}

    log("\n🔍 Поиск микрофонов...")
    mic_devices = detect_microphones(use_all=use_all, manual_indices=manual_mics)
    if not mic_devices:
        log("❌ Не найдено микрофонов")
        sys.exit(1)
    log(f"\n✅ Выбрано микрофонов: {len(mic_devices)}")
    for item in mic_devices:
        log(f"   • {describe_mic(item)}")

    atexit.register(cleanup)

    if mqtt_client:
        mqtt_client.loop_start()

    try:
        voice_listener()
    except KeyboardInterrupt:
        cleanup()
    except Exception as e:
        log(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        cleanup()

    sys.exit(0)
