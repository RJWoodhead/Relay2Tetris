"""
ALU board assembly test.
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

START_TICK = 1.0
MAX_TICK = 1 / 100.0
TICK_ACCEL = 0.1

# Delay between reads when debouncing board outputs; None = do not debounce.

DEBOUNCE = 1 / 500.0

# Number of bits in the ALU? Limits values used in testing.

BITS_POPULATED = 16
BIT_MASK = (1 << BITS_POPULATED) - 1
SIGN_BIT = (1 << BITS_POPULATED - 1)

# Boards in the ALU stack.

BOARDS = ["X", "Y", "ZXNX", "ZYNY", "AND", "ADD", "MUXN"]

# IO Expander Output Port assignments.

DATA = {"D": 0x20,
        "A": 0x21,
        "M": 0x00}  # if M is zero, do not use Y register MUX.

# IO Expander Input Port assignments (boards we are monitoring)

RESULTS = {"MUXN": 0x22,
           "COND": 0x23}

bus = smbus.SMBus(1)    # Communications bus.

# Register board control lines (GPIO). When using one of my IO Expander
# boards, the GPIO lines are used for board control. Each board has 8
# IO lines available, in a dual-board setup you get 16.

gpio_pins = [5, 6, 16, 17, 22, 23, 24, 25, 12, 13, 18, 19, 20, 21, 26, 27]

# Control signals for the ALU.

CTL_CLR = 1 << 3
CTL_STO = 1 << 4

CTL_ENABXY = 1 << 1

CTL_A = 1 << 6
CTL_ZX = 1 << 7
CTL_NX = 1 << 8
CTL_ZY = 1 << 9
CTL_NY = 1 << 10
CTL_ADD = 1 << 11
CTL_NOT = 1 << 12

# ALU operation names and associated control lines

ALUOPS = {"A": CTL_A,       # M register if set, A register if not set
          "ZX": CTL_ZX,
          "NX": CTL_NX,
          "ZY": CTL_ZY,
          "NY": CTL_NY,
          "ADD": CTL_ADD,   # or AND if not set
          "NOT": CTL_NOT,
          "": 0}            # Dummy operation (needed to parse D&A instruction)

# ALU instruction encoding (and their operations), text version.

INSTRUCTIONS = {"0": "ZX,ZY,ADD",
                "1": "ZX,ZY,NX,NY,ADD,NOT",
                "-1": "ZX,ZY,NX,ADD",
                "D": "ZY,NY",
                "A": "ZX,NX",
                "!D": "ZY,NY,NOT",
                "!A": "ZX,NX,NOT",
                "-D": "ZY,NY,ADD,NOT",
                "-A": "ZX,NX,ADD,NOT",
                "D+1": "NX,ZY,NY,ADD,NOT",
                "A+1": "ZX,NX,NY,ADD,NOT",
                "D-1": "ZY,NY,ADD",
                "A-1": "ZX,NX,ADD",
                "D+A": "ADD",
                "D-A": "NX,ADD,NOT",
                "A-D": "NY,ADD,NOT",
                "D&A": "",
                "D|A": "NX,NY,NOT",
                "M": "A,ZX,NX",
                "!M": "A,ZX,NX,NOT",
                "M+1": "A,ZX,NX,NY,ADD,NOT",
                "M-1": "A,ZX,NX,ADD",
                "D+M": "A,ADD",
                "D-M": "A,NX,ADD,NOT",
                "M-D": "A,NY,ADD,NOT",
                "D&M": "A",
                "D|M": "A,NX,NY,NOT"}

# Omit M instructions if MUX not being used

if DATA["M"] == 0x00:
    INSTRUCTIONS = {k: v for (k, v) in INSTRUCTIONS.items() if "M" not in k}

print(INSTRUCTIONS)

# List version of the operations.

INSTROPS = {k: v.split(",") for (k, v) in INSTRUCTIONS.items()}

# True/False boolean version of the operations.

INSTRBITS = {k: {op: op in v for op in ALUOPS if op != ""} for (k, v) in INSTROPS.items()}

# Bit mask version of the operation.

INSTRMASK = {k: sum([ALUOPS[op] for op in v]) for (k, v) in INSTROPS.items()}

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

    for port in DATA.values():
        if port > 0:
            bus.write_byte_data(port, MCP23017_IODIRA, 0xFF)
            bus.write_byte_data(port, MCP23017_IODIRB, 0xFF)

    for port in RESULTS.values():
        if port > 0:
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

    # Set _WRITE pins to output.

    for port in DATA.values():
        if port > 0:
            for addr in range(22):
                bus.write_byte_data(port, addr, 0xFF if addr == 0 or addr == 1 else 0x00)
            bus.write_byte_data(port, MCP23017_IODIRA, 0x00)
            bus.write_byte_data(port, MCP23017_IODIRB, 0x00)

    # Set _READ pins to input and disable pullup.

    for port in RESULTS.values():
        if port > 0:
            for addr in range(22):
                bus.write_byte_data(port, addr, 0xFF if addr == 0 or addr == 1 else 0x00)
            bus.write_byte_data(port, MCP23017_IODIRA, 0xFF)
            bus.write_byte_data(port, MCP23017_IODIRB, 0xFF)
            bus.write_byte_data(port, MCP23017_GPPUA, 0x00)
            bus.write_byte_data(port, MCP23017_GPPUB, 0x00)


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
    you can probe them with a voltmeter on the board. Since this computes
    ZX-NX-ZY-NY-ADD-NOT, we get ZXNX = -1, ZYNY = -1, ADD = -2, AND = -1, ALU = 1
    """

    # Change this to change the data pattern being sent out.

    for port in DATA.values():
        if port > 0:
            send_bus(port, 0xFFFF, invert=False, pause=None, trace=False)

    send_gpio(0xFFFF, invert=False, pause=None, trace=False)

    # Wait until exited by user.

    print('Raised signals, CTRL-C to exit.')

    while True:
        sleep(1)


