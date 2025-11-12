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


def one_minus_pickiness(instance):
    return 1 - pickiness(instance)


def diversity_of_demand(instance):
    array = []
    for i in range(instance.resources_count):
        col = np.array([instance[a][i] for a in range(instance.agents_count)])
        array.append(sum(col))
    return _gini(np.array(array)) / (1 - 1 / instance.resources_count)


def diversity_of_votes(instance):
    dist = 0
    for i in range(instance.agents_count):
        row_i = np.array([instance[i]], dtype=float)
        for j in range(instance.agents_count):
            row_j = np.array([instance[j]], dtype=float)
            dist += spatial.distance.cosine(row_i.tolist()[0], row_j.tolist()[0])

    return dist / (instance.agents_count * (instance.agents_count - 1))


def diversity_of_votes_l2(instance):
    dist = 0
    for i in range(instance.agents_count):
        row_i = np.array([instance[i]], dtype=float)
        for j in range(instance.agents_count):
            row_j = np.array([instance[j]], dtype=float)
            dist += np.linalg.norm(row_i - row_j, ord=2)

    largest_dist = (2**0.5)*instance.agents_count*(instance.agents_count-1)

    return dist / largest_dist


def all_three(instance):
    return diversity_of_demand(instance) + diversity_of_votes(instance) + one_minus_pickiness(instance)


def larg_svd(instance):
    umf = [[float(v) for v in row] for row in instance.utility_matrix]
    _, S, _ = np.linalg.svd(umf)
    return S[0]


def sec_larg_svd(instance):
    umf = [[float(v) for v in row] for row in instance.utility_matrix]
    _, S, _ = np.linalg.svd(umf)
    return S[1]


def level_deviation(instance):
    usorted = [
        sorted([float(i) for i in r], reverse=True) for r in instance.utility_matrix
    ]
    s = 0
    n: int = instance.agents_count
    for r in range(instance.resources_count):
        s += np.std([usorted[a][r] for a in range(n)])
    return s


def min_demand(instance):
    return min(
        sum(instance[a][r] for a in range(instance.agents_count))
        for r in range(instance.resources_count)
    )

# Maximum demand
def max_demand(instance):
    return float(max(
        sum(instance[a][r] for a in range(instance.agents_count))
        for r in range(instance.resources_count)
    ))


def eff_m(instance):
    i = 0
    for r in range(instance.resources_count):
        if all(
            instance.utility_matrix[a][r] == 0 for a in range(instance.agents_count)
        ):
            continue
        i += 1
    return i

# Fraction of agents who are single-minded
def frac_sm(instance):
    sm_num = 0
    for a in range(instance.agents_count):
        wants = [
            instance.utility_matrix[a][r]
            for r in range(instance.resources_count)
            if instance.utility_matrix[a][r] > 0
        ]
        if len(wants) == 1:
            sm_num += 1
    return sm_num / (instance.agents_count)


def density(instance):
    nonzeros = [
        instance.utility_matrix[a][r]
        for r in range(instance.resources_count)
        for a in range(instance.agents_count)
        if instance.utility_matrix[a][r] > 0
    ]
    return len(nonzeros) / (instance.agents_count * instance.resources_count)

# Preference diversity
def preference_diversity(instance):
    dist = []
    for i in range(instance.agents_count):
        ui = [float(e) for e in instance.utility_matrix[i]]
        for j in range(instance.agents_count):
            uj = [float(e) for e in instance.utility_matrix[j]]
            dist.append(spatial.distance.euclidean(ui, uj))

    return sum(dist) / len(dist)

def sum_pref_demand_div_one_minus_picki(instance):
    return preference_diversity(instance) + diversity_of_demand(instance) + 1 - pickiness(instance)

