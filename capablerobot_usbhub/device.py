# The MIT License (MIT)
#
# Copyright (c) 2019 Chris Osterwood for Capable Robot Components
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import struct
import logging

from .i2c import USBHubI2C
from .spi import USBHubSPI
from .gpio import USBHubGPIO
from .power import USBHubPower
from .util import *

EEPROM_I2C_ADDR = 0x50
EEPROM_EUI_ADDR = 0xFA
EEPROM_EUI_BYTES = 0xFF - 0xFA + 1
EEPROM_SKU_ADDR = 0x00
EEPROM_SKU_BYTES = 0x06

MCP_I2C_ADDR = 0x20
MCP_REG_GPIO = 0x09

class USBHubDevice:

    CMD_REG_WRITE = 0x03
    CMD_REG_READ  = 0x04

    REG_BASE_DFT = 0xBF800000
    REG_BASE_ALT = 0xBFD20000

    def __init__(self, main, handle):
        self.main = main
        self.handle = handle

        self._serial = None
        self._sku = None

        self.i2c = USBHubI2C(self)
        self.spi = USBHubSPI(self)
        self.gpio = USBHubGPIO(self)
        self.power = USBHubPower(self, self.i2c)

        logging.debug("I2C and Power classes created")

    def register_read(self, name=None, addr=None, length=1, print=False, endian='big'):
        if name != None:
            addr, bits, endian = self.main.find_register_by_name(name)
            length = int(bits / 8)
        else:
            try:
                name = self.main.find_register_name_by_addr(addr)
            except ValueError as e:
                logging.error(e)
                print = False

            bits = length * 8

        if addr == None:
            raise ValueError('Must specify an name or address')

        ## Need to offset the register address for USB access
        address = addr + self.REG_BASE_DFT

        ## Split 32 bit register address into the 16 bit value & index fields
        value = address & 0xFFFF
        index = address >> 16

        data = list(self.handle.ctrl_transfer(REQ_IN, self.CMD_REG_READ, value, index, length))

        if length != len(data):
            raise ValueError('Incorrect data length')

        shift = 0

        if bits == 8:
            code = 'B'
        elif bits == 16:
            code = 'H'
        elif bits == 24:
            ## There is no good way to extract a 3 byte number.
            ##
            ## So we tell pack it's a 4 byte number and shift all the data over 1 byte
            ## so it decodes correctly (as the register defn starts from the MSB)
            code = 'L'
            shift = 8
        elif bits == 32:
            code = 'L'

        if name is None:
            parsed = None
        else:
            num    = bits_to_bytes(bits)
            value  = int_from_bytes(data, endian)
            stream = struct.pack(">HB" + code, *[addr, num, value << shift])
            parsed = self.main.parse_register(name, stream)

        if print:
            self.main.print_register(parsed)

        logging.debug("{} [0x{}] read {} [{}]".format(name, hexstr(addr), length, " ".join(["0x"+hexstr(v) for v in data])))
        
        return data, parsed

    def register_write(self, name=None, addr=None, buf=[]):
        if name != None:
            addr, _, _ = self.find_register_by_name(name)

        if addr == None:
            raise ValueError('Must specify an name or address')

        ## Need to offset the register address for USB access
        address = addr + self.REG_BASE_DFT

        ## Split 32 bit register address into the 16 bit value & index fields
        value = address & 0xFFFF
        index = address >> 16

        try:
            length = self.handle.ctrl_transfer(REQ_OUT, self.CMD_REG_WRITE, value, index, buf)
        except usb.core.USBError:
            raise OSError('Unable to write to register {}'.format(addr))

        if length != len(buf):
            raise OSError('Number of bytes written to bus was {}, expected {}'.format(length, len(buf)))

        return length

    def connections(self):
        _, conn = self.register_read(name='port::connection')
        return [conn.body[key] == 1 for key in register_keys(conn)]

    def speeds(self):
        _, speed = self.register_read(name='port::device_speed')
        speeds = ['none', 'low', 'full', 'high']
        return [speeds[speed.body[key]] for key in register_keys(speed)]

    @property
    def serial(self):
        if self._serial is None:
            data = self.i2c.read_i2c_block_data(EEPROM_I2C_ADDR, EEPROM_EUI_ADDR, EEPROM_EUI_BYTES)
            data = [char for char in data]

            if len(data) == 6:
                data = data[0:3] + [0xFF, 0xFE] + data[3:6]

            self._serial = ''.join(["%0.2X" % v for v in data])

        return self._serial

    @property
    def key(self):
        return self.serial[-self.main.KEY_LENGTH:]

    @property    
    def sku(self):
        if self._sku is None:
            data = self.i2c.read_i2c_block_data(EEPROM_I2C_ADDR, EEPROM_SKU_ADDR, EEPROM_SKU_BYTES)
            
            ## Prototype units didn't have the PCB SKU programmed into the EEPROM
            ## If EEPROM location is empty, we assume we're interacting with that hardware
            if data[0] == 0 or data[0] == 255:
                return '......'

            self._sku = ''.join([chr(char) for char in data])

        return self._sku

    def id(self):
        return [self.sku, self.serial]

    def _data_state(self):
        return self.i2c.read_i2c_block_data(MCP_I2C_ADDR, MCP_REG_GPIO, 1)[0]

    def data_state(self):
        value = self._data_state()
        return ["off" if get_bit(value, idx) else "on" for idx in [7,6,5,4]]

    def data_enable(self, ports=[]):
        value = self._data_state()

        for port in ports:
            value = clear_bit(value, 8-port)

        self.i2c.write_bytes(MCP_I2C_ADDR, bytes([MCP_REG_GPIO, int(value)]))

    def data_disable(self, ports=[]):
        value = self._data_state()

        for port in ports:
            value = set_bit(value, 8-port)

        self.i2c.write_bytes(MCP_I2C_ADDR, bytes([MCP_REG_GPIO, int(value)]))