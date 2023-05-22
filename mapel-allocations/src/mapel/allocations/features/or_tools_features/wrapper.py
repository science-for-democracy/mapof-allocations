from fractions import Fraction

from .envy_features import Goal, Solution, envy_and_pareto, envy_free_or_tools, rel_envy
from .feature_data import FeatureData
from .helpers import (
    Timer,
    get_float_utility_matrix,
    get_int_utility_matrix,
    get_int_utility_matrix_accuracy,
)
from .maximin_feature import get_mms_fair
from .nash_welfare_feature import nash_or_tools
from .social_welfare_feature import max_social_welfare


# Helper for finding envy-free allocations.
def envy_free_helper(
    instance, goal: Goal | None = None
) -> tuple[Solution | None, str, float | None, float]:
    umatrix = instance.utility_matrix
    try:
        utils_ints = get_int_utility_matrix(umatrix)
        data = FeatureData(utils_ints)
        with Timer() as t:
            sol, status, obj = envy_free_or_tools(data, goal)
        return sol, status, obj, t.time
    except:
        utils_floats = get_float_utility_matrix(umatrix)
        data = FeatureData(utils_floats)
        with Timer() as t:
            sol, status, obj = envy_free_or_tools(data, goal, milp=True)
        return sol, status, obj, t.time


# Returns 1.0 if an envy-free allocation exists for 'instance', otherwise 0.0.
def exists_envy_free(instance):
    res, _, _, _ = envy_free_helper(instance)
    if res is None:
        return 0.0
    return 1.0


# Returns the runtime of searching for an envy-free allocation.
def exists_envy_free_time(instance):
    _, _, _, t = envy_free_helper(instance)
    return t


# Returns the minimal maximal absolute envy for 'instance'.
def min_max_abs_envy(instance):
    res, _, _, _ = envy_free_helper(instance, Goal.ABS_ENVY)
    assert res is not None
    return FeatureData(instance.utility_matrix).get_max_abs_envy(res)


# Returns the runtime for finding the minimal maximal absolute envy for 'instance'.
def min_max_abs_envy_time(instance):
    _, _, _, t = envy_free_helper(instance, Goal.ABS_ENVY)
    return t


# Helper for finding the minimal maximal relative envy for 'instance'.
def rel_envy_helper(instance) -> tuple[Fraction | None, Solution | None, float]:
    umatrix = instance.utility_matrix
    try:
        utils_ints = get_int_utility_matrix(umatrix)
        with Timer() as t:
            rel_envy_frac, sol = rel_envy(FeatureData(utils_ints), 10)
        return rel_envy_frac, sol, t.time
    except:
        utils_floats = get_float_utility_matrix(umatrix)
        with Timer() as t:
            rel_envy_frac, rel_sol = rel_envy(FeatureData(utils_floats), 10, milp=True)
        return rel_envy_frac, rel_sol, t.time


# Returns the minimal maximal relative envy for 'instance' if it is defined, otherwise 1.2.
def relative_envy(instance):
    frac, _, _ = rel_envy_helper(instance)
    if frac is not None:
        return float(frac)
    return None


# Returns the runtime of searching the minimal maximal relative envy for 'instance'.
def relative_envy_time(instance):
    _, _, t = rel_envy_helper(instance)
    return t


# Helper for finding an allocation with the maximum Nash welfare.
# It uses "get_int_utility_matrix" to get utilities consisting of integers.
# However, if the sum of these newly computed utilities is larger than
# 10^5, utilities consisting of integers are computed
# taking only 4 decimal places of floats into account ('get_int_utility_matrix_accuracy').
# If no solution can be determined with the help of the function "nash_or_tools",
# 0 is returned.
def nash_helper(instance):
    umatrix = instance.utility_matrix
    utils_ints = get_int_utility_matrix(umatrix)
    if max(sum(i) for i in utils_ints) > 10**5:
        utils_decimal = get_int_utility_matrix_accuracy(umatrix, decimal_places=4)
        data = FeatureData(utils_decimal)
    else:
        data = FeatureData(utils_ints)

    with Timer() as t:
        sol, _ = nash_or_tools(data)
    if sol is None:
        return 0, t.time
    return FeatureData(instance.utility_matrix).get_nash_welfare(sol), t.time


# Returns the maximum Nash welfare for 'instance'.
# If not every agent can get a bundle with an utility of at least 1, 0 is returned.
def nash(instance):
    value, _ = nash_helper(instance)
    return value


# Returns the runtime of searching the maximum Nash welfare for 'instance'.
def nash_time(instance):
    _, t = nash_helper(instance)
    return t


# Helper for finding envy-free and pareto optimal allocations (with maximal social welfare).
def envy_pareto_helper(
    instance,
) -> tuple[Solution | None, str, float | None, float]:
    umatrix = instance.utility_matrix
    try:
        utils_ints = get_int_utility_matrix(umatrix)
        data = FeatureData(utils_ints)
        with Timer() as t:
            sol, stat, obj = envy_and_pareto(data, goal=Goal.SOCIAL_WEL)
        return sol, stat, obj, t.time
    except:
        utils_floats = get_float_utility_matrix(umatrix)
        data = FeatureData(utils_floats)
        with Timer() as t:
            sol, stat, obj = envy_and_pareto(data, goal=Goal.SOCIAL_WEL, milp=True)
        return sol, stat, obj, t.time


