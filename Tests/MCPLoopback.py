"""
Test MCP Chips using loopback connection.

Typically, the MCPs on the board are connected via a loopback connection.
Any GPIO lines are cross-connected.
"""

import RPi.GPIO as GPIO
import smbus
import time
import signal
import sys

# Trace testing?

TRACE = True

# Available tests.

MCP0TO1 = 0  # Send from first MCP to second one.
MCP1TO0 = 1  # Send from second MPC to first one.
RBPPINS = 2  # Send between RBP GPIO pins.

# Test command tuple: Command, BoardMCP0 address, BoardMCP1 address
# Standard MCP address pairs are 0x20-21, 22-23, 24-25, 26-27.
#
# Some common test configurations are defined below.

# Basic 1st Board test, also testing GPIO pins.

TESTS = [(MCP0TO1, 0x20, 0x21),
         (MCP1TO0, 0x20, 0x21),
         (RBPPINS, None, None)]

"""
# 2nd Board Test, no GPIO pins.

TESTS = [(MCP0TO1, 0x22, 0x23),
         (MCP1TO0, 0x22, 0x23)]

# 3nd Board Test, no GPIO pins.

TESTS = [(MCP0TO1, 0x24, 0x25),
         (MCP1TO0, 0x24, 0x25)]

# 4th Board Test, no GPIO pins.

TESTS = [(MCP0TO1, 0x26, 0x27),
         (MCP1TO0, 0x26, 0x27)]

# Dual Board Test, sending from one board to the other.

TESTS = [(MCP0TO1, 0x20, 0x22),
         (MCP0TO1, 0x21, 0x23)]

"""

# Extract addresses of MCPs used for test.

MCPs = set([item for test in TESTS for item in test if item and item >= 0x20])

# MCP can send/receive on 16 data lines. GPIOA0-7 are the least
# significant bits; GPIOB0-7 are the most significant bits. In a
# simple connection between the two MCPs, each pin will be
# connected to the same pin of each MCP, but since your mileage
# may vary, a table of pin-pairs is used to specify which pin
# connects to which. When sending in reverse, these pins are
# swapped.

MCP_PINS = [(x, x) for x in range(16)]

# Handy to have a table of 16-bit binary values for the above.

MCP_BITS = [(1 << x, 1 << y) for x, y in MCP_PINS]

# We also do the same thing for the GPIO pins; since we have 8 pins
# that's 4 pairs. These are the defaults if you use the lowest-
# numbered set of general-purpose GPIO pins on the RBP.

RBP_PINS = [(5, 6), (16, 17), (22, 23), (24, 25)]

# Also handy to have a flat list of all the RBP pins.

