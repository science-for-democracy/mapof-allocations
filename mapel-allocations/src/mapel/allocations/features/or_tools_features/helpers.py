from dataclasses import dataclass
from fractions import Fraction
from math import lcm, floor
from time import perf_counter

from colorama import Fore
from ortools.linear_solver import pywraplp
from ortools.sat.python import cp_model


# Used in with statements to get the time that was consumed in the corresponding block
@dataclass
class Timer:
    info: str | None = None
    verbose: bool = False

    def __enter__(self):
        self.time = perf_counter()
        return self

    def __exit__(self, type, value, traceback):
        self.time = perf_counter() - self.time
        if self.info is None:
            prefix = "Time"
        else:
            prefix = f"Time for {self.info}"
        self.readout = f"{Fore.BLUE}{prefix}: {self.time:.3f} s{Fore.RESET}"
        if self.verbose:
            print(self.readout)


# String representation of a solution's status determined by CP-SAT.
def get_status_str_cp_sat(status):
    if status == cp_model.OPTIMAL:
        status_str = "OPTIMAL"
    elif status == cp_model.INFEASIBLE:
        status_str = "INFEASIBLE"
    elif status == cp_model.MODEL_INVALID:
        status_str = "MODEL_INVALID"
    elif status == cp_model.FEASIBLE:
        status_str = "FEASIBLE"
    else:
        status_str = "UNKNOWN"
    return status_str


# String representation of a solution's status determined by pywraplp.
def get_status_str_pywraplp(status):
    if status == pywraplp.Solver.OPTIMAL:
        status_str = "OPTIMAL"
    elif status == pywraplp.Solver.INFEASIBLE:
        status_str = "INFEASIBLE"
    elif status == pywraplp.Solver.MODEL_INVALID:
        status_str = "MODEL_INVALID"
    elif status == pywraplp.Solver.FEASIBLE:
        status_str = "FEASIBLE"
    elif status == pywraplp.Solver.UNBOUNDED:
        status_str = "UNBOUNDED"
    elif status == pywraplp.Solver.ABNORMAL:
        status_str = "ABNORMAL"
    else:
        status_str = "NOT_SOLVED"
    return status_str


# Determines a Fraction (with the smallest positive denominator)
# so that the absolute difference between it and the float value is at most err.
# Based on https://en.wikipedia.org/wiki/Continued_fraction
# TODO returns Fraction(value) to be safe for now
def get_fraction(value: float, err: float = 1e-10) -> Fraction:
    return Fraction(value)

    coeffs: list[int] = []
    fraction = Fraction(value)

    while True:
        integer_part = floor(fraction)
        fraction -= integer_part
        if fraction == 0:
            break
        fraction = 1 / fraction

        coeffs.append(integer_part)

        approx_frac = Fraction()
        for coefficient in reversed(coeffs[1:]):
            approx_frac = Fraction(1, (coefficient + approx_frac))
        approx_frac = coeffs[0] + approx_frac

        if abs(approx_frac - value) < err:
            return approx_frac

    return Fraction(value)


# Transforms each Fraction from 'fract_utils' into an integer by multiplying them
# with the least common multiple of their denominators.
def fraction_to_int_utilities(
    fract_utils: list[list[Fraction]],
) -> tuple[list[list[int]], int]:
    denominators = [i.denominator for p in fract_utils for i in p]
    least_common_mult = lcm(*denominators)
    return [
        [i.numerator * least_common_mult // i.denominator for i in p]
        for p in fract_utils
    ], least_common_mult


# Returns utilities consisting of integers for the given 'utility_matrix'
# (by using 'fraction_to_int_utilities' if the utilities are of type Fraction or float).
# 'utility_matrix' has to be of type list[list[int]], list[list[float]], or list[list[Fraction]].
def get_int_utility_matrix(utility_matrix) -> list[list[int]]:
    utils_ints = None
    if all(isinstance(i, list) for i in utility_matrix):
        if all(isinstance(item, int) for i in utility_matrix for item in i):
            utils_ints = utility_matrix
        elif all(isinstance(item, float) for i in utility_matrix for item in i):
            f_votes: list[list[Fraction]] = [
                [get_fraction(i) for i in v] for v in utility_matrix
            ]
            utils_ints, _ = fraction_to_int_utilities(f_votes)
        elif all(isinstance(item, Fraction) for i in utility_matrix for item in i):
            utils_ints, _ = fraction_to_int_utilities(utility_matrix)

    assert utils_ints is not None
    return utils_ints


# Converts the numbers in 'utility_matrix' to integers by multiplying them with 10**decimal_places
# and rounding them to the nearest integer (unless they are already integers).
# 'utility_matrix' has to be of type list[list[int]], list[list[float]], or list[list[Fraction]].
def get_int_utility_matrix_accuracy(
    utility_matrix, decimal_places: int
) -> list[list[int]]:
    utils_decimal = None
    if all(isinstance(i, list) for i in utility_matrix):
        if all(isinstance(item, int) for i in utility_matrix for item in i):
            utils_decimal = utility_matrix
        elif all(isinstance(item, float) for i in utility_matrix for item in i):
            utils_decimal = [
                [round((10**decimal_places) * i) for i in p] for p in utility_matrix
            ]
        elif all(isinstance(item, Fraction) for i in utility_matrix for item in i):
            utils_decimal = [
                [round((10**decimal_places) * float(i)) for i in p]
                for p in utility_matrix
            ]

    assert utils_decimal is not None
    return utils_decimal


# Returns utilities consinsting of floats for the given 'utility_matrix'.
# 'utility_matrix' has to be of type list[list[int]], list[list[float]], or list[list[Fraction]].
def get_float_utility_matrix(utility_matrix) -> list[list[float]]:
    utils_floats = None
    if all(isinstance(i, list) for i in utility_matrix):
        if all(isinstance(item, int) for i in utility_matrix for item in i):
            utils_floats = [[float(i) for i in p] for p in utility_matrix]
        elif all(isinstance(item, float) for i in utility_matrix for item in i):
            utils_floats = utility_matrix
        elif all(isinstance(item, Fraction) for i in utility_matrix for item in i):
            utils_floats = [[float(i) for i in p] for p in utility_matrix]

    assert utils_floats is not None
    return utils_floats
