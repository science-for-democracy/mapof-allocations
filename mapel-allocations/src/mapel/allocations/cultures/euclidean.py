
import numpy as np
from sklearn.preprocessing import normalize


def euclidean_alloc_matrix(agents_cnt, resources_cnt, dim=2, space='uniform'):

    if space == 'uniform':
        resources_ = np.random.rand(resources_cnt, dim)
        agents_ = np.random.rand(agents_cnt, dim)
    elif space == 'gaussian':
        resources_ = np.random.normal(loc=0.5, scale=0.15, size=(resources_cnt, dim))
        agents_ = np.random.normal(loc=0.5, scale=0.15, size=(agents_cnt, dim))

    distance_matrix = np.zeros([agents_cnt, resources_cnt], dtype=float)

    for v in range(agents_cnt):
        for c in range(resources_cnt):
            if dim == 1:
                distance_matrix[v][c] = abs(agents_[v] - resources_[c])
            else:
                distance_matrix[v][c] = np.linalg.norm(agents_[v] - resources_[c])

    utility_matrix = np.zeros([agents_cnt, resources_cnt], dtype=float)

    for v in range(agents_cnt):
        for c in range(resources_cnt):
            utility_matrix[v][c] = 1 - distance_matrix[v][c]/max(distance_matrix[v])

    utility_matrix = normalize(utility_matrix, axis=1, norm='l1')
    return utility_matrix.tolist()


def attributes_alloc_matrix(agents_cnt, resources_cnt, dim=2, space='uniform'):

    if space == 'uniform':
        resources_skills = np.random.rand(resources_cnt, dim)
        agents_weights = np.random.rand(agents_cnt, dim)
    elif space == 'gaussian':
        resources_skills = np.random.normal(loc=0.5, scale=0.15, size=(resources_cnt, dim))
        agents_weights = np.random.normal(loc=0.5, scale=0.15, size=(agents_cnt, dim))

    utility_matrix = np.zeros([agents_cnt, resources_cnt], dtype=float)
    ones = np.ones([dim], dtype=float)

    for v in range(agents_cnt):
        for c in range(resources_cnt):
            if dim == 1:
                utility_matrix[v][c] = abs(1. - resources_skills[c]) * agents_weights[v]
            else:
                utility_matrix[v][c] = _weighted_l1(ones, resources_skills[c], agents_weights[v])

    utility_matrix = normalize(utility_matrix, axis=1, norm='l1')
    return utility_matrix.tolist()


def _weighted_l1(a1, a2, w):
    total = 0
    for i in range(len(a1)):
        total += abs(a1[i]-a2[i])*w[i]
    return total
