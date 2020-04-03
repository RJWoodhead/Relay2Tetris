# Relay2Tetris

In 2019, I had the great privilege of being able to see the FACOM 128B computer in operation at Fujitsu's company museum. Delving into the technical details of how this machine worked only increased my admiration for the engineers who designed it. This led to a decision to create my own relay-based computer as a hobby project.

A few years prior I ran across the Nand2Tetris course, which I highly recommend. The HACK CPU that students implement in the course is a masterpiece of minimalist CPU design, so it was a natural target for my ambitions.

The goal of this project is to completely implement the HACK CPU in relay logic, and also to provide other relay-computer builders with a set of standard board-level relay logic CPU components, such as registers, adders, and so on.

# Archive Contents

* [Conversion of the idealized HACK CPU architecture to a physical model that addresses timing considerations](Design.md).
* [Component-level HACK simulator](Simulator.md)
* [Datasheets for various hardware components](Datasheets)

The fleshing-out of this archive is an ongoing project; please be patient with the author.

# Current Project Status

* Simulator created.
* 16-Bit Memory Register (Revision 2) built and tested.
* 40-Channel Raspberry PI Output expander designed, test boards in manufacture.
* 16-bit Zuse Adder in design stages; 1-bit prototype built.

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

The materials in this repository are licensed under the [Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0)](https://creativecommons.org/licenses/by-nc-sa/4.0/).
