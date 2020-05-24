"""
Test MCP Chips using loopback connection.

Tests direct-connected MCP chips and/or grouped GPIO pins.
"""

import RPi.GPIO as GPIO
import smbus
import time
import signal
import sys

# Trace testing?

TRACE = True

# GPIO pin hookups - 16 GPIO on 2 boards.

GPIO_PINS = [5, 6, 16, 17, 22, 23, 24, 25, 12, 13, 18, 19, 20, 21, 26, 27]

# List of tests to perform. Each test is a tuple that lists the source
# and destination devices. If a tuple element is an integer, it is the
# MCP device address; if it is a list, it is a set of GPIO pins.
#
# In this instance, we are testing sending from GPIO pins to a MCP input.

TESTS = [(GPIO_PINS, 0x27)]

# Extract addresses of MCPs used for test.

MCPs = set([item for test in TESTS for item in test if type(item) is not list])

# MCP can send/receive on 16 data lines. GPIOA0-7 are the least
# significant bits; GPIOB0-7 are the most significant bits. In a
# simple connection between the two MCPs, each pin will be
# connected to the same pin of each MCP, but since your mileage
# may vary, a table of pin-pairs is used to specify which pin
# connects to which.

MCP_PINS = [(x, x) for x in range(16)]

# Handy to have a table of 16-bit binary values for the above.

MCP_BITS = [(1 << x, 1 << y) for x, y in MCP_PINS]

# How long do we wait for the data to settle down? As it happens,
# a SETTLE of 0.0 will work fine with pulldown on the data lines
# because since we do a write-A, write-B, read-A, read-B sequence,
# there's a gap between the time we write something and when we
# read it. This may not be the case if there is no external pulldown
# on the lines.

SETTLE = 0.001

# MCP Control Codes.

MCP23017_IODIRA = 0x00
MCP23017_IPOLA = 0x02
MCP23017_GPINTENA = 0x04
MCP23017_DEFVALA = 0x06
MCP23017_INTCONA = 0x08
MCP23017_IOCONA = 0x0A
MCP23017_GPPUA = 0x0C
MCP23017_INTFA = 0x0E
MCP23017_INTCAPA = 0x10
MCP23017_GPIOA = 0x12
MCP23017_OLATA = 0x14

MCP23017_IODIRB = 0x01
MCP23017_IPOLB = 0x03
MCP23017_GPINTENB = 0x05
MCP23017_DEFVALB = 0x07
MCP23017_INTCONB = 0x09
MCP23017_IOCONB = 0x0B
MCP23017_GPPUB = 0x0D
MCP23017_INTFB = 0x0F
MCP23017_INTCAPB = 0x11
MCP23017_GPIOB = 0x13
MCP23017_OLATB = 0x15

bus = smbus.SMBus(1)


def cleanup(signo=None, stack_frame=None):
    """
    Clean up the MCP buses and GPIO, then exit.
    """

    for mcp in MCPs:
        bus.write_byte_data(mcp, MCP23017_IODIRA, 0xFF)
        bus.write_byte_data(mcp, MCP23017_IODIRB, 0xFF)

    GPIO.setup(GPIO_PINS, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    print("\n")
    sys.exit(0)


def test_pin(sender, receiver, pins, bits, trace=False):
    """
    Test devices by sending data from one to the other.
    """

    out_pin, in_pin = pins
    out_data, in_data = bits

    # Write the individual bytes.

    if type(sender) is list:
        bits = [c == '1' for c in bin(out_data)[2:]]
        bits.reverse()
        bits = [bits[n] if n < len(bits) else False for n in range(len(GPIO_PINS))]
        GPIO.output(GPIO_PINS, bits)
    else:
        bus.write_byte_data(sender, MCP23017_GPIOA, out_data & 0xFF)
        bus.write_byte_data(sender, MCP23017_GPIOB, out_data >> 8)

    # Give time for results to settle.

    time.sleep(SETTLE)

    # Read the data from the other device.

    if type(receiver) is list:
        results = 0
        for pin in GPIO_PINS[::-1]:
            results = results + results + GPIO.input(pin)
    else:
        lsb = bus.read_byte_data(receiver, MCP23017_GPIOA)
        msb = bus.read_byte_data(receiver, MCP23017_GPIOB)

        results = (msb << 8) + lsb

    if in_data != results:
        print(f' Error: Pin {out_pin:2} -> {in_pin:2}: Wrote {out_data:016b}, received {results:016b}, expected {in_data:016b}.')
    elif trace:
        print(f'    OK: Pin {out_pin:2} -> {in_pin:2}: Wrote {out_data:016b}, received {results:016b}, expected {in_data:016b}.')

    return in_data == results


def test_loopback(sender, receiver, trace=True):
    """
    Test connection between two devices
    """

    # Configure sender for writing.

    if type(sender) is list:
        if type(receiver) is list:
            print('Error: GPIO -> GPIO test not supported!')
            return
        print(f'Testing GPIO -> MCP {receiver:02x}...')
        GPIO.setup(sender, GPIO.OUT, initial=GPIO.LOW)
        bus_width = len(sender)
    else:
        bus.write_byte_data(sender, MCP23017_IODIRA, 0x00)
        bus.write_byte_data(sender, MCP23017_IODIRB, 0x00)
        bus_width = len(MCP_PINS)

    # Configure receiver for reading.

    if type(receiver) is list:
        print(f'Testing MCP {sender:02x} -> GPIO...')
        GPIO.setup(receiver, GPIO.IN, initial=GPIO.LOW)
    else:
        if type(sender) is not list:
            print(f'Testing MCP {sender:02x} -> MCP {receiver:02x}...')
        bus.write_byte_data(receiver, MCP23017_IODIRA, 0xFF)
        bus.write_byte_data(receiver, MCP23017_IODIRB, 0xFF)
        bus.write_byte_data(receiver, MCP23017_GPPUA, 0x00)
        bus.write_byte_data(receiver, MCP23017_GPPUB, 0x00)

    passed = True
    for i in range(bus_width):
        passed = test_pin(sender, receiver, MCP_PINS[i], MCP_BITS[i], trace) and passed

    print(f'Passed!' if passed else f'** FAILED **')


"""
Main Program
"""

# Configure the MCP registers to default values, and set to input, no pullup.

for mcp in MCPs:
    for addr in range(22):
        bus.write_byte_data(mcp, addr, 0xFF if addr < 2 else 0x00)

# Configure the RBP GPIO to input.

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(GPIO_PINS, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

# Configure for cleanup on program termination.

signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)

# Perform tests.

for sender, receiver in TESTS:
    test_loopback(sender, receiver)

cleanup()
