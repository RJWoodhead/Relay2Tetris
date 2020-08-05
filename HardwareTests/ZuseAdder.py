"""
16 Bit Zuse Adder/Subtractor board test. Updated for Revision 2.0
"""

import RPi.GPIO as GPIO
import smbus
import time
import signal
import sys
import random

# Sometimes it is handy to exit without cleaning up, for hardware debugging.

EXIT_DIRTY = False

# Clock tick speed; for demo purposes, we start slow and ramp up.

START_TICK = 0.5
MAX_TICK = 1 / 200.0
TICK_ACCEL = 0.1

# Delay between reads when debouncing board outputs; None = do not debounce.

DEBOUNCE = 1 / 500.0

# Is adder configured as an incrementor or an adder/subtractor.

IS_INCREMENTOR = True

# Is SUBTRACTOR present?

SUBPRESENT = False

# Number of bits in the unit? Limits values used in testing.

BITS_POPULATED = 8
BIT_MASK = (1 << BITS_POPULATED) - 1

# IO Expander Port assignments.

DATAINA = 0x20
DATAINB = 0x21
DATAOUT = 0x22
CONDOUT = 0x23

bus = smbus.SMBus(1)    # Communications bus.

# GPIO pin hookups - 16 GPIO on 2 boards.

gpio_pins = [5, 6, 16, 17, 22, 23, 24, 25, 12, 13, 18, 19, 20, 21, 26, 27]

# Register board control lines (GPIO). When using one of my IO Expander
# boards, the GPIO lines are used for board control. Each board has 8
# IO lines available, in a dual-board setup you get 16. Change these
# depending on what control lines the board being tested uses.

CTL_SUB = 1 << 0

# Handy to have all the control signals together.

CTL_ALL = CTL_SUB
CTL_NONE = 0

# MCP command bytes.

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


def sleep(duration):
    """
    A hopefully reasonably accurate sleep function that we can check if needed.
    """

    elapsed = time.clock_gettime(time.CLOCK_MONOTONIC_RAW)
    time.sleep(duration)
    elapsed = time.clock_gettime(time.CLOCK_MONOTONIC_RAW) - elapsed


def accel():
    """
    Accelerate from START_TICK to MAX_TICK. Apologies for the side-effect.
    """

    global START_TICK

    result = START_TICK
    START_TICK += (MAX_TICK - START_TICK) * TICK_ACCEL

    return result


