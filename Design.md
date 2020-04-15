# HACK CPU design

The [HACK CPU](https://www.nand2tetris.org/project05) is a minimalist CPU design, but for simplicity, the Nand2Tetris hardware simulator assumes idealized hardware with no gate delays. In the real world of clicky relays, a more detailed design is required. In particular, extra internal registers are needed to break up potential cycles (such as when a register is both the input to and destination of an ALU operation).

![Block diagram for the expanded design](/Images/BlockDiagram.jpg)

The current design uses a "tick-tock" clock that sequences through an 8-state loop per instruction. The states are then converted into control signals via a matrix.

![Instruction State Matrix](/Images/TimingDiagram.jpg)
