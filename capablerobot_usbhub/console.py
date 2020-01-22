#!/usr/bin/env python3

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

import os, sys, inspect
import time
import argparse
import logging

import click
import usb

# This allows this file to be run directly and still be able to import the
# driver library -- as relative imports do not work without running as a package.  
# If this library is installed, the else path is followed and relative imports work as expected.
if __name__ == '__main__' and __package__ is None:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from capablerobot_usbhub.main import USBHub
else:
    from .main import USBHub



COL_WIDTH = 12
PORTS = ["Port {}".format(num) for num in [1,2,3,4]]


def _print_row(data):
    print(*[str(v).rjust(COL_WIDTH) for v in data])

def setup_logging():
    fmtstr = '%(asctime)s | %(filename)25s:%(lineno)4d %(funcName)20s() | %(levelname)7s | %(message)s'
    formatter = logging.Formatter(fmtstr)

    handler   = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(formatter)

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)

@click.group()
@click.option('--hub', 'key', default='0', help='Numeric index or key (last 4 characters of serial number) of Hub for command to operate on.')
@click.option('--verbose', default=False, is_flag=True, help='Increase logging level.')
def cli(key, verbose):
    global hub

    if verbose:
        setup_logging()
        logging.debug("Logging Setup")

    hub = USBHub()

    if len(key) == hub.KEY_LENGTH:
        ## CLI parameter is the string key of the hub, so directly use it
        result = hub.activate(key)

        if result is None:
            print("Cannot locate Hub with serial number ending in '{}'".format(key))
            sys.exit(0)

    else:
        ## CLI parameter is the index of the hub, so convert to int
        try:
            result = hub.activate(int(key))
        except ValueError:
            print("Cannot locate Hub at index '{}' as it is not an integer".format(key))
            sys.exit(0)

        if result is None:
            print("Can't attach to Hub with index {} as there only {} were detected".format(key, len(hub.devices)))
            sys.exit(0)

    print()

@cli.command()
def id():
    """Print serial number for attached hub"""

    devices = hub.id(all=True)
    
    if len(devices) > 1:
        print("Revision / Serial")
        for idx,dev in enumerate(devices):
            print("    Hub {} : {} / {}".format(idx, *dev))
    else:
        print("Revision / Serial : {} / {}".format(*(devices[0])))

@cli.group()
def data():
    """Sub-commands for data control & monitoring"""
    pass

@data.command()
@click.option('--port', default=None, help='Comma separated list of ports (1 thru 4) to act upon.')
@click.option('--on', default=False, is_flag=True, help='Enable data to the listed ports.')
@click.option('--off', default=False, is_flag=True, help='Disable data to the listed ports.')
def state(port, on, off):
    """ Get or set per-port data state.  With no arguments, will print out if port data is on or off. """

    if on and off:
        print("Error : Please specify '--on' or '--off', not both.")
        return

    if on or off:
        if port is None:
            print("Error : Please specify at least one port with '--port' flag")
            return
        else:
            port = [int(p) for p in port.split(",")]

    if on:
        hub.data_enable(ports=port)
    elif off:
        hub.data_disable(ports=port)
    else:
        _print_row(PORTS)
        _print_row(hub.data_state())
        _print_row(hub.speeds())

@cli.group()
def power():
    """Sub-commands for power control & monitoring"""
    pass

@power.command()
@click.option('--loop', default=False, is_flag=True, help='Continue to output data until CTRL-C.')
@click.option('--delay', default=500, help='Delay in ms between current samples.')
def measure(loop, delay):
    """ Reports single-shot or continuous power measurements. """

    if loop:
        delay_ms = float(delay)/1000
        start = time.time()

        while True:
            try:
                ellapsed = time.time() - start
                data = hub.power.measurements()

                print("%.3f" % ellapsed, " ".join([("%.2f" % v).rjust(7) for v in data]))
            except usb.core.USBError:
                pass

            time.sleep(delay_ms)
    else:
        _print_row(PORTS)
        _print_row(["%.2f mA" % v for v in hub.power.measurements()])

@power.command()
@click.option('--port', default=None, help='Comma separated list of ports (1 thru 4) to act upon.')
@click.option('--ma', default=2670, help='Current limit in mA for specified ports.')
def limits(port, ma):
    """ Get or set per-port current limits.  With no arguments, will print out active limits. """

    if port is None:
        _print_row(PORTS)
        _print_row(["{} mA".format(v) for v in hub.power.limits()])
    else:
        try:
            port = [int(p) for p in port.split(",")]
            hub.power.set_limits(port, ma)
        except ValueError as e:
            print(e)

@power.command()
def alerts():
    """ Print any power alerts on the downstream ports. """
    data = hub.power.alerts()

    if len(data) == 0:
        print(" -- no alerts --")

    for alert in data:
        print(alert)

@power.command()
@click.option('--port', default=None, help='Comma separated list of ports (1 thru 4) to act upon.')
@click.option('--on', default=False, is_flag=True, help='Enable power to the listed ports.')
@click.option('--off', default=False, is_flag=True, help='Disable power to the listed ports.')
@click.option('--reset', default=False, is_flag=True, help='Reset power to the listed ports (cycles power off & on).')
@click.option('--delay', default=500, help='Delay in ms between off and on states during reset action.')
def state(port, on, off, reset, delay):
    """ Get or set per-port power state.  With no arguments, will print out if port power is on or off. """

    if on and off:
        print("Error : Please specify '--on' or '--off', not both.")
        return

    if on or off or reset:
        if port is None:
            print("Error : Please specify at least one port with '--port' flag")
            return
        else:
            port = [int(p) for p in port.split(",")]

    if on:
        hub.power.enable(ports=port)
    elif off:
        hub.power.disable(ports=port)
    elif reset:
        hub.power.disable(ports=port)
        time.sleep(float(delay)/1000)
        hub.power.enable(ports=port)
    else:
        _print_row(PORTS)
        _print_row(["on" if s else "off" for s in hub.power.state()])


def main():
    cli()
    
if __name__ == '__main__':
    main()