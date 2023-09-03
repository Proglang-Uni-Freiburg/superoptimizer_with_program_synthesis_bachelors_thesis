import timeit
from cegis_verify import Verifier

ex1 = "x + 10 - 5"
ex2 = "(x + 2) * 4"
divideprint = lambda x: print("\n" + 3 * "-" + x + 3 * "-")

divideprint(ex1)
synth_enum = Verifier.fromStr(ex1)
synth_cegis = Verifier.fromStr(ex1)
print("Enum:", timeit.timeit(synth_enum.bottom_up, number=1))
print("CEGIS:", timeit.timeit(synth_cegis.cegis_2, number=1))

divideprint(ex2)
synth_enum = Verifier.fromStr(ex2)
synth_cegis = Verifier.fromStr(ex1)
print("Enum:", timeit.timeit(synth_enum.bottom_up, number=1))
print("CEGIS:", timeit.timeit(synth_cegis.cegis_2, number=1))