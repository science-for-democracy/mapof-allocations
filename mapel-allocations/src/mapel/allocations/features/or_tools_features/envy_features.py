from enum import IntEnum, auto
from fractions import Fraction

from colorama import Fore
from ortools.linear_solver import pywraplp
from ortools.sat.python import cp_model

from .feature_data import FeatureData, Solution
from .helpers import get_status_str_cp_sat, get_status_str_pywraplp


# Possible objectives when searching for an envy-free solution/pareto-dominating solution
class Goal(IntEnum):
    # Minimize maximum absolute envy
    ABS_ENVY = auto()
    # Maximize social welfare
    SOCIAL_WEL = auto()


# The function returns an allocation for the instance described by "data" which is envy-free
# and not pareto-dominated by a solution in 'data.non_dominating'
# with the objective "goal" if goal is not None or otherwise with no objective
# if an envy-free solution exists, otherwise None is returned.
# If 'milp' is set to True, pywraplp is used, otherwise CP-SAT is used.
# 'milp' has to be set to True if 'data.utilities' is of type list[list[float]].
# The function returns a tuple consisting of
# - the solution (i.e. allocation) if one has been determined and otherwise None
# - the status (i.e. whether the found solution is optimal, feasible, or the model is infeasible or invalid)
# - the value of the objecive function if an allocation has been determined
#   and if 'goal is not None' and otherwise None
def envy_free_or_tools(
    data: FeatureData,
    goal: Goal | None = None,
    verbose: bool = False,
    milp: bool = False,
) -> tuple[Solution | None, str, float | None]:
    if milp:
        model = pywraplp.Solver.CreateSolver("SCIP")
    else:
        model: cp_model.CpModel = cp_model.CpModel()

    utils = data.utilities
    agents = range(len(utils))
    items = range(len(utils[0]))
    non_dominating_num = len(data.non_dominating)

    # The variables
    # Agent 'i' has item 'j' assigned to it
    if milp:
        is_assigned = {
            (agent, item): model.BoolVar(f"ass_({agent},{item}")  # type: ignore
            for agent in agents
            for item in items
        }
    else:
        is_assigned = {
            (agent, item): model.NewBoolVar(f"ass_({agent},{item}")
            for agent in agents
            for item in items
        }

    # Each item is assigned to exactly one agent
    for i in items:
        model.Add(sum(is_assigned[a, i] for a in agents) == 1)

    if goal is None or goal is Goal.SOCIAL_WEL:
        # Envy-freeness: For each agent a1, no other agent a2 has a bundle that a1 prefers to their own
        for a1 in agents:
            for a2 in agents:
                model.Add(
                    sum(is_assigned[a1, i] * data.utilities[a1][i] for i in items)
                    >= sum(is_assigned[a2, i] * data.utilities[a1][i] for i in items)
                )

    # Agent 'i' is now at least as satisfied as in non_dominating_solutions[idx]
    if milp:
        at_least_as_satisfied = {
            (nds_idx, agent): model.BoolVar(f"als_({nds_idx},{agent})")  # type: ignore
            for nds_idx in range(non_dominating_num)
            for agent in agents
        }
    else:
        at_least_as_satisfied = {
            (nds_idx, agent): model.NewBoolVar(f"als_({nds_idx},{agent})")
            for nds_idx in range(non_dominating_num)
            for agent in agents
        }

    # Define at_least_as_satisfied
    for idx, non_dom_sol in enumerate(data.non_dominating):
        for a in agents:
            min_util = min(a for i in data.utilities for a in i if a > 0)
            if milp:
                model.Add(
                    sum(is_assigned[a, i] * data.utilities[a][i] for i in items)
                    >= sum(non_dom_sol[a][i] * data.utilities[a][i] for i in items)
                    * at_least_as_satisfied[idx, a]
                )

                model.Add(
                    sum(is_assigned[a, i] * data.utilities[a][i] for i in items)
                    + min_util
                    <= sum(non_dom_sol[a][i] * data.utilities[a][i] for i in items)
                    + at_least_as_satisfied[idx, a]
                    * (sum(data.utilities[a][i] for i in items) + min_util)
                )
            else:
                model.Add(
                    sum(is_assigned[a, i] * data.utilities[a][i] for i in items)
                    >= sum(non_dom_sol[a][i] * data.utilities[a][i] for i in items)
                ).OnlyEnforceIf(  # type: ignore
                    at_least_as_satisfied[idx, a]
                )

                model.Add(
                    sum(is_assigned[a, i] * data.utilities[a][i] for i in items)
                    + min_util
                    <= sum(non_dom_sol[a][i] * data.utilities[a][i] for i in items)
                ).OnlyEnforceIf(  # type: ignore
                    at_least_as_satisfied[idx, a].Not()
                )

    # Whether the following holds for non_dominating_solutions[idx]:
    # forall(a in agents)(at_least_as_satisfied[idx,a])
    if milp:
        all_at_least_satisfied = {
            nds_idx: model.BoolVar(f"all_als_({nds_idx})")  # type: ignore
            for nds_idx in range(non_dominating_num)
        }
    else:
        all_at_least_satisfied = {
            nds_idx: model.NewBoolVar(f"all_als_({nds_idx})")
            for nds_idx in range(non_dominating_num)
        }

    # Define all_at_least_satisfied
    for nd_idx in range(non_dominating_num):
        if milp:
            model.Add(
                all_at_least_satisfied[nd_idx]
                + sum(1 - at_least_as_satisfied[nd_idx, a] for a in agents)
                >= 1
            )
            model.Add(
                sum(at_least_as_satisfied[nd_idx, a] for a in agents)
                >= all_at_least_satisfied[nd_idx] * len(agents)
            )
        else:
            model.AddMinEquality(
                all_at_least_satisfied[nd_idx],
                [at_least_as_satisfied[nd_idx, a] for a in agents],
            )

    # Agent 'i' is now more satisfied than in non_dominating_solutions[idx]
    if milp:
        more_satisfied = {
            (nds_idx, agent): model.BoolVar(f"ms_({nds_idx},{agent})")  # type: ignore
            for nds_idx in range(non_dominating_num)
            for agent in agents
        }
    else:
        more_satisfied = {
            (nds_idx, agent): model.NewBoolVar(f"ms_({nds_idx},{agent})")
            for nds_idx in range(non_dominating_num)
            for agent in agents
        }

    # Define more_satisfied
    for idx, non_dom_sol in enumerate(data.non_dominating):
        min_util = min(a for i in data.utilities for a in i if a > 0)
        for a in agents:
            if milp:
                model.Add(
                    (
                        sum(non_dom_sol[a][i] * data.utilities[a][i] for i in items)
                        + min_util
                    )
                    * more_satisfied[idx, a]
                    <= sum(is_assigned[a, i] * data.utilities[a][i] for i in items)
                )
                model.Add(
                    sum(is_assigned[a, i] * data.utilities[a][i] for i in items)
                    <= sum(non_dom_sol[a][i] * data.utilities[a][i] for i in items)
                    + more_satisfied[idx, a] * sum(data.utilities[a][i] for i in items)
                )
            else:
                model.Add(
                    sum(non_dom_sol[a][i] * data.utilities[a][i] for i in items)
                    + min_util
                    <= sum(is_assigned[a, i] * data.utilities[a][i] for i in items)
                ).OnlyEnforceIf(  # type: ignore
                    more_satisfied[idx, a]
                )
                model.Add(
                    sum(is_assigned[a, i] * data.utilities[a][i] for i in items)
                    <= sum(non_dom_sol[a][i] * data.utilities[a][i] for i in items)
                ).OnlyEnforceIf(  # type: ignore
                    more_satisfied[idx, a].Not()
                )

    # Ensure that the solution is not dominated by any of the given solutions
    # That means (1) that the utilities of each bundle are at least as large
    # or (2) that at least one is larger
    for nds_idx in range(non_dominating_num):
        if milp:
            model.Add(
                all_at_least_satisfied[nds_idx]
                + sum(more_satisfied[nds_idx, a] for a in agents)
                >= 1
            )
        else:
            model.AddBoolOr(
                [all_at_least_satisfied[nds_idx]]
                + [more_satisfied[nds_idx, a] for a in agents]
            )

    if goal is Goal.ABS_ENVY:
        # Upper bound of the absoluty envy for each pair of agents
        max_val = max([sum(i) for i in data.utilities])
        if milp:
            abs_env = model.Var(-max_val, max_val, False, f"abs_env")  # type: ignore
        else:
            abs_env = model.NewIntVar(-max_val, max_val, f"abs_env")

        # Define abs_env
        for a1 in agents:
            for a2 in agents:
                model.Add(
                    (
                        sum(is_assigned[a2, i] * data.utilities[a1][i] for i in items)
                        - sum(is_assigned[a1, i] * data.utilities[a1][i] for i in items)
                    )
                    <= abs_env
                )

        # Objective function
        model.Minimize(abs_env)

    if goal is Goal.SOCIAL_WEL:
        # Objective function
        model.Maximize(
            sum(
                sum(is_assigned[a, i] * data.utilities[a][i] for i in items)
                for a in agents
            )
        )

    if milp:
        status = model.Solve()  # type: ignore
        if verbose:
            print(f"Problem solved in {model.wall_time()/1000} seconds.")  # type: ignore
        status_str = get_status_str_pywraplp(status)
    else:
        solver = cp_model.CpSolver()
        solver.parameters.cp_model_presolve = True
        status = solver.Solve(model)
        status_str = get_status_str_cp_sat(status)

    if status_str in ["OPTIMAL", "FEASIBLE"]:
        if milp:
            sol = [[is_assigned[a, i].solution_value() for i in items] for a in agents]  # type: ignore
            obj = model.Objective().Value()  # type: ignore
        else:
            sol = [[solver.BooleanValue(is_assigned[a, i]) for i in items] for a in agents]  # type: ignore
            obj = solver.ObjectiveValue()  # type: ignore
        if verbose:
            print(f"{obj}")
        return sol, status_str, obj
    else:
        return None, status_str, None


