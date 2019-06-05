import os, sys, inspect
import time

lib_folder = os.path.join(os.path.split(inspect.getfile( inspect.currentframe() ))[0], '..')
lib_load = os.path.realpath(os.path.abspath(lib_folder))

if lib_load not in sys.path:
    sys.path.insert(0, lib_load)

import capablerobot_usbhub 

hub = capablerobot_usbhub.USBHub()
hub.i2c.enable()


import adafruit_ssd1306
oled = adafruit_ssd1306.SSD1306_I2C(128, 32, hub.i2c)

while True:
    oled.fill(0)
    oled.text('Hello World', 0, 0, 1)
    oled.text("{}".format(time.time()), 0, 10, 1)
    oled.show()