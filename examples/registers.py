import os, sys, inspect

lib_folder = os.path.join(os.path.split(inspect.getfile( inspect.currentframe() ))[0], '..')
lib_load = os.path.realpath(os.path.abspath(lib_folder))

if lib_load not in sys.path:
    sys.path.insert(0, lib_load)

import capablerobot_usbhub 

hub = capablerobot_usbhub.USBHub()

hub.register_read(name='main::product_id', print=True)
hub.register_read(name='port::connection', print=True)
hub.register_read(name='port::device_speed', print=True)