# The function returns an allocation for the instance described by "data" which pareto-dominates 'ref_solution'
# with the objective "goal" if goal is not None or otherwise with no objective
# if an allocation exists, otherwise None is returned.
# If 'milp' is set to True, pywraplp is used, otherwise CP-SAT is used.
# 'milp' has to be set to True if 'data.utilities' is of type list[list[float]].
# The function returns a tuple consisting of
# - the solution (i.e. allocation) if one has been determined and otherwise None
# - the status (i.e. whether the found solution is optimal, feasible, or the model is infeasible or invalid)
# - the value of the objecive function if an allocation has been determined
#   and if 'goal is not None' and otherwise None
def pareto_dominating_or_tools(
    data: FeatureData,
    ref_solution: Solution,
    goal: Goal | None = None,
    verbose: bool = False,
    milp: bool = False,
) -> tuple[Solution | None, str, float | None]:
    if milp:
        model = pywraplp.Solver.CreateSolver("SCIP")
    else:
        model = cp_model.CpModel()

    utils = data.utilities
    agents = range(len(utils))
    item_num = len(utils[0])
    items = range(item_num)

    # The variables
    # Agent 'i' has item 'j' assigned to it
    if milp:
        is_assigned = {
            (agent, item): model.BoolVar(f"ass_({agent},{item}")  # type: ignore
            for agent in agents
            for item in items
        }
    else:
        is_assigned = {
            (agent, item): model.NewBoolVar(f"ass_({agent},{item}")
            for agent in agents
            for item in items
        }

    # The constraints
    # Each item is assigned to exactly one agent
    for i in items:
        model.Add(sum(is_assigned[a, i] for a in agents) == 1)

    # At least as good as the reference solution
    for a in agents:
        model.Add(
            sum(is_assigned[a, i] * utils[a][i] for i in items)
            >= sum(ref_solution[a][i] * utils[a][i] for i in items)
        )

    # Overall better
    min_util = min(a for i in utils for a in i if a > 0)
    model.Add(
        sum(ref_solution[a][i] * utils[a][i] for a in agents for i in items) + min_util
        <= sum(is_assigned[a, i] * utils[a][i] for a in agents for i in items)
    )

    if goal is Goal.ABS_ENVY:
        # Upper bound of the absoluty envy for each pair of agents
        max_val = max([sum(i) for i in data.utilities])
        if milp:
            abs_env = model.Var(-max_val, max_val, False, f"abs_env")  # type: ignore
        else:
            abs_env = model.NewIntVar(-max_val, max_val, f"abs_env")

        # Define abs_env
        for a1 in agents:
            for a2 in agents:
                model.Add(
                    (
                        sum(is_assigned[a2, i] * data.utilities[a1][i] for i in items)
                        - sum(is_assigned[a1, i] * data.utilities[a1][i] for i in items)
                    )
                    <= abs_env
                )

        # Objective function
        model.Minimize(abs_env)

    elif goal == Goal.SOCIAL_WEL:
        # Objective function (maximize social welfare)
        model.Maximize(
            sum(
                sum(is_assigned[a, i] * data.utilities[a][i] for i in items)
                for a in agents
            )
        )

    if milp:
        status = model.Solve()  # type: ignore
        if verbose:
            print(f"Problem solved in {model.wall_time()/1000} seconds.")  # type: ignore
        status_str = get_status_str_pywraplp(status)
    else:
        solver = cp_model.CpSolver()
        solver.parameters.cp_model_presolve = True
        status = solver.Solve(model)
        status_str = get_status_str_cp_sat(status)

    if status_str in ["OPTIMAL", "FEASIBLE"]:
        if milp:
            sol = [[is_assigned[a, i].solution_value() for i in items] for a in agents]  # type: ignore
            obj = model.Objective().Value()  # type: ignore
        else:
            sol = [[solver.BooleanValue(is_assigned[a, i]) for i in items] for a in agents]  # type: ignore
            obj = solver.ObjectiveValue()  # type: ignore
        if verbose:
            print(f"{obj}")
        return sol, status_str, obj
    else:
        return None, status_str, None


