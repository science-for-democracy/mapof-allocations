from fractions import Fraction
from typing import Iterable

from .envy_features import (
    Goal,
    Solution,
    envy_and_pareto,
    envy_free_or_tools,
    rel_envy,
    sum_abs_envs_or_tools,
)
from .feature_data import FeatureData
from .helpers import (
    Timer,
    get_float_utility_matrix,
    get_int_utility_matrix,
    get_int_utility_matrix_accuracy,
)
from .maximin_feature import get_mms_fair
from .nash_welfare_feature import nash_or_tools
from .prop_share import alpha_prop_share
from .social_welfare_feature import max_social_welfare


# Helper for finding envy-free allocations.
def envy_free_helper(
    instance, goal: Goal | None = None
) -> tuple[Solution | None, str, float | None, float]:
    umatrix = instance.utility_matrix
    utils_ints = get_int_utility_matrix(umatrix)
    data_ints = FeatureData(utils_ints)

    def do_if_int_not_poss():
        utils_floats = get_float_utility_matrix(umatrix)
        with Timer() as t:
            sol, status, obj = envy_free_or_tools(
                FeatureData(utils_floats), goal, milp=True
            )
        return sol, status, obj, t.time

    try:
        with Timer() as t:
            sol, status, obj = envy_free_or_tools(data_ints, goal)
        if status == "MODEL_INVALID":
            return do_if_int_not_poss()
        return sol, status, obj, t.time
    except:
        return do_if_int_not_poss()


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

    def do_if_int_not_poss():
        utils_floats = get_float_utility_matrix(umatrix)
        with Timer() as t:
            rel_envy_frac, _, rel_sol = rel_envy(
                FeatureData(utils_floats), 10, milp=True
            )
        return rel_envy_frac, rel_sol, t.time

    try:
        utils_ints = get_int_utility_matrix(umatrix)
        with Timer() as t:
            rel_envy_frac, status, sol = rel_envy(FeatureData(utils_ints), 10)
        if status == "MODEL_INVALID":
            return do_if_int_not_poss()
        return rel_envy_frac, sol, t.time
    except:
        return do_if_int_not_poss()


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
def nash_helper(instance, decimal_places: None | int = None):
    umatrix = instance.utility_matrix
    if decimal_places is not None:
        utils_decimal = get_int_utility_matrix_accuracy(
            umatrix, decimal_places=decimal_places
        )
        data = FeatureData(utils_decimal)
    else:
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


# Returns the maximum Nash welfare for 'instance' by exhaustively trying all allocations
# and the time needed for finding it.
def nash_exhaustive(instance):
    fdata = FeatureData(instance.utility_matrix)
    res_num: int = instance.resources_count
    ag_num: int = instance.agents_count

    def allocs():
        def rec(cur_res: int) -> Iterable[tuple[int, ...]]:
            if cur_res == res_num:
                yield tuple()
                return

            for i in range(ag_num):
                for alloc in rec(cur_res + 1):
                    yield (i,) + alloc

        return rec(0)

    def alloc_mats():
        for alloc in allocs():
            mat = [[False] * res_num for _ in range(ag_num)]
            for res, ag in enumerate(alloc):
                mat[ag][res] = True
            yield mat

    with Timer() as t:
        best_nash = 0
        for alloc in alloc_mats():
            cnash = fdata.get_nash_welfare(alloc)
            if cnash > best_nash:
                best_nash = cnash
    return best_nash, t.time


# Returns the maximum Nash welfare for 'instance'.
def nash(instance):
    # value, _ = nash_helper(instance)
    value, _ = nash_exhaustive(instance)
    return value


# Returns the runtime of searching the maximum Nash welfare for 'instance'.
def nash_time(instance):
    _, t = nash_helper(instance)
    return t

# Returns the maximum Nash welfare for 'instance', but using a lower precision.
def nash_lp(instance):
    value, _ = nash_helper(instance, 3)
    return value

