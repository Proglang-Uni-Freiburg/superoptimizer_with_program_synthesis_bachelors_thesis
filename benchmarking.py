import signal
import timeit
from memory_profiler import memory_usage
import matplotlib.pyplot as plt
from cegis_verify import Verifier

divideprint = lambda x: print("\n" + 3 * "-" + x + 3 * "-")

def runall_takeaverage(name, f, l):
    res = []
    for input_func in l:
        synth = Verifier.fromStr(input_func)
        divideprint(input_func)
        signal.alarm(600)
        try:
            single_res = timeit.timeit(lambda: f(synth), number=1)
            res.append(single_res)
        except Exception as e:
            res.append(600)
        print(name, res[-1])
    return (sum(res) / len(res))

def runall_memory(name, f, l):
    res = []
    for input_func in l:
        synth = Verifier.fromStr(input_func)
        divideprint(input_func)
        signal.alarm(600)
        try:
            single_res = max(memory_usage(lambda: f(synth)))
            res.append(single_res)
        except Exception as e:
            res.append(600)
        print(name, res[-1])
    return (sum(res) / len(res))


def signal_handler(signum, frame):
    raise Exception('Timeout')

signal.signal(signal.SIGALRM, signal_handler)
    
ex1_add = ["3", "x + 10 - 5", "x * 1"]
ex1_shift = ["x * 4", "x % y", "x / 4"]
ex2 = ["(x + 2) * 4", "x * 2 + 20", "x + y + 1"]
ex3 = ["(((x + 3)* 4) - 1) * 2", "x % 3", "x / 3"]
ex4 = ["x * y * z", "(x / 3) + 3"]

def run_benchmarking():
    make_two_time_bar_graph(*run_time_benchmarking(ex1_add, ex1_shift, ex2, ex3))


# due to signal function, this is unfortunately linux-only. different approaches to timeout lead to segfaults
def run_time_benchmarking(*args) -> tuple[list, list]:
    enum_time_results = []
    cegis_time_results = []
    for arg in args:
        enum_time_results.append(runall_takeaverage('Enum', Verifier.bottom_up, arg))
        cegis_time_results.append(runall_takeaverage('CEGIS', Verifier.cegis_2, arg))
    return enum_time_results, cegis_time_results


def make_two_time_bar_graph(enum_vals, cegis_vals):
    width = 0.25
    xval_range = range(0, len(cegis_vals))
    plt.bar(xval_range, enum_vals, color = 'g', width=width, edgecolor='black', label='Simple Enumeration')
    plt.bar([i + width for i in xval_range], cegis_vals, color = 'b', width=width, edgecolor='black', label='CEGIS')
    plt.title("Time Analysis")
    plt.xlabel('Number of Lines in Solution')
    plt.ylabel('Time in seconds')
    
    plt.xticks([i + width/2 for i in xval_range], ["1, Simple", "1, Complex", "2, Simple", "2, Complex"])
    plt.legend()
    x1, x2, y1, y2 = plt.axis()
    plt.axis((x1, x2, 0, 4))
    plt.show()

def run_memory_benchmarking():
    mem_usage_cegis0 = []
    mem_usage_cegis1 = []
    mem_usage_cegis2 = []
    mem_usage_enum = []
    for arg in [ex1_add, ex1_shift, ex2, ex3]:
        mem_usage_cegis0.append(runall_memory('Cegis0', Verifier.cegis_0, arg))
        mem_usage_cegis1.append(runall_memory('Cegis1', Verifier.cegis_1, arg))
        mem_usage_cegis2.append(runall_memory('Cegis2', Verifier.cegis_2, arg))
        mem_usage_enum.append(runall_memory('Enum', Verifier.bottom_up, arg))
    width=0.18
    plt.bar([0, 1, 2, 3], mem_usage_cegis0, color = 'g', width=width, edgecolor='black', label='Variant 1')
    plt.bar([width, 1 + width, 2 + width, 3+width], mem_usage_cegis1, color = 'r', width=width, edgecolor='black', label='Variant 2')
    plt.bar([2*width, 1 + 2*width, 2 + 2*width, 3 + 2*width], mem_usage_cegis2, color = 'b', width=width, edgecolor='black', label='Final Variant')
    plt.bar([3*width, 1 + 3*width, 2 + 3*width, 3 + 3*width], mem_usage_cegis2, color = 'purple', width=width, edgecolor='black', label='Simple Enumeration')

    plt.title("Memory Analysis")
    plt.xlabel('Number of Lines in Solution')
    plt.ylabel('Max. number of memory used in MB')
    plt.xticks([(3/2)*width, 1+(3/2)*width, 2+(3/2)*width, 3+(3/2)*width], ["1, Simple", "1, Complex", "2, Simple", "2, Complex"])
    plt.legend()
    plt.show()

    verifier = Verifier.fromStr("(x / 3) + 3")
    mem_usage_cegis2 = memory_usage(verifier.cegis_2)
    mem_usage_cegis1 = memory_usage(verifier.cegis_1)
    print(f"(x / 3) + 3\ncegis1: {max(mem_usage_cegis1)}, cegis final: {max(mem_usage_cegis2)}")
    


def compare_cegis_variants():
    width=0.25
    res1 = []
    res2 = [] 
    res3 = []
    for arg in [ex1_add, ex1_shift, ex2, ex3]:
        res1.append(runall_takeaverage('Cegis0', Verifier.cegis_0, arg))
        res2.append(runall_takeaverage('Cegis1', Verifier.cegis_1, arg))
        res3.append(runall_takeaverage('Cegis2', Verifier.cegis_2, arg))
    plt.bar([0, 1, 2, 3], res1, color = 'g', width=width, edgecolor='black', label='Variant 1')
    plt.bar([width, 1 + width, 2 + width, 3+width], res2, color = 'r', width=width, edgecolor='black', label='Variant 2')
    plt.bar([2*width, 1 + 2*width, 2 + 2*width, 3 + 2*width], res3, color = 'b', width=width, edgecolor='black', label='Final Variant')

    plt.title("Time Analysis")
    plt.xlabel('Number of Lines in Solution')
    plt.ylabel('Time in seconds')
    plt.xticks([width, 1+width, 2+width, 3+width], ["1, Simple", "1, Complex", "2, Simple", "2, Complex"])
    plt.legend()
    plt.show()

    verifier = Verifier.fromStr("(x / 3) + 3")
    time_cegis2 = timeit.timeit(verifier.cegis_2, number=1)
    time_cegis1 = timeit.timeit(verifier.cegis_1, number=1)
    print(f"(x / 3) + 3\ncegis 1: {time_cegis1}, cegis final: {time_cegis2}")


if __name__ == "__main__":
    run_benchmarking()
    compare_cegis_variants()
    run_memory_benchmarking()