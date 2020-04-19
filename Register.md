# 16 Bit Register

The Relay2Tetris project uses dual-pole, dual-throw (DPDT) relays. These have two independent circuits (the poles), each of which has an input and two outputs. When the relay is not energized, the inputs are connected to the normally-closed (NC) outputs, and when energized, the inputs are connected to the normally-open (NO) outputs.

The core element of the register is the self-latching relay circuit. In this circuit, when the BIT relay that holds the data is energized, one of the poles is used to complete a HOLD circuit that connects the relay coil to the power source. So once it gets energized, it stays energized. The second pole of the BIT relay is used to control the output of the register.

However, this circuit is also routed through the NC part of a second relay, the Clear (CLR) relay. Thus, when the CLR relay is energized, the HOLD circuit is broken. This circuit is hilighted in red in the illustration below.

![2 Bit Register Circuit](/Images/RegisterWiring.jpg)

The second half of the circuit is the SET circuit. This is a relay that uses a NO part to gate the DATA-IN bit to the BIT relay coil, shown in blue above. When the relay is not energized, the BIT relay is isolated from the DATA-IN; it therefore maintains its state and is not affected by changes in DATA-IN.

Thus, the behavior of the circuit is as follows:

SET | CLR | Behavior
--- | --- | -------------------
Off | Off | BIT relays hold their value.
Off | On  | BIT relays reset to 0.
On  | Off | BIT relays are OR'd with incoming DATA
On  | On  | BIT relays are set to incoming DATA.

The usual control sequence for updating the register is thus SET+CLR (to replace the contents of the register), followed by SET alone (to ensure the data is being maintained by the HOLD circuit), followed by neither (to isolate the register from the inputs).

Since the CLR and SET relays have two poles, they can support two BIT relays. Thus, the basic building block is a 4-relay unit that stores 2 bits.

Repeat this 2-bit register 8 times, and the result is a 16-bit register.

![16 Bit Register Rev 1.0](/Images/Register-Rev1.jpeg)

The Revision 1.0 board used inexpensive 5V through-hole relays. While fully functional, I did run into a few problems, the most confusing one being a voltage drop "gotcha" with the MIC2981 driver chips (see the [IOExpander](/IOExpander.md) writeup for details). After experimenting with the board at length, I designed a Revision 2.0 board that used 3V relays, and also moved to using surface mount components.

This allowed me to increase the component density and shrink the board significantly. Also, the 3V relays, while 3x as expensive as the cheap 5V ones, also switch 4x faster! So all in all, a good deal! In addition, I added a optional 2:1 multiplexer on the DATA-IN lines, as many of the registers in the final design have two possible inputs.

# Revision 2.0 Features

* Onboard 3V3 regulator.

* Optional diode isolation of inputs and outputs.

* Control signals set by jumpers.

* Optional 2:1 Input Multiplexer.

* Optional signal passthrough connectors.

* Jumperable passthrough of the 4 unused IDC-20 signal lines on input to output.

* 3V0 relays running at ~3V3. Selectable 3V3 or 5V0 signal output.


![16 Bit Register Rev 2.0](/Images/Register-Rev2.jpeg)

A detailed [Board Test Script](/HardwareTests/Register16.py) is also available. It requires my IOExpander board.

[![YouTube Video](https://img.youtube.com/vi/gMaYLL4p_do/0.jpg)](https://www.youtube.com/watch?v=gMaYLL4p_do)

A short video showing the Revision 2.0 board being tested is available on [YouTube](https://www.youtube.com/watch?v=gMaYLL4p_do).

# Revision 3.0

Based on my experience with the Revision 1.0 and 2.0 boards, I have designed a Revision 3.0 board with several improvements:

* Removed signal passthrough connectors because that function can be handled with custom cables that are easier to configure.

* Removed power isolation relays, they are not really needed.

* Changed ENABLE relay so that it controls the SET and CLR relays by disconnecting their GND connections.

* Changed trace sizes to match the expected current loads.

* Made 3V3 regulator optional.

* Moved many of the passthrough jumpers to the rear of the board to save space.

* Eliminated passthrough of pins 17-20 on the IDC connector (again, can be done with cabling), but added jumpers to connect 3V3 and GND to pins 19 and 20. This may be handy if using the output to directly drive a small satellite component, such as a display board.

* Moved traces closer to the edge of the board and rearranged everything to maximize the central area available for a relay array. Currently can handle a grid of 23x6 relays.

I have not yet manufactured any Revision 3.0 boards, but the designs are contained in the EasyEda projects (links below). The core layout (which is actually an edge layout!) will be used in subsequent functional boards.

![16 Bit Register Rev 2.0/3.0 Comparison](/Images/Register-Rev2-3.gif)

# Board Availability

Because of the minimum quantity requirements of the board manufacturer, I have extra Revision 1.0 and 2.0 boards that I don't need. If you want one, email me at trebor@animeigo.com and you can have one for cost+shipping. $10 gets you a board, shipped anywhere in the USA, while supplies last.

# Resources

* [Board Test Script](/HardwareTests/Register16.py).

* 16 Bit Register [EasyEda Project](https://easyeda.com/MadOverlord/16-bit-register) and [Gerber Files](/Gerber/Register_Rev_2.0.zip).

* Boards were manufactured by [JLCPCB](https://jlcpcb.com/). Parts were sourced from [LCSC](https://lcsc.com/) and [Digikey](https://www.digikey.com/).