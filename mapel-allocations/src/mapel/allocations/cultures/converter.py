import numpy as np

from mapel.elections.cultures_ import generate_approval_votes
from mapel.elections.cultures_ import generate_ordinal_votes


def convert_approval_votes_to_utility_matrix(culture_id=None,
                                                agents_cnt=None,
                                                resources_cnt=None,
                                                params=None):

    approval_votes = generate_approval_votes(culture_id=culture_id,
                                             num_voters=agents_cnt,
                                             num_candidates=resources_cnt,
                                             params=params)

    utility_matrix = np.zeros([agents_cnt, resources_cnt])
    for i, vote in enumerate(approval_votes):
        for candidate in vote:
            utility_matrix[i][int(candidate)] = 1/len(vote)

    return utility_matrix


# EXAMPLE
# convert_approval_votes_to_utility_matrix(culture_id='impartial_culture',
#                                                 agents_cnt=20,
#                                                 resources_cnt=10,
#                                                 params={'p':0.5, 'phi':0.5})


def convert_ordinal_votes_to_utility_matrix(culture_id=None,
                                             agents_cnt=None,
                                             resources_cnt=None,
                                             params=None,
                                             top_k=None):

    ordinal_votes = generate_ordinal_votes(culture_id=culture_id,
                                             num_voters=agents_cnt,
                                             num_candidates=resources_cnt,
                                             params=params)

    utility_matrix = np.zeros([agents_cnt, resources_cnt])
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