# Returns an allocation for the instance described by "dat" which is
# envy-free and pareto optimal if there is one.
# Otherwise, None is returned.
# The objective is "goal" if goal is not None. Otherwise, there is no objective.
# If 'milp' is set to True, pywraplp is used, otherwise CP-SAT is used.
# 'milp' has to be set to True if 'data.utilities' is of type list[list[float]].
# The function returns a tuple consisting of
# - the solution (i.e. allocation) if one has been determined and otherwise None
# - the status (i.e. whether the found solution is optimal, feasible, or the model is infeasible or invalid)
# - the number of iterations needed to get the result
def envy_and_pareto(
    data: FeatureData,
    goal: Goal | None = None,
    verbose: bool = False,
    milp: bool = False,
) -> tuple[Solution | None, str, int]:
    run = True
    sol = None
    res = ""
    sols = []
    iterations = 1
    while run:
        c_data = FeatureData(data.utilities, sols)
        sol, res, _ = envy_free_or_tools(c_data, goal, verbose, milp)

        if sol is None:
            return sol, res, iterations
        if verbose:
            values = c_data.get_bundle_vals(sol)
            print(f"{Fore.BLUE}{sol} {res} {values} → {sum(values)}{Fore.RESET}")

        solp, resp, _ = pareto_dominating_or_tools(c_data, sol, goal, verbose, milp)
        if verbose:
            print(f"{Fore.GREEN}{solp} {resp}{Fore.RESET}")
        if solp is not None:
            sols.append(solp)
        else:
            return sol, res, iterations
        iterations += 1

    return sol, res, iterations


