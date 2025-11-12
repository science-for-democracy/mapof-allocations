import math

from ortools.linear_solver import pywraplp

from .feature_data import FeatureData, Solution
from .helpers import get_status_str_pywraplp

# This is currently not used.
# Implementation of https://dl.acm.org/doi/10.1145/3355902, Fig. 4
# (“The Unreasonable Fairness of Maximum Nash Welfare”).
# The assumption is that each utility is >= 0. If not every agent can get a bundle with
# an utility of at least 1, the problem is infeasible.
# The function returns a tuple consisting of
# - the solution (i.e. allocation) if one has been determined and otherwise None
# - the status (i.e. whether the found solution is optimal, feasible,
#   or the model is infeasible or invalid)
def nash_or_tools(
    data: FeatureData,
    verbose: bool = False,
) -> tuple[Solution | None, str]:
    utils = data.utilities
    agents = range(len(utils))
    items = range(len(utils[0]))

    solver: pywraplp.Solver = pywraplp.Solver.CreateSolver("SCIP")

    # The variables
    # Agent 'i' has item 'j' assigned to it
    is_assigned = {
        (agent, item): solver.BoolVar(f"ass_({agent},{item}")
        for agent in agents
        for item in items
    }

    # w_i
    w_i = {
        agent: solver.Var(
            0,
            sum(data.utilities[agent]),
            False,
            f"w_{agent}",
        )
        for agent in agents
    }

    # The constraints
    # Each item is assigned to exactly one agent
    for i in items:
        solver.Add(sum(is_assigned[a, i] for a in agents) == 1)

    # The value of the assigned bundle has to be greater or equal 1 for each agent (because of the logarithm)
    for a in agents:
        solver.Add(sum(is_assigned[a, i] * data.utilities[a][i] for i in items) >= 1)

    # Define w_i
    for a in agents:
        util_a = data.utilities[a]
        for k in range(max(math.floor(min(util_a)), 1), math.ceil(sum(util_a)), +2):
            solver.Add(
                w_i[a]
                <= math.log(k)
                + (math.log(k + 1) - math.log(k))
                * (sum(is_assigned[a, i] * data.utilities[a][i] for i in items) - k)
            )

    # Objective function
    solver.Maximize(sum(w_i[a] for a in agents))
    status = solver.Solve()

    if verbose:
        print(f"Problem solved in {solver.wall_time()/1000} seconds.")

    status_str = get_status_str_pywraplp(status)
    if status_str in ["OPTIMAL", "FEASIBLE"]:
        sol = [[is_assigned[a, i].solution_value() for i in items] for a in agents]
        if verbose:
            print(solver.Objective().Value())
        return sol, status_str

    return None, status_str
