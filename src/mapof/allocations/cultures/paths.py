from fractions import Fraction
from mapof.allocations.cultures.basic_cultures import *
import numpy as np

# depr
def get_idun_path_utility_matrix(agents_cnt, resources_cnt, k=1):
    """
    for k=1 we get ID
    for k=resources_cnt we get UN
    """
    row = [Fraction(1, k) for _ in range(k)] + [Fraction(0) for _ in range(resources_cnt - k)]
    return [row for _ in range(agents_cnt)]


# depr
def get_idsep_path_utility_matrix(agents_cnt, resources_cnt, k=1):
    """
    for k=1 we get ID
    for k=resources_cnt we get SEP
    """
    matrix = [[Fraction(0) for _ in range(resources_cnt)] for _ in range(agents_cnt)]
    for i in range(resources_cnt):
        if i < k:
            matrix[i][0] = Fraction(1)
        else:
            matrix[i][i] = Fraction(1)
    return matrix


# depr
def get_unsep_path_utility_matrix(agents_cnt, resources_cnt, k=1):
    """
    for k=1 we get UN
    for k=resources_cnt we get SEP
    """
    matrix = [[Fraction(0) for _ in range(resources_cnt)] for _ in range(agents_cnt)]
    for i in range(resources_cnt):
        for j in range(k):
            matrix[i][(i+j) % resources_cnt] = Fraction(1, k)
    return matrix


# convex
def get_indsep_convex_utility_matrix(agents_cnt, resources_cnt, alpha=None):

    if alpha is None:
        alpha = np.random.random()

    matrix = [[Fraction(0) for _ in range(resources_cnt)] for _ in range(agents_cnt)]
    IND = indifference_alloct_matrix(agents_cnt, resources_cnt)
    SEP = separability_alloct_matrix(agents_cnt, resources_cnt)

    for i in range(agents_cnt):
        for j in range(resources_cnt):
            a = alpha * IND[i][j]
            b = (1-alpha) * SEP[i][j]
            matrix[i][j] = Fraction(a+b)

    return matrix

# convex
def get_indcon_convex_utility_matrix(agents_cnt, resources_cnt, alpha=None):

    if alpha is None:
        alpha = np.random.random()

    matrix = [[Fraction(0) for _ in range(resources_cnt)] for _ in range(agents_cnt)]
    IND = indifference_alloct_matrix(agents_cnt, resources_cnt)
    CON = contention_alloct_matrix(agents_cnt, resources_cnt)

    for i in range(agents_cnt):
        for j in range(resources_cnt):
            a = alpha * IND[i][j]
            b = (1-alpha) * CON[i][j]
            matrix[i][j] = Fraction(a+b)

    return matrix

# convex
def get_consep_convex_utility_matrix(agents_cnt, resources_cnt, alpha=None):

    if alpha is None:
        alpha = np.random.random()

    matrix = [[Fraction(0) for _ in range(resources_cnt)] for _ in range(agents_cnt)]
    CON = contention_alloct_matrix(agents_cnt, resources_cnt)
    SEP = separability_alloct_matrix(agents_cnt, resources_cnt)

    for i in range(agents_cnt):
        for j in range(resources_cnt):
            a = alpha * CON[i][j]
            b = (1-alpha) * SEP[i][j]
            matrix[i][j] = Fraction(a+b)

    return matrix

# convex
def get_conbcon_convex_utility_matrix(agents_cnt, resources_cnt, alpha=None):

    if alpha is None:
        alpha = np.random.random()

    matrix = [[Fraction(0) for _ in range(resources_cnt)] for _ in range(agents_cnt)]
    BCON = bicontention_alloct_matrix(agents_cnt, resources_cnt)
    CON = contention_alloct_matrix(agents_cnt, resources_cnt)

    for i in range(agents_cnt):
        for j in range(resources_cnt):
            a = alpha * CON[i][j]
            b = (1-alpha) * BCON[i][j]
            matrix[i][j] = Fraction(a+b)

    return matrix

# convex
def get_bconsep_convex_utility_matrix(agents_cnt, resources_cnt, alpha=None):

    if alpha is None:
        alpha = np.random.random()

    matrix = [[Fraction(0) for _ in range(resources_cnt)] for _ in range(agents_cnt)]
    BCON = bicontention_alloct_matrix(agents_cnt, resources_cnt)
    SEP = separability_alloct_matrix(agents_cnt, resources_cnt)

    for i in range(agents_cnt):
        for j in range(resources_cnt):
            a = alpha * BCON[i][j]
            b = (1-alpha) * SEP[i][j]
            matrix[i][j] = Fraction(a+b)

    return matrix

# convex
def get_sepwsep_convex_utility_matrix(agents_cnt, resources_cnt, alpha=None):

    if alpha is None:
        alpha = np.random.random()

    matrix = [[Fraction(0) for _ in range(resources_cnt)] for _ in range(agents_cnt)]

    for i in range(agents_cnt):
        first = 2*i % resources_cnt
        second = (first + 1) % resources_cnt
        matrix[i][first] = Fraction(0.5 + 0.5*alpha)
        matrix[i][second] = Fraction(0.5 - 0.5*alpha)

    return matrix

# convex
def get_wsepind_convex_utility_matrix(agents_cnt, resources_cnt, alpha=None):

    if alpha is None:
        alpha = np.random.random()

    matrix = [[Fraction(0) for _ in range(resources_cnt)] for _ in range(agents_cnt)]
    WSEP = wide_separability_alloct_matrix(agents_cnt, resources_cnt)
    IND = indifference_alloct_matrix(agents_cnt, resources_cnt)

    for i in range(agents_cnt):
        for j in range(resources_cnt):
            a = alpha * WSEP[i][j]
            b = (1-alpha) * IND[i][j]
            matrix[i][j] = Fraction(a+b)

    return matrix

# convex
def get_bconwsep_convex_utility_matrix(agents_cnt, resources_cnt, alpha=None):

    if alpha is None:
        alpha = np.random.random()

    matrix = [[Fraction(0) for _ in range(resources_cnt)] for _ in range(agents_cnt)]
    BCON = bicontention_alloct_matrix(agents_cnt, resources_cnt)
    WSEP = wide_separability_alloct_matrix(agents_cnt, resources_cnt)

    for i in range(agents_cnt):
        for j in range(resources_cnt):
            a = alpha * BCON[i][j]
            b = (1-alpha) * WSEP[i][j]
            matrix[i][j] = Fraction(a+b)

    return matrix
