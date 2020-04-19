"""
Simple 16 Bit Register board test.
"""

import RPi.GPIO as GPIO
import smbus
import time
import signal
import sys

# Clock tick time. Starts to become unreliable around 400-500hz.

TICK = 1.0 / 250.0

# Number of cycles in torture test section.

TORTURE = 25

# Is MUX present?

MUXPRESENT = False

# IO Expander Port assignments.

DATAIN0 = 0x20
DATAIN1 = 0x21
DATAOUT = 0x22

bus = smbus.SMBus(1)    # Communications bus.

# IO Expander GPIO pin hookups.

gpio_pins = [5, 6, 16, 17, 22, 23, 24, 25]

# Register board control lines (GPIO). When using one of my IO Expander
# boards, the GPIO lines are used for board control, so there are 8
# possible control lines.

CTL_ACTIVE = 0b00000001
CTL_ENABLE = 0b00000010
CTL_MUX = 0b00000100
CTL_SET = 0b00001000
CTL_CLR = 0b00010000

# Handy to have all the control signals together.

CTL_ALL = CTL_ACTIVE | CTL_ENABLE | CTL_SET | CTL_CLR | CTL_MUX

# The sequence of control operations in a store operation. Note that
# the output value does not become stable until the end of the final
# CTL_ACTIVE cycle. The register needs a tick after CTL_SET
# goes down before it becomes reliably valid. I don't quite understand
# what is going on here, because halving the clock rate doesn't remove
# the need for the sub-tick.
#
# This sequence does not include MUX operations.

SEQUENCE = [(TICK, CTL_ACTIVE | CTL_ENABLE),
            (TICK, CTL_ACTIVE | CTL_ENABLE | CTL_SET | CTL_CLR),
            (TICK, CTL_ACTIVE | CTL_ENABLE | CTL_SET | CTL_CLR),
            (TICK, CTL_ACTIVE | CTL_ENABLE | CTL_SET),
            (TICK, CTL_ACTIVE | CTL_ENABLE | CTL_SET),
            (TICK, CTL_ACTIVE)]

# MUX-enabled version of SEQUENCE.

SEQUENCE_MUX = [(tick, bits | CTL_MUX) if bits != CTL_ACTIVE else (tick, bits) for (tick, bits) in SEQUENCE]

# Basic test patterns for the torture test.

PATTERNS = [0b1111111111111111,
            0b0000000000000000,
            0b1010101010101010,
            0b0101010101010101,
            0b1100110011001100,
            0b0011001100110011,
            0b1111000011110000,
            0b0000111100001111,
            0b1111111100000000,
            0b0000000011111111]

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


