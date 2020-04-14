meta:
  id: usb4715_mcu
  title: Structure that allows communication with the MCU inside the Programmable USB Hub
types:
  control:
    seq:
      - id: command
        type: b3
      - id: name
        type: b5
      - id: value
        type: b16
      - id: crc
        type: b8
  status:
    seq:
      - id: command
        type: b3
      - id: name
        type: b5
      - id: value
        type: b16
      - id: crc
        type: b8