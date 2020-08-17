# --------------------------------------------------------------------------------------------
# Validate Relay2Tetris hardware by simulating it in software. The eventual
# goal will be to replace each software component with a hardware component
# as it is built, using a hardware interface to send and receive the control
# signals. This will make debugging a lot easier.
#
# Usage: python3 validate.py [Test name (subfolder of Tests folder)] {{Trace Level: [N]one|[I]nstruction|[C]lock|[S]ettle}}}
#
# Test folder [xxx] will contain up to 4 files.
#
#   [xxx].hack      The machine code source file (output of the Nand2Tetris assembler) - required
#   [xxx].asm       Human-readable source code (input to the Nand2Tetris assembler)
#   [xxx].tst       Validation test script (input to the Nand2Tetris emulator)
#   [xxx].cmp       Validation comparison results
#
# If [xxx].tst is present, the validator runs the test script and compares the output to the
# contents of the [xxx].cmp file. If not, the validator just runs the machine code.
#
# To make parsing simpler, there is a restriction on the test scripts: there can be only
# one output-list, and the formatting is ignored.
#
# The load, output-file, and compare-to commands are ignored because they are implied by the
# files in the test folder, and these files need to be loaded before the script is executed.
#
# For convenience, the validator recognizes when the machine has entered the infinite-loop
# end condition and exits script repeat loops early in this situation.
#
# The default trace level is [I]nstruction, which provides machine state at the start of
# each instruction cycle. [C]lock lets you see the internal state of all signals at
# each machine clock. [S]ettle shows that plus the process of settling on the hardware
# state. [N]one just reports the results of the validation.
#
# IMPORTANT: According to Shimon Schocken, the correct hardware behavior when an instruction
# updates AREG *and* executes a branch is that the branch should go to the value in
# AREG at the start of the instruction, not the new value computed by the instruction.
# When the simulator is updated to the current hardware design, keep this in mind!
#
# (C)2019 Robert Woodhead - trebor@animeigo.com
# License: Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0)
#
# -------------------------------------------------------------------------------------------

from Modules.Comp import Reset, Clock, Sequencer, Matrix, ROM, RAM, Mocked
from Modules.Comp import Register, Decoder, Multiplexer, ALU, Incrementor, Branch, ConditionCodes
from Modules.Comp import Color

# from Modules.Test import Script

import random
import sys
import os
import re

ps_sources = {}     # global print_state sources list
ps_order = []       # global print_state signal ordering

term_rows, term_columns = [int(x) for x in os.popen('stty size', 'r').read().split()]

T_OFF = 0       # No debug trace, just give results
T_ON = 1        # Instruction-by-Instruction tracing
T_FULL = 2      # Tick-by-tick tracing
T_SETTLE = 3    # Trace settling of hardware state

USAGE = True    # Print usage of signals for power computations


# Load and parse all the test files, return assembly, code, script and results