def cleanup(signo=None, stack_frame=None):
    """
    Clean up the MCP buses and GPIO, then exit.
    """

    bus.write_byte_data(DATAIN0, MCP23017_IODIRA, 0xFF)
    bus.write_byte_data(DATAIN0, MCP23017_IODIRB, 0xFF)

    if MUXPRESENT:
        bus.write_byte_data(DATAIN1, MCP23017_IODIRA, 0xFF)
        bus.write_byte_data(DATAIN1, MCP23017_IODIRB, 0xFF)

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
        bus.write_byte_data(DATAIN0, addr, 0xFF if addr == 0 or addr == 1 else 0x00)
        if MUXPRESENT:
            bus.write_byte_data(DATAIN1, addr, 0xFF if addr == 0 or addr == 1 else 0x00)

    # Set _WRITE pins to output.

    bus.write_byte_data(DATAIN0, MCP23017_IODIRA, 0x00)
    bus.write_byte_data(DATAIN0, MCP23017_IODIRB, 0x00)

    if MUXPRESENT:
        bus.write_byte_data(DATAIN1, MCP23017_IODIRA, 0x00)
        bus.write_byte_data(DATAIN1, MCP23017_IODIRB, 0x00)

    # Set _READ pins to input.

    bus.write_byte_data(DATAOUT, MCP23017_IODIRA, 0xFF)
    bus.write_byte_data(DATAOUT, MCP23017_IODIRB, 0xFF)

    # Disable pullup on _READ pins (we have external pulldown if needed on the board).

    bus.write_byte_data(DATAOUT, MCP23017_GPPUA, 0x00)
    bus.write_byte_data(DATAOUT, MCP23017_GPPUB, 0x00)


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

    if trace:
        print(f'DATA_IN:  device={device:02x} hi={hi_in:08b} lo={lo_in:08b}')

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
        print(f'GPIO_OUT: data={data:0{len(gpio_pins)}b} invert={invert}')

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
    relays are being driven. So since MUX is raised, if you plug the data output
    into DATA-IN-1, you'll get a lower value since the data lines will be driving
    relays (and all the outputs will light up). But if you plug the output into
    DATA-IN-0, you'll get a higher voltage on the data pins because the MIC2981
    isn't doing any real work.

    My repurposed PC power supply provides about 5.15v under no-load conditions,
    and sags to 4.75v when signal_test() turns on all the data lines.
    """

    # Change this to change the data pattern being sent out.

    send_bus(DATAIN0, 0xFFFF, invert=False, pause=None, trace=False)
    if MUXPRESENT:
        send_bus(DATAIN1, 0xFFFF, invert=False, pause=None, trace=False)
    send_gpio(CTL_ALL, invert=False, pause=None, trace=False)

    # Wait until exited by user.

    print('Raised all signals, CTRL-C to exit. Remember: since MUX raised, data is on second connector...')

    while True:
        sleep(1)


def test_register_mux(data0, data1, sequence, expected, trace=True, subtrace=False):
    """
    Test the register. Set the data line(s), send the control sequence, and
    check to see if the expected data appears on the output lines.
    """

    if trace:
        print(f'REG_OUT:  data0={data0:016b}, data1={data1:016b}, expected={expected:016b}')

    # Set up output lines.

    send_bus(DATAIN0, data0, invert=False, pause=None, trace=subtrace)

    if MUXPRESENT:
        send_bus(DATAIN1, data1, invert=False, pause=None, trace=subtrace)

    # Send command sequence with individual settle times.

    for settle, control_lines in sequence:
        if trace:
            output = get_bus(DATAOUT, trace=subtrace)
            print(f'Control={control_lines}, Settle={settle}, REG_VAL=data={output:016b}')
        send_gpio(control_lines, invert=False, pause=settle, trace=subtrace)

    # Check if output == expected.

    output = get_bus(DATAOUT, trace=subtrace)

    if trace:
        print(f'REG_VAL:  data={output:016b}')

    if output != expected:
        print(f'Error:  data0={data0:016b}, data1={data1:016b}, expected={expected:016b}, result={output:016b}')

    return output == expected


def test_register(data, trace=False, subtrace=False):
    """
    Test the register, first using the DATA-IN-0 port, and then
    the DATA-IN-1 port if the MUX is present. The other port
    always gets the inverse of the desired data.
    """

    antidata = data ^ 0xFFFF

    results = test_register_mux(data, antidata, SEQUENCE, data, trace, subtrace)

    if MUXPRESENT:
        test_register_mux(antidata, data, SEQUENCE_MUX, data, trace, subtrace) and results

    return results


"""
Main Program
"""

print(f'Testing 16 bit register...')

signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)

configure_gpio()
configure_bus()

results = (0, 0)

# Signal test routine - uncomment to set all control lines and pause.
# Useful for doing multimeter level checks.

# signal_test()

# Basic tests.

if not test_register(0, trace=True, subtrace=False):
    print('** FAILED ALL-ZEROS TEST')
    cleanup()

print('')

if not test_register(0xFFFF, trace=True, subtrace=False):
    print('** FAILED ALL-ONES TEST')
    sys.exit(0)
    cleanup()

print('')

for b in range(16):
    if not test_register(1 << b, trace=True, subtrace=False):
        print(f'** FAILED {1 << b:016b} BIT TEST')
        cleanup()
    print('')


tests = 18
loops = 0

while True:

    # Rotation Test.

    for w in range(1, 15):
        base = sum([1 << n for n in range(w)])
        for s in range(16):
            if not test_register(base, trace=False):
                print(f'*** FAILED AFTER {tests} tests!')
                cleanup()
            tests += 1
            base = base << 1
            if base >= 65536:
                base = base - 65535

    # Torture Tests.

    for w in range(1, TORTURE):
        b = test_register(0b0000000000000000, trace=False)
        b = b & test_register(0b1111111111111111, trace=False)
        if not b:
            print(f'*** FAILED AFTER {tests} tests!')
            cleanup()
        tests += 2

    for w in range(1, TORTURE):
        b = test_register(0b1010101010101010, trace=False)
        b = b & test_register(0b0101010101010101, trace=False)
        if not b:
            print(f'*** FAILED AFTER {tests} tests!')
            cleanup()
        tests += 2

    for w in range(1, TORTURE):
        b = test_register(0b1100110011001100, trace=False)
        b = b & test_register(0b0011001100110011, trace=False)
        if not b:
            print(f'*** FAILED AFTER {tests} tests!')
            cleanup()
        tests += 2

    for w in range(1, TORTURE):
        b = test_register(0b1111000011110000, trace=False)
        b = b & test_register(0b0000111100001111, trace=False)
        if not b:
            print(f'*** FAILED AFTER {tests} tests!')
            cleanup()
        tests += 2

    for w in range(1, TORTURE):
        b = test_register(0b1111111100000000, trace=False)
        b = b & test_register(0b0000000011111111, trace=False)
        if not b:
            print(f'*** FAILED AFTER {tests} tests!')
            cleanup()
        tests += 2

    test_register(0b0000000000000000, trace=False)

    loops += 1
    print(f'Loop {loops} completed; {tests} tests performed!')

cleanup()
