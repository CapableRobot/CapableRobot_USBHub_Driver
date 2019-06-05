def bits_to_bytes(bits):
    return int(bits / 8)

def int_from_bytes(xbytes, endian='big'):
    return int.from_bytes(xbytes, endian)

def hexstr(value):
    return hex(value).upper().replace("0X","")

def split(value):
    return [value & 0xFF, value >> 8]

def build_value(start=True, stop=True, nack=True, addr=0):
    flags = 0
    if nack:
        flags += 4
    if start:
        flags += 2
    if stop:
        flags += 1

    return (flags << 8) + addr