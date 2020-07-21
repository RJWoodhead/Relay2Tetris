# The War on Voltage Drop

As previously mentioned, I am an electronics n00b. This caused me to make a fundamental -- but fortunately, easily rectifiable -- mistake when originally designing the boards.

I chose to use 3 volt relays in the design because I thought it would make the interconnection to the Raspberry Pi easier, but to my chagrin, it ended up casting my electronics inexperience in a harsher light than I would prefer.

In any circuit, there is a voltage applied across the entire circuit. So for one of my relay circuits, this would typically be about 3.3 volts, as this was the standard signal voltage for the Pi. So if you measure the voltage from the voltage source to the ground, you'd get 3.3 volts.

The relays have a minimum reliable operating voltage of 80% of their rating; in this case that would be 2.4 volts. 3.3 is > 2.4, so this should be okay, right?

Nope.

What counts is the voltage drop across the relay (measured from one side of the relay coil to the other). That has to be at least 2.4 volts. And that voltage depends on the entire circuit.

You can think of the circuit as having three segments in series; the wires leading from the voltage source to the relay, the relay, and the wires leading from the relay to ground. The voltage drop across each segment is proportional to the resistance of each segment - so as long as the resistance of the wires is less than about 28% of the resistance of the relay, the relay will have a voltage drop above our 2.4 volt minimum threshold.

What's the resistance of the coil of the 3 volt relays? 91 ohms. This means that the total resistance of all the wires in series with the coil can only be about 30 ohms. That's not all that much.

But it gets worse. If you drive two relays with the same signal, they are in parallel. This means the resistance across both relays is halved. So now you can only afford 15 ohms of wire resistance. If you are driving three relays, you're down to 10.

Danger, Will Robinson!

There is, however, an easy fix. Returning to the relay data sheet, we are surprised to learn that the coil resistance of the 12 volt relay is... 1315 ohms! Quadrupling the voltage of the coil increases its resistance by 14.5x!

It took me a little while to wrap my pointy head around why this is so. It works like this:

* Both the 3 volt and 12 volt relays consume about the same amount of power.

* Power = Voltage * Current.

* Voltage = Current * Resistance -> Current = Voltage / Resistance.

* So Power = Voltage * Voltage / Resistance.

* Since Power must remain the same, in an ideal world if we 4x the voltage, we have to 16x the resistance.

The end result is that if I switch from 3 volt to 12 volt relays, the relay resistance dominates, and the voltage drops caused by the wiring become much less significant.

Therefore, I am:

* Switching to 12 volt relays. Anyone need any 3 volt relays? I've got a few extras... :(

* Revising all the PCB designs in light of what I've learned; in particular, embiggening the PCB traces as much as possible to reduce their resistance. In addition, the power circuitry has been simplified, with optional on-board regulation, and using either regulated or unregulated power for both the board power and output power.

* Manufacturing the new boards with 2oz copper traces instead of the normal 1oz out of pure paranoia.

* Designing a new IO Expander daughterboard that uses a voltage divider circuit to reduce 12 volt signals coming from the boards down to 3.3 volt signals that can be read directly by the MCP23017 chips.

So far I have received, populated and tested both the Register and Zuse Adder boards using 12 volt relays; the voltage drop caused by the cabling is now negligible. In addition, even with the voltage drop from the MIC2981 drivers on the IO Expander board, when driven by a 12 volt PC power supply (which really only provides 11.7 volts), the voltage is high enough to reliably drive the relays (at least in a single-board test). If this turns out not to be the case in a multi-board configuration, I can provide a separate, slightly higher voltage power supply to the 2981s.

I'd say "Mission Accomplished" but history tells us that saying that doesn't age well. :)
