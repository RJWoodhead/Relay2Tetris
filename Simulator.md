The [Relay2Tetris simulator](/Simulators) simulates the proposed HACK CPU implementation at the board-level, and updates the state of control signals and component inputs and output every clock tick.

Eventually, this simulator will have the ability to interface with the actual hardware, and gradually migrate more and more component functions to the actual device.

The Tests subdirectory contains a set of test programs for the simulator, adapted from the Nand2Tetris HACK tests.

**NOTE**: The current version of the simulator is running an older version of the hardware design that does not match the [current design](design.md). The simulator will be updated to match the hardware design when larger chunks of the hardware are being integrated.

# Running the simulator

Usage: python3 validate.py [Test name (subfolder of Tests folder)] {Trace Level: [N]one|[I]nstruction|[C]lock|[S]ettle}

Test folder [xxx] will contain up to 4 files.

* [xxx].hack : The machine code source file (output of the Nand2Tetris assembler) - required

* [xxx].asm : Human-readable source code (input to the Nand2Tetris assembler)

* [xxx].tst : Validation test script (input to the Nand2Tetris emulator)

* [xxx].cmp : Validation comparison results

If [xxx].tst is present, the validator runs the test script and compares the output to the contents of the [xxx].cmp file. If not, the validator just runs the machine code.

To make parsing simpler, there is a restriction on the test scripts: there can be only one output-list, and the formatting is ignored.

The load, output-file, and compare-to commands are ignored because they are implied by the files in the test folder, and these files need to be loaded before the script is executed.

For convenience, the validator recognizes when the machine has entered the infinite-loop end condition and exits script repeat loops early in this situation.

The default trace level is [I]nstruction, which provides machine state at the start of each instruction cycle. [C]lock lets you see the internal state of all signals at each machine clock. [S]ettle shows that plus the process of settling on the hardware state. [N]one just reports the results of the validation.
