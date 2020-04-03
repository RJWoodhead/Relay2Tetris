#
# Relay2Tetris Component definitions. Each component simulates a physical hardware component,
# and can optionally control the physical component for testing
#
# (C)2019 Robert Woodhead - trebor@animeigo.com
# License: Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0)
#
# Please note that I have chosen readability over economy of expression/efficiency
# in this code.

# --------------------------------------------------------------
# Base Class for all components
# --------------------------------------------------------------

import sys
import re


class Color:
    """ Color codes: see https://stackoverflow.com/questions/8924173/how-do-i-print-bold-text-in-python """
    PURPLE = "\033[95m"
    CYAN = "\033[96m"
    DARKCYAN = "\033[36m"
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    END = "\033[0m"


# -----------------------------------------------------
# Utility function to determine if component has power.
# True if there is any active source of power, or if
# no sources are defined (default is powered!)
# -----------------------------------------------------

def powered(power, signals):

    if power == []:
        return True
    else:
        for p in power:
            if p in signals and signals[p]:
                return True

    return False


class Component:
    """ Base hardware component class

        inputs are the input signals.
        outputs are the output signals.
        power is the list of potential power sources; if any are True, the component generates output.
        state is a dictionary of internal state that is maintained by the component, or config parameters.
        emulated is True if we are doing a software emulation.
        sequence is the definition sequence, used to sort components when displaying detailed machine state.
    """

    __sequence__ = 0

    # Massage the inputs into regular form, handle defaults.

    def _massage(self, name, inputs, outputs, power, state, emulated, sequence):

        # Allow string for single element parameter

        inputs = inputs if isinstance(inputs, list) else [inputs]
        outputs = outputs if isinstance(outputs, list) else [outputs]
        power = power if isinstance(power, list) else [power]

        # Default output and power values

        outputs = [name] if not outputs else outputs
        power = ["TRUE"] if not power else power

        return name, inputs, outputs, power, state, emulated, sequence

    # Initialize state of the component - set inputs and outputs randomly to simulate
    # power-on.

    def __init__(self, name="", inputs=[], outputs=[], power=[], state={}, emulated=True, sequence=None):

        self.name = name                                # Component name
        self.inputs = {i: False for i in inputs}        # Input lines
        self.outputs = {o: False for o in outputs}      # Output lines
        self.power = {p: False for p in power}          # Power sources (any one will do, none=always on)
        self.state = {k: v for k, v in state.items()}   # Internal state - must make a copy!
        self.emulated = emulated                        # Emulated in software

        # Display order for debugging.

        if sequence is None:
            self.sequence = Component.__sequence__      # Order of declaration
            Component.__sequence__ += 1                 # Increment
        else:
            self.sequence = sequence

    # Print instance.

    def __str__(self):

        items = []
        if self.inputs != {}:
            items.append(f'inputs={self.inputs}')
        if self.outputs != {}:
            items.append(f'outputs={self.outputs}')
        if self.power != {}:
            items.append(f'power={self.power}')
        if self.state != {}:
            items.append(f'state=={self.state}')
        items.append("Emulated" if self.emulated else "PHYSICAL")
        items.append(f'Sequence={self.sequence}')

        return f'{self.name}({", ".join(items)})'

    # Update state of the component.

    def update(self, signals={}):

        # Update the state of the controls and inputs from the global machine state
        # subclasses will use this for their initial update, then compute output.
        # This is done both to validate inputs and for potential tracing later on.

        for c in self.inputs:
            if c in signals:
                self.inputs[c] = signals[c]
            else:
                sys.exit(f'{Color.RED}Error: Component [{self.name}] requires unknown input signal [{c}]{Color.END}')

        for c in self.power:
            if c in signals:
                self.power[c] = signals[c]
            else:
                sys.exit(f'{Color.RED}Error: Component [{self.name}] requires unknown power signal [{c}]{Color.END}')


# --------------------------------------------------------------
# Reset button
# --------------------------------------------------------------