def load_test(test_path, test_name):

    # Load machine code.

    code_file = os.path.join(test_path, f'{test_name}.hack')

    if os.path.exists(code_file) and os.path.isfile(code_file):
        with open(code_file, "r") as f:
            code = f.readlines()
            code = [line.strip() for line in code]                  # Remove leading and trailing spaces
            code = [int(line, 2) for line in code if line != ""]    # Remove empty lines
            print(f'# Read code in {code_file} : {len(code)} lines.')
    else:
        code = None

    # Load and reformat assembly code.

    asm_file = os.path.join(test_path, f'{test_name}.asm')

    if os.path.exists(asm_file) and os.path.isfile(asm_file):
        with open(asm_file, 'r') as f:
            asm = f.readlines()
            asm = [line.split("//")[0] for line in asm]             # Remove comments
            asm = [line.strip() for line in asm]                    # Remove leading and trailing spaces
            asm = [line for line in asm if line != ""]              # Remove empty lines

            # Move labels down into the subsequent line. Done in reversed order so that
            # shifted labels don't propagate. Don't need to check last element.

            for index, line in reversed(list(enumerate(asm[:-1]))):
                if "(" in line:
                    asm[index + 1] = f'{asm[index]} {asm[index + 1]}'
                    asm[index] = None

            # Eliminate labels that got moved.

            asm = [line for line in asm if line]
            print(f'# Read assembly in {code_file} : {len(asm)} lines.')
    else:
        asm = None

    # Load and reformat test script. Since I do not have a specification for
    # what can be in test scripts, I am making some assumptions! I also strip
    # off the formatting commands on output-list statements to make life
    # easier. Generates list of lists of tokens.
    #
    # Implementation restriction:
    #
    #     Output-list must be on a single line.

    test_file = os.path.join(test_path, f'{test_name}.tst')

    if os.path.exists(test_file) and os.path.isfile(test_file):
        with open(test_file, 'r') as f:
            script = f.readlines()
            script = [line.split("//")[0] for line in script]                         # Remove comments
            script = [re.split("[,;]", line) for line in script]                      # Split by delimiters
            script = [line if type(line) == list else list(line) for line in script]  # Make into regular list of lists
            script = [line for sublist in script for line in sublist]                 # Flatten the list
            script = [re.sub("%[^ ]*", "", line) for line in script]                  # Remove formatting
            script = [line.strip() for line in script]                                # Remove leading and trailing spaces, punctuation
            script = [line.lower() for line in script if line != ""]                  # Remove empty lines, lowercase remainder
            print(f'# Read test script in {test_file} : {len(script)} commands.')
    else:
        script = None

    # Load and reformat results. Generates list of list of results columns,
    # the first of which is the name of the variables.

    results_file = os.path.join(test_path, f'{test_name}.cmp')

    if os.path.exists(results_file) and os.path.isfile(results_file):
        with open(results_file, 'r') as f:
            results = f.readlines()
            results = [re.sub("[ \n]+", "", line) for line in results]  # remove all the spaces and newlines
            results = [line.strip("|") for line in results]             # Remove the leading and trailing | separators
            results = [line.lower().split("|") for line in results]     # split into fields and lowercase
            print(results)
            results[0] = [line + ("" if line.endswith("]") else "]") for line in results[0]]    # hack to fix bad headers
            print(f'# Read test results in {results_file} : {len(results)} entries.')
    else:
        results = None

    return asm, code, script, results


# Gather state of all the outputs of all the hardware. We always have TRUE and FALSE
# signals.

def state_of(machine):

    signals = {"TRUE": True, "FALSE": False}

    for board in machine.values():
        for output in board.outputs.keys():
            if output in signals:
                sys.exit(f'{Color.RED}# Error: Output signal {output} is being generated by multiple boards (incl. {board.name})!{Color.END}')
            else:
                signals[output] = board.outputs[output]

    return signals


# Gather state of all the outputs of all the hardware. This version is only
# run once, and also generates the dictionary of sources and signal order
# list that are stashed in ps_sources and ps_order for the convenience of
# the print_state() function.

def initial_state_of(machine):

    # True and False are always available

    signals = {"TRUE": True, "FALSE": False}
    sources = {"TRUE": "", "FALSE": ""}
    sequence = {"TRUE": 9999, "FALSE": 9999}
    inputs = []

    for board in machine.values():
        inputs.extend(board.inputs.keys())
        inputs.extend(board.power.keys())
        for output in board.outputs.keys():
            if output in signals:
                sys.exit(f'{Color.RED}# Error1: Output signal {output} is being generated by both {board.name} and {str(sources[output])}.{Color.END}')
            else:
                signals[output] = board.outputs[output]
                sources[output] = board.name
                sequence[output] = board.sequence

    ignorable = ['TRUE', 'FALSE', 'RESET', '~RESET', 'ASM', 'PREV']

    for output in signals.keys():
        if output not in inputs and output not in ignorable:
            print(f'{Color.YELLOW}# Warning: Unused output {output} generated by {sources[output]}.')

    order = [(sequence[k], k) for k in signals.keys()]
    order.sort()
    order = [item[1] for item in order]

    return (signals,
            sources,
            order)


# Value formatters used in generating state reports.

def vfmt(value):

    if value is None:
        return "none"
    elif value is False:
        return " --  "
    elif value is True:
        return "HIGH "
    elif isinstance(value, int):
        return hex(value)[2:].rjust(4, '0')
    else:
        return str(value)


def signed(value):

    return value if value < 32768 else value - 65536


# Print state of all the signals on the machine. Got a little fancy here because
# I'm going to spend a lot of time looking at this, so it generates multicolumn
# output and is aware of the terminal width.