# Helper for finding envy-free and pareto optimal allocations (with maximal social welfare).
def envy_pareto_helper(
    instance,
) -> tuple[Solution | None, str, float | None, float]:
    umatrix = instance.utility_matrix

    def do_if_int_not_poss():
        utils_floats = get_float_utility_matrix(umatrix)
        with Timer() as t:
            sol, stat, obj = envy_and_pareto(
                FeatureData(utils_floats), goal=Goal.SOCIAL_WEL, milp=True
            )
        return sol, stat, obj, t.time

    try:
        utils_ints = get_int_utility_matrix(umatrix)
        data = FeatureData(utils_ints)
        with Timer() as t:
            sol, stat, obj = envy_and_pareto(data, goal=Goal.SOCIAL_WEL)
        if stat == "MODEL_INVALID":
            return do_if_int_not_poss()
        return sol, stat, obj, t.time
    except:
        return do_if_int_not_poss()


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

    def do_if_int_not_poss():
        utils_floats = get_float_utility_matrix(umatrix)
        with Timer() as t:
            sol, status, obj = get_mms_fair(FeatureData(utils_floats), milp=True)
        return sol, status, obj, t.time

    try:
        utils_ints = get_int_utility_matrix(umatrix)
        data = FeatureData(utils_ints)
        with Timer() as t:
            sol, status, obj = get_mms_fair(data)
        if status == "MODEL_INVALID":
            return do_if_int_not_poss()
        return sol, status, obj, t.time
    except:
        return do_if_int_not_poss()


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

    def do_if_int_not_poss():
        utils_floats = get_float_utility_matrix(umatrix)
        data_floats = FeatureData(utils_floats)
        sol_env, _, obj_env = envy_free_or_tools(
            data_floats, Goal.SOCIAL_WEL, milp=True
        )
        sol_soc, _, obj_soc = max_social_welfare(data_floats, milp=True)
        return sol_env, obj_env, sol_soc, obj_soc

    with Timer() as t:
        try:
            utils_ints = get_int_utility_matrix(umatrix)
            data_ints = FeatureData(utils_ints)
            sol_env, stat1, obj_env = envy_free_or_tools(data_ints, Goal.SOCIAL_WEL)
            sol_soc, stat2, obj_soc = max_social_welfare(data_ints)
            if stat1 == "MODEL_INVALID" or stat2 == "MODEL_INVALID":
                sol_env, obj_env, sol_soc, obj_soc = do_if_int_not_poss()
        except:
            sol_env, obj_env, sol_soc, obj_soc = do_if_int_not_poss()

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
    def do_if_int_not_poss():
        utils_floats = get_float_utility_matrix(umatrix)
        data_floats = FeatureData(utils_floats)
        sol_env_par, _, obj_env_par = envy_and_pareto(
            data_floats, goal=Goal.SOCIAL_WEL, milp=True
        )
        sol_soc, _, obj_soc = max_social_welfare(data_floats, milp=True)
        return sol_env_par, obj_env_par, sol_soc, obj_soc

    umatrix = instance.utility_matrix
    utils_ints = get_int_utility_matrix(umatrix)
    data_ints = FeatureData(utils_ints)
    with Timer() as t:
        try:
            sol_env_par, stat1, obj_env_par = envy_and_pareto(
                data_ints, goal=Goal.SOCIAL_WEL
            )
            sol_soc, stat2, obj_soc = max_social_welfare(data_ints)
            if stat1 == "MODEL_INVALID" or stat2 == "MODEL_INVALID":
                sol_env_par, obj_env_par, sol_soc, obj_soc = do_if_int_not_poss()
        except:
            sol_env_par, obj_env_par, sol_soc, obj_soc = do_if_int_not_poss()

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