class Reset(Component):
    """ Reset button

        No inputs (but has set/clear functions).
    """

    def __init__(self,
                 name="RESET",
                 inputs=[],
                 outputs=["RESET", "~RESET"],
                 power=["TRUE"],
                 state={"RESET": False},
                 emulated=True,
                 sequence=None):

        name, inputs, outputs, power, state, emulated, sequence = \
            super()._massage(name, inputs, outputs, power, state, emulated, sequence)

        super().__init__(
            name=name,
            inputs=inputs,
            outputs=outputs,
            power=power,
            state=state,
            emulated=emulated,
            sequence=sequence)

        self.reset = outputs[0]     # Reset signal name.
        self.notreset = outputs[1]  # ~Reset signal name.

    # Update state of the component.

    def update(self, signals={}):

        super().update(signals)

        if not powered(self.power, signals):
            for output in self.outputs.keys():
                self.outputs[output] = False
            self.state["RESET"] = False
            return

        self.outputs[self.reset] = self.state["RESET"]
        self.outputs[self.notreset] = not self.state["RESET"]

    # Raise and lower reset line.

    def set(self):

        print(f'{Color.GREEN}{Color.BOLD}RESET raised.{Color.END}')
        self.state["RESET"] = True
        self.state["~RESET"] = False
        self.outputs[self.reset] = self.state["RESET"]
        self.outputs[self.notreset] = not self.state["RESET"]

    def clr(self):

        print(f'{Color.GREEN}{Color.BOLD}RESET dropped.{Color.END}')
        self.state["RESET"] = False
        self.state["~RESET"] = True
        self.outputs[self.reset] = self.state["RESET"]
        self.outputs[self.notreset] = not self.state["RESET"]


# --------------------------------------------------------------
# Master system clock just goes tick-tock-tick-tock.
# --------------------------------------------------------------

class Clock(Component):
    """ System clock

        Ticks off machine cycles, alternates between True and False.
        Can have multiple outputs, but why would you?
    """

    def __init__(self,
                 name="CLOCK",
                 inputs=[],
                 outputs=["CLOCK"],
                 power=[],
                 state={"TICKTOCK": False, "TIME": 0},
                 emulated=True,
                 sequence=None):

        name, inputs, outputs, power, state, emulated, sequence = \
            super()._massage(name, inputs, outputs, power, state, emulated, sequence)

        super().__init__(
            name=name,
            inputs=inputs,
            outputs=outputs,
            power=power,
            state=state,
            emulated=emulated,
            sequence=sequence)

    # Update state of the component.

    def update(self, signals={}):

        super().update(signals)

        if not powered(self.power, signals):
            for output in self.outputs.keys():
                self.outputs[output] = False
            self.state["TICKTOCK"] = False
            self.state["TIME"] = 0
            return

        for output in self.outputs.keys():
            self.outputs[output] = self.state["TICKTOCK"]

    # Tick the clock.

    def tick(self, signals):

        if not powered(self.power, signals):
            for output in self.outputs.keys():
                self.outputs[output] = False
            self.state["TICKTOCK"] = False
            self.state["TIME"] = 0
            return self.state["TIME"]

        self.state["TICKTOCK"] = not self.state["TICKTOCK"]
        self.state["TIME"] += 1

        return self.state["TIME"]


# --------------------------------------------------------------
# Sequencer cycles between states once per tick transition.
# --------------------------------------------------------------

