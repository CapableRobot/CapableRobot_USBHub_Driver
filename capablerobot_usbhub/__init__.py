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

import usb.core
import usb.util

from .registers import registers
from .i2c import USBHubI2C
from .util import *


ADDR_USC12 = 0x57
ADDR_USC34 = 0x56

UCS2113_PORT1_CURRENT = 0x00
UCS2113_PORT2_CURRENT = 0x01

REQ_OUT = usb.util.build_request_type(
    usb.util.CTRL_OUT,
    usb.util.CTRL_TYPE_VENDOR,
    usb.util.CTRL_RECIPIENT_DEVICE)

REQ_IN = usb.util.build_request_type(
    usb.util.CTRL_IN,
    usb.util.CTRL_TYPE_VENDOR,
    usb.util.CTRL_RECIPIENT_DEVICE)

class USBHub:

    CMD_REG_WRITE = 0x03
    CMD_REG_READ  = 0x04
    CMD_I2C_ENTER = 0x70
    CMD_I2C_WRITE = 0x71
    CMD_I2C_READ  = 0x72

    ID_PRODUCT = 0x494C
    ID_VENDOR  = 0x0424

    REG_BASE_DFT = 0xBF800000
    REG_BASE_ALT = 0xBFD20000

    TIMEOUT = 10000

    def __init__(self, vendor=None, product=None):
        if vendor == None:
            vendor = self.ID_VENDOR
        if product == None:
            product = self.ID_PRODUCT

        self.attach(vendor, product)

        this_dir = os.path.dirname(os.path.abspath(__file__))
        self.definition = {}

        for file in glob.glob("%s/../formats/*.ksy" % this_dir):
            key = os.path.basename(file).replace(".ksy","")
            self.definition[key] = yaml.load(open(file))

        # Extract the dictionary of register addresses to names
        # Flip the keys and values (name will now be key)
        # Add number of bytes to the mapping table, extracted from the YAML file
        #
        # Register names (keys) have the 'DEVICE_' prefix removed from them
        # but still have the '::' and '_' seperators
        mapping = self.definition['usb4715']['types']['register']['seq'][-1]['type']['cases']
        mapping = {v:k for k,v in mapping.items()}
        self.mapping = {k.replace('usb4715_',''):[v,self.get_register_length(k),self.get_register_endian(k)] for k,v in mapping.items()}

    # Function to extract and sum the number of bits in each register defintion.
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

    def find_name(self, register):
        for name, value in self.mapping.items():
            if value[0] == register:
                return name

        raise ValueError("Unknown register address : %s" % hex(register))

    def find(self, name):

        if name in self.mapping:
            register, bits, endian = self.mapping[name]

            if bits in [8, 16, 24, 32]:
                return register, bits, endian
            else:
                raise ValueError("Register %s has %d bits" % (name, bits))
        else:
            raise ValueError("Unknown register name : %s" % name)

    def attach(self, vendor=ID_VENDOR, product=ID_PRODUCT):
        self.dev = usb.core.find(idVendor=vendor, idProduct=product)

        if self.dev  is None:
            raise ValueError('Device not found')

        cfg = self.dev.get_active_configuration()
        interface = cfg[(2,0)]
        self.out_ep, self.in_ep = sorted([ep.bEndpointAddress for ep in interface])

        self.i2c = USBHubI2C(self.dev)

    def register_read(self, name=None, addr=None, length=1, print=False):
        if name != None:
            address, bits, endian = self.find(name)
            addr = address + self.REG_BASE_DFT
            length = int(bits / 8)
        else:
            name = ''

        if addr == None:
            raise ValueError('Must specify an name or address')

        logging.info("-- register {} ({}) read {} -- ".format(name, hexstr(addr), length))

        ## Split 32 bit register address into the 16 bit value & index fields
        value = addr & 0xFFFF
        index = addr >> 16

        data = list(self.dev.ctrl_transfer(REQ_IN, self.CMD_REG_READ, value, index, length))

        if length != len(data):
            raise ValueError('Incorrect data length')

        if print:
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

            num    = bits_to_bytes(bits)
            value  = int_from_bytes(data, endian)
            stream = struct.pack(">fHB" + code, *[time.time(), address, num, value << shift])
            self.print_register(registers.parse(stream)[0])

        data.reverse()
        logging.info(" ".join([hexstr(v) for v in data]))
        return data

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

        addr = hex(data.code).upper().replace("0X","0x")
        # name = type(data.body).__name__

        name = self.find_name(data.code)

        print("%s %s" % (addr, name) )
        for key in sorted(meta.keys()):
            value = meta[key]
            print("       %s : %s" % (key, hex(value)))

    def currents(self,ports=[1,2,3,4]):
        TO_MA = 13.3

        out = []

        for port in ports:
            if port == 1 or port == 2:
                i2c_addr = ADDR_USC12
            else:
                i2c_addr = ADDR_USC34

            if port == 1 or port == 3:
                reg_addr = UCS2113_PORT1_CURRENT
            else:
                reg_addr = UCS2113_PORT2_CURRENT

            value = self.i2c.read_i2c_block_data(i2c_addr, reg_addr)[0]
            out.append(float(value) * TO_MA)

        return out