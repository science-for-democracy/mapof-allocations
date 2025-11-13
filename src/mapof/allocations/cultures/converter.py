import copy

import numpy as np
from fractions import Fraction
from numpy.random import default_rng
import random

from mapof.elections.cultures import generate_approval_votes
from mapof.elections.cultures import generate_ordinal_votes
from mapof.elections.objects.OrdinalElection import update_params_ordinal
from mapof.elections.objects.ApprovalElection import update_params_approval


def convert_approval_votes_to_utility_matrix(culture_id=None,
                                             agents_cnt=None,
                                             resources_cnt=None,
                                             params=None):

    params, _ = update_params_approval(params, dict(), None, culture_id, num_candidates = resources_cnt)
    approval_votes = generate_approval_votes(culture_id=culture_id,
                                             num_voters=agents_cnt,
                                             num_candidates=resources_cnt,
                                             params=params)

    # utility_matrix = np.zeros([agents_cnt, resources_cnt])
    utility_matrix = [[Fraction(0) for _ in range(resources_cnt)] for _ in range(agents_cnt)]

    for i, vote in enumerate(approval_votes):
        for candidate in vote:
            utility_matrix[i][int(candidate)] = Fraction(1, len(vote))

    for i in range(agents_cnt):
        if sum(utility_matrix[i]) == 0.:
            # utility_matrix[i] = [Fraction(1, resources_cnt) for _ in range(resources_cnt)]
            utility_matrix[i] = [0 for _ in range(resources_cnt)]
            utility_matrix[i][random.randint(0, resources_cnt - 1)] = 1

    return utility_matrix


# EXAMPLE
# convert_approval_votes_to_utility_matrix(culture_id='impartial_culture',
#                                                 agents_cnt=20,
#                                                 resources_cnt=10,
#                                                 params={'p':0.5, 'phi':0.5})


def convert_ordinal_votes_to_utility_matrix__top_k(culture_id=None,
                                                   agents_cnt=None,
                                                   resources_cnt=None,
                                                   params=None,
                                                   top_k=None):
    params, _ = update_params_ordinal(params, None, culture_id, resources_cnt)

    ordinal_votes = generate_ordinal_votes(culture_id=culture_id,
                                           num_voters=agents_cnt,
                                           num_candidates=resources_cnt,
                                           params=params)

    # utility_matrix = np.zeros([agents_cnt, resources_cnt])
    utility_matrix = [[0 for _ in range(resources_cnt)] for _ in range(agents_cnt)]
    for i, vote in enumerate(ordinal_votes):
        for j in range(top_k):
            utility_matrix[i][vote[j]] = 1 / top_k

    return utility_matrix


# EXAMPLE
# convert_ordinal_votes_to_utility_matrix(culture_id='impartial_culture',
#                                                 agents_cnt=20,
#                                                 resources_cnt=10,
#                                          params=None,
#                                          top_k=5)

def n_linear_sum(n):
    return sum([i for i in range(n)])


def n_square_sum(n):
    return sum([(i) ** 2 for i in range(n)])


def n_cube_sum(n):
    return sum([(i) ** 3 for i in range(n)])


def get_func_from_str(func, n):

    if func == 'linear':
        vector = [i / n_linear_sum(n) for i in range(n)]
    elif func == 'square':
        vector = [i * i / n_square_sum(n) for i in range(n)]
    elif func == 'cube':
        vector = [i * i * i / n_cube_sum(n) for i in range(n)]
    else:
        print('no such func name')
        return None

    vector.reverse()
    return vector


def convert_ordinal_votes_to_utility_matrix__proportional(culture_id=None,
                                                          agents_cnt=None,
                                                          resources_cnt=None,
                                                          params=None,
                                                          func=None):
    params, _ = update_params_ordinal(params, dict(), None, culture_id, num_candidates=resources_cnt)

    ordinal_votes = generate_ordinal_votes(culture_id=culture_id,
                                           num_voters=agents_cnt,
                                           num_candidates=resources_cnt,
                                           params=params)

    if type(func) is str:
        func = get_func_from_str(func, resources_cnt)

    # utility_matrix = np.zeros([agents_cnt, resources_cnt])
    utility_matrix = [[0 for _ in range(resources_cnt)] for _ in range(agents_cnt)]
    for i, vote in enumerate(ordinal_votes):
        for j in range(resources_cnt):
            utility_matrix[i][vote[j]] = func[j]

    return utility_matrix


# EXAMPLE
# convert_ordinal_votes_to_utility_matrix__proportional(culture_id='impartial_culture',
#                                                 agents_cnt=20,
#                                                 resources_cnt=10,
#                                          params=None,
#                                          func='linear')


def ordinal(agents_cnt, resources_cnt, culture_id, ordinal_params, func):
    return convert_ordinal_votes_to_utility_matrix__proportional(culture_id=culture_id,
                                                                 agents_cnt=agents_cnt,
                                                                 resources_cnt=resources_cnt,
                                                                 params=copy.deepcopy(ordinal_params),
                                                                 func=func)
    # return convert_ordinal_votes_to_utility_matrix__top_k(culture_id=culture_id,
    #                                                       agents_cnt=agents_cnt,
    #                                                       resources_cnt=resources_cnt,
    #                                                       params=ordinal_params,
    #                                                       top_k=1)


def approval(agents_cnt, resources_cnt, culture_id, approval_params):
    return convert_approval_votes_to_utility_matrix(culture_id=culture_id,
                                                    agents_cnt=agents_cnt,
                                                    resources_cnt=resources_cnt,
                                                    params=copy.deepcopy(approval_params))
