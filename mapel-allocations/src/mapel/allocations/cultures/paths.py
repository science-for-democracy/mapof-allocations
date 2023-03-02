from fractions import Fraction


def get_idun_path_utility_matrix(agents_cnt, resources_cnt, k=1):
    """
    for k=1 we get ID
    for k=resources_cnt we get UN
    """
    row = [Fraction(1, k) for _ in range(k)] + [Fraction(0) for _ in range(resources_cnt - k)]
    return [row for _ in range(agents_cnt)]


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