# Returns an allocation for the instance described by "data" so that the relative envy of each agent is at most
# alpha/factor, if there is one.
# If 'milp' is set to True, pywraplp is used, otherwise CP-SAT is used.
# 'milp' has to be set to True if 'data.utilities' is of type list[list[float]].
# The function returns a tuple consisting of
# - the solution (i.e. allocation) if there is one and otherwise None
# - the status (i.e. whether the found solution is optimal, feasible, or the model is infeasible or invalid)
def rel_envy_alpha_or_tools(
    data: FeatureData,
    alpha: float,
    factor: int,
    verbose: bool = False,
    milp: bool = False,
) -> tuple[Solution | None, str, float | None]:
    if milp:
        model = pywraplp.Solver.CreateSolver("SCIP")
    else:
        model = cp_model.CpModel()

    utils = data.utilities
    agents = range(len(utils))
    items = range(len(utils[0]))

    # The variables
    # Agent 'i' has item 'j' assigned to it
    if milp:
        is_assigned = {
            (agent, item): model.BoolVar(f"ass_({agent},{item}")  # type: ignore
            for agent in agents
            for item in items
        }
    else:
        is_assigned = {
            (agent, item): model.NewBoolVar(f"ass_({agent},{item}")
            for agent in agents
            for item in items
        }

    # Each item is assigned to exactly one agent
    for i in items:
        model.Add(sum(is_assigned[a, i] for a in agents) == 1)

    # The relative envy has to be alpha
    for a1 in agents:
        for a2 in agents:
            if a1 == a2:
                continue
            a1_sum = sum(is_assigned[a1, i] * data.utilities[a1][i] for i in items)
            a2_sum = sum(is_assigned[a2, i] * data.utilities[a1][i] for i in items)
            model.Add(alpha * a1_sum >= factor * a2_sum)

    if milp:
        status = model.Solve()  # type: ignore
        if verbose:
            print(f"Problem solved in {model.wall_time()/1000} seconds.")  # type: ignore
        status_str = get_status_str_pywraplp(status)
    else:
        solver = cp_model.CpSolver()
        solver.parameters.cp_model_presolve = True
        status = solver.Solve(model)
        status_str = get_status_str_cp_sat(status)

    if status_str in ["OPTIMAL", "FEASIBLE"]:
        if milp:
            sol = [[is_assigned[a, i].solution_value() for i in items] for a in agents]  # type: ignore
            obj = model.Objective().Value()  # type: ignore
        else:
            sol = [[solver.BooleanValue(is_assigned[a, i]) for i in items] for a in agents]  # type: ignore
            obj = solver.ObjectiveValue()  # type: ignore
        if verbose:
            print(obj)
        return sol, status_str, obj
    else:
        return None, status_str, None


