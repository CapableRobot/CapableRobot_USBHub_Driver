import os, sys, inspect
import time

lib_folder = os.path.join(os.path.split(inspect.getfile( inspect.currentframe() ))[0], '..')
lib_load = os.path.realpath(os.path.abspath(lib_folder))

if lib_load not in sys.path:
    sys.path.insert(0, lib_load)

import capablerobot_usbhub 

hub = capablerobot_usbhub.USBHub()
last = int(time.time() * 1000)

while True:
    now = int(time.time() * 1000)
    print(str(now - last).rjust(3), " ".join([("%.2f" % v).rjust(7) for v in hub.power.measurements()]))
    last = now
    time.sleep(0.5)