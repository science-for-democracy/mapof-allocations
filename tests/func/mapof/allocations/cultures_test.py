import os
from fractions import Fraction

from mapof.allocations.core.alloctask import AllocationTask
import pytest


class TestGeneratingCultures:
    cultures = [
        ("contention", {}),
        ("bicontention", {}),
        ("indifference", {}),
        ("separability", {}),
        ("wideseparability", {}),
        ("lowerdiag", {}),
        ("dirichlet", {}),
        ("dirichlet_shift", {"shift_val":1}),
        ("blurred_separability", {}),
        ("attributes", {}),
        ("approval_dirichlet", {}),
        ("approval_gen_dirichlet", {}),
        ("euclidean", {}),
        ("indsep", {}),
        ("consep", {}),
        ("indcon", {}),
        ("conbcon", {}),
        ("bconsep", {}),
        ("wsepind", {}),
        ("sepwsep", {}),
        ("bconwsep", {}),
        ("uniform", {}),
        ("expon", {"rate": 0.5}),
        ("block", {"per_row_zeros_cnt": 1}),
    ]
    agents_count = 10
    resources_count = 10

    @pytest.mark.parametrize("culture, params", cultures)
    def test_culture(self, culture, params):
        task = AllocationTask.from_culture(
            instance_id=f"test_{culture}",
            agents_count=self.agents_count,
            resources_count=self.resources_count,
            culture_id=culture,
            params=params
        )
        assert self.agents_count == task.agents_count
        assert self.resources_count == task.resources_count
        assert task.utility_matrix is not None
