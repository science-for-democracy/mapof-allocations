from ortools.linear_solver import pywraplp
from ortools.sat.python import cp_model

from .feature_data import FeatureData
from .helpers import get_status_str_cp_sat, get_status_str_pywraplp


# alpha-proportional share (pywraplp is used)
# Returns
# - the maximal alpha if it has been determined and otherwise None
# - the status (i.e. whether the found solution is optimal, feasible, or the model is infeasible or invalid)
# - the value of the objecive function if an allocation has been determined
def alpha_prop_share(
    data: FeatureData,
    verbose: bool = False,
) -> tuple[float | None, str, float | None]:
    # model: pywraplp.Solver = pywraplp.Solver.CreateSolver("SCIP")
    model: pywraplp.Solver = pywraplp.Solver.CreateSolver("GUROBI")

    utils = data.utilities
    n = len(utils)
    agents = range(n)
    items = range(len(utils[0]))

    # The variables
    # Agent 'i' has item 'j' assigned to it
    is_assigned = {
        (agent, item): model.BoolVar(f"ass_({agent},{item}")  # type: ignore
        for agent in agents
        for item in items
    }

    # Each item is assigned to exactly one agent
    for i in items:
        model.Add(sum(is_assigned[a, i] for a in agents) == 1)

    # The alpha to be maximized
    alpha = model.Var(0, n, False, "alpha")

    # Condition for alpha-proportional fair
    for a in agents:
        model.Add(
            n * sum(is_assigned[a, i] * utils[a][i] for i in items)
            >= sum(utils[a]) * alpha
        )

    # Objective function
    model.Maximize(alpha)

    status = model.Solve()
    if verbose:
        print(f"Problem solved in {model.wall_time()/1000} seconds.")
    status_str = get_status_str_pywraplp(status)

    if status_str in ["OPTIMAL", "FEASIBLE"]:
        obj = model.Objective().Value()
        if verbose:
            print(f"{obj}")
        return obj, status_str, obj
    else:
        return None, status_str, None


# Determine whether an proportional share allocation exists for 'instance',
def ex_prop_share(
    data: FeatureData,
    verbose: bool = False,
    milp: bool = False,
) -> tuple[bool | None, str]:
    if milp:
        model = pywraplp.Solver.CreateSolver("SCIP")
    else:
        model: cp_model.CpModel = cp_model.CpModel()

    utils = data.utilities
    agents = range(len(utils))
    n = len(utils[0])
    items = range(n)

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

    # Condition for alpha-proportional fair
    for a in agents:
        model.Add(
            n * sum(is_assigned[a, i] * utils[a][i] for i in items) >= sum(utils[a])
        )

    if milp:
        status = model.Solve()  # type: ignore
        if verbose:
            print(f"Problem solved in {model.wall_time()/1000} seconds.")  # type: ignore
        status_str = get_status_str_pywraplp(status)
    else:
        solver = cp_model.CpSolver()
        solver.parameters.cp_model_presolve = True
        # solver.parameters.log_search_progress = True
        # solver.parameters.log_to_stdout = True
        status = solver.Solve(model)
        status_str = get_status_str_cp_sat(status)

    if status_str in ["OPTIMAL", "FEASIBLE"]:
        if milp:
            obj = model.Objective().Value()  # type: ignore
        else:
            obj = solver.ObjectiveValue()  # type: ignore
        if verbose:
            print(f"{obj}")
        return True, status_str
    elif status_str in ["INFEASIBLE"]:
        return False, status_str
    else:
        return None, status_str
