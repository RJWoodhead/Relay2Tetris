// filepath /Users/trebor/Desktop/nand2tetris/projects/07/MemoryAccess/PointerTest/PointerTest.vm (Line 0)
// push constant 3030 (Line 8)
@3030
D=A
@SP
A=M
M=D
@SP
M=M+1
// pop pointer 0 (Line 9)
@SP
AM=M-1
D=M
@R3
M=D
// push constant 3040 (Line 10)
@3040
D=A
@SP
A=M
M=D
@SP
M=M+1
// pop pointer 1 (Line 11)
@SP
AM=M-1
D=M
@R4
M=D
// push constant 32 (Line 12)
@32
D=A
@SP
A=M
M=D
@SP
M=M+1
// pop this 2 (Line 13)
@2
D=A
@THIS
D=M+D
@R15
M=D
@SP
AM=M-1
D=M
@R15
A=M
M=D
// push constant 46 (Line 14)
@46
D=A
@SP
A=M
M=D
@SP
M=M+1
// pop that 6 (Line 15)
@6
D=A
@THAT
D=M+D
@R15
M=D
@SP
AM=M-1
D=M
@R15
A=M
M=D
// push pointer 0 (Line 16)
@R3
D=M
@SP
A=M
M=D
@SP
M=M+1
// push pointer 1 (Line 17)
@R4
D=M
@SP
A=M
M=D
@SP
M=M+1
// add (Line 18)
@SP
AM=M-1
D=M
@R15
M=D
@SP
A=M-1
D=M
@R15
D=D+M
@SP
A=M-1
M=D
// push this 2 (Line 19)
@2
D=A
@THIS
A=M+D
D=M
@SP
A=M
M=D
@SP
M=M+1
// sub (Line 20)
@SP
AM=M-1
D=M
@R15
M=D
@SP
A=M-1
D=M
@R15
D=D-M
@SP
A=M-1
M=D
// push that 6 (Line 21)
@6
D=A
@THAT
A=M+D
D=M
@SP
A=M
M=D
@SP
M=M+1
// add (Line 22)
@SP
AM=M-1
D=M
@R15
M=D
@SP
A=M-1
D=M
@R15
D=D+M
@SP
A=M-1
M=D
// end of program
@.STOP
(.STOP)
0;JMP
