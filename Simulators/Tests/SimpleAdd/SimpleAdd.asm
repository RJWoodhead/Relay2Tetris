// filepath /Users/trebor/Desktop/nand2tetris/projects/07/StackArithmetic/SimpleAdd/SimpleAdd.vm (Line 0)
// push constant 7 (Line 7)
@7
D=A
@SP
A=M
M=D
@SP
M=M+1
// push constant 8 (Line 8)
@8
D=A
@SP
A=M
M=D
@SP
M=M+1
// add (Line 9)
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