# This function uses a binary search to find the minimal maximal relative envy (called alpha)
# for the allocation instance described by "data".
# "factor" determines the accuracy of alpha: Internally, alpha*factor is determined using only integers.
# If 'milp' is set to True, pywraplp is used, otherwise CP-SAT is used.
# 'milp' has to be set to True if 'data.utilities' is of type list[list[float]].
# The function returns the determined alpha as a Fraction, the status, and the corresponding allocation.
def rel_envy(
    data: FeatureData, factor: int, verbose: bool = False, milp: bool = False
) -> tuple[Fraction | None, str, Solution | None]:
    get_sol = lambda a: rel_envy_alpha_or_tools(data, a, factor, verbose, milp)[:2]

    max_alpha = (max(sum(i for i in p if i > 0) for p in data.utilities) + 1) * factor
    if verbose:
        print(f"{max_alpha=}")

    lb = 0
    ub = 1
    last_sol, last_stat = get_sol(ub)
    if last_stat == "MODEL_INVALID":
        return None, last_stat, None
    while last_sol is None:
        lb = ub
        ub *= 2
        if ub > max_alpha:
            return None, last_stat, None
        last_sol, last_stat = get_sol(ub)
    if verbose:
        print(f"After first phase: [{lb}, {ub}]")

    while lb + 1 != ub:
        mid = (lb + ub) // 2
        last_sol, last_stat = get_sol(mid)
        if last_stat == "MODEL_INVALID":
            return None, last_stat, None
        if last_sol is None:
            lb = mid
        else:
            ub = mid

    last_sol, last_stat = get_sol(ub)
    return Fraction(ub, factor), last_stat, last_sol


