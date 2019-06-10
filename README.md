# Capable Robot CircuitPython USBHub Bridge

This library has two functions:

- It provides access to internal state of the Capable Robot USB Hub, allowing you to monitor and control the Hub from an upstream computer.
- It creates a transparent CircuitPython Bridge, allowing unmodified CircuitPython code to run on the host computer and interact with I2C devices attached to the USB Hub.

## Installing Dependencies

	pip3 install pyusb construct pyyaml

## Working Functionality

- Reading USB Hub registers over USB and decoding of register data.
- Reading & writing I2C data thru the Hub.
- CircuitPython I2C Bridge.  

## Not Working / Not Implemented Yet

- Writing USB Hub registers over USB.
- CircuitPython SPI Bridge.
- CircuitPython GPIO Bridge.

## Contributing 

Contributions are welcome! Please read our 
[Code of Conduct](https://github.com/capablerobot/CapableRobot_CircuitPython_USBHub_Bridge/blob/master/CODE_OF_CONDUCT.md)
before contributing to help this project stay welcoming.