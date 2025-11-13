from fractions import Fraction
# As we discussed on Nov 10, it seems like we should handle values as exact fractions.
# The reason is that rounding or floating point errors might otherwise introduce envy
# where no envy originally exists.

from numpy.random import default_rng

import mapof.allocations.core.logs as logs

logger = logs.get_logger(__name__)
from .tools import float_matrix_to_rational

from sklearn.preprocessing import normalize

def contention_alloct_matrix(agents_cnt, resources_cnt):
    # 1 0 0 … 0
    # 1 0 0 … 0
    # …
    # 1 0 0 … 0
    logger.debug("Creating the CON allocation task matrix")
    row = [Fraction(1)] + [Fraction(0) for _ in range(resources_cnt - 1)]
    return [row for _ in range(agents_cnt)]


def indifference_alloct_matrix(agents_cnt, resources_cnt):
    # 1/m 1/m … 1/m
    # 1/m 1/m … 1/m # …
    # 1/m 1/m … 1/m
    logger.debug("Creating the IND allocation task matrix")
    row = [Fraction(1, resources_cnt) for _ in range(resources_cnt)]
    return [row for _ in range(agents_cnt)]


def separability_alloct_matrix(agents_cnt, resources_cnt):
    # 1 0 0 … 0
    # 0 1 0 … 0
    # 0 0 1 … 0
    # …
    logger.debug("Creating the SEP allocation task matrix")
    alloct_matrix = []
    for a in range(agents_cnt):
        row = [Fraction(0) for _ in range(resources_cnt)]
        preceeding_zeros = a % resources_cnt
        row[a % resources_cnt] = Fraction(1)
        alloct_matrix.append(row)
    return alloct_matrix


def wide_separability_alloct_matrix(agents_cnt, resources_cnt):
    # 1/2 1/2 0 … 0
    # 0     0 1/2 1/2 0  … 0
    # …
    logger.debug("Creating the wide separability allocation task matrix")
    if resources_cnt < 2*agents_cnt:
      logger.warning("Wide separability applied for an instance in which"
                     " the number of resources is smaller than the number of"
                     " agents divided by two.")
    alloct_matrix = []
    for a in range(agents_cnt):
      row = [Fraction(0) for _ in range(resources_cnt)]
      row[(2*a) % resources_cnt] = Fraction(1, 2)
      row[(2*a + 1) % resources_cnt] = Fraction(1, 2)
      alloct_matrix.append(row) 
    return alloct_matrix

def bicontention_alloct_matrix(agents_cnt, resources_cnt):
    # 1 0 0 … 0
    # . . . . .
    # 1 0 0 … 0
    # 0 1 0 … 0
    # . . . . .
    # 0 1 0 … 0
    # 0 0 1 … 0 (if the number of agents is odd)
    logger.debug("Creating the bicontention allocation task matrix")
    alloct_matrix = []
    half_agents = int(agents_cnt/2)
    for a in range(agents_cnt):
      row = [Fraction(0) for _ in range(resources_cnt)]
      if a < half_agents:
        row[0] = Fraction(1)
      elif a >= half_agents and a < 2*half_agents:
        row[1] = Fraction(1)
      else:
        row[2] = Fraction(1)
      alloct_matrix.append(row) 
    return alloct_matrix

def lowerdiag_alloct_matrix(agents_cnt, resources_cnt):
    # 1 0 0 … 0
    # 1/2 1/2 0 0 0
    # 1/3 1/3 1/3 0 
    logger.debug("Creating the lower diagonal allocation task matrix")
    alloct_matrix = []
    for a in range(agents_cnt):
      row = [Fraction(0) for _ in range(resources_cnt)]
      for i in range(a+1):
          row[i] = Fraction(1, a+1)
      alloct_matrix.append(row) 
    return alloct_matrix