class Sequencer(Component):
    """ System clock sequencer

        Advances state each time clock state changes.
        Input 0 is CLOCK.
        Input 1 is RESET.
        Outputs are Sx and SxA, Sx starts at cycle X and lasts 2 cycles, SxA starts at cycle X and lasts 1 cycle.
        Generates output names automatically.
        state["TICKS"] is how many cycles there are in a machine instruction.
    """

    def __init__(self,
                 name="SEQUENCER",
                 inputs=["CLOCK", "RESET"],
                 outputs=[],
                 power=[],
                 state={"TICKS": 10},
                 emulated=True,
                 sequence=None):

        name, inputs, outputs, power, state, emulated, sequence = \
            super()._massage(name, inputs, outputs, power, state, emulated, sequence)

        # Assemble the output names.

        ticks = state["TICKS"]
        outputs = [f'S{tick}' for tick in range(ticks)]
        outputs.extend([f'S{tick}A' for tick in range(ticks)])

        self.clock = inputs[0]              # Clock signal name.
        self.reset = inputs[1]              # Reset signal name.

        state["LASTCLOCK"] = False          # Value of last clock edge.
        state["CYCLE"] = 0                  # Current cycle.

        super().__init__(
            name=name,
            inputs=inputs,
            outputs=outputs,
            power=power,
            state=state,
            emulated=emulated,
            sequence=sequence)

    # Update state of the component.

    def update(self, signals={}):

        super().update(signals)

        # Handle power-off situation.

        if not powered(self.power, signals):
            for output in self.outputs.keys():
                self.outputs[output] = False
            self.state["CYCLE"] = 0
            self.state["LASTCLOCK"] = False
            return

        # Move to next tick if clock state has changed, with two
        # restrictions: only move from state 0 if RESET is low
        # and new clock state is high.

        cycle = self.state["CYCLE"]

        if self.inputs[self.clock] != self.state["LASTCLOCK"]:
            if cycle > 0:
                cycle += 1
                if cycle == self.state["TICKS"]:
                    cycle = 0
            else:
                if self.inputs[self.reset]:
                    pass
                else:
                    cycle = 1

        self.state["LASTCLOCK"] = self.inputs[self.clock]
        self.state["CYCLE"] = cycle

        # Clear all the outputs.

        for output in self.outputs.keys():
            self.outputs[output] = False

        # Current signal outputs

        self.outputs[f'S{cycle}'] = True
        self.outputs[f'S{cycle}A'] = True

        if cycle != 0:
            self.outputs[f'S{cycle-1}'] = True


# --------------------------------------------------------------
# Matrix takes the sequencer signals and computes the sequence
# control signals.
# --------------------------------------------------------------

class Matrix(Component):
    """ System control generator
        state["ARRAY"] is dictionary of output:[inputs]. If any of the signals in an inputs
        list is True, the associated output is true.
    """

    def __init__(self,
                 name="MATRIX",
                 inputs=[],
                 outputs=[],
                 power=[],
                 state={},
                 emulated=True,
                 sequence=None):

        name, inputs, outputs, power, state, emulated, sequence = \
            super()._massage(name, inputs, outputs, power, state, emulated, sequence)

        super().__init__(
            name=name,
            inputs=inputs,
            outputs=outputs,
            power=power,
            state=state,
            emulated=emulated,
            sequence=sequence)

    # Update state of the component.

    def update(self, signals={}):

        super().update(signals)

        # Handle power-off situation.

        if not powered(self.power, signals):
            for output in self.outputs.keys():
                self.outputs[output] = False
            return

        # For each item in the state array, the output is the or of all
        # the inputs. In hardware this is a sparse diode array.

        for output, inputs in self.state["ARRAY"].items():
            self.outputs[output] = any([self.inputs[input] for input in inputs])

# --------------------------------------------------------------
# System ROM (contains programs). Also generates fake signal
# containing assembly language code.
# --------------------------------------------------------------