RBP_ALLPINS = [pin for pins in RBP_PINS for pin in pins]

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

    GPIO.setup(RBP_ALLPINS, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    print("\n")
    sys.exit(0)


def test_MCP_pin(MCPs, pins, bits, swap, trace=False):
    """
    Test MCP by sending data from one chip to the other. If swap is
    True, swap the sender & receiver and their respective pins.
    """

    sender, receiver = MCPs
    out_pin, in_pin = pins
    out_data, in_data = bits

    if swap:
        out_pin, in_pin = in_pin, out_pin
        out_data, in_data = in_data, out_data
        sender, receiver = receiver, sender

    # Write the individual bytes.

    bus.write_byte_data(sender, MCP23017_GPIOA, out_data & 0xFF)
    bus.write_byte_data(sender, MCP23017_GPIOB, out_data >> 8)

    # Give time for results to settle.

    time.sleep(SETTLE)

    # Read the data from the other device.

    lsb = bus.read_byte_data(receiver, MCP23017_GPIOA)
    msb = bus.read_byte_data(receiver, MCP23017_GPIOB)

    results = (msb << 8) + lsb

    if in_data != results:
        print(f' Error: MCP[{sender:02x}] -> MCP[{receiver:02x}]: Pin {out_pin:2} -> {in_pin:2}: Wrote {out_data:016b}, received {results:016b}, expected {in_data:016b}.')
    elif trace:
        print(f'    OK: MCP[{sender:02x}] -> MCP[{receiver:02x}]: Pin {out_pin:2} -> {in_pin:2}: Wrote {out_data:016b}, received {results:016b}, expected {in_data:016b}.')

    # Check RBP GPIO input lines to see if there is any leakage, just out of paranoia.

    gpio_data = [GPIO.input(pin) for pin in RBP_ALLPINS]
    gpio_leak = [pin for bit, pin in zip(gpio_data, RBP_ALLPINS) if bit != GPIO.LOW]

    if gpio_leak:
        print(f' NOTE: MCP[{sender:02x}] -> MCP[{receiver:02x}]: Wrote {out_data:016b}, leaked to RBP GPIO pins {gpio_leak}.')

    return in_data == results


def test_MCP_pair(MCPs, swap, trace=False):
    """
    Test connection between MCP chips. If swap == True, swap sender & receiver devices.
    """

    sender, receiver = MCPs

    if swap:
        sender, receiver = receiver, sender

    print(f'Testing MCP[{sender:02x}] -> MCP[{receiver:02x}]...')

    # Configure sender for writing.

    bus.write_byte_data(sender, MCP23017_IODIRA, 0x00)
    bus.write_byte_data(sender, MCP23017_IODIRB, 0x00)

    # Configure receiver for reading.

    bus.write_byte_data(receiver, MCP23017_IODIRA, 0xFF)
    bus.write_byte_data(receiver, MCP23017_IODIRB, 0xFF)
    bus.write_byte_data(receiver, MCP23017_GPPUA, 0x00)
    bus.write_byte_data(receiver, MCP23017_GPPUB, 0x00)

    passed = True
    for i in range(len(MCP_PINS)):
        passed = test_MCP_pin(MCPs, MCP_PINS[i], MCP_BITS[i], swap, trace) and passed

    print(f'Passed!' if passed else f'** FAILED **')


def test_RBP_GPIO(trace=False):
    """
    Test RBP GPIO loopback.
    """

    print(f'Testing RBP GPIO...')

    passed = True

    # For each pair of pins and direction.

    for pin_a, pin_b in RBP_PINS:
        for swap in [False, True]:

            if swap:
                pin_a, pin_b = pin_b, pin_a

            # Write pin_a, read all others.

            otherpins = [pin for pin in RBP_ALLPINS if pin != pin_a]

            GPIO.setup(otherpins, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
            GPIO.setup(pin_a, GPIO.OUT, initial=GPIO.HIGH)

            # Give time for results to settle.

            time.sleep(SETTLE)

            # Read the state of all the input pins, and filter out the high bits

            gpio_data = [(pin, GPIO.input(pin)) for pin in otherpins]
            gpio_data = [data for data in gpio_data if data[1] != GPIO.LOW]

            if len(gpio_data) != 1 or gpio_data[0][0] != pin_b:
                passed = False
                print(f' Error: GPIO set pin {pin_a}, expected data on {pin_b}, received data on {[pin for pin, data in gpio_data]}.')
            elif trace:
                print(f'    OK: GPIO set pin {pin_a}, expected data on {pin_b}, received data on {[pin for pin, data in gpio_data]}.')

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
GPIO.setup(RBP_ALLPINS, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

# Configure for cleanup on program termination.

signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)

# Perform tests.

for test, mcp0, mcp1 in TESTS:
    if test == MCP0TO1:
        test_MCP_pair([mcp0, mcp1], False, TRACE)
    elif test == MCP1TO0:
        test_MCP_pair([mcp0, mcp1], True, TRACE)
    elif test == RBPPINS:
        test_RBP_GPIO(TRACE)
    else:
        print(f'Error: Unknown test type [{test}].')

cleanup()