# Helper for finding an allocation with maximal utilitarian social welfare.
def max_social_wels_helper(instance) -> tuple[list[float], float]:
    umatrix = instance.utility_matrix
    utils_ints = get_int_utility_matrix(umatrix)
    data_ints = FeatureData(utils_ints)

    def do_if_int_not_poss():
        utils_floats = get_float_utility_matrix(umatrix)
        data_floats = FeatureData(utils_floats)
        sol_soc, _, obj_soc = max_social_welfare(data_floats, milp=True)
        return sol_soc, obj_soc

    with Timer() as t:
        try:
            sol_soc, stat, obj_soc = max_social_welfare(data_ints)
            if stat == "MODEL_INVALID":
                sol_soc, obj_soc = do_if_int_not_poss()

        except:
            sol_soc, obj_soc = do_if_int_not_poss()

    assert sol_soc is not None and obj_soc is not None
    return FeatureData(umatrix).get_bundle_vals(sol_soc), t.time


# Returns the maximal utilitarian social welfare for 'instance'.
def max_social_wel(instance) -> float:
    wels, _ = max_social_wels_helper(instance)
    return sum(wels)


# Returns the runtime for finding the maximal utilitarian social welfare for 'instance'.
def max_social_wel_time(instance) -> float:
    _, t = max_social_wels_helper(instance)
    return t


# Returns the maximal utilitarian social welfare divided by the number of agents.
def max_social_wel_scaled(instance) -> float:
    sum_welfares = max_social_wel(instance)
    return sum_welfares / instance.agents_count


# Helper for finding the minimal sum of the maximal absolute envies.
def sum_abs_helper(instance) -> tuple[Solution | None, str, float | None, float]:
    umatrix = instance.utility_matrix
    utils_ints = get_int_utility_matrix(umatrix)
    data = FeatureData(utils_ints)

    def do_if_int_not_poss():
        utils_floats = get_float_utility_matrix(umatrix)
        with Timer() as t:
            sol, status, obj = sum_abs_envs_or_tools(
                FeatureData(utils_floats), milp=True
            )
        return sol, status, obj, t.time

    try:
        with Timer() as t:
            sol, status, obj = sum_abs_envs_or_tools(data)
        if status == "MODEL_INVALID":
            return do_if_int_not_poss()
        return sol, status, obj, t.time
    except:
        return do_if_int_not_poss()


# Returns the minimal sum of the maximal absolute envies for 'instance'.
def min_sum_max_abs_envy(instance):
    res, _, _, _ = sum_abs_helper(instance)
    assert res is not None
    return FeatureData(instance.utility_matrix).get_sum_max_abs_envies(res)


# Returns the minimal sum of the maximal absolute envies divided by the number of agents.
def min_sum_max_abs_envy_scaled(instance) -> float:
    sum_mae = min_sum_max_abs_envy(instance)
    return sum_mae / instance.agents_count


# Returns the runtime for finding the minimal sum of the maximal absolute envies for 'instance'.
def min_sum_max_abs_envy_time(instance):
    _, _, _, t = sum_abs_helper(instance)
    return t


# Returns the maximal alpha so that an alpha-proportional share exists
# First, a helper
def a_prop_share_helper(instance) -> tuple[float | None, str, float | None, float]:
    umatrix = instance.utility_matrix
    utils_ints = get_int_utility_matrix(umatrix)
    data_ints = FeatureData(utils_ints)

    def do_if_int_not_poss():
        utils_floats = get_float_utility_matrix(umatrix)
        with Timer() as t:
            sol, status, obj = alpha_prop_share(FeatureData(utils_floats))
        return sol, status, obj, t.time

    try:
        with Timer() as t:
            sol, status, obj = alpha_prop_share(data_ints)
        if status == "MODEL_INVALID":
            return do_if_int_not_poss()
        return sol, status, obj, t.time
    except:
        return do_if_int_not_poss()


def a_prop_share(instance):
    sol, _, _, _ = a_prop_share_helper(instance)
    return sol


# Returns 1.0 if an proportional share allocation exists for 'instance',
# otherwise 0.0.
def exists_prop_share(instance):
    alpha = a_prop_share(instance)
    assert alpha is not None
    if alpha >= 1:
        return 1.0
    return 0.0
