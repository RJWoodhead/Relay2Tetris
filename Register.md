# 16 Bit Register

Note: Please read [The War on Voltage Drop](Voltage.md) for context on the revision history of the PCB boards.

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

# Revision 2.0 Features (many of these also in 1.0)

* Onboard 3V3 regulator.

* Optional diode isolation of inputs and outputs.

* Control signals are ACT (Active, board is powered), ENA (Enable, board responds to control signals), SET, CLR, and MUX (controls whether DATA-0 or DATA-1 input is read). ACT and ENA can be jumpered to be always-on.

* All control inputs power isolation relays; this means an input signal only has to power one relay, even if the signal controls multiple relays on the board. This minimizes the current flowing through the ribbon cables. So for example, the SET control signal activates a single SETALL relay; that relay controls the 8 SET relays on the board. Each relay draws about 33 milli-amps @ 3V, and each relay contact is limited to about 1 amp, so using both contacts on a relay, you can source 2 amps = 60 relays using a single isolation relay. In practice, you don't want to approach this, so ~40 relays per isolation relay is a reasonable limit. The 16-bit register board has 40 relays driven by power sourced from the ACT relay.

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

* Removed input and output isolation diodes as they are not needed in boards where the inputs are isolated via relays and the outputs do not connect to relay coils, so backfeed to relays is not possible. I had read that backfeed was an issue with relay circuits but I went overboard and didn't think it all the way through. A version of the Rev 3.0 board with isolation relays is available in the EasyEda project in case it is needed for a specific board.

* Changed ENABLE relay so that it controls the SET and CLR relays by disconnecting their GND connections.

* Changed trace sizes to match the expected current loads.

* Made 3V3 regulator optional.

* Moved passthrough jumpers to the rear of the board where possible to save space.

* Eliminated passthrough of pins 17-20 on the IDC connector (again, can be done with cabling), but added jumpers to connect 3V3 and GND to pins 19 and 20. This may be handy if using the output to directly drive a small satellite component, such as a display board.

* Moved traces closer to the edge of the board and rearranged everything to maximize the central area available for a relay array. Currently can handle a grid of 23x6 relays.

I have not yet manufactured any Revision 3.0 boards, but the designs are contained in the EasyEda projects (links below). The core layout (which is actually an edge layout!) will be used in subsequent functional boards.

Note: It turns out there is a design error with the ENABLE circuit in the Rev 3.0 boards that I am working on addressing. See [this note](LogicUnit.md#board-design-mistake) for more details.

![16 Bit Register Rev 2.0/3.0 Comparison](/Images/Register-Rev2-3.gif)

# Revision 4.0 / 4.1

As a consequence of the [The War on Voltage Drop](Voltage.md), the Rev 4.0 board has many improvements:

* Fatter traces to reduce resistance of signal wires.

* Two voltage supply inputs, one of which can be regulated. Board voltage and output voltage can be selected from these.

* Removed ACTIVE signal as it is not really needed.

* Added RESET signal that clears register even when ENABLE is not raised. In the 4.0 board, the RESET may not work correctly if both ENABLE and SET are also raised and the data bus is non-zero. In practice this should not be a problem since RESET would be raised for many cycles, but this has been fixed in the 4.1 board.

* Since there was space on the board, also added a bit test functional unit. There are two independent test channels (one for each pole in the relays), and for each bit position you can specify that the bit has to be True, False, or Don't Care. The tests can also be set up into subtests that only look at a sequence of bits (so you can test high and low bytes separately, for example). Finally, there are outputs for each of the bits, two additional relays for implementing special purpose logic, and you can then jumper all of these to indicator leds and the upper 4 bits of the 20 pin IDC data connectors as well as any of the control lines. A typical use for this would be detecting when the register is zero or negative.

![16 Bit Register Rev 4.0](/Images/Register-Rev4.jpeg)

In the above image, the board is wired to detect 0, -1, and <0.

# Resources

* [Board Test Script](/HardwareTests/Register16.py).

* [EasyEda Project](https://easyeda.com/MadOverlord/16-bit-register), [Gerber Files](/Gerber/Register.zip) and [BOM](/BOMs/Register.csv) for the latest revision of the board.

* Boards were manufactured by [JLCPCB](https://jlcpcb.com/). Parts were sourced from [LCSC](https://lcsc.com/) and [Digikey](https://www.digikey.com/).
