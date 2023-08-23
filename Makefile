.PHONY: compile clean run

run: out
	$(shell ./out)
	@echo "result: $(.SHELLSTATUS)"
	

compile: out

clean: 
	rm -rf out *.o
	
out.o: out.s
	riscv64-linux-gnu-as out.s -o out.o

out: out.o
	riscv64-linux-gnu-gcc -o out out.o -nostdlib -static
