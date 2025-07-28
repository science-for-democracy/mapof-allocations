import mapel.allocations.core.logs as logs
logger = logs.get_logger(__name__)

from mapel.allocations.metrics import idealdist, rrobin, fastdist, abs_soc_dist, features_singles_dist

__distances = { 'ideal': idealdist.ideal_distance,
                'ideal-ilp': idealdist.ideal_distance_ilp,
                'round-robin': rrobin.rr_distance,
                'fast': fastdist.fast_distance,
                'fast2': fastdist.fast_distance_ell2,
                'prematching': fastdist.mixed_distance,
                "abs_2soc": abs_soc_dist.abs_2soc_distance,
                "abs_soc": abs_soc_dist.abs_soc_distance,
                "sum_abs_2soc": abs_soc_dist.sum_abs_2soc_distance,
                # "abs": features_singles_dist.abs_distance,
                # "env_fr_soc": env_soc_dist.env_free_soc_distance,
                # "env_fr_1_2soc": env_soc_dist.env_free_1_2_soc_distance,
                # "env_fr_2soc": env_soc_dist.env_free_2_soc_distance,
}


def get_distance(left_task, right_task, distance_id):
    """ Return: distance between instances, (if applicable) optimal matching """
    logger.debug(f"Getting distance: {distance_id}")
    distance_function = __distances.get(distance_id, None)
    if not distance_function:
      logger.warning(f"No distance with id: {distance_id}")
      return (0, None)
    return distance_function(left_task, right_task)


