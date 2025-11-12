from fractions import Fraction


def float_matrix_to_rational(float_matrix):
    rational_matrix = []
    for float_row in float_matrix:
        rational_row = [Fraction(value) for value in float_row]
        row_sum = sum(rational_row)
        rational_row = [value / row_sum for value in rational_row]
        rational_matrix.append(rational_row)
    return rational_matrix