# The function returns an allocation for the instance described by "data" with minimal sum of the maximal absolute envies.
# If 'milp' is set to True, pywraplp is used, otherwise CP-SAT is used.
# 'milp' has to be set to True if 'data.utilities' is of type list[list[float]].
# The function returns a tuple consisting of
# - the solution (i.e. allocation) if one has been determined and otherwise None
# - the status (i.e. whether the found solution is optimal, feasible, or the model is infeasible or invalid)
# - the value of the objecive function if an allocation has been determined
def sum_abs_envs_or_tools(
    data: FeatureData,
    verbose: bool = False,
    milp: bool = False,
) -> tuple[Solution | None, str, float | None]:
    if milp:
        model = pywraplp.Solver.CreateSolver("SCIP")
    else:
        model: cp_model.CpModel = cp_model.CpModel()

    utils = data.utilities
    agents = range(len(utils))
    items = range(len(utils[0]))

    # The variables
    # Agent 'i' has item 'j' assigned to it
    if milp:
        is_assigned = {
            (agent, item): model.BoolVar(f"ass_({agent},{item}")  # type: ignore
            for agent in agents
            for item in items
        }
    else:
        is_assigned = {
            (agent, item): model.NewBoolVar(f"ass_({agent},{item}")
            for agent in agents
            for item in items
        }

    # Each item is assigned to exactly one agent
    for i in items:
        model.Add(sum(is_assigned[a, i] for a in agents) == 1)

    # Upper bound of the absoluty envy for each pair of agents
    max_val = max([sum(i) for i in data.utilities])
    if milp:
        abs_envy_ag = {
            agent: model.Var(-max_val, max_val, False, f"abs_env_{agent}")  # type: ignore
            for agent in agents
        }

    else:
        abs_envy_ag = {
            agent: model.NewIntVar(-max_val, max_val, f"abs_env_{agent}")  # type: ignore
            for agent in agents
        }

    # Define abs_env_ag
    for a1 in agents:
        for a2 in agents:
            model.Add(
                (
                    sum(is_assigned[a2, i] * data.utilities[a1][i] for i in items)
                    - sum(is_assigned[a1, i] * data.utilities[a1][i] for i in items)
                )
                <= abs_envy_ag[a1]
            )

    # Objective function
    model.Minimize(sum(abs_envy_ag[a] for a in agents))

    if milp:
        status = model.Solve()  # type: ignore
        if verbose:
            print(f"Problem solved in {model.wall_time()/1000} seconds.")  # type: ignore
        status_str = get_status_str_pywraplp(status)
    else:
        solver = cp_model.CpSolver()
        solver.parameters.cp_model_presolve = True
        status = solver.Solve(model)
        status_str = get_status_str_cp_sat(status)

    if status_str in ["OPTIMAL", "FEASIBLE"]:
        if milp:
            sol = [[is_assigned[a, i].solution_value() for i in items] for a in agents]  # type: ignore
            obj = model.Objective().Value()  # type: ignore
        else:
            sol = [[solver.BooleanValue(is_assigned[a, i]) for i in items] for a in agents]  # type: ignore
            obj = solver.ObjectiveValue()  # type: ignore
        if verbose:
            print(f"{obj}")
        return sol, status_str, obj
    else:
        return None, status_str, None
