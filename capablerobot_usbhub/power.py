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

from .util import *

ADDR_USC12 = 0x57
ADDR_USC34 = 0x56

_PORT_CONTROL  = 0x3C00

_PORT1_CURRENT = 0x00
_PORT2_CURRENT = 0x01
_PORT_STATUS   = 0x02
_INTERRUPT1    = 0x03
_INTERRUPT2    = 0x04
_CONFIG1       = 0x11
_CONFIG2       = 0x12
_CURRENT_LIMIT = 0x14

_CURRENT_MAPPING = [
    530,
    960,
    1070,
    1280,
    1600,
    2130,
    2670,
    3200
]

class USBHubPower:

    def __init__(self, hub, i2c):
        self.hub = hub
        self.i2c = i2c

    def state(self, ports=[1,2,3,4]):
        out = []

        for port in ports:
            data, _ = self.hub.register_read(addr=_PORT_CONTROL+(port-1)*4)
            out.append(get_bit(data[0], 0))

        return out

    def disable(self, ports=[]):
        for port in ports:
            self.hub.register_write(addr=_PORT_CONTROL+(port-1)*4, buf=[0x80])

    def enable(self, ports=[]):
        for port in ports:
            self.hub.register_write(addr=_PORT_CONTROL+(port-1)*4, buf=[0x81])

    def measurements(self, ports=[1,2,3,4]):
        TO_MA = 13.3

        out = []

        for port in ports:
            if port == 1 or port == 2:
                i2c_addr = ADDR_USC12
            else:
                i2c_addr = ADDR_USC34

            if port == 1 or port == 3:
                reg_addr = _PORT1_CURRENT
            else:
                reg_addr = _PORT2_CURRENT

            value = self.i2c.read_i2c_block_data(i2c_addr, reg_addr, number=1)[0]
            out.append(float(value) * TO_MA)

        return out

    def limits(self):
        out = []
        reg_addr = _CURRENT_LIMIT

        for i2c_addr in [ADDR_USC12, ADDR_USC34]:
            value = self.i2c.read_i2c_block_data(i2c_addr, reg_addr, number=1)[0]

            ## Extract Port 1 of this chip
            out.append(value & 0b111)

            ## Extract Port 2 of this chip
            out.append((value >> 3) & 0b111)

        return [_CURRENT_MAPPING[key] for key in out]

    def set_limits(self, ports, limit):
        if limit not in _CURRENT_MAPPING:
            raise ValueError("Specified current limit of {} is not valid. Limits can be: {}".format(limit, _CURRENT_MAPPING))

        setting = _CURRENT_MAPPING.index(limit)
        reg_addr = _CURRENT_LIMIT

        if 1 in ports or 2 in ports:
            value = self.i2c.read_i2c_block_data(ADDR_USC12, reg_addr, number=1)[0]
            value = BitVector(value)

            if 1 in ports:
                value[0:3] = setting

            if 2 in ports:
                value[3:6] = setting

            self.i2c.write_bytes(ADDR_USC12, bytes([reg_addr, int(value)]))

        if 3 in ports or 4 in ports:
            value = self.i2c.read_i2c_block_data(ADDR_USC34, reg_addr, number=1)[0]
            value = BitVector(value)

            if 3 in ports:
                value[0:3] = setting

            if 4 in ports:
                value[3:6] = setting

            self.i2c.write_bytes(ADDR_USC34, bytes([reg_addr, int(value)]))

    def alerts(self):
        out = []

        for idx, i2c_addr in enumerate([ADDR_USC12, ADDR_USC34]):

            value = self.i2c.read_i2c_block_data(i2c_addr, _PORT_STATUS, number=1)[0]

            if get_bit(value, 7):
                out.append("ALERT.{}".format(idx*2+1))

            if get_bit(value, 6):
                out.append("ALERT.{}".format(idx*2+2))

            if get_bit(value, 5):
                out.append("CC_MODE.{}".format(idx*2+1))

            if get_bit(value, 4):
                out.append("CC_MODE.{}".format(idx*2+2))


            value = self.i2c.read_i2c_block_data(i2c_addr, _INTERRUPT1, number=1)[0]

            if get_bit(value, 7):
                out.append("ERROR.{}".format(idx*2+1))

            if get_bit(value, 6):
                out.append("DISCHARGE.{}".format(idx*2+1))

            if get_bit(value, 5):
                if idx == 0:
                    out.append("RESET.12")
                else:
                    out.append("RESET.34")

            if get_bit(value, 4):
                out.append("KEEP_OUT.{}".format(idx*2+1))

            if get_bit(value, 3):
                if idx == 0:
                    out.append("DIE_TEMP_HIGH.12")
                else:
                    out.append("DIE_TEMP_HIGH.34")

            if get_bit(value, 2):
                if idx == 0:
                    out.append("OVER_VOLT.12")
                else:
                    out.append("OVER_VOLT.34")

            if get_bit(value, 1):
                out.append("BACK_BIAS.{}".format(idx*2+1))

            if get_bit(value, 0):
                out.append("OVER_LIMIT.{}".format(idx*2+1))


            value = self.i2c.read_i2c_block_data(i2c_addr, _INTERRUPT2, number=1)[0]

            if get_bit(value, 7):
                out.append("ERROR.{}".format(idx*2+2))

            if get_bit(value, 6):
                out.append("DISCHARGE.{}".format(idx*2+2))

            if get_bit(value, 5):
                if idx == 0:
                    out.append("VS_LOW.12")
                else:
                    out.append("VS_LOW.34")

            if get_bit(value, 4):
                out.append("KEEP_OUT.{}".format(idx*2+2))

            if get_bit(value, 3):
                if idx == 0:
                    out.append("DIE_TEMP_LOW.12")
                else:
                    out.append("DIE_TEMP_LOW.34")

            ## Bit 2 is unimplemented

            if get_bit(value, 1):
                out.append("BACK_BIAS.{}".format(idx*2+2))

            if get_bit(value, 0):
                out.append("OVER_LIMIT.{}".format(idx*2+2))

        return out