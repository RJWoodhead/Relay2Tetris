// A Register order of operations test

load Order.asm,
output-file Order.out,
compare-to Order.cmp,
output-list RAM[0]%D1.6.1 RAM[1]%D1.6.1 RAM[2]%D1.6.1;

repeat 50 {
  ticktock;
}

output;
