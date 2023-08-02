# RISC-V Superoptimizer with Program Synthesis


### About
This project aims to explore the automatic generation of RISC-V Code for Integer Arithmetic.


Current capabilities are:  
- Converting user input to a python arithmetic function (any occuring variables are converted to function arguments)
- Running RISC-V Code for arithmetic directly in Python without compilation
- Generating RISC-V Assembler code for arithmetic from user input using a bottom-up approach
- Checking if a given RISC-V arithmetic function and a python arithmetic function are equivalent (using Z3)
- By combining the above, checking the equivalence of two RISC-V arithmetic functions are equivalent


next todo: synthesizing RISC-V code using Z3. This can be passed back and forth from the existing verifier to create a complete CEGIS synthesizer.


Link to Thesis Report: https://www.overleaf.com/read/ghwmsjzvbvdn

### Usage
```input_to_naive_riscv.py``` currently runs in the terminal and showcases the naive bottom up convertion approach.  
Input: Arithmetic expression that may include variables and Integer constants. Supported operators are +, -, *, / (computed as //).  
```synthesize.py``` currently only computes an example of checking equivalence of a python function and RISC-V function. Should succeed twice