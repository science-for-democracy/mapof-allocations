import mapel.core.logs as logs
logger = logs.get_logger(__name__)

import mapel.allocations.cultures.basic_cultures as basic
import mapel.allocations.cultures.misc as misc

registered_cultures_of_alloct_matrix = {
  "identity": basic.identity_alloct_matrix,
  "uniformity": basic.uniformity_alloct_matrix,
  "separability": basic.separability_alloct_matrix,
  "dirichlet": basic.dirichlet_matrix,
  "from_spliddit": misc.from_spliddit_file_matrix,
}

def get_matr_for_culture(culture_id: str,
                agents_count: int,
                resources_count: int,
                params: dict = {}):
    # TODO: consider the params argument; do we want to use **kwargs instead?
    logger.debug(f'Getting: {culture_id}')
    if generator := registered_cultures_of_alloct_matrix.get(culture_id, None):
      return generator(agents_count, resources_count, **params)

    logger.warning(f'No such culture id: {culture_id}. ID returned')
    return [[1] + [0]*(resources_count - 1) for _ in range(agents_count)]