def alu_output(data, op):
    """
    Compute the expected results of a data, operation pair. Each parameter is
    a dictionary of values. Returns a dictionary of the expected output of
    each board in the stack.
    """

    xreg = data["D"]
    xreg &= BIT_MASK

    yreg = data["M"] if op["A"] else data["A"]
    yreg &= BIT_MASK

    zxnx = 0 if op["ZX"] else xreg
    zxnx = ~zxnx if op["NX"] else zxnx
    zxnx &= BIT_MASK

    zyny = 0 if op["ZY"] else yreg
    zyny = ~zyny if op["NY"] else zyny
    zyny &= BIT_MASK

    andop = zxnx & zyny
    andop &= BIT_MASK

    addop = zxnx + zyny
    addop &= BIT_MASK

    muxn = addop if op["ADD"] else andop
    muxn = ~muxn if op["NOT"] else muxn
    muxn &= BIT_MASK

    cond = 0b010 if muxn == 0 else 0b100 if muxn & SIGN_BIT == 0 else 0b001

    return {"X": xreg,
            "Y": yreg,
            "ZXNX": zxnx,
            "ZYNY": zyny,
            "AND": andop,
            "ADD": addop,
            "MUXN": muxn,
            "COND": cond}


def test_alu(d, a, m, ops={}, omit=[], slomo=False, trace=True):
    """
    Run the ALU and compare the results to what is expected. If slomo
    is true, update the control signals one at a time to animate the
    computation process.
    """

    data = {"D": d, "A": a, "M": m}

    print(f'TEST_ALU : data={data}')

    # Set up data output channels. In slomo mode we animate them later.

    for register, value in data.items():
        if DATA[register] > 0:
            send_bus(DATA[register], 0 if slomo else value, invert=False, pause=None, trace=False)

    ops = ops if ops else INSTRUCTIONS
    ops = {op: signals for op, signals in ops.items() if op not in omit}

    for op, signals in ops.items():

        settle = accel()

        bits = INSTRBITS[op]
        expected = alu_output(data, bits)

        if slomo:
            for register, value in data.items():
                if DATA[register] > 0:
                    send_bus(DATA[register], 0, invert=False, pause=None, trace=False)

        # Clock the D/A/M data into the X and Y registers and compute the answer.

        send_gpio(CTL_ENABXY, invert=False, pause=settle, trace=False)
        send_gpio((CTL_A if bits["A"] else 0) | CTL_ENABXY | CTL_STO | CTL_CLR, invert=False, pause=settle, trace=False)

        # If slomo mode, individually update the incoming data values so they populate the registers, then
        # individually update the control lines.

        if slomo:
            for register, value in data.items():
                if DATA[register] > 0:
                    send_bus(DATA[register], value, invert=False, pause=settle, trace=False)
                    print(f'   DATA-{register}={value} {value:016b}')
            command = 0
            for control_line, value in bits.items():
                if value:
                    command |= ALUOPS[control_line]
                    print(f'   {control_line} added = {command:016b}')
                    send_gpio(command | CTL_ENABXY | CTL_STO, invert=False, pause=settle, trace=False)
            send_gpio(command | CTL_ENABXY | CTL_STO, invert=False, pause=settle, trace=False)
            send_gpio(command | CTL_ENABXY, invert=False, pause=settle, trace=False)
        else:
            send_gpio((CTL_A if bits["A"] else 0) | CTL_ENABXY | CTL_STO | INSTRMASK[op], invert=False, pause=settle, trace=False)
            send_gpio((CTL_A if bits["A"] else 0) | CTL_ENABXY | INSTRMASK[op], invert=False, pause=settle, trace=False)

        # send_gpio(INSTRMASK[op], invert=False, pause=settle, trace=False)

        received = {k: get_bus(reg, trace=False) for (k, reg) in RESULTS.items()}
        failed = [result != expected[k] for (k, result) in received.items()]
        if trace or any(failed):
            print(f'   Op={op}, Sig={signals}, CTL={INSTRMASK[op]:016b}, Exp={expected}, Rcv={received}')
        if any(failed):
            return False

    if trace:
        print('')

    return True


