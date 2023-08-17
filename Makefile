.PHONY: compile_riscv clean

compile_riscv: out

clean: rm -rf out *.o
	
out.o: riscv64-linux-gnu-as out.s -o out.o

out: riscv64-linux-gnu-gcc -o out out.o -nostdlib -static
