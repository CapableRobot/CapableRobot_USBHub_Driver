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

import os
import glob
import yaml
import struct
import time
import logging
import copy
import subprocess

import usb.core
import usb.util

from .registers import registers
from .i2c import USBHubI2C
from .spi import USBHubSPI
from .gpio import USBHubGPIO
from .power import USBHubPower
from .util import *

PORT_MAP = ["port2", "port4", "port1", "port3"]

REGISTER_NEEDS_PORT_REMAP = [
    'port::connection',
    'port::device_speed'
]

REQ_OUT = usb.util.build_request_type(
    usb.util.CTRL_OUT,
    usb.util.CTRL_TYPE_VENDOR,
    usb.util.CTRL_RECIPIENT_DEVICE)

REQ_IN = usb.util.build_request_type(
    usb.util.CTRL_IN,
    usb.util.CTRL_TYPE_VENDOR,
    usb.util.CTRL_RECIPIENT_DEVICE)

EEPROM_I2C_ADDR = 0x50
EEPROM_EUI_ADDR = 0xFA
EEPROM_EUI_BYTES = 0xFF - 0xFA + 1
EEPROM_SKU_ADDR = 0x00
EEPROM_SKU_BYTES = 0x06

MCP_I2C_ADDR = 0x20
MCP_REG_GPIO = 0x09

def register_keys(parsed, sort=True):
    if sort:
        keys = sorted(parsed.body.keys())
    else:
        parsed.body.keys()

    ## Remove any key which starts with 'reserved' or '_'
    return list(filter(lambda key: key[0] != '_' and ~key.startswith("reserved") , keys))


