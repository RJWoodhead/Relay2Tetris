// This file is part of www.nand2tetris.org
// and the book "The Elements of Computing Systems"
// by Nisan and Schocken, MIT Press.
// File name: projects/04/Mult.asm

// Multiplies R0 and R1 and stores the result in R2.
// (R0, R1, R2 refer to RAM[0], RAM[1], and RAM[2], respectively.)

// IMPORTANT: DOES NOT TRASH R0,R1 (even though the test allows it, it's terrible form)

// Efficiency discussion: The key to improving overall efficiency of the multiplier is
// reducing the number of times we have to loop. The simple algorithm does one loop per
// bit of the multiplier (so 15 times since we don't care about the top bit). However,
// if we know the position of the topmost 1 bit, then we can quit at that point since
// there will never be any more additions and the job is complete.
//
// Doing this requires a slightly more expensive loop (20 invariant instructions vs.
// 16 for the simple loop). Since the simple loop runs 15 times, that's 240 instructions.
// This means that the more complex algorithm is a win whenever the multiplier has 12 or
// fewer bits we need to check. In addition, we can compare the multiplier and multiplicand
// and swap them so the multiplier is the smaller number. This means that the simple
// algorithm only wins when *both* the multiplier and multiplicand have 12 or more
// significant bits -- and since the result is a 15 bit number, you're not going to get
// a usable result in that case anyway! So the more complex loop is a *win*
//
// The trick therefore is finding a simple way to determine if we have any more bits we
// need to check in the Multiplier. The way we do this is use a negative mask to strip
// bits out of it one at a time; if it ever becomes 0, then we know we are done. This
// also means we don't need a loop counter, but we do need a copy of the multiplier

(INIT)
	@R2 				// Initialize product (R2) to 0
	M = 0

	@MASK 				// Initialize MASK to 1111...1110
	M = -1 				// which is -2
	M = M - 1

	@R0 				// Check if R0 >= R1
	D = M 				// If so, R1 is Multiplicand
	@R1 				// If not, R0 is Multiplicand
	D = D - M 			// This minimizes the number of times
	@R0GER1 			// through the main loop.
	D ; JGE

	@R1 				// Initialize Multiplicand to copy of R1
	D = M
	@MULC
	M = D

	@R0					// Initialize Multiplier to copy of R0
	D = M
	@MULP
	M = D

	@LOOP 				// Jump to top of loop
	0 ; JMP

(R0GER1) 				// R0 >= R1, so R1 is MULP

	@R0 				// Initialize Multiplicand to copy of R0
	D = M
	@MULC
	M = D

	@R1					// Initialize Multiplier to copy of R1
	D = M
	@MULP
	M = D

// Efficiency note: We could place a check here to see if MULP is 0 and exit immediately. This costs
// 2 instructions on every multiply. Omitting this check means that if MULP is 0, we'll go through the
// loop once (20 instructions), so this is only a win if we expect MULP to be 0 more than 10% of the
// time.

(LOOP) 					// D = MULP and non-zero at this point (unless it starts as zero).

	@OMULP 				// Save a copy of MULP as it currently is
	M = D

	@MASK 				// MULP = MULP & MASK. Because MASK is a negative mask, only the bit
	D = D & M 			// we currently care about is set to 0 if it is 1. We save the
	@MULP 				// *changed* version back into MULP
	M = D

	@OMULP 				// if MULP == OMULP, nothing to do on this round
	D = D - M
	@NEXT
	D ; JEQ

	@MULC 				// R2 = R2 + MULC
	D = M
	@R2
	M = M + D

(NEXT)

	@MULC 				// MULC = MULC * 2 (Shift Left 1 bit)
	D = M
	M = M + D

	@MASK 				// MASK = MASK * 2 (Shift left 1 bit)
	D = M
	M = M + D

	@MULP 				// Load up MULP again
	D = M
	@LOOP 				// and loop if non-zero
	D ; JNE

	@END
(END)
	0 ; JMP