class ROM(Component):
    """ ROM

        Emulates the ROM.

        Input is the ROM address to read.
        Output 0 is the contents of the ROM.
        Output 1 is the assembly language version of the ROM.

        Also parses the assembly code and extracts names of symbols, which
        are stored as value:name pairs in the state. Assumes the HACK convention
        of allocating new symbols starting at location 16. All of this is
        an attempt to make the execution traces more readable.
    """

    def __init__(self,
                 name="ROM",
                 inputs=["PC"],
                 outputs=["ROM", "ASM"],
                 power=[],
                 state={"ROM": [], "ASM": [], "SYMB": []},
                 emulated=True,
                 sequence=None):

        name, inputs, outputs, power, state, emulated, sequence = \
            super()._massage(name, inputs, outputs, power, state, emulated, sequence)

        super().__init__(
            name=name,
            inputs=inputs,
            outputs=outputs,
            power=power,
            state=state,
            emulated=emulated,
            sequence=sequence)

        self.addr = inputs[0]
        self.rom = outputs[0]
        self.asm = outputs[1]

        # Parse the assembly code and generate the symbols list.

        symbols = {0: "R0/SP", 1: "R1/LCL", 2: "R2/ARG", 3: "R3/THIS",
                   4: "R4/THAT", 5: "R5", 6: "R6", 7: "R7", 8: "R8",
                   9: "R9", 10: "R10", 11: "R11", 12: "R12", 13: "R13",
                   14: "R14", 15: "R15", 16384: "SCREEN", 24576: "KBD"
                   }

        # Need to keep separate list of known symbols because of the double-symbols like RO/SP.

        known = ["R0", "SP", "R1", "LCL", "R2", "ARG", "R3", "THIS", "R4", "THAT",
                 "R5", "R6", "R7", "R8", "R9", "R10", "R11", "R12", "R13",
                 "R14", "R15", "SCREEN", "KBD"
                 ]

        # Find the @symbols in the assembly code and add them to the symbols list.
        # This will make the machine display more readable.

        found = {}

        # Parse the lines for @symbols and (labels). An @symbol could
        # be a reference to a predefined location, a label, or a new
        # symbol we need to allocate.

        for addr, line in enumerate(self.state["ASM"]):
            match = re.search("@([A-Za-z_.$:][0-9A-Za-z_.$:]*)", line)
            if match and match.group(1) not in found:   # New @symbol, we don't know it's value yet.
                found[match.group(1)] = None

            match = re.search("[(]([A-Za-z_.$:][0-9A-Za-z_.$:]+)[)]", line)
            if match:
                symbol = match.group(1)
                if symbol in found:
                    if found[symbol] is None:           # Now we know symbol we previously saw was a
                        found[symbol] = addr            # reference to a label, so we can set its value.
                    else:
                        sys.exit(f'{Color.RED}Redefined symbol {symbol} in program @ {addr} : {line}.{Color.END}')
                else:
                    found[symbol] = addr                # New label.

        # Any symbol that does not yet have a value and is not already in
        # the symbols dictionary is a new variable we need to add, starting
        # at memory location 16.

        next_addr = 16
        for symbol, value in found.items():
            if symbol not in known and value is None:
                value = next_addr
                next_addr += 1
                symbols[value] = symbol
                known.append(symbol)

        width = max([len(s) for s in symbols.values()])
        symbols = {k: v.ljust(width) for k, v in symbols.items()}

        self.state["SYMB"] = symbols

    # Update state of the component.

    def update(self, signals={}):

        super().update(signals)

        # Handle power-off situation.

        if not powered(self.power, signals):
            self.outputs[self.rom] = 0x0000
            self.outputs[self.asm] = "@0"
            return

        # Error check.

        pc = self.inputs[self.addr]

        if pc < 0 or pc >= len(self.state["ROM"]):
            sys.exit(f'{Color.RED}Error: ROM address [{pc}] is out of bounds!{Color.END}')

        self.outputs[self.rom] = self.state["ROM"][pc]
        self.outputs[self.asm] = self.state["ASM"][pc]


# --------------------------------------------------------------
# 16 Bit Register, will be instantiated with unique name,
# inputs and output. In addition to the CLR and STO signals
# registers have an additional GATE input that must be high
# in order for CLR and STO to be active.
# --------------------------------------------------------------

