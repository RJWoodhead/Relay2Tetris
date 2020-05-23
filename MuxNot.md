# 2:1 Mux + NOT Board

This board is pretty simple. It consists of a 2:1 input multiplexer connected to a NOT unit.

![16 Bit Mux + Not 1.0](/Images/MuxNot.jpg)

Two of these board will be used in the ALU to compute the ZERO and NOT operations on the X and Y inputs. ZERO is a simple matter of not connecting B-IN to anything! If the MUX bit is then set, the input to the NOT unit is all zeroes.

The desired operations can be hardwired for the entire board or on a per-bit basis using solder bridges.

[![YouTube Video](https://img.youtube.com/vi/2-9iTJ1my6Y/0.jpg)](https://youtu.be/2-9iTJ1my6Y)

A short video showing the Revision 1.0 board being tested is available on [YouTube](https://youtu.be/2-9iTJ1my6Y).

Note: It turns out there is a design error with the ENABLE circuit in this board that I am working on addressing. See [this note](LogicUnit.md#board-design-mistake) for more details. The temporary workaround is to jumper the board so it is always ENABLEd.

# Board Availability

Because of the minimum quantity requirements of the board manufacturer, I have extra Revision 1.0 boards that I don't need. If you want one, email me at trebor@animeigo.com and you can have one for cost+shipping. $10 gets you a board, shipped anywhere in the USA, while supplies last.

# Resources

* [Board Test Script](/HardwareTests/MuxNot.py).

* [EasyEda Project](https://easyeda.com/MadOverlord/16-bit-relay-2-1-mux-not) and Gerber files for [Rev 1.0](/GerberMuxNot_Rev_1.0.zip).

* Boards were manufactured by [JLCPCB](https://jlcpcb.com/). Parts were sourced from [LCSC](https://lcsc.com/) and [Digikey](https://www.digikey.com/).
