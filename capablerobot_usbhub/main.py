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
from .device import USBHubDevice
from .util import *

PORT_MAP = ["port2", "port4", "port1", "port3"]

REGISTER_NEEDS_PORT_REMAP = [
    'port::connection',
    'port::device_speed'
]

class USBHub:

    ID_PRODUCT = 0x494C
    ID_VENDOR  = 0x0424

    KEY_LENGTH = 4

    def __init__(self, vendor=None, product=None):
        if vendor == None:
            vendor = self.ID_VENDOR
        if product == None:
            product = self.ID_PRODUCT

        self._active_device = None
        self._device_keys = []

        self.devices = {}
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

    def activate(self, selector):

        if isinstance(selector, int):
            if selector >= len(self.devices):
                key = None
            else:
                key = self._device_keys[selector]
    
        else:
            if selector in self._device_keys:
                key = selector
            else:
                key = None

        self._active_device = key
        return self._active_device


    def attach(self, vendor=ID_VENDOR, product=ID_PRODUCT):
        logging.debug("Looking for USB Hubs")
        handles = list(usb.core.find(idVendor=vendor, idProduct=product, find_all=True))

        logging.debug("Found {} Hub(s)".format(len(handles)))

        if handles is None or len(handles) == 0:
            raise ValueError('No USB Hub was found')

        for handle in handles:
            device = USBHubDevice(self, handle)
            self.devices[device.key] = device

            self._active_device = device.key
            self._device_keys.append(device.key)
    

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


    def id(self, all=False):
        if all:
            return [device.id() for _,device in self.devices.items()]

        return self.device.id()


    def connections(self):
        return self.device.connections()

    def speeds(self):
        return self.device.speeds()

    @property
    def serial(self):
        return self.device.serial

    @property
    def sku(self):
        return self.device.sku

    def data_state(self):
        return self.device.data_state()

    def data_enable(self, ports=[]):
        return self.device.data_enable(ports)

    def data_disable(self, ports=[]):
        return self.device.data_disable(ports)

    def register_read(self, name=None, addr=None, length=1, print=False, endian='big'):
        return self.device.register_read(name, addr, length, print, endian)

    def register_write(self, name=None, addr=None, buf=[]):
        return self.device.register_write(name, addr, buf)

    @property
    def power(self):
        return self.device.power

    @property
    def gpio(self):
        return self.device.gpio

    @property
    def i2c(self):
        return self.device.i2c

    @property
    def spi(self):
        return self.device.spi
    

    def print_permission_instructions(self):
        message = ['User has insufficient permissions to access the USB Hub.']

        ## Check that this linux distro has 'udevadm' before instructing 
        ## the user on how to install udev rule.
        check = subprocess.run(["which", "udevadm"], stdout=subprocess.PIPE)
        check = check.stdout.decode("utf-8")
        
        if len(check) > 0 and check[0] == "/":
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