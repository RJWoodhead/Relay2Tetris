"""
Read MCP chip(s) and report their values.
"""

import smbus
import time
import signal
import sys


# List of MCPs to poll.

MCPs = [0x22]

# How often do we poll?

RATE = 0.01

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
    Clean up the MCP buses, then exit.
    """

    for mcp in MCPs:
        bus.write_byte_data(mcp, MCP23017_IODIRA, 0xFF)
        bus.write_byte_data(mcp, MCP23017_IODIRB, 0xFF)

    print("\n")
    sys.exit(0)


def read_mcp(receiver, previous, masklsb, maskmsb, loop_count, trace=False):
    """
    Read a MCP (debouncing signal) and display value
    """

    lsb = bus.read_byte_data(receiver, MCP23017_GPIOA) & masklsb
    msb = bus.read_byte_data(receiver, MCP23017_GPIOB) & maskmsb

    lsb2 = bus.read_byte_data(receiver, MCP23017_GPIOA) & masklsb
    msb2 = bus.read_byte_data(receiver, MCP23017_GPIOB) & maskmsb

    while (lsb != lsb2) or (msb != msb2):
        lsb, msb = lsb2, msb2
        lsb2 = bus.read_byte_data(receiver, MCP23017_GPIOA) & masklsb
        msb2 = bus.read_byte_data(receiver, MCP23017_GPIOB) & maskmsb

    results = (msb << 8) + lsb

    if trace:
        prev = f' != {previous:016b}' if results != previous and previous is not None else ''
        print(f'{loop_count:03d} : MCP 0x{receiver:02x} & 0x{maskmsb:02x}{masklsb:02x}: {results:016b}{prev}')

    return results


"""
Main Program
"""

# Configure the MCP registers to default values, and set to input, no pullup.

for mcp in MCPs:
    for addr in range(22):
        bus.write_byte_data(mcp, addr, 0xFF if addr < 2 else 0x00)

# Configure for cleanup on program termination.

signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)

# Perform tests.

loop_count = 1
previous = {receiver: None for receiver in MCPs}

while True:
    for receiver in MCPs:
        previous[receiver] = read_mcp(receiver, previous[receiver], 0xFF, 0xFF, loop_count, True)
    loop_count = (loop_count + 1) % 1000
    time.sleep(RATE)

cleanup()