def print_state(signals, previous=None, sources=None, order=None):

    # Default values.

    sources = ps_sources if sources is None else sources
    order = ps_order if order is None else order

    # Generate formatted values.

    values = {signal: vfmt(signals[signal]) for signal in order}

    # Figure out column widths, formatting.

    signals_width = max([8, max([len(s) for s in signals.keys()])])
    sources_width = max([8, max([len(s) for s in sources.values()])])
    values_width = max([4, max([len(str(values[signal])) for signal in order])])
    fmt = f'{{0:{signals_width}}}  {{1:{sources_width}}}  {{2:{values_width}}}'
    col_space = 5
    col_spacer = "  |  "

    # Generate the entries, with appropriate formatting.

    entries = [[signal,
                sources[signal],
                values[signal]] for signal in order]

    # Format results.

    entries = [fmt.format(entry[0], entry[1], entry[2]) for entry in entries]

    # Figure out number of columns and rows.

    max_width = col_space + max([len(s) for s in entries])

    num_columns = (term_columns + 2) // max_width
    num_rows = (len(entries) + num_columns - 1) // num_columns
    offsets = [num_rows*x for x in range(num_columns)]

    # Print the headers.

    hdr = f'{Color.BOLD}{fmt.format("Signal", "Source", "Val.")}{Color.END}'
    print(col_spacer.join([hdr for column in range(num_columns)]))

    hdr = fmt.format("-"*signals_width, "-"*sources_width, "-" * values_width)
    print(col_spacer.join([hdr for column in range(num_columns)]))

    # Color code changes from previous?

    if previous is not None:
        for i, _ in enumerate(order):
            if signals[order[i]] != previous[order[i]]:
                entries[i] = Color.BLUE + Color.BOLD + entries[i] + Color.END

    # Print rows, with a bit of cleverness to handle empty entries in the final
    # column.

    for row in range(num_rows):
        print(col_spacer.join([entries[row+col] if row+col < len(entries) else "" for col in offsets]))

    print('')


# Print a summary of the machine state (the external programmer's view).

def print_machine(machine, signals):

    W_BEFORE = 15                       # Words before current location to display
    W_AFTER = 16                        # Words after current location to display
    W_FULL = W_BEFORE + W_AFTER + 1     # Full size

    def bold(str, bool):

        return f'{Color.BOLD}{str}{Color.END}' if bool else str

    # current memory locations

    pc = machine["PC"].state["DATA"]
    a = machine["AREG"].state["DATA"]
    d = machine["DREG"].state["DATA"]
    m = machine["RAM"].state["DATA"][a]

    # display windows

    rom_lo = max([pc - W_BEFORE, 0])
    rom_hi = min([rom_lo + W_FULL, len(machine["ROM"].state["ROM"])])
    rom_lo = max([rom_lo, rom_hi - W_FULL])

    # Format rom and ram display. Display rom near current PC,
    # display ram locations most recently visited, sorted in ascending order

    blank = " "*len(machine["ROM"].state["SYMB"][0])
    rom = [f'{x:5d} {machine["ROM"].state["ROM"][x]:016b} {vfmt(machine["ROM"].state["ASM"][x])}' for x in range(rom_lo, rom_hi)]

    recent = [(when, addr) for addr, when in enumerate(machine["RAM"].state["WHEN"]) if when > 0]
    recent.sort(reverse=True)
    recent = recent[:W_FULL]
    recent = [addr for when, addr in recent]
    recent.sort()

    ram = [(x, f'{x:5d} {machine["ROM"].state["SYMB"].get(x,blank)}{machine["RAM"].state["DATA"][x]:6d}{signed(machine["RAM"].state["DATA"][x]):7d}') for x in recent]

    # Left-justify RAM display because it can be variable width, and boldface most recent item.

    rom_width = max([len(x) for x in rom])
    rom = [x.ljust(rom_width) for x in rom]
    rom[pc-rom_lo] = f'{Color.BOLD}{rom[pc-rom_lo]}{Color.END}'

    # Same for RAM (may be empty!)

    if ram:
        ram_width = max([len(line) for x, line in ram])
        ram = [(x, line.ljust(ram_width)) for x, line in ram]
        ram = [f'{Color.BOLD}{line}{Color.END}' if x == a else line for x, line in ram]
    else:
        ram_width = 0

    # Summary of machine state

    p = machine["PREV"].state

    _pc = p["_PC"]
    _a = p["_A"]
    _m = p["_M"]
    _d = p["_D"]
    _reset = p["_RESET"]

    state = [f'PC  = {pc:5d}',
             f'A   = {a:5d}',
             f'M   = {m:5d} {vfmt(m)} {m:016b}',
             f'D   = {d:5d} {vfmt(d)} {d:016b}',
             "",
             f'RST ={machine["RESET"].outputs["RESET"]}',
             "",
             f'_PC = {_pc:5d}',
             f'_A  = {_a:5d}',
             f'_M  = {_m:5d} {vfmt(_m)} {_m:016b}',
             f'_D  = {_d:5d} {vfmt(_d)} {_d:016b}',
             "",
             f'_RST={_reset}'
             ]

    state_width = max([len(x) for x in state])

    # Pad state and ram to match rom lists.

    state = [state[x].ljust(state_width) if x < len(state) else " "*state_width for x in range(len(rom))]
    ram = [ram[x] if x < len(ram) else " "*ram_width for x in range(len(rom))]

    # Can only bold items after we've gotten the widths and padded because
    # of the non-printing characters used.

    state[1] = bold(state[1], a != _a)
    state[2] = bold(state[2], m != _m)
    state[3] = bold(state[3], d != _d)

    print(f'+- ROM {"-"*(rom_width-4)}--+- RAM {"-"*(ram_width-4)}--+--{"-"*state_width}--+')

    for line in range(len(rom)):
        print(f'|  {rom[line]}  |  {ram[line]}  |  {state[line]}  |')

    print(f'+------{"-"*(rom_width-4)}--+------{"-"*(ram_width-4)}--+--{"-"*state_width}--+')
    print('')


