"""
Quick Test Skeleton for GPIO. Used to manually check GPIO -> Pin 33-40 connections
"""

import RPi.GPIO as GPIO
import time
import signal
import sys

# Sometimes it is handy to exit without cleaning up, for hardware debugging.

EXIT_DIRTY = True

# GPIO pin hookups - 16 GPIO on 2 boards

gpio_pins = [5, 6, 16, 17, 22, 23, 24, 25, 12, 13, 18, 19, 20, 21, 26, 27]


def sleep(duration):
    """
    A hopefully reasonably accurate sleep function that we can check if needed.
    """

    elapsed = time.clock_gettime(time.CLOCK_MONOTONIC_RAW)
    time.sleep(duration)
    elapsed = time.clock_gettime(time.CLOCK_MONOTONIC_RAW) - elapsed


def cleanup(signo=None, stack_frame=None):
    """
    Clean up the GPIO, then exit.
    """

    if EXIT_DIRTY:
        sys.exit(0)

    GPIO.setup(gpio_pins, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    GPIO.cleanup()
    print("\n")
    sys.exit(0)


# IO Routines...

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

    if trace:
        print(f'HIGH_PINS: {[pin for pin, bit in zip(gpio_pins, bits) if bit]}')

    # Give time for results to settle.

    if pause is not None:
        sleep(pause)


"""
Main Program
"""

print(f'Setting GPIO...')

signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)

# Set the GPIO to whatever is needed, then quit without cleanup.

configure_gpio()

send_gpio(0b1000000000000011)

# cleanup()