def cleanup(signo=None, stack_frame=None):
    """
    Clean up the MCP buses and GPIO, then exit.
    """

    if EXIT_DIRTY:
        sys.exit(0)

    bus.write_byte_data(DATAINA, MCP23017_IODIRA, 0xFF)
    bus.write_byte_data(DATAINA, MCP23017_IODIRB, 0xFF)

    bus.write_byte_data(DATAINB, MCP23017_IODIRA, 0xFF)
    bus.write_byte_data(DATAINB, MCP23017_IODIRB, 0xFF)

    GPIO.setup(gpio_pins, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    GPIO.cleanup()
    print("\n")
    sys.exit(0)


# IO Routines...

def configure_bus():
    """
    Configure the MCP registers to default values.
    """

    for addr in range(22):
        bus.write_byte_data(DATAOUT, addr, 0xFF if addr == 0 or addr == 1 else 0x00)
        bus.write_byte_data(CONDOUT, addr, 0xFF if addr == 0 or addr == 1 else 0x00)
        bus.write_byte_data(DATAINA, addr, 0xFF if addr == 0 or addr == 1 else 0x00)
        bus.write_byte_data(DATAINB, addr, 0xFF if addr == 0 or addr == 1 else 0x00)

    # Set _WRITE pins to output.

    bus.write_byte_data(DATAINA, MCP23017_IODIRA, 0x00)
    bus.write_byte_data(DATAINA, MCP23017_IODIRB, 0x00)

    bus.write_byte_data(DATAINB, MCP23017_IODIRA, 0x00)
    bus.write_byte_data(DATAINB, MCP23017_IODIRB, 0x00)

    # Set _READ pins to input.

    bus.write_byte_data(DATAOUT, MCP23017_IODIRA, 0xFF)
    bus.write_byte_data(DATAOUT, MCP23017_IODIRB, 0xFF)
    bus.write_byte_data(CONDOUT, MCP23017_IODIRA, 0xFF)
    bus.write_byte_data(CONDOUT, MCP23017_IODIRB, 0xFF)

    # Disable pullup on _READ pins (we have external pulldown if needed on the board).

    bus.write_byte_data(DATAOUT, MCP23017_GPPUA, 0x00)
    bus.write_byte_data(DATAOUT, MCP23017_GPPUB, 0x00)
    bus.write_byte_data(CONDOUT, MCP23017_GPPUA, 0x00)
    bus.write_byte_data(CONDOUT, MCP23017_GPPUB, 0x00)


def send_bus(device, data, invert=False, pause=None, trace=True):
    """
    Write 16 bits of data to a MCP device.
    """

    lo = data % 256
    hi = data // 256

    if trace:
        print(f'DATA_OUT: device={device:02x} hi={hi:08b} lo={lo:08b} invert={invert}')

    # Note: Signals must be inverted to control common relay boards.

    xor = 0xFF if invert else 0x00

    bus.write_byte_data(device, MCP23017_GPIOA, lo ^ xor)
    bus.write_byte_data(device, MCP23017_GPIOB, hi ^ xor)

    # Give time for results to settle.

    if pause is not None:
        sleep(pause)


def get_bus(device, trace=True):
    """
    Read 16 bits of data from a MCP device.
    """

    lo_in = bus.read_byte_data(device, MCP23017_GPIOA)
    hi_in = bus.read_byte_data(device, MCP23017_GPIOB)

    # Debounce input

    if DEBOUNCE is not None:
        lo_in2, hi_in2 = None, None
        while (lo_in != lo_in2) or (hi_in != hi_in2):
            lo_in2, hi_in2 = lo_in, hi_in
            sleep(DEBOUNCE)
            lo_in = bus.read_byte_data(device, MCP23017_GPIOA)
            hi_in = bus.read_byte_data(device, MCP23017_GPIOB)

    if trace:
        print(f'DATA_IN  : device={device:02x} hi={hi_in:08b} lo={lo_in:08b}')

    return 256*hi_in + lo_in


def configure_gpio():
    """
    Configure GPIO pins.
    """

    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)

    GPIO.setup(gpio_pins, GPIO.OUT, initial=GPIO.LOW)


def send_gpio(data, invert=False, pause=None, trace=True):
    """
    Send 1..N bits of data to the N defined GPIO pins.
    """

    bits = [c == '1' for c in bin(data)[2:]]
    bits.reverse()
    bits = [bits[n] if n < len(bits) else False for n in range(len(gpio_pins))]

    if trace:
        print(f'GPIO_OUT : data={data:0{len(gpio_pins)}b} invert={invert}')

    if invert:
        bits = [not bit for bit in bits]

    GPIO.output(gpio_pins, bits)

    # Give time for results to settle.

    if pause is not None:
        sleep(pause)


def signal_test():
    """
    This is a test routine you can use to raise all the data and control lines so
    you can probe them with a voltmeter on the board. Using MIC2981 @ 5V, you
    should see between 3.0 and 3.6v at the data pins, depending on how many
    relays are being driven.

    My repurposed PC power supply provides about 5.15v under no-load conditions,
    and sags to 4.75v when signal_test() turns on all the data lines.
    """

    # Change this to change the data pattern being sent out.

    send_bus(DATAINA, 0xFF00, invert=False, pause=None, trace=False)
    send_bus(DATAINB, 0x00FF, invert=False, pause=None, trace=False)

    send_gpio(CTL_SUB if SUBPRESENT else CTL_NONE, invert=False, pause=None, trace=False)

    # Wait until exited by user.

    print('Raised all signals, CTRL-C to exit.')

    while True:
        sleep(1)


