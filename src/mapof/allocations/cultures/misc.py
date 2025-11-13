import mapof.allocations.core.logs as logs

logger = logs.get_logger(__name__)
from .tools import float_matrix_to_rational
import mapof.allocations.core.alloctasklibrarian as librarian


def check_agents_and_resources_counts(utility_matrix, agents_cnt, resources_cnt):
    if len(utility_matrix) != agents_cnt:
        raise ValueError("The collected allocation task does not have "
                         f"{agents_cnt} agents")
    for agent_utils in utility_matrix:
        if len(agent_utils) != resources_cnt:
            logger.warning(f"Some agent does not report {resources_cnt} utility values.")
            raise ValueError(f"At least one of the agents does not report "
                             f"{resources_cnt} utility values.")


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
    check_agents_and_resources_counts(utility_matrix, agents_cnt, resources_cnt)
    rational_matrix = float_matrix_to_rational(utility_matrix)
    return rational_matrix


def from_mapel_allocation_instance(agents_cnt, resources_cnt, path, ensure_sizes=True):
    """
    Reads in a mapel allocation instance. 
    """
    logger.debug(f"Reading in mapel task allocation file: {path}")
    rational_utility_matrix = librarian.AllocationTaskLibrarian.read_utility_matrix(path)
    if ensure_sizes:
        check_agents_and_resources_counts(rational_utility_matrix, agents_cnt,
                                          resources_cnt)
    return rational_utility_matrix