class Register(Component):
    """ Register """

    def __init__(self,
                 name="Register",
                 inputs=["DATA", "CLR", "STO", "GATE"],
                 outputs=[],
                 power=[],
                 state={"DATA": 0x0000},
                 emulated=True,
                 sequence=None):

        name, inputs, outputs, power, state, emulated, sequence = \
            super()._massage(name, inputs, outputs, power, state, emulated, sequence)

        super().__init__(
            name=name,
            inputs=inputs,
            outputs=outputs,
            power=power,
            state=state,
            emulated=emulated,
            sequence=sequence)

        # Keep local copies of the input and output line names
        # because they will change in each instantiation.

        self.data = inputs[0]
        self.clr = inputs[1]
        self.sto = inputs[2]
        self.gate = inputs[3]
        self.output = outputs[0]

    # Update state of the component.

    def update(self, signals={}):

        super().update(signals)

        # Handle power-off situation.

        if not powered(self.power, signals):
            for output in self.outputs.keys():
                self.outputs[output] = False
                self.state["DATA"] = 0x0000
            return

        # If CLR is low, the register will always become the OR of itself and input,
        # because high bits are held. But if it goes high, then it just becomes input,
        # because the hold current goes away. This is only done if the gate is open.

        if self.inputs[self.gate]:
            data = self.inputs[self.data] if self.inputs[self.sto] else 0x0000
            data = data | 0x0000 if self.inputs[self.clr] else self.state["DATA"]
            self.state["DATA"] = data
            self.outputs[self.output] = data


# --------------------------------------------------------------
# 2 Bit Condition Codes register. Can probably be implemented as
# a latch that gets power during cycles so it latches after ALU
# settles.
# --------------------------------------------------------------

class ConditionCodes(Component):
    """ Register """

    def __init__(self,
                 name="ALUCC",
                 inputs=["CCZR", "CCNG", "CLR", "STO", "GATE"],
                 outputs=["ZR", "NG"],
                 power=[],
                 state={"ZR": False, "NG": False},
                 emulated=True,
                 sequence=None):

        name, inputs, outputs, power, state, emulated, sequence = \
            super()._massage(name, inputs, outputs, power, state, emulated, sequence)

        super().__init__(
            name=name,
            inputs=inputs,
            outputs=outputs,
            power=power,
            state=state,
            emulated=emulated,
            sequence=sequence)

        self.clr = inputs[2]
        self.sto = inputs[3]
        self.gate = inputs[4]

    # Update state of the component.

    def update(self, signals={}):

        super().update(signals)

        # Handle power-off situation.

        if not powered(self.power, signals):
            for output in self.outputs.keys():
                self.outputs[output] = False
                self.state[output] = False
            return

        # Incoming value is only gated to memory cell if STO is high.

        # If CLR is low, the register will always become the OR of itself and input,
        # because high bits are held. But if it goes high, then it just becomes input,
        # because the hold current goes away. This is only done if the gate is open.

        if self.inputs[self.gate]:
            zr = self.inputs["CCZR"] if self.inputs[self.sto] else False
            ng = self.inputs["CCNG"] if self.inputs[self.sto] else False
            zr = zr | False if self.inputs[self.clr] else self.state["ZR"]
            ng = ng | False if self.inputs[self.clr] else self.state["NG"]
            self.state["ZR"] = zr
            self.outputs["ZR"] = zr
            self.state["NG"] = ng
            self.outputs["NG"] = ng


# --------------------------------------------------------------
# 2-1 Multiplexer, will be instantiated with unique name,
# inputs and output. Only generates an output if POWER is high;
# uses CTRL to select A (High) or B (Low) inputs.
# --------------------------------------------------------------

class Multiplexer(Component):
    """ Multiplexer """

    def __init__(self,
                 name="Multiplexer",
                 inputs=["CTRL", "A", "B"],
                 outputs=[],
                 power=[],
                 state={},
                 emulated=True,
                 sequence=None):

        name, inputs, outputs, power, state, emulated, sequence = \
            super()._massage(name, inputs, outputs, power, state, emulated, sequence)

        super().__init__(
            name=name,
            inputs=inputs,
            outputs=outputs,
            power=power,
            state=state,
            emulated=emulated,
            sequence=sequence)

        # Keep local copies of the input and output line names
        # because they will change in each instantiation.

        self.ctrl = inputs[0]
        self.a = inputs[1]
        self.b = inputs[2]
        self.output = outputs[0]

    # Update state of the component.

    def update(self, signals={}):

        super().update(signals)

        # Handle power-off situation.

        if not powered(self.power, signals):
            for output in self.outputs.keys():
                self.outputs[output] = False
            return

        self.outputs[self.output] = self.inputs[self.a] if self.inputs[self.ctrl] else self.inputs[self.b]


