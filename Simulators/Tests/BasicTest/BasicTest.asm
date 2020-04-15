// File: /Users/trebor/Desktop/nand2tetris/projects/07/MemoryAccess/BasicTest/BasicTest.vm
// push constant 10 (Line 7)
@10
D=A
@SP
AM=M+1
A=A-1
M=D
// pop local 0 (Line 8)
@SP
AM=M-1
D=M
@LCL
A=M
M=D
// push constant 21 (Line 9)
@21
D=A
@SP
AM=M+1
A=A-1
M=D
// push constant 22 (Line 10)
@22
D=A
@SP
AM=M+1
A=A-1
M=D
// pop argument 2 (Line 11)
@SP
AM=M-1
D=M
@ARG
A=M+1
A=A+1
M=D
// pop argument 1 (Line 12)
@SP
AM=M-1
D=M
@ARG
A=M+1
M=D
// push constant 36 (Line 13)
@36
D=A
@SP
AM=M+1
A=A-1
M=D
// pop this 6 (Line 14)
@SP
AM=M-1
D=M
@THIS
A=M+1
A=A+1
A=A+1
A=A+1
A=A+1
A=A+1
M=D
// push constant 42 (Line 15)
@42
D=A
@SP
AM=M+1
A=A-1
M=D
// push constant 45 (Line 16)
@45
D=A
@SP
AM=M+1
A=A-1
M=D
// pop that 5 (Line 17)
@SP
AM=M-1
D=M
@THAT
A=M+1
A=A+1
A=A+1
A=A+1
A=A+1
M=D
// pop that 2 (Line 18)
@SP
AM=M-1
D=M
@THAT
A=M+1
A=A+1
M=D
// push constant 510 (Line 19)
@510
D=A
@SP
AM=M+1
A=A-1
M=D
// pop temp 6 (Line 20)
@SP
AM=M-1
D=M
@R11
M=D
// push local 0 (Line 21)
@LCL
A=M
D=M
@SP
AM=M+1
A=A-1
M=D
// push that 5 (Line 22)
@5
D=A
@THAT
A=M+D
D=M
@SP
AM=M+1
A=A-1
M=D
// add (Line 23)
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
// push argument 1 (Line 24)
@ARG
A=M+1
D=M
@SP
AM=M+1
A=A-1
M=D
// sub (Line 25)
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
// push this 6 (Line 26)
@6
D=A
@THIS
A=M+D
D=M
@SP
AM=M+1
A=A-1
M=D
// push this 6 (Line 27)
@6
D=A
@THIS
A=M+D
D=M
@SP
AM=M+1
A=A-1
M=D
// add (Line 28)
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
// sub (Line 29)
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
// push temp 6 (Line 30)
@R11
D=M
@SP
AM=M+1
A=A-1
M=D
// add (Line 31)
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
