# Raspberry Pi 40-channel IO Expander

In order to control and test the relay-based functional modules this project will require, the ability to control a large number of data channels is required. For example, the 16-bit register board requires 2 16-bit data inputs, 5 bits of control input, and produces 16 bits of data output.

This is far more channels than the Raspberry Pi natively provides, and so some sort of IO Expansion device is needed.

*Note: I am not an electrical engineer. Everything I've learned has been from reading and trying things out. Therefore, take everything here with a grain of salt. It seems to work, but...*

![Operating IO Expander](/Images/IOExp-Operating.jpg)

The common approach in this situation is to use one or more [MCP23017](/Datasheets/MCP23017.pdf) bidirectional IO port chips; each provides 16 channels, and up to 8 can be connected to the Raspberry Pi. However, controlling relays adds a layer of complexity because each relay requires ~30ma of current and the maximum amount of current the chip can provide is 25ma per pin, and 125ma total.

Another chip that people often use when connecting circuits to the Raspberry Pi is the [TXS0108e](/Datasheets/txs0108e.pdf) bidirectional level converter. It is an 8-channel chip that can increase or reduce the voltage of a signal, so it can (for example) convert from 3.3v to 5.0v. However, it too is limited to 50ma per signal and 100ma total.

Therefore, to drive relays, we need to put something between the MCP23017 and the relays that can provide the needed current. What I settled on was the [MIC2981](/Datasheets/mic2981.pdf) driver array; it can provide 8 channels of up to 500ma per channel.

* **One thing about the MIC2981 to be aware of**: under load, the output voltage on a signal line will sag from 1.5-2.0v. On the datasheet, this is cryptically (to a n00b like me) listed as "Collector-Emitter Saturation Voltage". What this means is that if you power the chip at 5v0 (5 volts), what your relays will see is ~3V3 (3.3 volts), which is at the low end of what the relay will respond to. And since the sag is affected by the total amount of current the chip is sourcing, the more signal lines that are high, the lower the voltage on those lines. Before I understood this, I was going nuts trying to figure out why Revision 1 of my relay register board (which used 5V relays) would become unreliable when I asked it to store numbers with lots of set bits! The solution is to provide the MIC2981 with about 1.7v more input voltage than the desired output voltage. In my case, to keep things simple, in the Revision 2 relay board (shown above), I provide 5V0 to the MIC2981 chips, and use 3V relays on the board (which are comfortable with voltages up to 4.5v, so giving them 3.3-3.5v is fine). This also lets me use a standard PC power supply, which provides both 3V3 and 5V0.

I tested using the MCP23017/MIC2981 combination on a breadboard, and then built a project-board version that was a complete rats-nest of wires. It worked, but it certainly wasn't pretty. Since I was going to need a significant number of IO channels, I decided to build a PCB version of the IO expander. This is what I came up with:

![Unpopulated IO Expander](/Images/IOExp-Unpopulated.jpg)

This board supports two MCP23017 chips (2x16 channels) plus 8 channels of direct GPIO from the Raspberry Pi. Up to 4 boards can be daisy-chained together.

Features include:

* For flexibility, each group of 8 channels is routed through a small daughterboard, which is configured to accept one of the TXS0108e daughterboards that are commonly available from lots of different suppliers. In addition, I designed a compatible daughterboard that will accept a MIC2981 or can be jumpered as a passive passthrough. The daughterboard uses the through-hole variant of the MIC2981 because (a) I had some of them and (b) they are slightly cheaper than the surface mount version.

* A forest of output pins make it easy to install IDC-style headers, or wire up custom connectors.

* The MCPs and the A and B sides of the daughterboards can receive their power from the Raspberry Pi or an external power source.

* The Enable signals that the TXS0108e boards require can be jumpered always-on or controlled by GPIO signals.

* Mounting holes for a Raspberry Pi. Typically, you'd mount the Pi above the IO Expander, so the Expander isn't a "Hat", it's a "Shoe".

A detailed [Board Test Script](/HardwareTests/MCPLoopback.py) is also available.

![Populated IO Expander](/Images/IOExp-Populated.jpg)

# Random Things I Learned

These are very simple things. Marvel at my n00bitude.

* Surface mount soldering is fun and easy, but the 0603 resistor arrays are a bit finicky; they tend to accumulate solder bridges. Using a pencil-tip soldering iron set at 280c and flicking the tip between bridged pads is a quick way to eliminate the bridges.

* You can test for bridges on the resistor arrays by measuring the resistance between adjacent pins on the non-ground side; if there is no bridge, the reading will be about 2x the resistor value. Note that this won't work on the first two pins of the arrays below the MCP pins, as the first pin is separate; it's connected to +V and the ~RESET line of the chip.

* The easy way to connect the solder jumpers is to use the soldering iron to heat both pads and then pour a big drop of solder onto it.

# Revision 2.0

Based on my experience with the Revision 1.0 boards, I have designed a Revision 2.0 board with several improvements:

* Solder jumpers for common GPIO hookups (so no nest of wires like in my populated board).

* Optional pulldowns on the underside of the daughterboard on both input and output lines, which may be more convenient than the pulldowns on the mainboard.

* Extra mount hole in the lower part of the board for a support standoff when stacking boards.

I have not yet manufactured any Revision 2.0 boards, but the designs are contained in the EasyEda projects (links below).

![IO Expander Stack](/Images/IOExp-Stack.jpg)

# Board Availability

Because of the minimum quantity requirements of the board manufacturer, I have extra IO Expander and Daughterboard Revision 1.0 boards that I don't need. If you want one, email me at trebor@animeigo.com and you can have one for cost+shipping. $10 gets you the mainboard and 15 daughterboards, shipped anywhere in the USA, while supplies last.

If there is sufficient interest, I may put together a kit of parts and boards.

# Resources

* [Board Test Script](/HardwareTests/MCPLoopback.py)

* IO Expander [EasyEda Project](https://easyeda.com/MadOverlord/rbp-io-expander) and [Gerber Files](/Gerber/IO_Expander_Rev_1.0.zip).

* MIC2981 / Passthrough Daughterboard [EasyEda Project](https://easyeda.com/MadOverlord/io-expander-daughterboard) and [Gerber Files](/Gerber/IO_Expander_Daughterboard_Rev_1.0.zip).

* Boards were manufactured by [JLCPCB](https://jlcpcb.com/). Parts were sourced from [LCSC](https://lcsc.com/) and [Digikey](https://www.digikey.com/).
