import numpy as np
from scipy import spatial


def _gini(x):
    # (Warning: This is a concise implementation, but it is O(n**2)
    # in time and memory, where n = len(x).  *Don't* pass in huge
    # samples!)

    # Mean absolute difference
    mad = np.abs(np.subtract.outer(x, x)).mean()
    # Relative mean absolute difference
    rmad = mad / np.mean(x)
    # Gini coefficient
    g = 0.5 * rmad
    return g


def pickiness(instance):
    total_gini = 0
    for i in range(instance.agents_count):
        array = np.asarray(instance[i], dtype="float")
        agent_gini = _gini(array)
        total_gini += agent_gini
    feature_value = total_gini / instance.agents_count
    max_gini = _gini(np.asarray([1] + ([0] * (instance.resources_count - 1))))
    norm_value = feature_value / max_gini
    return norm_value


def diversity_of_demand(instance):
    array = []
    for i in range(instance.resources_count):
        col = np.array([instance[a][i] for a in range(instance.agents_count)])
        array.append(sum(col))
    return _gini(np.array(array)) / (1 - 1 / instance.resources_count)


def diversity_of_votes(instance):
    dist = 0
    for i in range(instance.resources_count):
        row_i = np.array([instance[i]], dtype=float)
        for j in range(instance.resources_count):
            row_j = np.array([instance[j]], dtype=float)
            dist += spatial.distance.cosine(row_i.tolist()[0], row_j.tolist()[0])

    return dist / (instance.resources_count * (instance.resources_count - 1))