# Update the state of hardware modules in random order until they
# settle on a stable configuration.

def settle(machine, signals, trace=T_OFF):

    settled = False                         # We are not settled yet.
    settle_time = 0                         # Number of settling iterations.
    order = [board for board in machine]    # The boards in the machine.
    initial_signals = signals

    if trace == T_SETTLE:
        print(f'Settle(0): Cycle={machine["SEQUENCER"].state["CYCLE"]}')
        print_state(signals)

    # Try to settle the hardware, but give up after a while.

    while not settled and settle_time < 10:

        # Vary the order in which we settle the components to simulate random timing
        # issues in clock edges.

        random.shuffle(order)
        settle_time += 1

        for board in order:
            machine[board].update(signals)

        new_signals = state_of(machine)

        if trace == T_SETTLE:
            print(f'Settle({settle_time}): Cycle={machine["SEQUENCER"].state["CYCLE"]} - {", ".join([machine[x].name for x in order])}')
            print('')
            print_state(new_signals, signals)

        if new_signals == signals:
            settled = True
        else:
            old_signals = signals
            signals = new_signals

    if trace >= T_FULL:
        print(f'Settled: Cycle={machine["SEQUENCER"].state["CYCLE"]}')
        print_state(new_signals, initial_signals)

# If we failed to settle, it's a hardware problem! :)

    if not settled:
        print(new_signals)
        print(old_signals)
        sys.exit(f'{Color.RED}# Error: Hardware failed to settle!{Color.END}')

    return new_signals


# -----------------------------
# Tick the clock.
# -----------------------------

def tick(machine, signals, clock, trace=T_OFF):

    clock.tick(signals)

    return settle(machine=machine, signals=signals, trace=trace)


# -----------------------------
# Execute a full machine cycle.
# -----------------------------

def cycle(machine, signals, clock, instr_count=0, trace=T_OFF):

    if trace != T_OFF:
        print(f'{Color.GREEN}Instruction {instr_count}: Initial State{Color.END}')
        print_machine(machine=machine, signals=signals)

    # Make a copy of the internal state of the machine at start of instruction cycle

    prev = machine["PREV"].state

    prev["_A"] = machine["AREG"].state["DATA"]
    prev["_D"] = machine["DREG"].state["DATA"]
    prev["_PC"] = machine["PC"].state["DATA"]
    prev["_RESET"] = machine["RESET"].state["RESET"]
    prev["_M"] = machine["INM"].state["DATA"]

    # Run through the clock ticks in a cycle.

    for t in range(machine["SEQUENCER"].state["TICKS"]):
        signals = tick(machine=machine, signals=signals, clock=clock, trace=trace)

    return signals, instr_count + 1


# -----------------------------
# Run the test.
# -----------------------------

