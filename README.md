# Relay2Tetris

In 2019, I had the great privilege of being able to see the [FACOM 128B](/Documents/FACOM-128B.pdf) computer in operation at Fujitsu's company museum. Delving into the technical details of how this machine worked only increased my admiration for the engineers who designed it. This has inspired me to create my own relay-based computer as a hobby project.

A few years prior I was introduced to the [Nand2Tetris](https://www.nand2tetris.org/) course, which I highly recommend. The HACK CPU that students implement in the course is a masterpiece of minimalist CPU design, so it was a natural target for my ambitions.

The goal of this project is to completely implement the HACK CPU in relay logic, and also to provide other relay-computer builders with a set of standard board-level relay logic CPU components, such as registers, adders, and so on.

# August 2020 Project Status Video

[![YouTube Video](https://img.youtube.com/vi/P-tVBMidEhQ/0.jpg)](https://youtu.be/P-tVBMidEhQ)

# Completed So Far

* [Conversion of the idealized HACK CPU architecture to a physical model that addresses timing considerations](Design.md).
* [Component-level HACK simulator](Simulator.md).
* [40-Channel Daisy-chainable Raspberry Pi IO Expansion Board](IOExpander.md).
* [The War on Voltage Drop](Voltage.md)
* [Register Board](Register.md).
* [Zuse Adder/Subtractor/Incrementor](ZuseAdder.md)
* [8 Function Boolean Logic Unit](LogicUnit.md)
* [2:1 Mux + NOT / Breadboard](MuxNot.md)
* [Useful EasyEDA scripts](EasyEDA.md).
* [Gerber Files for all boards](Gerber).
* [Bills of Materials for all boards](BOMs). (Note: does not include optional components like relay coil voltage drop resistors, voltage regulators, etc., as they will rarely if ever be needed. BOMs are for fully-populated boards including any breadboard relays)
* [Datasheets for various hardware components](Datasheets).
* [YouTube project playlist](https://www.youtube.com/playlist?list=PL5v_4nsiG1zsZgzh9NE4S_au2oJwVJGt1).

The fleshing-out of this archive is an ongoing project; please be patient with the author.

# Recent Update History

2020-08-06: Updated all the board design documents, improved the hardware tests, did some project cleanups. Added a project status video.

2020-07-20: Launched the [War on Voltage Drop](Voltage.md). Redesigned all boards based on the results (see individual board pages for details). Created new IO Expander Daughterboard. Added BOMs for all boards.

# Ongoing Projects

* HACK Machine ALU. Being assembled.

# Still To Do

* Clock and Sequencer.
* Program Counter & Branch Logic.
* Program ROM.
* RAM.

# Surplus Board Availability

Due to minimum quantity requirements, I have extras of most of the various versions of the various boards. If you want one, email me at trebor@animeigo.com and we'll work something out.

# Acknowledgements

Given that I am a programmer by trade, and thus a clueless n00b at hardware design, I am indebted to those who know better than me, including, but not limited to:

[Harry Porter's Relay Computer Project](http://web.cecs.pdx.edu/~harry/Relay/) and [Technical Paper](http://web.cecs.pdx.edu/~harry/Relay/RelayPaper.pdf)

[The Relay Computer Blog](https://relaycomputer.co.uk/)

[The Clicks Relay CPU](http://clicksrelaycpu.blogspot.com/?view=classic)

FACOM 128B Information:

* http://museum.ipsj.or.jp/en/computer/dawn/0012.html
* https://hackaday.com/2019/12/06/visiting-the-facom-128b-1958-relay-computer/

The complete Nand2Tetris course can be found at: https://www.nand2tetris.org/

# License

The materials in this repository (except for those provided by outside sources) are licensed under the [Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0)](https://creativecommons.org/licenses/by-nc-sa/4.0/).
