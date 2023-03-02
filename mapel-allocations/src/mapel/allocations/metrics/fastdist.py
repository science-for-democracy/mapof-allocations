import mapel.core.logs as logs
logger = logs.get_logger(__name__)
import itertools
import numpy as np

import mapel.core.matchings as matchings
import mapel.core.inner_distances as inner_distances


def fast_distance(left_task, right_task, *args, **kwargs):
    logger.debug("Computing single fast distance")
    cost_table = get_matching_cost_table(left_task, right_task)
    return matchings.solve_matching_vectors(cost_table)


def get_matching_cost_table(left_task, right_task):
    """ Return: Cost table """

    vectors_1 = convert_to_vectors(left_task)
    vectors_2 = convert_to_vectors(right_task)
    size = left_task.resources_count
    return [[inner_distances.emd(vectors_1[i], vectors_2[j]) for i in range(size)] for j in range(size)]


def convert_to_vectors(task):
    precision = 100
    vectors = np.zeros([task.resources_count, precision+1])

    for i in range(task.agents_count):
        for j in range(task.resources_count):
            vectors[j][int(task.utility_matrix[i][j]*precision)] += 1
    vectors /= precision
    return vectors
