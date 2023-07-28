default:
	rm -rf out
	riscv64-linux-gnu-as out.s -o out.o
	riscv64-linux-gnu-gcc -o out out.o -nostdlib -static