def blurred_separability_alloct_matrix(agents_cnt, resources_cnt, ratio=0):
    # 1-r  r   0 … 0
    # 0    1-r r … 0
    # 0    0   1-r r… 0
    # …
    logger.debug(f"Generating blurred separability with: {ratio}")
    if ratio > 0.5 or ratio < 0.0:
        raise ValueError(f"Blur ratio should be between 0.0 and 0.5 (inclusive).")

    separability = separability_alloct_matrix(agents_cnt, resources_cnt)
    new_matrix = []
    new_diagonal_value = Fraction(1 - ratio)
    past_diagonal_value = Fraction(ratio)

    for i in range(len(separability)):
        row_len = len(separability[i])
        new_row = [Fraction(0)] * row_len
        past_diagonal_index = (i + 1) % row_len
        new_row[i] = new_diagonal_value
        new_row[past_diagonal_index] = past_diagonal_value
        new_matrix.append(new_row)
    return new_matrix

def block_alloct_matrix(agents_cnt, resources_cnt, per_row_zeros_cnt):
    logger.debug(f"Generating block matrix with zeros per row: {per_row_zeros_cnt}")
    block_size = int(resources_cnt/agents_cnt * per_row_zeros_cnt)
    #if block_size > resources_cnt/2:
    #    raise ValueError(f"Block size must be at most half the number of resources")
    #if per_row_zeros_cnt > agents_cnt/2:
    #    raise ValueError(f"Zeros per row be more than half the number of agents")

    entry_value = Fraction(1, int(resources_cnt - block_size))

    alloct_matrix = []

    for i in range(agents_cnt):
        row = [entry_value] * resources_cnt
        alloct_matrix.append(row)
    for i in range(resources_cnt):
        for j in range(per_row_zeros_cnt):
            alloct_matrix[(i+j)%agents_cnt][i] = 0
    
    return alloct_matrix


def dirichlet_matrix(agents_cnt, resources_cnt, alphas=None):
    """For each agent independently, draw their values from a
  scaled Dirichlet distribution. The Dirichlet distribution
  is parameterized by values αⱼ>0 for each resource j,
  which can bias the randomness towards high values for some
  resources. If the argument `alphas` is not specified,
  the alphas are all set to 1, which corresponds to values being
  drawn uniformly from the (scaled) standard simplex.
  """

    logger.debug(f"Generating Dirichlet matrix with: {alphas}")
    if alphas is None:
        alphas = [1. for _ in range(resources_cnt)]
    assert len(alphas) == resources_cnt

    float_matrix = default_rng().dirichlet(alphas, size=agents_cnt)
    rational_matrix = float_matrix_to_rational(float_matrix)
    return rational_matrix


def dirichlet_shift_matrix(agents_cnt, resources_cnt, shift_val, alphas=None):
    """Generates the matrix using the dirichlet_matrix() function
  and then circular-shifts each row by the given shift_val. The purpose is to gain
  a possibility of simulating different alphas vector for some agents. However,
  this function does the shift in a very structured manner. """

    logger.debug(f"Generating Dirichlet-shifted matrix with: {alphas} and shift: {shift_val}")
    non_shifted_matrix = dirichlet_matrix(agents_cnt, resources_cnt, alphas)
    new_matrix = []

    for i in range(len(non_shifted_matrix)):
        row_len = len(non_shifted_matrix[i])
        shift_by = i * shift_val
        new_row = [Fraction(0)] * row_len
        for j in range(row_len):
          new_row_index = (j + shift_by) % row_len
          new_row[new_row_index] = non_shifted_matrix[i][j]
        new_matrix.append(new_row)

    return new_matrix

def uniform_matrix(agents_cnt, resources_cnt):
    new_matrix = default_rng().uniform(size=(agents_cnt, resources_cnt))
    normed = normalize(new_matrix, axis=1, norm="l1")
    return float_matrix_to_rational(normed)

def expon_matrix(agents_cnt, resources_cnt, rate):
    new_matrix = default_rng().exponential(scale = 1/rate, size=(agents_cnt,
                                                                 resources_cnt))
    normed = normalize(new_matrix, axis=1, norm="l1")
    return float_matrix_to_rational(normed)
