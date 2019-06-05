meta:
  id: usb4715_port
  title: Microchip USB4715 Port Status Registers
types:
  power_status:
    doc-ref: Table 3-52
    doc: Read only register.  Returns State of Port Power Enables.
    seq:
      - id: reserved1
        type: b3
      - id: port4
        type: b1
      - id: port3
        type: b1
      - id: port2
        type: b1
      - id: port1
        type: b1
      - id: reserved2
        type: b1
  remap12:
    doc-ref: Table 3-56
    doc: Writes to this register are disabled unless PRTMAP_EN bit in HUB_CFG_3 is set.
    seq:
      - id: port2
        type: b4
      - id: port1
        type: b4
  remap34:
    doc-ref: Table 3-57
    doc: Writes to this register are disabled unless PRTMAP_EN bit in HUB_CFG_3 is set.
    seq:
      - id: port4
        type: b4
      - id: port3
        type: b4
  power_state:
    doc-ref: Table 3-60, 3-61
    doc: Read only register.  Returns state of downstream ports (normal, sleep, suspend, off).
    seq:
      - id: port3
        type: b2
        enum: state
      - id: port2
        type: b2
        enum: state
      - id: port1
        type: b2
        enum: state
      - id: port0
        type: b2
        enum: state
      - id: reserved
        type: b6
      - id: port4
        type: b2
        enum: state
    enums:
      state:
        0: normal
        1: sleep
        2: suspend
        3: off
  connection:
    doc-ref: Table 3-66
    seq:
      - id: reserved
        type: b3
      - id: port4
        type: b1
      - id: port3
        type: b1
      - id: port2
        type: b1
      - id: port1
        type: b1
      - id: port0
        type: b1
  device_speed:
    doc-ref: Table 3-67
    seq:
      - id: port4
        type: b2
        enum: state
      - id: port3
        type: b2
        enum: state
      - id: port2
        type: b2
        enum: state
      - id: port1
        type: b2
        enum: state
    enums:
      state:
        0: none
        1: low
        2: full
        3: high
  power_select_1:
    doc-ref: Table 3-72
    seq:
      - id: combined_mode
        type: b1
      - id: gang_mode
        type: b1
      - id: reserved
        type: b2
      - id: source
        type: b4
        enum: source
    enums:
      source:
        0: disabled
        1: software
        8: gpio
  power_select_2:
    doc-ref: Table 3-73
    seq:
      - id: combined_mode
        type: b1
      - id: gang_mode
        type: b1
      - id: reserved
        type: b2
      - id: source
        type: b4
        enum: source
    enums:
      source:
        0: disabled
        1: software
        8: gpio
  power_select_3:
    doc-ref: Table 3-74
    seq:
      - id: combined_mode
        type: b1
      - id: gang_mode
        type: b1
      - id: reserved
        type: b2
      - id: source
        type: b4
        enum: source
    enums:
      source:
        0: disabled
        1: software
        8: gpio
  power_select_4:
    doc-ref: Table 3-75
    seq:
      - id: combined_mode
        type: b1
      - id: gang_mode
        type: b1
      - id: reserved
        type: b2
      - id: source
        type: b4
        enum: source
    enums:
      source:
        0: disabled
        1: software
        8: gpio