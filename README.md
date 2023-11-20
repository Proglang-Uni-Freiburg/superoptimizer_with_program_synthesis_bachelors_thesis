# RISC-V Superoptimizer with Program Synthesis


### About
This project aims to explore the synthesis of RISC-V Code for Integer Arithmetic with variables.

A summary of current features of the implementation:
- Synthesis and superoptimization of RISC-V assembly matching a arithmetic function, using CEGIS or a simple enumerative approach
- Converting between User Input of an arithmetic expression, python functions, an internal representation of RISC-V assembly, and RISC-V assembly files in the supported format
- Running RISC-V Code for arithmetic directly in Python without compilation
- Generating RISC-V Assembler code for arithmetic from user input using a naive bottom-up approach
- Checking if a given RISC-V arithmetic function and a python arithmetic function or another RISC-V arithmetic function are equivalent (using Z3)


Link to Thesis Report: https://www.overleaf.com/read/ghwmsjzvbvdn

### Usage
To run the synthesis in the terminal, you may simply call `main.py`, which will provide the necessary instructions.  
By using `make run`, you can compile and execute the generated code, provided riscv64-linux-gnu is installed. For simple debugging, the result for the function, if all variables are set to 0, is returned in the console in the form of the exit code (therefore, the result is not exact as the exit code is limited to a number between 0 and 255).

### Implementation
This project uses CEGIS with Z3 for synthesizing optimal RISC-V instruction sequences. Due to performance limits, solutions of a length higher than 3 instructions are difficult to generate.  
The verifier for arithmetic expression equivalence and the synthesis functions are contained in `cegis_verify.py`. The functions enabling synthesis are contained in `synthesis.py`.  
Benchmarking of the different methods implemented is implemented in `benchmarking.py`; the results on a test machine running Ubuntu 22.04 with 16GB of RAM and a 3.6GHz processor are already stored in the Benchmarking folder.  
The internal RISC-V assmebly DSL is defined in `riscv_dsl.py`. This also contains replacement functions for Python's modulo and floor division functions, to match other programming languages.  
Naive compilation for generating RISC-V assembly can be found in `python_ast_to_func.py`. Conversion from user input or a python function to RISC-V DSL can be found in `python_ast_to_dsl.py`, conversion from RISC-V assembly code to the DSL and back in `dsl_input_output.py`, conversion from RISC-V DSL to a python function in `dsl_to_func`.