def validate(machine, signals, test, results, trace):

    # Parse a variable reference into components. Currently only
    # understands RAM[x] and PC.

    def var_parse(ref):

        if ref == "pc":
            return ref
        else:
            regex = re.search(r"(.+?)\[(-*[0-9]+?)\]", ref)
            if regex:
                return (regex.group(1), int(regex.group(2)))
            else:
                sys.exit(f'{Color.RED}Error: Malformed or unknown variable {ref}.{Color.END}')

    # Get a variable's value.

    def var_get(ref):

        if isinstance(ref, str):
            if ref == "pc":
                return machine["PC"].outputs["PC"]
            else:
                sys.exit(f'{Color.RED}Error: Unknown variable {ref}.{Color.END}')
        else:
            if ref[0] == "ram":
                ram = machine["RAM"].state["DATA"]
                if ref[1] < len(ram):
                    value = ram[ref[1]]
                    return value - 65536 if value > 32757 else value    # 2's complement
                else:
                    sys.exit(f'{Color.RED}Error: RAM[{ref[1]}] is out of range.{Color.END}')
            else:
                sys.exit(f'{Color.RED}Error: Unknown variable {ref}.{Color.END}')

    # Set a variable's value.

    def var_set(ref, value):

        value = int(value) & 0xFFFF

        if isinstance(ref, str):
            if ref == "pc":
                machine["PC"].state["DATA"] = value
                print(f'{Color.GREEN}Set: PC = {value}')
            else:
                sys.exit(f'{Color.RED}Error: Unknown variable {ref}.{Color.END}')
        else:
            if ref[0] == "ram":
                ram = machine["RAM"].state["DATA"]
                if ref[1] < len(ram):
                    ram[ref[1]] = value                         # Set value
                    machine["RAM"].state["WHEN"][ref[1]] = 1    # Mark as visited
                    print(f'{Color.GREEN}Set: RAM[{ref[1]}] = {value}{Color.END}')
                else:
                    sys.exit(f'{Color.RED}Error: RAM[{ref[1]}] is out of range.{Color.END}')
            else:
                sys.exit(f'{Color.RED}Error: Unknown variable {ref}.{Color.END}')

    # Run through the test script.

    test_pc = 0
    output_list = []
    output = []
    stack = []
    instr_count = 1

    while (test_pc < len(test)):

        line = test[test_pc]
        tokens = line.split()
        cmd = tokens[0].lower()

        if cmd == "load" or cmd == "output-file" or cmd == "compare-to":

            print(f'{Color.YELLOW}Ignored: {line}{Color.END}')

        elif cmd == "output-list":

            output_list = tokens[1:]
            if output_list != results[0]:
                sys.exit(f'{Color.RED}Error: output-list {output_list} does not match results {results[0]}.{Color.END}')
            output = [output_list]
            output_list = [var_parse(token) for token in output_list]
            print(f'{Color.GREEN}Output List: {output_list}{Color.END}')

        elif cmd == "set":

            var_set(var_parse(tokens[1]), tokens[2])

        elif cmd == "repeat":

            stack.append([test_pc, int(tokens[1])])
            print(f'{Color.GREEN}Repeat {tokens[1]} times:{Color.END}')

        elif cmd == "}":

            # Check to see if we are in a halt condition (looping on same instruction).
            # If so, pop the innermost loop.

            if machine["PC"].state["DATA"] == machine["PREV"].state["_PC"]:
                stack.pop()
                print(f'{Color.YELLOW}Program Halt detected, exiting loop.{Color.END}')
            elif stack == []:
                sys.exit(f'{Color.RED}Error: Empty stack.{Color.END}')
            elif stack[-1][1] > 1:
                stack[-1][1] -= 1
                test_pc = stack[-1][0]
            else:
                stack.pop()

        elif cmd == "ticktock":

            signals, instr_count = cycle(machine=machine, signals=signals, clock=clock, instr_count=instr_count, trace=trace)

        elif cmd == "output":

            values = [str(signed(var_get(item))) for item in output_list]
            output.append(values)
            if len(output) <= len(results):
                expected = results[len(output)-1]
                if values != expected:
                    print(f'{Color.RED}Output   : {values}{Color.END}')
                    print(f'{Color.RED}Expected : {expected}{Color.END}')
                    sys.exit()
                else:
                    print(f'{Color.GREEN}Output correct: {values}{Color.END}')
            else:
                print(f'{Color.RED}Output   : {values}{Color.END}')
                sys.exit(f'{Color.RED}More outputs than test results{Color.END}')

        else:

            sys.exit(f'{Color.RED}Unknown script command: {line}{Color.END}')

        test_pc += 1

    print(f'{Color.GREEN}# SCRIPT VALIDATED CORRECTLY!{Color.END}')


# -----------------------------------------------------------------------------------
# Setup hardware configuration. Output of component is same as name if not specified.
# Order of declaration affects how they are displayed in traces.
# -----------------------------------------------------------------------------------

# V1 - 10 cycle implementation

