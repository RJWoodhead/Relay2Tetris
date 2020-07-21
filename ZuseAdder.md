# 16 Bit Zuse Adder

Note: Please read [The War on Voltage Drop](Voltage.md) for context on the revision history of the PCB boards.

The Zuse Adder is an amazing relay circuit created by computing pioneer [Konrad Zuse](https://en.wikipedia.org/wiki/Konrad_Zuse) in the late 1930s. A normal adder has 3 inputs (the two data bits A and B plus a carry-in bit) and two outputs (the result plus carry-out). This is quite straightforward, but suffers from the problem of carry-propagation delay. Each bit in the sum has to wait until the previous bit is computed in order to get its carry-in bit, so you have to wait for the carry states to ripple down the adder.

The Zuse Adder, on the other hand, has 5 inputs (the two data bits A and B, carry-in, **not-carry-in**, and true) and 3 outputs (the result, carry-out, and not-carry-out). By propagating both the carry state and its inverse, each bit adder always has at least 2 current sources (one of the carries plus the true input), and a clever combination of two 4PDT relays per bit can route these to the correct outputs (only two of which can be true), with no carry propagation delay (other than the electrons meandering down the circuit paths, of course).

It takes a while to wrap your head around exactly how this electromechanical magic trick works, but I've hilighted the connection paths in the [schematic PDF](/Documents/ZuseAdder.pdf) for each of the 8 possible cases.

* Note: I created an alternate EasyEDA schematic for the relays that organized the common and NO/NC contacts in a way that made the schematic simpler. It comes in two variants, one of which has the coils energized. This makes it easier to follow the connection paths.

But it gets better. Normally you set the inputs to the first bit of the adder to carry-in=OFF, not-carry-in=ON. But if you swap this and give the adder carry-in=ON, not-carry-in=OFF, it happily computes A+B+1. If you then set B=0, you have an A+1 incrementor.

And then it gets even better than that. In binary arithmetic, A-B is equivalent to A+(~B)+1. We can already do A+B+1, so if we add a circuit that can produce ~B, the circuit can also subtract! All of this for only 5 DPDT relays per bit!

![16 Bit Zuse Adder Rev 1.0](/Images/ZuseAdder-Rev1.jpeg)

# Revision 1.0

The revision 1.0 Zuse Adder/Subtractor uses the Revision 3.0 Register board as its template, so it has all of the "infrastructure" features of that board.

* 16 Bit Zuse Adder implemented as 4 DPDT relays per bit (+1 if Subtract required)

* Configurable as multiple independent n-bit adders or incrementors. Each bit has solder jumpers that can set the carry-in and not-carry-in to be the start of a new adder, a new incrementor, or carry from the previous bit. So for example, you can configure the board as 2 independent 8-bit adders.

* Optional NOT unit if subtraction is needed; 1 relay per bit.

* Optional outputs for the carry-out of bits 7 and 15 (useful for ALU condition codes).

A short video showing the Revision 1.0 board being tested is available on [YouTube](https://www.youtube.com/watch?v=ZFYi-r_6CD0).

# Revision 2.0

While testing the Revision 1 board, I realized I had made a small mistake. All the relays and the ENABLE LED were connected to ground through the ENABLE relay, but the A and B data display LEDs were connected directly to ground. This meant that when power was provided to the board, there was a path from 3V3 through the power-on LED, then to the ENABLE line, and then backwards through any populated relay or its flyback diode to the associated data display LED, and then to ground. This caused all these LEDs to glow dimly. This did not affect function because as soon as the ENABLE relay connected everything to ground, everything corrected itself.

The solution to this was to cut the data display LED resistor ground connections and wire them to the ENABLE line; this is the blue wire in the photo above.

The other thing I didn't realize at the time was that if all you need is an incrementor, you don't need to populate the two B relays per bit; you just need to bridge their normally-closed pads. I did a quick test of this to create an 8-bit incrementor; a short video is up on [YouTube](https://youtu.be/ckB8yvfqFFo).

The Revision 2.0 board design fixes the ground connection problem and adds bridges on the B relays so you can hardwire them to create a fixed adder with any value (with or without the +1 from configuring things as an incrementor). In my test of the incrementor setup, I set up an incrementor with a fixed B input of 0 (I just bridged the pads with small wires) to get a +1 result.

* Note: I created an alternate EasyEDA PCB Library entry for the B relays that included the solder jumpers. This meant they didn't have to be manually added to the schematic.

Note: It turns out there is a design error with the ENABLE circuit in the Rev 2.0 boards that I am working on addressing. See [this note](LogicUnit.md#board-design-mistake) for more details.

A second error is that if the NOT relay array *is* populated but the SUB activation relay *is not* populated, and SUB is not jumpered, the NC SUB relay connections need to be bridged in order for the adder to operate properly. I omitted solder jumpers for this functionality. The workaround is to use some 0-ohm SMT resistors as jumper wires.

I only ran into this error because I fully populated the board to test out the subtract function, and then removed the activation relays to configure the board for use in my prototype ALU.

I have also incorporated the lessons from the War on Voltage Drop into the Revision 2.0 design.

This board has been manufactured and tested.

# Board Availability

Because of the minimum quantity requirements of the board manufacturer, I have extra Revision 1.0 and 2.0 boards that I don't need. If you want one, email me at trebor@animeigo.com and you can have one for cost+shipping. $10 gets you a board, shipped anywhere in the USA, while supplies last.

# Resources

* [The Z1: Architecture and Algorithms of Konrad Zuse’s First Computer](https://arxiv.org/pdf/1406.1886.pdf).

* [Konrad Zuse’s Legacy: The Architecture of the Z1 and Z3](https://www.semanticscholar.org/paper/Konrad-Zuse's-Legacy%3A-The-Architecture-of-the-Z1-Z3-Rojas/be8b813ffdd21a6d75172344f98ce4dcd67b2d44).

* [Board Test Script](/HardwareTests/ZuseAdder.py).

* [EasyEda Project](https://easyeda.com/MadOverlord/zuse-relay-adder), [Gerber Files](/Gerber/ZuseAdder_Rev_2.0.zip) and [BOM](/BOMs/ZuseAdder_Rev_2.0.zip) for Rev 2.0 board.

* Boards were manufactured by [JLCPCB](https://jlcpcb.com/). Parts were sourced from [LCSC](https://lcsc.com/) and [Digikey](https://www.digikey.com/).