def fibdemo():
    """
    Demonstrate fibonacci sequence in slow motion.
    """

    global START_TICK

    d = 0
    a = 1

    print(d)
    print(a)

    while d <= 46368:
        START_TICK = 0.25
        test_alu(d, a, 0, ops={"D+A": "ADD"}, slomo=True, trace=False)
        d, a = d+a, d
        print(d)


"""
Main Program
"""

print(f'Testing ALU...')

signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)

configure_gpio()
configure_bus()

results = (0, 0)

# Signal test routine - uncomment to set all control lines and pause.
# Useful for doing multimeter level checks.

# signal_test()

# Basic tests.

if not test_alu(BIT_MASK, BIT_MASK, BIT_MASK, slomo=False, trace=True):
    cleanup()

# After initial test we can omit constant operations.

if not test_alu(0x000F & BIT_MASK, 0x00F0 & BIT_MASK, 0xFF00 & BIT_MASK, omit=["0", "1", "-1"], slomo=False, trace=True):
    cleanup()

if not test_alu(BIT_MASK, BIT_MASK, 0, omit=["0", "1", "-1"], slomo=False, trace=True):
    cleanup()

if not test_alu(BIT_MASK, 0, BIT_MASK, omit=["0", "1", "-1"], slomo=False, trace=True):
    cleanup()

# After full-bit tests, we can omit M operations since MUX is now verified

for bit_position in range(BITS_POPULATED):
    bit = 1 << bit_position
    if not test_alu(bit, bit, 0, omit=["0", "1", "-1", "M", "!M", "M+1", "M-1", "D+M", "D-M", "M-D", "D&M", "D|M", "D", "A"], trace=True):
        cleanup()
    if not test_alu(0, bit, 0, omit=["0", "1", "-1", "M", "!M", "M+1", "M-1", "D+M", "D-M", "M-D", "D&M", "D|M", "D", "A"], trace=True):
        cleanup()
    if not test_alu(bit, 0, 0, omit=["0", "1", "-1", "M", "!M", "M+1", "M-1", "D+M", "D-M", "M-D", "D&M", "D|M", "D", "A"], trace=True):
        cleanup()

fibdemo()

tests = 52

print('Commencing Random Tests...')
print('')

while test_alu(random.randint(0, BIT_MASK),
               random.randint(0, BIT_MASK),
               0,
               omit=["0", "1", "-1", "M", "!M", "M+1", "M-1", "D+M", "D-M", "M-D", "D&M", "D|M"],
               trace=False):
    tests += 1
    if tests % 100 == 0:
        print(f'{tests} tests completed!')

cleanup()