def setup_v1(asm, code, trace):

    global ps_sources
    global ps_order

    print(f'{Color.BOLD}Loading Hardware V1 Simulation')
    print()

    reset = Reset(name="RESET", inputs=[], outputs=["RESET", "~RESET"], power=["TRUE"], sequence=-100)
    clock = Clock(name="CLOCK", inputs=[])

    sequencer = Sequencer(name="SEQUENCER",
                          inputs=["CLOCK", "RESET"],
                          state={"TICKS": 10})

    # Control signal generation. It may seem a little strange to combine signals like S1,S2,S3
    # which are 2-cycle wide and thus overlap, but it's a reminder that during hardware
    # development, we always have clock edge issues to worry about, and by doing this we
    # insure that signals don't flicker.

    matrix = Matrix(name="MATRIX",
                    inputs=["S0", "S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8", "S9",
                            "S0A", "S1A", "S2A", "S3A", "S4A", "S5A", "S6A", "S7A", "S8A", "S9A"],
                    outputs=["MEM", "CLRIN", "STOIN", "DECODEON", "ALUMUXON", "ALUON", "ALUOUTON", "ALUCCON", "CLRALU", "STOALU", "AMUXON",
                             "PCMUXON", "CLRMEM", "STOMEM", "CLRAD", "STOAD", "CLRPC", "STOPC"],
                    state={"ARRAY": {"MEM": ["S0"],
                                     "CLRIN": ["S0A"],
                                     "STOIN": ["S0"],
                                     "DECODEON": ["S3", "S4", "S5", "S6", "S7", "S8"],
                                     "ALUMUXON": ["S1", "S2", "S3"],
                                     "ALUON": ["S2", "S3"],
                                     "ALUOUTON": ["S3", "S4", "S5", "S6"],
                                     "ALUCCON": ["S3", "S4", "S5", "S6", "S7", "S8"],
                                     "CLRALU": ["S3A"],
                                     "STOALU": ["S3"],
                                     "AMUXON": ["S3", "S4", "S5", "S6"],
                                     "PCMUXON": ["S6", "S7", "S8"],
                                     "CLRMEM": ["S4A"],
                                     "STOMEM": ["S4"],
                                     "CLRAD": ["S6A"],
                                     "STOAD": ["S6"],
                                     "CLRPC": ["S8A"],
                                     "STOPC": ["S8"]
                                     }
                           }
                    )

    decoder = Decoder(name="DECODE",
                      inputs=["INSTR"],
                      outputs=["CINST", "A",
                               "ZX", "NX", "ZY", "NY", "F", "NO",
                               "STOA", "STOD", "STOM", "JLT", "JEQ", "JGT"],
                      power=["DECODEON"],
                      sequence=-60)

    rom = ROM(name="ROM", inputs=["PC"], outputs=["ROM", "ASM"], state={"ROM": code, "ASM": asm})
    ram = RAM(name="RAM", inputs=["AREG", "ALUOUT", "CLRMEM", "STOMEM", "STOM"])

    areg = Register(name="AREG", inputs=["AMUX", "CLRAD", "STOAD", "STOA"], sequence=-90)
    dreg = Register(name="DREG", inputs=["ALUOUT", "CLRAD", "STOAD", "STOD"], sequence=-80)
    pc = Register(name="PC", inputs=["PCMUX", "CLRPC", "STOPC", "TRUE"], power=["~RESET"], sequence=-70)

    alu = ALU(name="ALU", inputs=["DREG", "ALUMUX", "ZX", "NX", "ZY", "NY", "F", "NO"], outputs=["ALU", "CCZR", "CCNG"], power=["ALUON"], sequence=-50)
    aluout = Register(name="ALUOUT", inputs=["ALU", "CLRALU", "STOALU", "TRUE"], power=["ALUOUTON"], sequence=-40)
    alucc = ConditionCodes(name="ALUCC", inputs=["CCZR", "CCNG", "CLRALU", "STOALU", "TRUE"], outputs=["ZR", "NG"], power=["ALUCCON"], sequence=-30)

    instr = Register(name="INSTR", inputs=["ROM", "CLRIN", "STOIN", "TRUE"])
    inm = Register(name="INM", inputs=["RAM", "CLRIN", "STOIN", "TRUE"])

    amux = Multiplexer(name="AMUX", inputs=["CINST", "ALUOUT", "INSTR"], power=["AMUXON"])

    alumux = Multiplexer(name="ALUMUX", inputs=["A", "INM", "AREG"], power=["ALUMUXON"])

    incr = Incrementor(name="INCR", inputs=["PC"], power="ALUON")

    pcinc = Register(name="PCINC", inputs=["INCR", "CLRALU", "STOALU", "TRUE"])

    branch = Branch(name="BRANCH", inputs=["ZR", "NG", "JLT", "JEQ", "JGT"], power=["PCMUXON"])

    pcmux = Multiplexer(name="PCMUX", inputs=["BRANCH", "AREG", "PCINC"], power=["PCMUXON"])

    prev = Mocked(name="PREV", inputs=[], state={"_A": 0, "_D": 0, "_PC": -1, "_RESET": False, "_M": 0})

    machine = [reset,
               clock,
               rom,
               ram,
               areg,
               dreg,
               pc,
               alu,
               aluout,
               alucc,
               instr,
               inm,
               sequencer,
               matrix,
               decoder,
               amux,
               alumux,
               incr,
               pcinc,
               branch,
               pcmux,
               prev]

    machine = {board.name: board for board in machine}

    reset.set()
    signals, ps_sources, ps_order = initial_state_of(machine)
    signals = settle(machine=machine, signals=signals, trace=T_OFF)

    if trace != T_OFF:
        print(f'{Color.BOLD}Initial machine state:{Color.END}')
        print_machine(machine=machine, signals=signals)

    return machine, signals, clock