"""
Truth functions for the board; these compute the expected outputs of the device.
Returns a (result, overflow_16, overflow_8) tuple.
"""


def add_results(a, b):

    a = a & 0xFFFF

    if IS_INCREMENTOR:
        b = 1
    else:
        b = b & 0xFFFF

    result = a + b

    overflow_16 = (result > 0xFFFF)
    result = result & BIT_MASK

    overflow_8 = ((a & 0xFF) + (b & 0xFF)) > 0xFF

    return (result, overflow_16, overflow_8)


def sub_results(a, b):

    a = a & 0xFFFF
    b = b & 0xFFFF

    result = a - b

    overflow_16 = result >= 0
    result = result & 0xFFFF

    overflow_8 = ((a & 0xFF) - (b & 0xFF)) >= 0

    return (result, overflow_16, overflow_8)


def test_zuse(a, b, trace=True, subtrace=True):

    def subtest_zuse(a, b, control, results, settle):

        expected = results(a, b)

        if trace:
            print(f'REG_OUT:  A={a:016b} ({a}), B={b:016b} ({b}), expected={expected}')

        # Set up output lines.

        send_bus(DATAINA, a, invert=False, pause=None, trace=subtrace)
        send_bus(DATAINB, b, invert=False, pause=None, trace=subtrace)

        # Control signals

        send_gpio(control, invert=False, pause=settle, trace=subtrace)

        # Check if output == expected.

        data = get_bus(DATAOUT, trace=subtrace)
        conditions = get_bus(CONDOUT, trace=subtrace)

        output = (data, conditions & 0b01 != 0, conditions & 0b10 != 0)

        if trace:
            print(f'RESULTS:  data={data:016b} ({output})')

        if output != expected:
            print(f'Error:  a={a:016b}, b={b:016b}, expected={expected}, result={output}')

        return output == expected

    settle = accel()

    if not subtest_zuse(a, b, CTL_NONE, add_results, settle):
        return False

    if SUBPRESENT:
        if not subtest_zuse(a, b, CTL_SUB, sub_results, settle):
            return False

    return True


"""
Main Program
"""

print(f'Testing Zuse {"Incrementor" if IS_INCREMENTOR else "Adder"}...')

signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)

configure_gpio()
configure_bus()

results = (0, 0)

# Signal test routine - uncomment to set all control lines and pause.
# Useful for doing multimeter level checks.

# signal_test()

# Basic tests.

if not test_zuse(0, 0, trace=True, subtrace=False):
    cleanup()

print('')

if not test_zuse(BIT_MASK, BIT_MASK, trace=True, subtrace=False):
    cleanup()

print('')

if not IS_INCREMENTOR:
    for bits in [1, 3, 7, 15, 31, 63, 127, 255]:
        for b in range(BITS_POPULATED):
            bit = bits << b
            if not test_zuse(bit, 0, trace=True, subtrace=False):
                cleanup()
            print('')
            if not test_zuse(0, bit, trace=True, subtrace=False):
                cleanup()
            print('')
            if not test_zuse(bit, bit, trace=True, subtrace=False):
                cleanup()
            print('')

    tests = 0
    while test_zuse(random.randint(0, BIT_MASK), random.randint(0, BIT_MASK), trace=False, subtrace=False):
        tests += 1
        if tests % 100 == 0:
            print(f'{tests} random tests completed!')
else:
    print(f'Testing adjacent bits...')
    for bits in [1, 3, 7, 15, 31, 63, 127, 255]:
        for b in range(BITS_POPULATED):
            bit = bits << b
            if bit <= BIT_MASK:
                if not test_zuse(bit, 0, trace=False, subtrace=False):
                    cleanup()
    print(f'Exhaustive test of all values...')
    for i in range(0, BIT_MASK+1):
        if not test_zuse(i, 0, trace=False, subtrace=False):
            cleanup()


cleanup()
