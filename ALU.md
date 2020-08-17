# Arithmetic-Logic Unit Assembly

The ALU is the first multi-board assembly in the project. It consists of:

* Two input data registers, X and Y. In the full computer, the X register is loaded with the value of D,
and the Y register is loaded with either A or M (using a multiplexer to select the desired input).

* Two Mux-Not boards, ZXNX and ZYNY. These first use the multiplexer to select either the input data or zero,
and then the Not unit to optionally negate the result. Thus, the ZXNX board can generate 0, -1, X and ~X,
and the ZYNY unit can generate 0, -1, Y and ~Y.

* An AND board and an ADD board, both of which are fed the outputs of ZXNX and ZYNY.

* A final Mux-Not board, which selects either desired AND or ADD output, and then optionally negates it.
This generates the output data value.

The ALU thus has 6 control lines, ZX (Zero X), NX (Negate X), ZY (Zero Y), NY (Negate Y), ADD (if 0, the AND output is used),
and NR (Not Result).

Surprisingly, the resulting ALU can compute all of the following values:

0, 1, -1, X, Y, ~X, ~Y, -X, -Y, X+1, Y+1, X-1, Y-1, X+Y, X-Y, Y-X, X&Y and X|Y

Actually, these are just the operations that are defined as part of the Hack machine language.
There are also some other [undefined operations of various utility](https://medium.com/@MadOverlord/14-nand2tetris-opcodes-they-dont-want-you-to-know-about-f3246831d1d1) that the ALU can perform.

# Physical Assembly

The boards are assembled using some [simple 3D-printed brackets](/STL) and connected using custom IDC cables.

![16 Bit Logic Unit 1.0](/Images/AluBottom.jpeg)

# Testing

The ALU flawlessly completes the test script at a clock speed of 100 hz; it starts to become slightly unreliable at ~200 hz. Voltage drops are negligible, typically 100-150 millivolts. The drivers on the IO Expander provide a little over 10 volts when driven by the 12 volt input, but have no problems driving the control relays on the all boards. This bodes well.

Here is a video of the board being exercised.

[![YouTube Video](https://img.youtube.com/vi/6PPwGQYELfU/0.jpg)](https://youtu.be/6PPwGQYELfU)

# Resources

* [Board Test Script](/HardwareTests/ALU.py).