# V2 - 5 cycle implementation

def setup_v2(asm, code, trace):

    global ps_sources
    global ps_order

    print(f'{Color.BOLD}Loading Hardware V2 Simulation')
    print()

    reset = Reset(name="RESET", inputs=[], outputs=["RESET", "~RESET"], power=["TRUE"], sequence=-100)
    clock = Clock(name="CLOCK", inputs=[])

    sequencer = Sequencer(name="SEQUENCER",
                          inputs=["CLOCK", "RESET"],
                          state={"TICKS": 5})

    # Control signal generation. It may seem a little strange to combine signals like S1,S2,S3
    # which are 2-cycle wide and thus overlap, but it's a reminder that during hardware
    # development, we always have clock edge issues to worry about, and by doing this we
    # insure that signals don't flicker.

    matrix = Matrix(name="MATRIX",
                    inputs=["S0", "S1", "S2", "S3", "S4",
                            "S0A", "S1A", "S2A", "S3A", "S4A"],
                    outputs=["CLRIN", "STOIN", "DECON", "CLRXY", "STOXY", "ALUON", "CLROUT", "STOOUT"],
                    state={"ARRAY": {"CLRIN": ["S0A"],
                                     "STOIN": ["S0"],
                                     "DECON": ["S1", "S2", "S3"],
                                     "CLRXY": ["S1A"],
                                     "STOXY": ["S1"],
                                     "ALUON": ["S2", "S3"],
                                     "CLROUT": ["S3A"],
                                     "STOOUT": ["S3"]
                                     }
                           }
                    )

    decoder = Decoder(name="DECODE",
                      inputs=["INSTR"],
                      outputs=["CINST", "A",
                               "ZX", "NX", "ZY", "NY", "F", "NO",
                               "STOA", "STOD", "STOM", "JLT", "JEQ", "JGT"],
                      power=["DECON"],
                      sequence=-60)

    rom = ROM(name="ROM", inputs=["PC"], outputs=["ROM", "ASM"], state={"ROM": code, "ASM": asm})
    ram = RAM(name="RAM", inputs=["ADDRMUX", "ALU", "CLROUT", "STOOUT", "STOM"])

    areg = Register(name="AREG", inputs=["AMUX", "CLROUT", "STOOUT", "STOA"], sequence=-90)
    dreg = Register(name="DREG", inputs=["ALU", "CLROUT", "STOOUT", "STOD"], sequence=-80)
    pc = Register(name="PC", inputs=["PCMUX", "CLROUT", "STOOUT", "TRUE"], power=["~RESET"], sequence=-70)

    alumux = Multiplexer(name="ALUMUX", inputs=["A", "INM", "AREG"], power=["STOXY"])

    asav = Register(name="ASAV", inputs=["AREG", "CLRIN", "STOIN", "TRUE"], sequence=-67)
    xreg = Register(name="XREG", inputs=["DREG", "CLRXY", "STOXY", "TRUE"], sequence=-65)
    yreg = Register(name="YREG", inputs=["ALUMUX", "CLRXY", "CLRXY", "TRUE"], sequence=-63)

    alu = ALU(name="ALU", inputs=["XREG", "YREG", "ZX", "NX", "ZY", "NY", "F", "NO"], outputs=["ALU", "ZR", "NG"], power=["ALUON"], sequence=-50)

    instr = Register(name="INSTR", inputs=["ROM", "CLRIN", "STOIN", "TRUE"])
    inm = Register(name="INM", inputs=["RAM", "CLRIN", "STOIN", "TRUE"])

    amux = Multiplexer(name="AMUX", inputs=["CINST", "ALU", "INSTR"], power=["ALUON"])
    addrmux = Multiplexer(name="ADDRMUX", inputs=["STOIN", "AREG", "ASAV"], power=["TRUE"])

    incr = Incrementor(name="INCR", inputs=["PC"], power="STOXY")
    pcinc = Register(name="PCINC", inputs=["INCR", "CLRXY", "STOXY", "TRUE"], power="DECON")

    branch = Branch(name="BRANCH", inputs=["ZR", "NG", "JLT", "JEQ", "JGT"], power=["ALUON"])

    jmpmux = Multiplexer(name="JMPMUX", inputs=["STOA", "ALU", "ASAV"], power=["ALUON"])
    pcmux = Multiplexer(name="PCMUX", inputs=["BRANCH", "JMPMUX", "PCINC"], power=["ALUON"])

    prev = Mocked(name="PREV", inputs=[], state={"_A": 0, "_D": 0, "_PC": -1, "_RESET": False, "_M": 0})

    machine = [reset,
               clock, sequencer, matrix, decoder,
               rom, ram,
               areg, dreg, pc,
               asav, xreg, yreg,
               alu,
               instr, inm,
               amux, alumux, addrmux,
               incr,
               pcinc,
               branch,
               jmpmux,
               pcmux,
               prev]

    machine = {board.name: board for board in machine}

    reset.set()
    signals, ps_sources, ps_order = initial_state_of(machine)
    signals = settle(machine=machine, signals=signals, trace=T_OFF)

    if USAGE:
        inputs = {}
        for component in machine:
            for input in machine[component].inputs:
                if input in inputs:
                    inputs[input] += 1
                else:
                    inputs[input] = 1

        print(f'{Color.BOLD}Input usage count:{Color.END}')

        width = max([len(input) for input in inputs])
        for input in inputs:
            print(f'{input.rjust(width)} = {inputs[input]}')
        print('')

    if trace != T_OFF:
        print(f'{Color.BOLD}Initial machine state:{Color.END}')
        print_machine(machine=machine, signals=signals)

    return machine, signals, clock


