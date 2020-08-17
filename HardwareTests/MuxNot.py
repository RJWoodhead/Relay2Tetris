"""
16 Bit MUX-NOT board test.
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

# Number of bits in the unit? Limits values used in testing.

BITS_POPULATED = 16
BIT_MASK = (1 << BITS_POPULATED) - 1

# IO Expander Port assignments.

DATAIN0 = 0x20
DATAIN1 = None  # 0x21  # None to disable (for ZXNX, ZYNY boards)
DATAOUT = 0x22
DATACND = None  # 0x23  # Condition codes output from board (None to disable)

ACTIVE_PORTS = [port for port in [DATAIN0, DATAIN1, DATAOUT, DATACND] if port is not None]

bus = smbus.SMBus(1)    # Communications bus.

# GPIO pin hookups - 16 GPIO on 2 boards.

gpio_pins = [5, 6, 16, 17, 22, 23, 24, 25, 12, 13, 18, 19, 20, 21, 26, 27]

# Register board control lines (GPIO). When using one of my IO Expander
# boards, the GPIO lines are used for board control. Each board has 8
# IO lines available, in a dual-board setup you get 16. Change these
# depending on what control lines the board being tested uses.

CTL_MUX = 1 << 9
CTL_NOT = 1 << 10

CTL_ALL = CTL_MUX | CTL_NOT
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

    for port in ACTIVE_PORTS:
        bus.write_byte_data(port, MCP23017_IODIRA, 0xFF)
        bus.write_byte_data(port, MCP23017_IODIRB, 0xFF)

    GPIO.setup(gpio_pins, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    GPIO.cleanup()
    print("\n")
    sys.exit(0)


# IO Routines...

def configure_bus():
    """
    Configure the MCP registers to default values.
    """

    # Reset to defaults, set ports to input.

    for port in ACTIVE_PORTS:
        for addr in range(22):
            bus.write_byte_data(port, addr, 0xFF if addr <= 1 else 0x00)

    # Set _WRITE pins to output.

    if DATAIN0 is not None:
        bus.write_byte_data(DATAIN0, MCP23017_IODIRA, 0x00)
        bus.write_byte_data(DATAIN0, MCP23017_IODIRB, 0x00)

    if DATAIN1 is not None:
        bus.write_byte_data(DATAIN1, MCP23017_IODIRA, 0x00)
        bus.write_byte_data(DATAIN1, MCP23017_IODIRB, 0x00)

    # Disable pullup on read pins.

    if DATAOUT is not None:
        bus.write_byte_data(DATAOUT, MCP23017_GPPUA, 0x00)
        bus.write_byte_data(DATAOUT, MCP23017_GPPUB, 0x00)

    if DATACND is not None:
        bus.write_byte_data(DATACND, MCP23017_GPPUA, 0x00)
        bus.write_byte_data(DATACND, MCP23017_GPPUB, 0x00)


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

    send_bus(DATAIN0, 0x0000, invert=False, pause=None, trace=False)
    if DATAIN1 is not None:
        send_bus(DATAIN1, 0x0000, invert=False, pause=None, trace=False)

    send_gpio(CTL_ALL, invert=False, pause=None, trace=False)

    # Wait until exited by user.

    print('Raised all signals, CTRL-C to exit.')

    while True:
        sleep(1)


def condition_codes(value):
    """
    Computes the condition codes for any result value. Will vary depending on how you have things wired up.
    In this case, treat the unsigned result as signed.
    """

    return 0b001 if value > 32767 else 0b010 if value == 0 else 0b100


"""
Truth functions for the board; these compute the expected outputs of the device
for each operation. Returns an integer value, name of test tuple
"""


def mux_off_not_off_results(a, b):

    return (a & BIT_MASK, "MUX-OFF NOT-OFF")


def mux_on_not_off_results(a, b):

    return (b & BIT_MASK, "MUX-ON NOT-OFF")


def mux_off_not_on_results(a, b):

    return ((a ^ 0xFFFF) & BIT_MASK, "MUX-OFF NOT-ON")


def mux_on_not_on_results(a, b):

    return ((b ^ 0xFFFF) & BIT_MASK, "MUX-ON NOT-ON")


def test_board(data0, data1, trace=True, subtrace=True):

    def subtest_board(data0, data1, control, results, settle):

        expected = results(data0, data1)

        expected_conditions = condition_codes(expected[0]) if DATACND is not None else 0

        if trace:
            print(f'REG_OUT: data0={data0:016b}, data1={data1:016b}, {expected[1]}: expected={expected[0]:016b}:{expected_conditions:04b}')

        # Set up output lines.

        send_bus(DATAIN0, data0, invert=False, pause=None, trace=subtrace)

        if DATAIN1 is not None:
            send_bus(DATAIN1, data1, invert=False, pause=None, trace=subtrace)

        # Control signals

        send_gpio(control, invert=False, pause=settle, trace=subtrace)

        # Check if output == expected.

        output = get_bus(DATAOUT, trace=subtrace)
        conditions = get_bus(DATACND, trace=subtrace) if DATACND is not None else 0

        if trace:
            print(f'REG_VAL: data={output:016b}')

        if output != expected[0] or conditions != expected_conditions:
            print(f'Error:  data0={data0:016b}, data1={data1:016b}, {expected[1]}: expected={expected[0]:016b}:{expected_conditions:04b}, result={output:016b}:{conditions:04b}')

        return output == expected[0] and conditions == expected_conditions

    # Abort test if second input not available and its value is not zero.

    if DATAIN1 is None and data1 != 0:
        return True

    settle = accel()

    subtests = [(mux_off_not_off_results, CTL_NONE),
                (mux_on_not_off_results, CTL_MUX),
                (mux_off_not_on_results, CTL_NOT),
                (mux_on_not_on_results, CTL_MUX | CTL_NOT)]

    for test, control in subtests:
        if not subtest_board(data0, data1, control, test, settle):
            return False

    return True


"""
Main Program
"""

print(f'Testing Mux-Not Unit...')

signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)

configure_gpio()
configure_bus()

results = (0, 0)

# Signal test routine - uncomment to set all control lines and pause.
# Useful for doing multimeter level checks.

# signal_test()

# Basic tests.

if not test_board(0, 0, trace=True, subtrace=False):
    cleanup()

print('')

if not test_board(BIT_MASK, BIT_MASK, trace=True, subtrace=False):
    cleanup()

print('')

if not test_board(0, BIT_MASK, trace=True, subtrace=False):
    cleanup()

print('')

if not test_board(BIT_MASK, 0, trace=True, subtrace=False):
    cleanup()

print('')

for b in range(BITS_POPULATED):
    bit = 1 << b
    if not test_board(bit, 0, trace=True, subtrace=False):
        cleanup()
    print('')
    if not test_board(0, bit, trace=True, subtrace=False):
        cleanup()
    print('')
    if not test_board(bit, BIT_MASK, trace=True, subtrace=False):
        cleanup()
    print('')

    if not test_board(BIT_MASK, bit, trace=True, subtrace=False):
        cleanup()
    print('')

# Only do random tests if second input is available.

if DATAIN1 is not None:
    tests = 50

    while test_board(random.randint(0, BIT_MASK), random.randint(0, BIT_MASK), trace=False, subtrace=False):
        tests += 1
        if tests % 100 == 0:
            print(f'{tests} tests completed!')

cleanup()