# --------------------------------------------------------------
# Various logic gates, used to build composite signals.
# --------------------------------------------------------------

class AND(Component):
    """ N-way AND gate """

    def __init__(self,
                 name="AND",
                 inputs=["A", "B", "C"],
                 outputs=[],
                 power=[],
                 state={},
                 emulated=True,
                 sequence=None):

        name, inputs, outputs, power, state, emulated, sequence = \
            super()._massage(name, inputs, outputs, power, state, emulated, sequence)

        super().__init__(
            name=name,
            inputs=inputs,
            outputs=outputs,
            power=power,
            state=state,
            emulated=emulated,
            sequence=sequence)

        self.output = outputs[0]

# Update state of the component

    def update(self, signals={}):

        super().update(signals)

        # Handle power-off situation

        if not powered(self.power, signals):
            for output in self.outputs.keys():
                self.outputs[output] = False
            return

        self.outputs[self.output] = all([value for _, value in self.inputs.items()])


class OR(Component):
    """ N-way OR gate """

    def __init__(self,
                 name="OR",
                 inputs=["A", "B", "C"],
                 outputs=[],
                 power=[],
                 state={},
                 emulated=True,
                 sequence=None):

        name, inputs, outputs, power, state, emulated, sequence = \
            super()._massage(name, inputs, outputs, power, state, emulated, sequence)

        super().__init__(
            name=name,
            inputs=inputs,
            outputs=outputs,
            power=power,
            state=state,
            emulated=emulated,
            sequence=sequence)

        self.output = outputs[0]

# Update state of the component.

    def update(self, signals={}):

        super().update(signals)

        # Handle power-off situation.

        if not powered(self.power, signals):
            for output in self.outputs.keys():
                self.outputs[output] = False
            return

        self.outputs[self.output] = any([value for _, value in self.inputs.items()])


# --------------------------------------------------------------
# The almighty ALU! Destroyer of Worlds!
# --------------------------------------------------------------

class ALU(Component):
    """ The Arithmetic-Logic Unit """

    def __init__(self,
                 name="ALU",
                 inputs=["XREG", "YREG", "ZX", "NX", "ZY", "NY", "F", "NO"],
                 outputs=["ALU", "ZR", "NG"],
                 power=["ALUON"],
                 state={},
                 emulated=True,
                 sequence=None):

        name, inputs, outputs, power, state, emulated, sequence = \
            super()._massage(name, inputs, outputs, power, state, emulated, sequence)

        super().__init__(
            name=name,
            inputs=inputs,
            outputs=outputs,
            power=power,
            state=state,
            emulated=emulated,
            sequence=sequence)

        self.xreg = inputs[0]   # X Register input name.
        self.yreg = inputs[1]   # Y Register input name.
        self.alu = outputs[0]   # ALU output name.
        self.zr = outputs[1]    # ZR output signal.
        self.ng = outputs[2]    # NG output signal.

    # Update state of the component (nothing for now).

    def update(self, signals={}):

        super().update(signals)

        if not powered(self.power, signals):
            self.outputs["ALU"] = 0x0000
            self.outputs["CCLT"] = False
            self.outputs["CCGT"] = False
            self.outputs["CCEQ"] = False
            return

        # Numeric inputs.

        x = self.inputs[self.xreg]
        y = self.inputs[self.yreg]

        # Computations (anding with 0xFFFF to keep things 16-bit at all times).

        if self.inputs["ZX"]:
            x = 0

        if self.inputs["NX"]:
            x = ~x & 0xFFFF

        if self.inputs["ZY"]:
            y = 0

        if self.inputs["NY"]:
            y = ~y & 0xFFFF

        if self.inputs["F"]:
            out = (x + y)
        else:
            out = x & y

        if self.inputs["NO"]:
            out = ~out & 0xFFFF
        else:
            out = out & 0xFFFF

        self.outputs[self.alu] = out
        self.outputs[self.zr] = out == 0
        self.outputs[self.ng] = (out & 0x8000) != 0


