# HACK CPU design

The [HACK CPU](https://www.nand2tetris.org/project05) is a minimalist CPU design, but for simplicity, the Nand2Tetris hardware simulator assumes idealized hardware with no gate delays. In the real world of clicky relays, a more detailed design is required. In particular, extra internal registers are needed to break up potential cycles (such as when a register is both the input to and destination of an ALU operation).

This design is a work-in-progress and will undergo significant revision as the actual hardware gets built.

![Block diagram for the expanded design](/Images/BlockDiagram.jpg)

The computer a "tick-tock" clock that sequences through an 12-state loop per instruction. The states are then converted into control signals via a matrix or finite-state machine.

![Instruction State Matrix](/Images/TimingDiagram.jpg)

The clock and sequencer design will be heavily influenced by the excellent work done on the [Relay Computer Blog](https://relaycomputer.co.uk/2014/09/sequencing-control-design-overview).