# Returns 1.0 if an envy-free and pareto optimal allocation exists for 'instance',
# otherwise 0.0.
def exists_envy_free_pareto(instance):
    res, _, _, _ = envy_pareto_helper(instance)
    if res is None:
        return 0.0
    return 1.0


# Returns the runtime of searching for an envy-free and pareto-optimal allocation.
def exists_envy_free_pareto_time(instance):
    _, _, _, t = envy_pareto_helper(instance)
    return t


# Helper for finding MMS-fair allocations for "instance".
def mms_helper(instance) -> tuple[Solution | None, str, list[int | None], float]:
    umatrix = instance.utility_matrix
    try:
        utils_ints = get_int_utility_matrix(umatrix)
        data = FeatureData(utils_ints)
        with Timer() as t:
            sol, status, obj = get_mms_fair(data)
        return sol, status, obj, t.time
    except:
        utils_floats = get_float_utility_matrix(umatrix)
        data = FeatureData(utils_floats)
        with Timer() as t:
            sol, status, obj = get_mms_fair(data, milp=True)
        return sol, status, obj, t.time


# Returns 1.0 if an MMS-fair allocation exists for 'instance',
# otherwise 0.0.
def exists_mms(instance):
    res, _, _, _ = mms_helper(instance)
    if res is None:
        return 0.0
    return 1.0


# Returns the runtime of searching for an MMS-fair allocation.
def exists_mms_time(instance):
    _, _, _, t = mms_helper(instance)
    return t


# Helper for finding the maximum quotient of
# (1) the maximum social welfare for an envy-free allocation (or 0 if there is none) and
# (2) the maximum social welfare.
def price_of_envy_freeness_helper(instance) -> tuple[float, float]:
    umatrix = instance.utility_matrix
    utils_ints = get_int_utility_matrix(umatrix)
    data_ints = FeatureData(utils_ints)
    utils_floats = get_float_utility_matrix(umatrix)
    data_floats = FeatureData(utils_floats)
    with Timer() as t:
        try:
            sol_env, _, obj_env = envy_free_or_tools(data_ints, Goal.SOCIAL_WEL)
            sol_soc, _, obj_soc = max_social_welfare(data_ints)
        except:
            sol_env, _, obj_env = envy_free_or_tools(
                data_floats, Goal.SOCIAL_WEL, milp=True
            )
            sol_soc, _, obj_soc = max_social_welfare(data_floats, milp=True)
    assert sol_soc is not None and obj_soc is not None

    if sol_env is None:
        return 0.0, t.time
    assert obj_env is not None
    return obj_env / obj_soc, t.time


# Returns the maximum quotient of
# (1) the maximum social welfare for an envy-free allocation (or 0 if there is none) and
# (2) the maximum social welfare.
def price_of_envy_freeness(instance):
    return price_of_envy_freeness_helper(instance)[0]


# Returns the runtime for finding the maximun quotient of
# (1) the maximum social welfare for an envy-free allocation (or 0 if there is none) and
# (2) the maximum social welfare.
def price_of_envy_freeness_time(instance):
    return price_of_envy_freeness_helper(instance)[1]


# Helper for finding the maximum quotient of
# (1) the maximum social welfare for an envy-free and
#     pareto optimal allocation (or 0 if there is none) and
# (2) the maximum social welfare.
def price_of_envy_pareto_helper(instance) -> tuple[float, float]:
    umatrix = instance.utility_matrix
    utils_ints = get_int_utility_matrix(umatrix)
    data_ints = FeatureData(utils_ints)
    utils_floats = get_float_utility_matrix(umatrix)
    data_floats = FeatureData(utils_floats)
    with Timer() as t:
        try:
            sol_env_par, _, obj_env_par = envy_and_pareto(
                data_ints, goal=Goal.SOCIAL_WEL
            )
            sol_soc, _, obj_soc = max_social_welfare(data_ints)
        except:
            sol_env_par, _, obj_env_par = envy_and_pareto(
                data_floats, goal=Goal.SOCIAL_WEL, milp=True
            )
            sol_soc, _, obj_soc = max_social_welfare(data_floats, milp=True)

    assert sol_soc is not None and obj_soc is not None
    if sol_env_par is None:
        return 0.0, t.time

    assert obj_env_par is not None
    return obj_env_par / obj_soc, t.time


# Returns the maximum quotient of
# (1) the maximum social welfare for an envy-free and
#     pareto optimal allocation (or 0 if there is none) and
# (2) the maximum social welfare.
def price_of_envy_pareto(instance):
    return price_of_envy_pareto_helper(instance)[0]


# Returns the runtime for finding the maximun quotient of
# (1) the maximum social welfare for an envy-free and
#     pareto optimal allocation (or 0 if there is none) and
# (2) the maximum social welfare.
def price_of_envy_pareto_time(instance):
    return price_of_envy_pareto_helper(instance)[1]
