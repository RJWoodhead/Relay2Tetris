# 2:1 Mux + NOT Board

Note: Please read [The War on Voltage Drop](Voltage.md) for context on the revision history of the PCB boards.

This board is pretty simple. It consists of a 2:1 input multiplexer connected to a NOT unit.

# Revision 1.0

![16 Bit Mux + Not 1.0](/Images/MuxNot.jpg)

Two of these board will be used in the ALU to compute the ZERO and NOT operations on the X and Y inputs. ZERO is a simple matter of not connecting B-IN to anything! If the MUX bit is then set, the input to the NOT unit is all zeroes.

The desired operations can be hardwired for the entire board or on a per-bit basis using solder bridges.

[![YouTube Video](https://img.youtube.com/vi/2-9iTJ1my6Y/0.jpg)](https://youtu.be/2-9iTJ1my6Y)

A short video showing the Revision 1.0 board being tested is available on [YouTube](https://youtu.be/2-9iTJ1my6Y).

Note: It turns out there is a design error with the ENABLE circuit in this board that I am working on addressing. See [this note](LogicUnit.md#board-design-mistake) for more details. The temporary workaround is to jumper the board so it is always ENABLEd.

# Revision 2.0

![16 Bit Mux + Not 2.0](/Images/MuxNot-Rev2.jpeg)

Revision 2.0 of the board incorporates all of the lessons learned during the War on Voltage Drop. In addition, the unused space on the board has been filled with a relay breadboard that may come in handy.

# Resources

* [Board Test Script](/HardwareTests/MuxNot.py).

* [EasyEda Project](https://easyeda.com/MadOverlord/16-bit-relay-2-1-mux-not), [Gerber Files](/Gerber/MuxNot.zip) and [BOM](/BOMS/MuxNot.csv) for the latest revisions.

* Boards were manufactured by [JLCPCB](https://jlcpcb.com/). Parts were sourced from [LCSC](https://lcsc.com/) and [Digikey](https://www.digikey.com/).
