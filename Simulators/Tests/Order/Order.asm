// Test order of operations and usage of AM register
//
// 1) Test what happens when A and M are updated in same instruction
//
D=-1        // D=-1
@0          // A=0
M=D         // RAM[0] = -1
@1          // A=1
M=D         // RAM[1] = -1
@2          // A=2
M=D         // RAM[2] = -1
A=0         // A=0
D=1         // D=1
AM=D        // A=1, RAM[0] = 1 or RAM[1] = 1? Answer: RAM[0] = 1
//
// 2) Test what happens when A is updated and a branch occurs
//
@GOOD       // A=Address of (GOOD)
D=A         // D=Address of (GOOD)
@BAD        // A=Address of (BAD)
A=D;JMP     // A=Address of (GOOD), JMP executes
//
(GOOD)      // If jump occurs using updated A, we get here
@2          // A=2
M=1         // RAM[2]=1, then fall through
//
(BAD)       // If we jump directly here, RAM[2] will be -1
//
// Tighter and detectable-in-hardware end loop
//
@END        // End program
(END)
0;JMP
//
// Result: RAM[0] = 1, RAM[1] = -1, RAM[2] = 1
//