# -----------------------------
# Main program
# -----------------------------

if sys.version_info < (3, 7):
    sys.exit(f'{Color.RED}# Error: This program requires Python 3.7.0 or later.{Color.END}')

print(sys.argv)

if len(sys.argv) not in [2, 3]:
    sys.exit(f'{Color.RED}# Usage: python3 validate.py [Test name (subfolder of Tests folder)] {{Trace Level: [N]one|[I]nstruction|[C]lock|[S]ettle}}{Color.END}')

test_path = 'Tests/' + sys.argv[1]

if not os.path.exists(test_path):
    sys.exit(f'{Color.RED}# {test_path} : does not exist.{Color.END}')

if not os.path.isdir(test_path):
    sys.exit(f'{Color.RED}# {test_path} : not a folder.{Color.END}')

trace_level = T_ON

if len(sys.argv) == 3:
    if sys.argv[2].lower() == 'n':
        trace_level = T_OFF
    elif sys.argv[2].lower() == 'c':
        trace_level = T_FULL
    elif sys.argv[2].lower() == 's':
        trace_level = T_SETTLE
    elif sys.argv[2].lower() != 'i':
        sys.exit(f'{Color.RED}# Unknown trace level; must be [N]one|[I]nstruction|[C]lock|[S]ettle.{Color.END}')

# Load testing environment.

asm, code, test, results = load_test(test_path, sys.argv[1])

# Wire up the hardware.

machine, signals, clock = setup_v2(asm=asm, code=code, trace=trace_level)

# Run an instruction with RESET st (by setup).

signals, _ = cycle(machine=machine, signals=signals, clock=clock, instr_count=0, trace=T_OFF)

# Clear RESET and run the test.

machine["RESET"].clr()

if test:
    validate(machine=machine, signals=signals, test=test, results=results, trace=trace_level)
else:
    instr_count = 1
    machine["PREV"].state["_PC"] = -1
    while machine["PC"].state["DATA"] != machine["PREV"].state["_PC"]:
        signals, instr_count = cycle(machine=machine, signals=signals, clock=clock, instr_count=instr_count, trace=trace_level)
