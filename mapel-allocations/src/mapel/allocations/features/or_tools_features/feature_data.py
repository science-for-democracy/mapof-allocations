from dataclasses import dataclass, field

# Solution[i][j] is true iff the agent with index i has been assigned the object with index j.
Solution = list[list[bool]]


@dataclass
class FeatureData:
    utilities: list[list[int]] | list[list[float]]
    # The list of solutions (which have pareto-dominated previous solutions and)
    # which may not pareto-dominate a solution.
    non_dominating: list[Solution] = field(default_factory=list)

    @property
    def agents(self) -> list[str]:
        return [f"Agent {i}" for i in range(1, len(self.utilities) + 1)]

    @property
    def items(self) -> list[str]:
        return [f"Item {i}" for i in range(1, len(self.utilities[0]) + 1)]

    def get_max_abs_envies(self, sol: Solution) -> list[float]:
        abs_envies: list[float] = []
        for ag_idx, ag_utils in enumerate(self.utilities):
            own_bundle = 0
            for item_idx, u in enumerate(ag_utils):
                own_bundle += float(u) * int(sol[ag_idx][item_idx])

            v_envies = []
            for oag_idx in range(len(self.utilities)):
                if oag_idx == ag_idx:
                    continue
                other_bundle = 0
                for item_idx, u in enumerate(ag_utils):
                    other_bundle += float(u) * int(sol[oag_idx][item_idx])
                v_envies.append(other_bundle - own_bundle)
            abs_envies.append(max(v_envies))
        return abs_envies

    def get_max_abs_envy(self, sol: Solution):
        abs_envies = self.get_max_abs_envies(sol)
        return max(abs_envies)

    def get_sum_max_abs_envies(self, sol: Solution):
        abs_envies = self.get_max_abs_envies(sol)
        return sum(abs_envies)

    def get_nash_welfare(self, sol: Solution):
        res = 1
        for ag_idx, ag_utils in enumerate(self.utilities):
            own_bundle = 0
            for item_idx, u in enumerate(ag_utils):
                own_bundle += float(u) * int(sol[ag_idx][item_idx])
            res *= own_bundle
        return res

    def get_bundle_vals(self, sol: Solution) -> list[float]:
        return [
            sum(
                float(self.utilities[i][j]) * int(sol[i][j])
                for j in range(len(self.items))
            )
            for i in range(len(self.agents))
        ]
