module.exports = {
    mqtt: {
        host: "localhost",
        port: 1883,
        user: "qwe",
        password: "qwe"
    },
    https: {
        privateKey: "/etc/letsencrypt/live/qwe.ru/privkey.pem",
        certificate: "/etc/letsencrypt/live/qwe.ru/fullchain.pem",
        port: 443
    },
    clients: [
        {
            id: "1",
            name: "ID_qwe",
            clientId: "ID_qwe",
            clientSecret: "qwe",
            isTrusted: false
        }
    ],
    users: [
        {
            id: "1",
            username: "123@yandex.ru",
            password: "321",
            name: "123"
        }
    ],
    devices: [
        {
            id: "id_device_0",
            name: "Умный дом",
            room: "Зал",
            type: "devices.types.other",
            mqtt: [
                {
                    instance: "on",
                    set: "zigbee2mqtt/command/reboot",
                    state: "zigbee2mqtt/command/reboot"
                }
            ],
            valueMapping: [
                {
                    type: "on_off",
                    mapping: [
                        [
                            false,
                            true
                        ],
                        [
                            "off",
                            "on"
                        ]
                    ]
                }
            ],
            capabilities: [
                {
                    type: "devices.capabilities.on_off",
                    retrievable: true,
                    reportable: true
                }
            ]
        },
        {
            id: "id_device_1",
            name: "Контур",
            room: "Дом",
            type: "devices.types.light",
            mqtt: [
                {
                    instance: "on",
                    set: "input/light_z0_on_off",
                    state: "input/light_z0_on_off"
                },
                {
                    instance: "brightness",
                    set: "input/light_z0_brightness",
                    state: "input/light_z0_brightness"
                }
            ],
            valueMapping: [
                {
                    type: "on_off",
                    mapping: [
                        [
                            false,
                            true
                        ],
                        [
                            "off",
                            "on"
                        ]
                    ]
                }
            ],
            capabilities: [
                {
                    type: "devices.capabilities.on_off",
                    retrievable: true,
                    reportable: true,
                    state: {
                        instance: "on",
                        value: true
                    }
                },
                {
                    type: "devices.capabilities.range",
                    retrievable: true,
                    reportable: true,
                    parameters: {
                        instance: "brightness",
                        unit: "unit.percent",
                        range: {
                            min: 0,
                            max: 100,
                            precision: 10
                        }
                    },
                    state: {
                        instance: "brightness",
                        value: 100
                    }
                }
            ]
        },
        {
            id: "id_device_2",
            name: "Свет в прихожей",
            room: "Прихожая",
            type: "devices.types.light",
            mqtt: [
                {
                    instance: "on",
                    set: "input/light_z1_on_off",
                    state: "input/light_z1_on_off"
                },
                {
                    instance: "brightness",
                    set: "input/light_z1_brightness",
                    state: "input/light_z1_brightness"
                }
            ],
            valueMapping: [
                {
                    type: "on_off",
                    mapping: [
                        [
                            false,
                            true
                        ],
                        [
                            "off",
                            "on"
                        ]
                    ]
                }
            ],
            capabilities: [
                {
                    type: "devices.capabilities.on_off",
                    retrievable: true,
                    reportable: true,
                    state: {
                        instance: "on",
                        value: true
                    }
                },
                {
                    type: "devices.capabilities.range",
                    retrievable: true,
                    reportable: true,
                    parameters: {
                        instance: "brightness",
                        unit: "unit.percent",
                        range: {
                            min: 0,
                            max: 100,
                            precision: 10
                        }
                    },
                    state: {
                        instance: "brightness",
                        value: 100
                    }
                }
            ]
        },
        {
            id: "id_device_3",
            name: "Свет в зале",
            room: "Зал",
            type: "devices.types.light",
            mqtt: [
                {
                    instance: "on",
                    set: "input/light_z2_on_off",
                    state: "input/light_z2_on_off"
                },
                {
                    instance: "brightness",
                    set: "input/light_z2_brightness",
                    state: "input/light_z2_brightness"
                }
            ],
            valueMapping: [
                {
                    type: "on_off",
                    mapping: [
                        [
                            false,
                            true
                        ],
                        [
                            "off",
                            "on"
                        ]
                    ]
                }
            ],
            capabilities: [
                {
                    type: "devices.capabilities.on_off",
                    retrievable: true,
                    reportable: true,
                    state: {
                        instance: "on",
                        value: true
                    }
                },
                {
                    type: "devices.capabilities.range",
                    retrievable: true,
                    reportable: true,
                    parameters: {
                        instance: "brightness",
                        unit: "unit.percent",
                        range: {
                            min: 0,
                            max: 100,
                            precision: 10
                        }
                    },
                    state: {
                        instance: "brightness",
                        value: 100
                    }
                }
            ]
        },
        {
            id: "id_device_4",
            name: "Люстра",
            room: "Зал",
            type: "devices.types.light",
            mqtt: [
                {
                    instance: "on",
                    set: "input/light_z3_on_off",
                    state: "input/light_z3_on_off"
                },
                {
                    instance: "brightness",
                    set: "input/light_z3_brightness",
                    state: "input/light_z3_brightness"
                }
            ],
            valueMapping: [
                {
                    type: "on_off",
                    mapping: [
                        [
                            false,
                            true
                        ],
                        [
                            "off",
                            "on"
                        ]
                    ]
                }
            ],
            capabilities: [
                {
                    type: "devices.capabilities.on_off",
                    retrievable: true,
                    reportable: true,
                    state: {
                        instance: "on",
                        value: true
                    }
                },
                {
                    type: "devices.capabilities.range",
                    retrievable: true,
                    reportable: true,
                    parameters: {
                        instance: "brightness",
                        unit: "unit.percent",
                        range: {
                            min: 0,
                            max: 100,
                            precision: 10
                        }
                    },
                    state: {
                        instance: "brightness",
                        value: 100
                    }
                }
            ]
        },
        {
            id: "id_device_5",
            name: "Свет в кухне",
            room: "Кухня",
            type: "devices.types.light",
            mqtt: [
                {
                    instance: "on",
                    set: "input/light_z4_on_off",
                    state: "input/light_z4_on_off"
                },
                {
                    instance: "brightness",
                    set: "input/light_z4_brightness",
                    state: "input/light_z4_brightness"
                }
            ],
            valueMapping: [
                {
                    type: "on_off",
                    mapping: [
                        [
                            false,
                            true
                        ],
                        [
                            "off",
                            "on"
                        ]
                    ]
                }
            ],
            capabilities: [
                {
                    type: "devices.capabilities.on_off",
                    retrievable: true,
                    reportable: true,
                    state: {
                        instance: "on",
                        value: true
                    }
                },
                {
                    type: "devices.capabilities.range",
                    retrievable: true,
                    reportable: true,
                    parameters: {
                        instance: "brightness",
                        unit: "unit.percent",
                        range: {
                            min: 0,
                            max: 100,
                            precision: 10
                        }
                    },
                    state: {
                        instance: "brightness",
                        value: 100
                    }
                }
            ]
        },
        {
            id: "id_device_6",
            name: "Свет в ванной",
            room: "Ванная",
            type: "devices.types.light",
            mqtt: [
                {
                    instance: "on",
                    set: "zigbee2mqtt/9665. ВАННАЯ Свет/set",
                    state: "zigbee2mqtt/9665. ВАННАЯ Свет"
                }
            ],
            valueMapping: [
                {
                    type: "on_off",
                    mapping: [
                        [
                            false,
                            true
                        ],
                        [
                            "off",
                            "on"
                        ]
                    ]
                }
            ],
            capabilities: [
                {
                    type: "devices.capabilities.on_off",
                    retrievable: true,
                    reportable: true,
                    state: {
                        instance: "on",
                        value: true
                    }
                }
            ]
        },
        {
            id: "id_device_7",
            name: "Лампа в кухне",
            room: "Кухня",
            type: "devices.types.light",
            mqtt: [
                {
                    instance: "on",
                    set: "zigbee2mqtt/9d58. КУХНЯ Лампа/set",
                    state: "zigbee2mqtt/9d58. КУХНЯ Лампа"
                }
            ],
            valueMapping: [
                {
                    type: "on_off",
                    mapping: [
                        [
                            false,
                            true
                        ],
                        [
                            "OFF",
                            "ON"
                        ]
                    ]
                }
            ],
            capabilities: [
                {
                    type: "devices.capabilities.on_off",
                    retrievable: true,
                    reportable: true,
                    state: {
                        instance: "on",
                        value: true
                    }
                }
            ]
        },
        {
            id: "id_device_8",
            name: "Свет в нише",
            room: "Ниша",
            type: "devices.types.light",
            mqtt: [
                {
                    instance: "on",
                    set: "zigbee2mqtt/ebe3. НИША Свет/set",
                    state: "zigbee2mqtt/ebe3. НИША Свет"
                }
            ],
            valueMapping: [
                {
                    type: "on_off",
                    mapping: [
                        [
                            false,
                            true
                        ],
                        [
                            "OFF",
                            "ON"
                        ]
                    ]
                }
            ],
            capabilities: [
                {
                    type: "devices.capabilities.on_off",
                    retrievable: true,
                    reportable: true,
                    state: {
                        instance: "on",
                        value: true
                    }
                }
            ]
        },
        {
            id: "id_device_9",
            name: "Штора слева",
            room: "Зал",
            type: "devices.types.openable",
            mqtt: [
                {
                    instance: "on",
                    set: "zigbee2mqtt/8e8a. ЗАЛ Штора слева/set",
                    state: "zigbee2mqtt/8e8a. ЗАЛ Штора слева/state"
                }
            ],
            valueMapping: [
                {
                    type: "on_off",
                    mapping: [
                        [
                            false,
                            true
                        ],
                        [
                            "close",
                            "open"
                        ]
                    ]
                }
            ],
            capabilities: [
                {
                    type: "devices.capabilities.on_off",
                    retrievable: true,
                    reportable: true
                }
            ]
        },
        {
            id: "id_device_10",
            name: "Штора в центре",
            room: "Зал",
            type: "devices.types.openable",
            mqtt: [
                {
                    instance: "on",
                    set: "zigbee2mqtt/d38e. ЗАЛ Штора в центре/set",
                    state: "zigbee2mqtt/d38e. ЗАЛ Штора в центре/state"
                }
            ],
            valueMapping: [
                {
                    type: "on_off",
                    mapping: [
                        [
                            false,
                            true
                        ],
                        [
                            "close",
                            "open"
                        ]
                    ]
                }
            ],
            capabilities: [
                {
                    type: "devices.capabilities.on_off",
                    retrievable: true,
                    reportable: true
                }
            ]
        },
        {
            id: "id_device_11",
            name: "Штора справа",
            room: "Зал",
            type: "devices.types.openable",
            mqtt: [
                {
                    instance: "on",
                    set: "zigbee2mqtt/cfa4. ЗАЛ Штора справа/set",
                    state: "zigbee2mqtt/cfa4. ЗАЛ Штора справа/state"
                }
            ],
            valueMapping: [
                {
                    type: "on_off",
                    mapping: [
                        [
                            false,
                            true
                        ],
                        [
                            "close",
                            "open"
                        ]
                    ]
                }
            ],
            capabilities: [
                {
                    type: "devices.capabilities.on_off",
                    retrievable: true,
                    reportable: true
                }
            ]
        },
        {
            id: "id_device_12",
            name: "Датчик освещения, температуры и влажности",
            room: "Кухня",
            type: "devices.types.sensor",
            mqtt: [
                {
                    instance: "temperature",
                    state: "zigbee2mqtt/bc8b. КУХНЯ Датчик Температуры, освещения и влажности/temperature"
                },
                {
                    instance: "humidity",
                    state: "zigbee2mqtt/bc8b. КУХНЯ Датчик Температуры, освещения и влажности/humidity"
                },
                {
                    instance: "illumination",
                    state: "zigbee2mqtt/bc8b. КУХНЯ Датчик Температуры, освещения и влажности/illuminance_lux"
                },
                {
                    instance: "battery_level",
                    state: "zigbee2mqtt/bc8b. КУХНЯ Датчик Температуры, освещения и влажности/battery"
                }
            ],
            properties: [
                {
                    type: "devices.properties.float",
                    retrievable: true,
                    reportable: true,
                    parameters: {
                        instance: "temperature",
                        unit: "unit.temperature.celsius"
                    }
                },
                {
                    type: "devices.properties.float",
                    retrievable: true,
                    reportable: true,
                    parameters: {
                        instance: "humidity",
                        unit: "unit.percent"
                    }
                },
                {
                    type: "devices.properties.float",
                    retrievable: true,
                    reportable: true,
                    parameters: {
                        instance: "illumination",
                        unit: "unit.illumination.lux"
                    }
                },
                {
                    type: "devices.properties.float",
                    retrievable: true,
                    reportable: true,
                    parameters: {
                        instance: "battery_level",
                        unit: "unit.percent"
                    }
                }
            ]
        },
        {
            id: "id_device_13",
            name: "Датчик протечки",
            room: "Ванная",
            type: "devices.types.sensor",
            mqtt: [
                {
                    instance: "water_leak",
                    state: "zigbee2mqtt/7526. ВАННАЯ Датчик протечки/water_leak"
                },
                {
                    instance: "temperature",
                    state: "zigbee2mqtt/7526. ВАННАЯ Датчик протечки/device_temperature"
                },
                {
                    instance: "battery_level",
                    state: "zigbee2mqtt/7526. ВАННАЯ Датчик протечки/battery"
                }
            ],
            valueMapping: [
                {
                    type: "event",
                    mapping: [
                        [
                            "dry",
                            "leak"
                        ],
                        [
                            "false",
                            "true"
                        ]
                    ]
                }
            ],
            properties: [
                {
                    type: "devices.properties.event",
                    retrievable: true,
                    reportable: true,
                    parameters: {
                        instance: "water_leak",
                        events: [
                            {
                                value: "dry"
                            },
                            {
                                value: "leak"
                            }
                        ]
                    }
                },
                {
                    type: "devices.properties.float",
                    retrievable: true,
                    reportable: true,
                    parameters: {
                        instance: "temperature",
                        unit: "unit.temperature.celsius"
                    }
                },
                {
                    type: "devices.properties.float",
                    retrievable: true,
                    reportable: true,
                    parameters: {
                        instance: "battery_level",
                        unit: "unit.percent"
                    }
                }
            ]
        },
        {
            id: "id_device_14",
            name: "Датчик протечки",
            room: "Ванная",
            type: "devices.types.sensor",
            mqtt: [
                {
                    instance: "water_leak",
                    state: "zigbee2mqtt/7526. ВАННАЯ Датчик протечки/water_leak"
                },
                {
                    instance: "temperature",
                    state: "zigbee2mqtt/7526. ВАННАЯ Датчик протечки/device_temperature"
                },
                {
                    instance: "battery_level",
                    state: "zigbee2mqtt/7526. ВАННАЯ Датчик протечки/battery"
                }
            ],
            valueMapping: [
                {
                    type: "event",
                    mapping: [
                        [
                            "dry",
                            "leak"
                        ],
                        [
                            "false",
                            "true"
                        ]
                    ]
                }
            ],
            properties: [
                {
                    type: "devices.properties.event",
                    retrievable: true,
                    reportable: true,
                    parameters: {
                        instance: "water_leak",
                        events: [
                            {
                                value: "dry"
                            },
                            {
                                value: "leak"
                            }
                        ]
                    }
                },
                {
                    type: "devices.properties.float",
                    retrievable: true,
                    reportable: true,
                    parameters: {
                        instance: "temperature",
                        unit: "unit.temperature.celsius"
                    }
                },
                {
                    type: "devices.properties.float",
                    retrievable: true,
                    reportable: true,
                    parameters: {
                        instance: "battery_level",
                        unit: "unit.percent"
                    }
                }
            ]
        },
        {
            id: "id_device_15",
            name: "Пол",
            room: "Зал",
            type: "devices.types.thermostat",
            mqtt: [
                {
                    instance: "on",
                    set: "zigbee2mqtt/e945. ЗАЛ Теплый пол/heat",
                    state: "zigbee2mqtt/e945. ЗАЛ Теплый пол/heat"
                },
                {
                    instance: "temperature",
                    set: "zigbee2mqtt/e945. ЗАЛ Теплый пол/current_heating_setpoint",
                    state: "zigbee2mqtt/e945. ЗАЛ Теплый пол/current_heating_setpoint"
                }
            ],
            valueMapping: [
                {
                    type: "on_off",
                    mapping: [
                        [
                            false,
                            true
                        ],
                        [
                            "off",
                            "on"
                        ]
                    ]
                }
            ],
            capabilities: [
                {
                    type: "devices.capabilities.on_off",
                    retrievable: true,
                    reportable: true,
                    state: {
                        instance: "on",
                        value: true
                    }
                },
                {
                    type: "devices.capabilities.range",
                    retrievable: true,
                    reportable: true,
                    parameters: {
                        instance: "temperature",
                        unit: "unit.temperature.celsius",
                        range: {
                            min: 0,
                            max: 35,
                            precision: 1
                        }
                    },
                    state: {
                        instance: "temperature",
                        value: 35
                    }
                }
            ]
        },
        {
            id: "id_device_16",
            name: "Детектор дыма",
            room: "Зал",
            type: "devices.types.sensor",
            mqtt: [
                {
                    instance: "smoke",
                    state: "zigbee2mqtt/fdb4. ЗАЛ Детектор дыма/smoke"
                },
                {
                    instance: "battery_level",
                    state: "zigbee2mqtt/fdb4. ЗАЛ Детектор дыма/battery"
                }
            ],
            valueMapping: [
                {
                    type: "event",
                    mapping: [
                        [
                            "not_detected",
                            "detected"
                        ],
                        [
                            "false",
                            "true"
                        ]
                    ]
                }
            ],
            properties: [
                {
                    type: "devices.properties.event",
                    retrievable: true,
                    reportable: true,
                    parameters: {
                        instance: "smoke",
                        events: [
                            {
                                value: "not_detected"
                            },
                            {
                                value: "detected"
                            }
                        ]
                    }
                },
                {
                    type: "devices.properties.float",
                    retrievable: true,
                    reportable: true,
                    parameters: {
                        instance: "battery_level",
                        unit: "unit.percent"
                    }
                }
            ]
        },
        {
            id: "id_device_17",
            name: "Датчик открытия двери",
            room: "Прихожая",
            type: "devices.types.sensor",
            mqtt: [
                {
                    instance: "open",
                    state: "zigbee2mqtt/8968. ПРИХОЖАЯ Датчик открытия двери/contact"
                },
                {
                    instance: "battery_level",
                    state: "zigbee2mqtt/8968. ПРИХОЖАЯ Датчик открытия двери/battery"
                }
            ],
            valueMapping: [
                {
                    type: "event",
                    mapping: [
                        [
                            "opened",
                            "closed"
                        ],
                        [
                            "false",
                            "true"
                        ]
                    ]
                }
            ],
            properties: [
                {
                    type: "devices.properties.event",
                    retrievable: true,
                    reportable: true,
                    parameters: {
                        instance: "open",
                        events: [
                            {
                                value: "opened"
                            },
                            {
                                value: "closed"
                            }
                        ]
                    }
                },
                {
                    type: "devices.properties.float",
                    retrievable: true,
                    reportable: true,
                    parameters: {
                        instance: "battery_level",
                        unit: "unit.percent"
                    }
                }
            ]
        },
        {
            id: "id_device_18",
            name: "Клапан горячей воды",
            room: "Ванная",
            type: "devices.types.openable",
            mqtt: [
                {
                    instance: "on",
                    set: "zigbee2mqtt/639b. ВАННАЯ Клапан горячей воды/set",
                    state: "zigbee2mqtt/639b. ВАННАЯ Клапан горячей воды/state"
                }
            ],
            valueMapping: [
                {
                    type: "on_off",
                    mapping: [
                        [
                            false,
                            true
                        ],
                        [
                            "OFF",
                            "ON"
                        ]
                    ]
                }
            ],
            capabilities: [
                {
                    type: "devices.capabilities.on_off",
                    retrievable: true,
                    reportable: true
                }
            ]
        },
        {
            id: "id_device_19",
            name: "Клапан холодной воды",
            room: "Ванная",
            type: "devices.types.openable",
            mqtt: [
                {
                    instance: "on",
                    set: "zigbee2mqtt/37cf. ВАННАЯ Клапан холодной воды/set",
                    state: "zigbee2mqtt/37cf. ВАННАЯ Клапан холодной воды/state"
                }
            ],
            valueMapping: [
                {
                    type: "on_off",
                    mapping: [
                        [
                            false,
                            true
                        ],
                        [
                            "OFF",
                            "ON"
                        ]
                    ]
                }
            ],
            capabilities: [
                {
                    type: "devices.capabilities.on_off",
                    retrievable: true,
                    reportable: true
                }
            ]
        },
        {
            id: "id_device_20",
            name: "Датчик окна в кухне",
            room: "Кухня",
            type: "devices.types.sensor",
            mqtt: [
                {
                    instance: "open",
                    state: "zigbee2mqtt/9873. КУХНЯ Датчик открытия окна/contact"
                },
                {
                    instance: "battery_level",
                    state: "zigbee2mqtt/9873. КУХНЯ Датчик открытия окна/battery"
                }
            ],
            valueMapping: [
                {
                    type: "event",
                    mapping: [
                        [
                            "opened",
                            "closed"
                        ],
                        [
                            "false",
                            "true"
                        ]
                    ]
                }
            ],
            properties: [
                {
                    type: "devices.properties.event",
                    retrievable: true,
                    reportable: true,
                    parameters: {
                        instance: "open",
                        events: [
                            {
                                value: "opened"
                            },
                            {
                                value: "closed"
                            }
                        ]
                    }
                },
                {
                    type: "devices.properties.float",
                    retrievable: true,
                    reportable: true,
                    parameters: {
                        instance: "battery_level",
                        unit: "unit.percent"
                    }
                }
            ]
        },
        {
            id: "id_device_21",
            name: "Датчик окна в зале",
            room: "Зал",
            type: "devices.types.sensor",
            mqtt: [
                {
                    instance: "open",
                    state: "zigbee2mqtt/b20b. ЗАЛ Датчик открытия окна/contact"
                },
                {
                    instance: "battery_level",
                    state: "zigbee2mqtt/b20b. ЗАЛ Датчик открытия окна/battery"
                }
            ],
            valueMapping: [
                {
                    type: "event",
                    mapping: [
                        [
                            "opened",
                            "closed"
                        ],
                        [
                            "false",
                            "true"
                        ]
                    ]
                }
            ],
            properties: [
                {
                    type: "devices.properties.event",
                    retrievable: true,
                    reportable: true,
                    parameters: {
                        instance: "open",
                        events: [
                            {
                                value: "opened"
                            },
                            {
                                value: "closed"
                            }
                        ]
                    }
                },
                {
                    type: "devices.properties.float",
                    retrievable: true,
                    reportable: true,
                    parameters: {
                        instance: "battery_level",
                        unit: "unit.percent"
                    }
                }
            ]
        },
        {
            id: "id_device_22",
            name: "Умная розетка",
            room: "Зал",
            type: "devices.types.socket",
            mqtt: [
                {
                    instance: "on",
                    set: "zigbee2mqtt/e4ee. ЗАЛ Умная розетка/set",
                    state: "zigbee2mqtt/e4ee. ЗАЛ Умная розетка/state"
                },
                {
                    instance: "power",
                    state: "zigbee2mqtt/e4ee. ЗАЛ Умная розетка/power"
                },
                {
                    instance: "voltage",
                    state: "zigbee2mqtt/e4ee. ЗАЛ Умная розетка/voltage"
                },
                {
                    instance: "amperage",
                    state: "zigbee2mqtt/e4ee. ЗАЛ Умная розетка/current"
                }
            ],
            valueMapping: [
                {
                    type: "on_off",
                    mapping: [
                        [
                            false,
                            true
                        ],
                        [
                            "off",
                            "on"
                        ]
                    ]
                }
            ],
            capabilities: [
                {
                    type: "devices.capabilities.on_off",
                    retrievable: true,
                    reportable: true
                }
            ],
            properties: [
                {
                    type: "devices.properties.float",
                    retrievable: true,
                    reportable: true,
                    parameters: {
                        instance: "power",
                        unit: "unit.watt"
                    }
                },
                {
                    type: "devices.properties.float",
                    retrievable: true,
                    reportable: true,
                    parameters: {
                        instance: "voltage",
                        unit: "unit.volt"
                    }
                },
                {
                    type: "devices.properties.float",
                    retrievable: true,
                    reportable: true,
                    parameters: {
                        instance: "amperage",
                        unit: "unit.ampere"
                    }
                }
            ]
        },
        {
            id: "id_device_23",
            name: "Датчик протечки",
            room: "Кухня",
            type: "devices.types.sensor",
            mqtt: [
                {
                    instance: "water_leak",
                    state: "zigbee2mqtt/2235. КУХНЯ Датчик протечки/water_leak"
                },
                {
                    instance: "temperature",
                    state: "zigbee2mqtt/2235. КУХНЯ Датчик протечки/device_temperature"
                },
                {
                    instance: "battery_level",
                    state: "zigbee2mqtt/2235. КУХНЯ Датчик протечки/battery"
                }
            ],
            valueMapping: [
                {
                    type: "event",
                    mapping: [
                        [
                            "dry",
                            "leak"
                        ],
                        [
                            "false",
                            "true"
                        ]
                    ]
                }
            ],
            properties: [
                {
                    type: "devices.properties.event",
                    retrievable: true,
                    reportable: true,
                    parameters: {
                        instance: "water_leak",
                        events: [
                            {
                                value: "dry"
                            },
                            {
                                value: "leak"
                            }
                        ]
                    }
                },
                {
                    type: "devices.properties.float",
                    retrievable: true,
                    reportable: true,
                    parameters: {
                        instance: "temperature",
                        unit: "unit.temperature.celsius"
                    }
                },
                {
                    type: "devices.properties.float",
                    retrievable: true,
                    reportable: true,
                    parameters: {
                        instance: "battery_level",
                        unit: "unit.percent"
                    }
                }
            ]
        },
        {
            id: "id_device_24",
            name: "Датчик протечки",
            room: "Кухня",
            type: "devices.types.sensor",
            mqtt: [
                {
                    instance: "water_leak",
                    state: "zigbee2mqtt/2235. КУХНЯ Датчик протечки/water_leak"
                },
                {
                    instance: "temperature",
                    state: "zigbee2mqtt/2235. КУХНЯ Датчик протечки/device_temperature"
                },
                {
                    instance: "battery_level",
                    state: "zigbee2mqtt/2235. КУХНЯ Датчик протечки/battery"
                }
            ],
            valueMapping: [
                {
                    type: "event",
                    mapping: [
                        [
                            "dry",
                            "leak"
                        ],
                        [
                            "false",
                            "true"
                        ]
                    ]
                }
            ],
            properties: [
                {
                    type: "devices.properties.event",
                    retrievable: true,
                    reportable: true,
                    parameters: {
                        instance: "water_leak",
                        events: [
                            {
                                value: "dry"
                            },
                            {
                                value: "leak"
                            }
                        ]
                    }
                },
                {
                    type: "devices.properties.float",
                    retrievable: true,
                    reportable: true,
                    parameters: {
                        instance: "temperature",
                        unit: "unit.temperature.celsius"
                    }
                },
                {
                    type: "devices.properties.float",
                    retrievable: true,
                    reportable: true,
                    parameters: {
                        instance: "battery_level",
                        unit: "unit.percent"
                    }
                }
            ]
        },
        {
            id: "id_device_25",
            name: "Штора слева",
            room: "Кухня",
            type: "devices.types.openable",
            mqtt: [
                {
                    instance: "on",
                    set: "zigbee2mqtt/4d83. КУХНЯ Штора слева/set",
                    state: "zigbee2mqtt/4d83. КУХНЯ Штора слева/state"
                }
            ],
            valueMapping: [
                {
                    type: "on_off",
                    mapping: [
                        [
                            false,
                            true
                        ],
                        [
                            "close",
                            "open"
                        ]
                    ]
                }
            ],
            capabilities: [
                {
                    type: "devices.capabilities.on_off",
                    retrievable: true,
                    reportable: true
                }
            ]
        },
        {
            id: "id_device_26",
            name: "Штора справа",
            room: "Кухня",
            type: "devices.types.openable",
            mqtt: [
                {
                    instance: "on",
                    set: "zigbee2mqtt/29c6. КУХНЯ Штора справа/set",
                    state: "zigbee2mqtt/29c6. КУХНЯ Штора справа/state"
                }
            ],
            valueMapping: [
                {
                    type: "on_off",
                    mapping: [
                        [
                            false,
                            true
                        ],
                        [
                            "close",
                            "open"
                        ]
                    ]
                }
            ],
            capabilities: [
                {
                    type: "devices.capabilities.on_off",
                    retrievable: true,
                    reportable: true
                }
            ]
        },
        {
            id: "id_device_27",
            name: "Датчик температуры и влажности",
            room: "Кухня",
            type: "devices.types.sensor",
            mqtt: [
                {
                    instance: "temperature",
                    state: "zigbee2mqtt/7704. КУХНЯ Датчик температуры и влажности/temperature"
                },
                {
                    instance: "humidity",
                    state: "zigbee2mqtt/7704. КУХНЯ Датчик температуры и влажности/humidity"
                },
                {
                    instance: "battery_level",
                    state: "zigbee2mqtt/7704. КУХНЯ Датчик температуры и влажности/battery"
                }
            ],
            properties: [
                {
                    type: "devices.properties.float",
                    retrievable: true,
                    reportable: true,
                    parameters: {
                        instance: "temperature",
                        unit: "unit.temperature.celsius"
                    }
                },
                {
                    type: "devices.properties.float",
                    retrievable: true,
                    reportable: true,
                    parameters: {
                        instance: "humidity",
                        unit: "unit.percent"
                    }
                },
                {
                    type: "devices.properties.float",
                    retrievable: true,
                    reportable: true,
                    parameters: {
                        instance: "battery_level",
                        unit: "unit.percent"
                    }
                }
            ]
        },
        {
            id: "id_device_28",
            name: "Датчик температуры и влажности",
            room: "Кухня",
            type: "devices.types.sensor",
            mqtt: [
                {
                    instance: "temperature",
                    state: "zigbee2mqtt/12c2. ЗАЛ Датчик температуры и влажности/temperature"
                },
                {
                    instance: "humidity",
                    state: "zigbee2mqtt/12c2. ЗАЛ Датчик температуры и влажности/humidity"
                },
                {
                    instance: "battery_level",
                    state: "zigbee2mqtt/12c2. ЗАЛ Датчик температуры и влажности/battery"
                }
            ],
            properties: [
                {
                    type: "devices.properties.float",
                    retrievable: true,
                    reportable: true,
                    parameters: {
                        instance: "temperature",
                        unit: "unit.temperature.celsius"
                    }
                },
                {
                    type: "devices.properties.float",
                    retrievable: true,
                    reportable: true,
                    parameters: {
                        instance: "humidity",
                        unit: "unit.percent"
                    }
                },
                {
                    type: "devices.properties.float",
                    retrievable: true,
                    reportable: true,
                    parameters: {
                        instance: "battery_level",
                        unit: "unit.percent"
                    }
                }
            ]
        }
    ]
};
