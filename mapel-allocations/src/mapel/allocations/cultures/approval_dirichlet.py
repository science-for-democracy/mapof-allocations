import numpy as np
from fractions import Fraction
from numpy.random import default_rng
import random

from mapel.elections.cultures.resampling import generate_approval_resampling_votes
# from mapel.elections.objects.ApprovalElection import update_params_approval
from mapel.allocations.cultures.basic_cultures import dirichlet_matrix


def approval_dirichlet(agents_cnt=None,
                       resources_cnt=None,
                       phi=None, p=None):
    if phi is None:
        phi = np.random.random()
    if p is None:
        p = np.random.random()

    approval_votes = generate_approval_resampling_votes(
        num_voters=agents_cnt,
        num_candidates=resources_cnt,
        phi=phi,
        p=p)

    utility_matrix = []

    for i, vote in enumerate(approval_votes):
        if len(vote) == 0:
            vector = [0 for _ in range(resources_cnt)]
            vector[random.randint(0, resources_cnt - 1)] = 1
        else:
            alphas = [1e-10 for _ in range(resources_cnt)]
            for candidate in vote:
                alphas[int(candidate)] = 1.
            vector = default_rng().dirichlet(alphas, size=1)[0].tolist()

        utility_matrix.append(list(map(Fraction, vector)))

    return utility_matrix

