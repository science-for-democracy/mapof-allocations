from ortools.linear_solver import pywraplp
from ortools.sat.python import cp_model

from .feature_data import FeatureData, Solution
from .helpers import Timer, get_status_str_cp_sat, get_status_str_pywraplp


# Determines the maximin-share value of the agent with index "agent_idx" (the indices start with 0)
# for the instance described by "data".
# If 'milp' is set to True, pywraplp is used, otherwise CP-SAT is used.
# 'milp' has to be set to True if 'data.utilities' is of type list[list[float]].
def mms_agent_or_tools(
    data: FeatureData, agent_idx: int, verbose: bool = False, milp: bool = False
) -> tuple[int | None, str, float | None]:
    if milp:
        model = pywraplp.Solver.CreateSolver("SCIP")
    else:
        model = cp_model.CpModel()

    utils = data.utilities
    subsets = range(len(utils))
    items = range(len(utils[0]))

    # The variables
    # Whether item 'i' is part of the n-th subset of the partition
    if milp:
        part_of = {
            (item, subset): model.BoolVar(f"pof_({item}, {subset})")  # type: ignore
            for item in items
            for subset in subsets
        }
    else:
        part_of = {
            (item, subset): model.NewBoolVar(f"pof_({item}, {subset})")
            for item in items
            for subset in subsets
        }

    # Define part_of
    # An item is part of exactly one subset
    for item in items:
        if milp:
            model.Add(sum(part_of[item, b] for b in subsets) == 1)
        else:
            model.AddExactlyOne(part_of[item, b] for b in subsets)

    # The utility of the n-th bundle
    if milp:
        util = {
            bundle: model.Var(  # type: ignore
                0,
                sum(utils[agent_idx]),
                False,
                f"util_({bundle})",
            )
            for bundle in subsets
        }
    else:
        util = {
            bundle: model.NewIntVar(
                0,
                sum(utils[agent_idx]),
                f"util_({bundle})",
            )
            for bundle in subsets
        }

    # Define util
    for b in subsets:
        model.Add(
            util[b] == sum(part_of[i, b] * data.utilities[agent_idx][i] for i in items)
        )

    # The minimum of the utils
    if milp:
        util_min = model.Var(  # type: ignore
            0,
            sum(utils[agent_idx]),
            False,
            f"util_min",
        )
    else:
        util_min = model.NewIntVar(
            0,
            sum(utils[agent_idx]),
            f"util_min",
        )

    # Define util_min
    for b in subsets:
        model.Add(util_min <= util[b])

    # Objective function
    model.Maximize(util_min)

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
            obj = model.Objective().Value()  # type: ignore
            sol = util_min.solution_value()  # type: ignore
        else:
            obj = solver.ObjectiveValue()  # type: ignore
            sol = solver.Value(util_min)  # type: ignore
        if verbose:
            print(obj)
        return sol, status_str, obj
    else:
        if verbose:
            print(status_str)
        return None, status_str, None


# Determines an MMMS-fair allocation for the instance described by "data" given the maximin-share value
# of each agent ('mms_ag') if such an allocation exists.
# If 'milp' is set to True, pywraplp is used, otherwise CP-SAT is used.
# 'milp' has to be set to True if 'data.utilities' is of type list[list[float]].
def mms_fair_or_tools(
    data: FeatureData, mms_ag: list[int], verbose: bool = False, milp: bool = False
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

    # MMS-fair condition
    for ag in agents:
        model.Add(
            sum(is_assigned[ag, i] * data.utilities[ag][i] for i in items) >= mms_ag[ag]
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


# Determines a MMMS-fair allocation for the instance described by "data" if one exists.
# If 'milp' is set to True, pywraplp is used, otherwise CP-SAT is used.
# 'milp' has to be set to True if 'data.utilities' is of type list[list[float]].
def get_mms_fair(
    data: FeatureData, verbose: bool = False, milp: bool = False
) -> tuple[Solution | None, str, list[int | None]]:
    agents = range(len(data.utilities))

    with Timer() as to:
        ag_mms = []
        for ag_idx in agents:
            with Timer() as ti:
                sol, _, _ = mms_agent_or_tools(data, ag_idx, verbose, milp)
                ag_mms.append(sol)
            if verbose:
                print(f"Time for agent {ag_idx}: ", ti.time)

    if verbose:
        print("Overall time for getting MMS values of agents: ", to.time)
        print("MMS of agents: ", ag_mms)
    sol2, status_str, _ = mms_fair_or_tools(data, ag_mms, verbose, milp)

    if verbose and sol2 is not None:
        for ag_idx in agents:
            print(
                f"Bundle of agent {ag_idx}: {[f'Item {i}' for i, v in enumerate(sol2[ag_idx]) if v]}"
            )
            print(f"Utilities of agent {ag_idx}: {data.utilities[ag_idx]}")
    return sol2, status_str, ag_mms