class USBHub:

    CMD_REG_WRITE = 0x03
    CMD_REG_READ  = 0x04

    ID_PRODUCT = 0x494C
    ID_VENDOR  = 0x0424

    REG_BASE_DFT = 0xBF800000
    REG_BASE_ALT = 0xBFD20000

    TIMEOUT = 1000

    KEY_LENGTH = 4

    def __init__(self, vendor=None, product=None):
        if vendor == None:
            vendor = self.ID_VENDOR
        if product == None:
            product = self.ID_PRODUCT

        self.attach(vendor, product)

        this_dir = os.path.dirname(os.path.abspath(__file__))
        self.definition = {}

        for file in glob.glob("%s/formats/*.ksy" % this_dir):
            key = os.path.basename(file).replace(".ksy","")
            self.definition[key] = yaml.load(open(file), Loader=yaml.SafeLoader)

        # Extract the dictionary of register addresses to names
        # Flip the keys and values (name will now be key)
        # Add number of bytes to the mapping table, extracted from the YAML file
        #
        # Register names (keys) have the 'DEVICE_' prefix removed from them
        # but still have the '::' and '_' separators
        mapping = self.definition['usb4715']['types']['register']['seq'][-1]['type']['cases']
        mapping = {v:k for k,v in mapping.items()}
        self.mapping = {k.replace('usb4715_',''):[v,self.get_register_length(k),self.get_register_endian(k)] for k,v in mapping.items()}

    # Function to extract and sum the number of bits in each register definition.
    # For this to function correctly, all lengths MUST be in bit lengths
    # Key is split into namespace to correctly locate the right sequence field
    def get_register_length(self, key):
        key = key.split("::")
        seq = self.definition[key[0]]['types'][key[1]]['seq']
        return sum([int(v['type'].replace('b','')) for v in seq])

    def get_register_endian(self, key):
        key = key.split("::")
        obj = self.definition[key[0]]['types'][key[1]]

        if 'meta' in obj:
            if 'endian' in obj['meta']:
                value = obj['meta']['endian']
                if value == 'le':
                    return 'little'

        return 'big'

    def find_register_name_by_addr(self, register):
        for name, value in self.mapping.items():
            if value[0] == register:
                return name

        raise ValueError("Unknown register address : %s" % hex(register))

    def find_register_by_name(self, name):

        if name in self.mapping:
            register, bits, endian = self.mapping[name]

            if bits in [8, 16, 24, 32]:
                return register, bits, endian
            else:
                raise ValueError("Register %s has %d bits" % (name, bits))
        else:
            raise ValueError("Unknown register name : %s" % name)

    @property
    def device(self):
        return self.devices[self._active_device]

    def activate(self, key):

        if isinstance(key, int):
            idx = key

            if idx >= len(self.devices):
                idx = None
        else:
            try:
                idx = self._device_keys.index(key)
            except ValueError:
                idx = None

        self._active_device = idx
        return self._active_device


    def attach(self, vendor=ID_VENDOR, product=ID_PRODUCT):
        logging.debug("Looking for USB Hubs")
        self.devices = list(usb.core.find(idVendor=vendor, idProduct=product, find_all=True))
        self._active_device = 0
        logging.debug("Found {} Hub(s)".format(len(self.devices)))

        if self.devices is None or len(self.devices) == 0:
            raise ValueError('No USB Hub was found')

        # cfg = self.dev.get_active_configuration()
        # interface = cfg[(2,0)]
        # self.out_ep, self.in_ep = sorted([ep.bEndpointAddress for ep in interface])

        self.i2c = USBHubI2C(self)
        self.spi = USBHubSPI(self)
        self.gpio = USBHubGPIO(self)

        self.power = USBHubPower(self, self.i2c)
        logging.debug("I2C and Power classes created")

        ## Create null cache for device serial numbers
        self._device_ids = None

        ## Store last for digits of serial numbers for key-based Hub lookup
        self._device_keys = [d[1][-self.KEY_LENGTH:] for d in self.id()]

    def register_read(self, name=None, addr=None, length=1, print=False, endian='big'):
        if name != None:
            addr, bits, endian = self.find_register_by_name(name)
            length = int(bits / 8)
        else:
            try:
                name = self.find_register_name_by_addr(addr)
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

        data = list(self.device.ctrl_transfer(REQ_IN, self.CMD_REG_READ, value, index, length))

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
            parsed = self.parse_register(name, stream)

        if print:
            self.print_register(parsed)

        data.reverse()
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
            length = self.device.ctrl_transfer(REQ_OUT, self.CMD_REG_WRITE, value, index, buf)
        except usb.core.USBError:
            raise OSError('Unable to write to register {}'.format(addr))

        if length != len(buf):
            raise OSError('Number of bytes written to bus was {}, expected {}'.format(length, len(buf)))

        return length

    def print_register(self, data):
        meta = {}
        body = data.body

        # Allows for printing of KaiTai and Construct objects
        # Construct containers already inherit from dict, but
        # KaiTai objects need to be converted via vars call
        if not isinstance(body, dict):
            body = vars(data.body)

        for key, value in body.items():
            if key.startswith("reserved") or key[0] == "_":
                continue

            meta[key] = value

        addr = hex(data.addr).upper().replace("0X","0x")
        name = self.find_register_name_by_addr(data.addr)

        print("%s %s" % (addr, name) )
        for key in sorted(meta.keys()):
            value = meta[key]
            print("       %s : %s" % (key, hex(value)))

    def parse_register(self, name, stream):
        parsed = registers.parse(stream)[0]

        if name in REGISTER_NEEDS_PORT_REMAP:
            raw = copy.deepcopy(parsed)

            for key, value in raw.body.items():
                if key in PORT_MAP:
                    port = PORT_MAP[int(key.replace("port",""))-1]
                    parsed.body[port] = value

        return parsed



    def connections(self):
        _, conn = self.register_read(name='port::connection')
        return [conn.body[key] == 1 for key in register_keys(conn)]

    def speeds(self):
        _, speed = self.register_read(name='port::device_speed')
        speeds = ['none', 'low', 'full', 'high']
        return [speeds[speed.body[key]] for key in register_keys(speed)]

    def serial(self):
        data = self.i2c.read_i2c_block_data(EEPROM_I2C_ADDR, EEPROM_EUI_ADDR, EEPROM_EUI_BYTES)
        data = [char for char in data]

        if len(data) == 6:
            data = data[0:3] + [0xFF, 0xFE] + data[3:6]

        return ''.join(["%0.2X" % v for v in data])

    def sku(self):
        data = self.i2c.read_i2c_block_data(EEPROM_I2C_ADDR, EEPROM_SKU_ADDR, EEPROM_SKU_BYTES)
        
        ## Prototype units didn't have the PCB SKU programmed into the EEPROM
        ## If EEPROM location is empty, we assume we're interacting with that hardware
        if data[0] == 0 or data[0] == 255:
            return 'CRR3C4'

        return ''.join([chr(char) for char in data])

    def id(self):
        def get_id():
            return [self.sku(), self.serial()]

        if self._device_ids is None:
            self._device_ids = []

            for idx in range(len(self.devices)):
                self.activate(idx)
                self._device_ids.append(get_id())

        return self._device_ids


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

    def print_permission_instructions(self):
        message = ['User has insufficient permissions to access the USB Hub.']

        ## Check that this linux distro has 'udevadm' before instructing 
        ## the user on how to install udev rule.
        check = subprocess.run(["which", "udevadm"], stdout=subprocess.PIPE)
        if check.stdout.decode("utf-8")[0] == "/":
            folder = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

            message += [
                'Please run the following commands, then unplug and re-plug your Hub.',
                '',
                "sudo cp {}/50-capablerobot-usbhub.rules /etc/udev/rules.d/".format(folder),
                'sudo udevadm control --reload',
                'sudo udevadm trigger'
            ]

        print()
        for line in message:
            print(line)
        print()