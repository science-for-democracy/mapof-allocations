from fractions import Fraction
# As we discussed on Nov 10, it seems like we should handle values as exact fractions.
# The reason is that rounding or floating point errors might otherwise introduce envy
# where no envy originally exists.

from scipy.stats import dirichlet

import mapel.core.logs as logs
logger = logs.get_logger(__name__)
from mapel.allocations.core.alloctask import AllocationTask

def identity_alloct_matrix(agents_cnt, resources_cnt):
	# 1 0 0 … 0
	# 1 0 0 … 0
	# …
	# 1 0 0 … 0
	logger.debug("Creating the ID allocation task matrix")
	row = [Fraction(1)] + [Fraction(0) for _ in range(resources_cnt - 1)]
	return [row for _ in range(agents_cnt)]


def uniformity_alloct_matrix(agents_cnt, resources_cnt):
	# 1/m 1/m … 1/m
	# 1/m 1/m … 1/m
	# …
	# 1/m 1/m … 1/m
	logger.debug("Creating the UN allocation task matrix")
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


def dirichlet_matrix(agents_cnt, resources_cnt, alphas = None):
	"""For each agent independently, draw their values from a scaled Dirichlet distribution. The Dirichlet distribution
	is parameterized by values αⱼ>0 for each resource j, which can bias the randomness towards high values for some
	resources. If the argument `alphas` is not specified, the alphas are all set to 1, which corresponds to values being
	drawn uniformly from the (scaled) standard simplex.
	"""
	if alphas is None:
		alphas = [1. for _ in range(resources_cnt)]
	assert len(alphas) == resources_cnt

	float_matrix = (dirichlet.rvs(alphas, size=agents_cnt)).tolist()
	rational_matrix = []
	for float_row in float_matrix:
			rational_row = [Fraction(value) for value in float_row]
			row_sum = sum(rational_row)
			rational_row = [value / row_sum for value in rational_row]
			rational_matrix.append(rational_row)
	return rational_matrix

