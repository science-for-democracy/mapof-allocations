import mapel.allocations.core.logs as logs
logger = logs.get_logger(__name__)
from .tools import float_matrix_to_rational

def from_spliddit_file_matrix(agents_cnt, resources_cnt, path):
  """
   Reads in a spliddit file and returns the matrix fille with Fraction class
   objects
  """
  utility_matrix = []
  logger.debug(f"Reading in splidfit file: {path}")
  with open(path, 'r') as ffile:
    linecnt = 0
    for line in ffile:
      linecnt += 1
      if linecnt == 1:
        agnt_cnt, res_cnt = (int(val) for val in line.strip().split(" "))
        continue
      if linecnt == 2:
        continue
      if (linecnt > 2) and (linecnt <= 2 + agnt_cnt):
        utility_matrix.append([int(val) for val in line.strip().split()])
      continue
  if len(utility_matrix) != agents_cnt:
    raise ValueError("The collected allocation task does not have "
    f"{agents_cnt} agents")
  for agent_utils in utility_matrix:
    if len(agent_utils) != resources_cnt:
      raise ValueError(f"At least one of the agents does not report "
      f"{resources_cnt} utility values.")
  rational_matrix = float_matrix_to_rational(utility_matrix)
  return rational_matrix
