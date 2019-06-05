meta:
  id: usb4715_main
  title: Microchip USB4715 General Registers
types:
  revision:
    doc-ref: Table 3-4
    seq:
      - id: device_id
        type: b16
      - id: reserved
        type: b8
      - id: revision_id
        type: b8
  vendor_id:
    doc-ref: Table 3-30, 3-31
    meta:
      endian: le
    seq:
      - id: value
        type: b16
  product_id:
    doc-ref: Table 3-32, 3-33
    meta:
      endian: le
    seq:
      - id: value
        type: b16
  device_id:
    doc-ref: Table 3-34, 3-35
    meta:
      endian: le
    seq:
      - id: value
        type: b16
  hub_configuration:
    doc-ref: Table 3-36 thru 3-38
    seq:
      - id: self_power
        type: b1
      - id: vsm_disable
        type: b1
      - id: hs_disable
        type: b1
      - id: mtt_enable
        type: b1
      - id: eop_disable
        type: b1
      - id: current_sense
        type: b2
        enum: current_sense
      - id: port_power
        type: b1
        doc: 0 -> Ganged switching (all ports together). 1 -> Individual (port by port) switching.
      - id: reserved1
        type: b2
      - id: oc_timer
        type: b2
        enum: oc_timer
      - id: compound
        type: b1
      - id: reserved2
        type: b3
      - id: reserved3
        type: b4
      - id: prtmap_enable
        type: b1
      - id: reserved4
        type: b2
      - id: string_enable
        type: b1
    enums:
      current_sense:
        0: ganged_sensing
        1: port_by_port
        2: not_supported
        3: not_supported
      oc_timer:
        0: ns50
        1: ns100
        2: ns200
        3: ns400
  hub_configuration_1:
    doc-ref: Table 3-36
    seq:
      - id: self_power
        type: b1
      - id: vsm_disable
        type: b1
      - id: hs_disable
        type: b1
      - id: mtt_enable
        type: b1
      - id: eop_disable
        type: b1
      - id: current_sense
        type: b2
        enum: current_sense
      - id: port_power
        type: b1
        doc: 0 -> Ganged switching (all ports together). 1 -> Individual (port by port) switching.
    enums:
      current_sense:
        0: ganged_sensing
        1: port_by_port
        2: not_supported
        3: not_supported
  hub_configuration_2:
    doc-ref: Table 3-37
    seq:
      - id: reserved1
        type: b2
      - id: oc_timer
        type: b2
        enum: oc_timer
      - id: compound
        type: b1
      - id: reserved2
        type: b3
    enums:
      oc_timer:
        0: ns50
        1: ns100
        2: ns200
        3: ns400
  hub_configuration_3:
    doc-ref: Table 3-38 3-38
    seq:
      - id: reserved1
        type: b4
      - id: prtmap_enable
        type: b1
      - id: reserved2
        type: b2
      - id: string_enable
        type: b1
  port_swap:
    doc-ref: Table 3-55
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
  hub_control:
    doc-ref: Table 3-62
    seq:
      - id: reserved
        type: b6
      - id: lpm_disable
        type: b1
      - id: reset
        type: b1
  suspend:
    doc-ref: Table 3-69
    seq:
      - id: reserved
        type: b7
      - id: suspend
        type: b1