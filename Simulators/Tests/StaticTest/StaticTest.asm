// filepath /Users/trebor/Desktop/nand2tetris/projects/07/MemoryAccess/StaticTest/StaticTest.vm (Line 0)
// push constant 111 (Line 7)
@111
D=A
@SP
A=M
M=D
@SP
M=M+1
// push constant 333 (Line 8)
@333
D=A
@SP
A=M
M=D
@SP
M=M+1
// push constant 888 (Line 9)
@888
D=A
@SP
A=M
M=D
@SP
M=M+1
// pop static 8 (Line 10)
@SP
AM=M-1
D=M
@StaticTest.8
M=D
// pop static 3 (Line 11)
@SP
AM=M-1
D=M
@StaticTest.3
M=D
// pop static 1 (Line 12)
@SP
AM=M-1
D=M
@StaticTest.1
M=D
// push static 3 (Line 13)
@StaticTest.3
D=M
@SP
A=M
M=D
@SP
M=M+1
// push static 1 (Line 14)
@StaticTest.1
D=M
@SP
A=M
M=D
@SP
M=M+1
// sub (Line 15)
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
// push static 8 (Line 16)
@StaticTest.8
D=M
@SP
A=M
M=D
@SP
M=M+1
// add (Line 17)
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
