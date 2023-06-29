from ortools.linear_solver import pywraplp
from ortools.sat.python import cp_model

from .feature_data import FeatureData, Solution
from .helpers import get_status_str_cp_sat, get_status_str_pywraplp


# The function tries to find an allocation for the instance described by "data" which has a maximal utilitarian social welfare.
# If 'milp' is set to True, pywrapl is used, otherwise CP-SAT is used. 'milp' has to be set to True if 'data.utilities' is of type
# list[list[float]].
# The function returns a tuple consisting of
# - the solution (i.e. allocation) if one has been determined and otherwise None
# - the status (i.e. whether the found solution is optimal, feasible, or the model is infeasible or invalid)
# - the objective value if an allocation has been determined, otherwise None
def max_social_welfare(
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

    # Objective function
    model.Maximize(
        sum(
            sum(is_assigned[a, i] * data.utilities[a][i] for i in items) for a in agents
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
        # solver.parameters.log_search_progress = True
        # solver.parameters.log_to_stdout = True
        status = solver.Solve(model)
        status_str = get_status_str_cp_sat(status)
    if status_str in ["OPTIMAL", "FEASIBLE"]:
        if milp:
            obj = model.Objective().Value()  # type: ignore
            sol = [[is_assigned[a, i].solution_value() for i in items] for a in agents]  # type: ignore
        else:
            obj = solver.ObjectiveValue()  # type: ignore
            sol = [[solver.BooleanValue(is_assigned[a, i]) for i in items] for a in agents]  # type: ignore
        if verbose:
            print(obj)
        return sol, status_str, obj
    else:
        return None, status_str, None
