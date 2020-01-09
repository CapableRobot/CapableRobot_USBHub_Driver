meta:
  id: usb4715_gpio
  title: Microchip USB4715 GPIO Registers
types:
  output_enable:
    doc-ref: Table 3-4
    seq:
      - id: value
        type: b32
  input_enable:
    doc-ref: Table 3-8
    seq:
      - id: value
        type: b32
  output: 
    doc-ref: Table 3-11
    seq:
      - id: value
        type: b32
  input: 
    doc-ref: Table 3-14
    seq:
      - id: value
        type: b32
  pull_up:
    doc-ref: Table 3-17
    seq:
      - id: value
        type: b32
  pull_down:
    doc-ref: Table 3-20
    seq:
      - id: value
        type: b32
  open_drain:
    doc-ref: Table 3-23
    seq:
      - id: value
        type: b32
  debounce:
    doc-ref: Table 3-26
    seq:
      - id: value
        type: b32
  debounce_time:
    doc-ref: Table 3-29
    seq:
      - id: reserved
        type: b24
      - id: value
        type: b8
        doc: Debounce count in 10-msec increments