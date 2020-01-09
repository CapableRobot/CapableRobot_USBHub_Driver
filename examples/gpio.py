import os, sys, inspect, logging, time

lib_folder = os.path.join(os.path.split(inspect.getfile( inspect.currentframe() ))[0], '..')
lib_load = os.path.realpath(os.path.abspath(lib_folder))

if lib_load not in sys.path:
    sys.path.insert(0, lib_load)

import capablerobot_usbhub

hub = capablerobot_usbhub.USBHub()

## Input enabled here on the output so that reading the output's current state works
hub.gpio.configure(ios=[0], output=True, input=True)
hub.gpio.configure(ios=[1], input=True, pull_down=True)

while True:
    
    hub.gpio.io0 = True
    print("IO {} {}".format(*hub.gpio.io))
    time.sleep(1)

    hub.gpio.io0 = False

    print("IO {} {}".format(*hub.gpio.io))
    time.sleep(1)