# --------------------------------------------------------------
# +1 Adder
# --------------------------------------------------------------

class Incrementor(Component):
    """ Adds 1 to input """

    def __init__(self,
                 name="INC",
                 inputs=["INPUT"],
                 outputs=[],
                 power=[],
                 state={},
                 emulated=True,
                 sequence=None):

        name, inputs, outputs, power, state, emulated, sequence = \
            super()._massage(name, inputs, outputs, power, state, emulated, sequence)

        super().__init__(
            name=name,
            inputs=inputs,
            outputs=outputs,
            power=power,
            state=state,
            emulated=emulated,
            sequence=sequence)

        self.input = inputs[0]
        self.output = outputs[0]

    # Update state of the component.

    def update(self, signals={}):

        super().update(signals)

        if not powered(self.power, signals):
            self.outputs[self.output] = False
            return

        self.outputs[self.output] = self.inputs[self.input] + 1


# --------------------------------------------------------------
# Branch checker determines if branches will be taken.
# --------------------------------------------------------------

class Branch(Component):
    """ Adds 1 to input """

    def __init__(self,
                 name="BRANCH",
                 inputs=["ZR", "NG", "JLT", "JEQ", "JGT"],
                 outputs=["BRANCH"],
                 power=["PCMUXON"],
                 state={},
                 emulated=True,
                 sequence=None):

        name, inputs, outputs, power, state, emulated, sequence = \
            super()._massage(name, inputs, outputs, power, state, emulated, sequence)

        super().__init__(
            name=name,
            inputs=inputs,
            outputs=outputs,
            power=power,
            state=state,
            emulated=emulated,
            sequence=sequence)

    # Update state of the component.

    def update(self, signals={}):

        super().update(signals)

        if not powered(self.power, signals):
            self.outputs["BRANCH"] = False
            return

        eqBranch = self.inputs["JEQ"] and self.inputs["ZR"]
        ltBranch = self.inputs["JLT"] and self.inputs["NG"]
        gtBranch = self.inputs["JGT"] and not (self.inputs["NG"] or self.inputs["ZR"])

        self.outputs["BRANCH"] = eqBranch or ltBranch or gtBranch


# --------------------------------------------------------------
# Decode instruction into control signals.
# --------------------------------------------------------------

class Decoder(Component):
    """ Instruction Decoder """

    def __init__(self,
                 name="DECODE",
                 inputs=["INSTR"],
                 outputs=["CINST", "A",
                          "ZX", "NX", "ZY", "NY", "F", "NO",
                          "STOA", "STOD", "STOM", "JLT", "JEQ", "JGT"],
                 power=["~RESET"],
                 state={},
                 emulated=True,
                 sequence=None):

        name, inputs, outputs, power, state, emulated, sequence = \
            super()._massage(name, inputs, outputs, power, state, emulated, sequence)

        super().__init__(
            name=name,
            inputs=inputs,
            outputs=outputs,
            power=power,
            state=state,
            emulated=emulated,
            sequence=sequence)

    # Update state of the component.

    def update(self, signals={}):

        super().update(signals)

        if not powered(self.power, signals):
            for output in self.outputs.keys():
                self.outputs[output] = False
            return

        bits = [b == '1' for b in format(self.inputs["INSTR"], "016b")]

        cinstr = bits[0]
        ainstr = not cinstr
        self.outputs["CINST"] = cinstr

        # Only assert control bits if C instruction, except for STOD which
        # is also asserted during A instructions.

        self.outputs["A"] = bits[3] and cinstr      # A or M choice.
        self.outputs["ZX"] = bits[4] and cinstr     # 6 ALU control bits.
        self.outputs["NX"] = bits[5] and cinstr
        self.outputs["ZY"] = bits[6] and cinstr
        self.outputs["NY"] = bits[7] and cinstr
        self.outputs["F"] = bits[8] and cinstr
        self.outputs["NO"] = bits[9] and cinstr
        self.outputs["STOA"] = bits[10] or ainstr   # 3 register store bits.
        self.outputs["STOD"] = bits[11] and cinstr
        self.outputs["STOM"] = bits[12] and cinstr
        self.outputs["JLT"] = bits[13] and cinstr   # 3 jump control bits.
        self.outputs["JEQ"] = bits[14] and cinstr
        self.outputs["JGT"] = bits[15] and cinstr


