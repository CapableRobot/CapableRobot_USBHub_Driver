import os, sys, inspect, logging, time

lib_folder = os.path.join(os.path.split(inspect.getfile( inspect.currentframe() ))[0], '..')
lib_load = os.path.realpath(os.path.abspath(lib_folder))

if lib_load not in sys.path:
    sys.path.insert(0, lib_load)

FORMAT = '%(levelname)-8s %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger('USB Hub Status')
logger.setLevel(logging.DEBUG)

import capablerobot_usbhub

hub = capablerobot_usbhub.USBHub()

ports = [1,2,3,4]
for port in ports:
    logger.info("enable port %d" % port)
    hub.power.enable([port])
    time.sleep(0.5)
    logger.info("disable port %d" % port)
    hub.power.disable([port])
    time.sleep(0.5)
