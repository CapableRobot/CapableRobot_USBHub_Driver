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
import weakref

from .i2c import USBHubI2C
from .spi import USBHubSPI
from .gpio import USBHubGPIO
from .power import USBHubPower
from .config import USBHubConfig
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

    def __init__(self, main, handle,
        timeout           = 100,
        i2c_attempts_max  = 5,
        i2c_attempt_delay = 10,
        disable_i2c       = False
    ):

        self.main = main
        self.handle = handle

        self._serial = None
        self._sku = None
        self._revision = None

        proxy = weakref.proxy(self)

        ## Function to enable the I2C bus
        ##
        ## This is bound here so that passed-in parameters don't have
        ## to be saved as object parameters, and we can still enable later
        ## if we need to.
        def enable_i2c():
            self.i2c = USBHubI2C(proxy,
                timeout       = timeout,
                attempts_max  = i2c_attempts_max,
                attempt_delay = i2c_attempt_delay
            )

        if disable_i2c:
            ## For now, don't enable the I2C bus, but save the fuction to do so to a lambda.
            ## This allows delayed enabling of the I2C bus if it is needed later
            ## (e.g. to turn port data on and off).
            self.i2c = None
            self.enable_i2c = lambda : enable_i2c()
        else:
            enable_i2c()

        self.spi = USBHubSPI(proxy, timeout=timeout)
        self.gpio = USBHubGPIO(proxy)
        self.power = USBHubPower(proxy)
        self.config = USBHubConfig(proxy)

        logging.debug("Device class created")

    def register_read(self, name=None, addr=None, length=1, print=False, endian='big'):
        if name != None:
            addr, bits, endian = self.main.find_register_by_name(name)
            length = int(bits / 8)
        else:
            try:
                name = self.main.find_register_name_by_addr(addr)
            except :
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
        if self.i2c is None:
            return None

        if self._serial is None:
            data = self.i2c.read_i2c_block_data(EEPROM_I2C_ADDR, EEPROM_EUI_ADDR, EEPROM_EUI_BYTES)
            data = [char for char in data]

            if len(data) == 6:
                data = data[0:3] + [0xFF, 0xFE] + data[3:6]

            self._serial = ''.join(["%0.2X" % v for v in data])

        return self._serial

    @property
    def usb_path(self):
        return "{}-{}".format(self.handle.bus, self.handle.address)
   
    @property
    def key(self):
        if self.i2c is None:
            return self.usb_path

        return self.serial[-self.main.KEY_LENGTH:]

    @property    
    def sku(self):
        if self.i2c is None:
            return None

        if self._sku is None:
            data = self.i2c.read_i2c_block_data(EEPROM_I2C_ADDR, EEPROM_SKU_ADDR, EEPROM_SKU_BYTES+1)
            
            if data[0] == 0 or data[0] == 255:
                ## Prototype units didn't have the PCB SKU programmed into the EEPROM
                ## If EEPROM location is empty, we assume we're interacting with that hardware
                self._sku = ['......', 0]
            else:
                ## Cache the SKU and the revision stored in the EEPROM
                self._sku = [
                    ''.join([chr(char) for char in data[0:EEPROM_SKU_BYTES]]),
                    data[EEPROM_SKU_BYTES]
                ]

        ## Return just the SKU (not the revision value)
        return self._sku[0]

    @property
    def mpn(self):
        return self.sku

    @property
    def rev(self):
        return self.revision

    @property
    def revision(self):
        if self._revision is None:
            ## There was a hardware change between REV 1 and REV 2 which 
            ## necessites the host-side driver knowing of that change.
            ## Data should be correct in EEPROM, but the on-hub firmware
            ## puts hardware revision in this register with the format
            ## of [REV, 'C'].  If 'C' is in the second byte, the first
            ## byte has valid hardware information.
            data, _ = self.register_read(addr=0x3004, length=2)
            
            if data[1] == ord('C'):
                self._revision = data[0]
            else:
                ## Firmware has not set the revision in this address, so fall back
                ## to pulling hardwar revision from the on-device EEPROM
                _ = self.sku
                self._revision = self._sku[1]

        return self._revision

    def check_hardware_revision(self):
        _ = self.sku
        return self.revision == self._sku[1]

    def _data_state(self):
        if self.i2c is None:
            self.enable_i2c()

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