# --------------------------------------------------------------
# System RAM.
# --------------------------------------------------------------

class RAM(Component):
    """ RAM """

    SIZE = 32768

    def __init__(self,
                 name="RAM",
                 inputs=["ADDR", "DATA", "CLRMEM", "STOMEM", "STOM"],
                 outputs=["RAM"],
                 power=[],
                 state={"DATA": [0x0000 for _ in range(SIZE)],
                        "WHEN": [0x0000 for _ in range(SIZE)],
                        },
                 emulated=True,
                 sequence=None):

        name, inputs, outputs, power, state, emulated, sequence = \
            super()._massage(name, inputs, outputs, power, state, emulated, sequence)

        super().__init__(
            name=name,
            inputs=inputs,
            outputs=outputs,
            power=power,
            state=state,
            emulated=emulated,
            sequence=sequence)

        self.count = 0              # RAM write count for display sorting

        self.ADDR = inputs[0]       # Address bus
        self.DATA = inputs[1]       # Data bus
        self.CLRMEM = inputs[2]     # CLRMEM signal
        self.STOMEM = inputs[3]     # STOMEM signal
        self.STOM = inputs[4]       # Write enable signal

    # Update state of the component.

    def update(self, signals={}):

        super().update(signals)

        if not powered(self.power, signals):
            for output in self.outputs.keys():
                self.outputs[output] = False
            self.state["DATA"] = [0x0000 for _ in self.state["DATA"]]
            return

        # We only have so much RAM.

        addr = self.inputs[self.ADDR]

        if addr < 0 or addr >= len(self.state["DATA"]):
            sys.exit(f'{Color.RED}Error: RAM address [{addr}] is out of bounds!{Color.END}')

        # No write operations can occur unless STOM is high.

        if self.inputs[self.STOM]:
            # Data from CPU is only gated through to memory cell if STOMEM is high.

            aluout = self.inputs[self.DATA] if self.inputs[self.STOMEM] else 0

            # If CLRMEM is low, the addressed memory will always become the OR of itself and ALUOUT,
            # because high bits are held. But if it goes high, then it just becomes ALUOUT, because
            # the hold current goes away.

            cell = aluout | 0 if self.inputs[self.CLRMEM] else self.state["DATA"][addr]
            self.state["DATA"][addr] = cell
            self.outputs["RAM"] = cell

            # Mark the cell as visited, so we can display recent memory locations properly.

            self.count += 1
            self.state["WHEN"][addr] = self.count
        else:
            # Since we are not writing, return the value of the current cell
            self.outputs["RAM"] = self.state["DATA"][addr]


# --------------------------------------------------------------
# Mocked signals unit for testing.
# --------------------------------------------------------------

class Mocked(Component):
    """ Signal mockups """

    def __init__(self,
                 name="MOCKED",
                 inputs=[],
                 outputs=[],
                 power=["TRUE"],
                 state={},
                 emulated=True,
                 sequence=None):

        name, inputs, outputs, power, state, emulated, sequence = \
            super()._massage(name, inputs, outputs, power, state, emulated, sequence)

        super().__init__(
            name=name,
            inputs=inputs,
            outputs=outputs,
            power=power,
            state=state,
            emulated=emulated,
            sequence=sequence)

    # Update state of the component.

    def update(self, signals={}):

        super().update(signals)

        # Just copy state into outputs.

        for key in self.state.keys():
            self.outputs[key] = self.state[key]
