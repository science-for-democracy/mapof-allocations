from fractions import Fraction

import mapof.allocations.core.logs as logs

logger = logs.get_logger(__name__)

import mapof.allocations.cultures.basic_cultures as basic
import mapof.allocations.cultures.euclidean as euc

import mapof.allocations.cultures.misc as misc
import mapof.allocations.cultures.converter as converter
import mapof.allocations.cultures.paths as paths
import mapof.allocations.cultures.approval_dirichlet as apprd

import mapof.allocations.features.basic_features as features
import mapof.allocations.features.or_tools_features.wrapper as or_features


registered_cultures_of_alloct_matrix = {
    "contention": basic.contention_alloct_matrix,
    "bicontention": basic.bicontention_alloct_matrix,
    "indifference": basic.indifference_alloct_matrix,
    "separability": basic.separability_alloct_matrix,
    "wideseparability": basic.wide_separability_alloct_matrix,
    "lowerdiag": basic.lowerdiag_alloct_matrix,
    "dirichlet": basic.dirichlet_matrix,
    "from_spliddit": misc.from_spliddit_file_matrix,
    "from_mapel_instance": misc.from_mapel_allocation_instance,
    'ordinal': converter.ordinal,
    'approval': converter.approval,
    # 'idun': paths.get_idun_path_utility_matrix,
    # 'idsep': paths.get_idsep_path_utility_matrix,
    # 'unsep': paths.get_unsep_path_utility_matrix,
    "dirichlet_shift": basic.dirichlet_shift_matrix,
    "blurred_separability": basic.blurred_separability_alloct_matrix,
    "attributes": euc.attributes_alloc_matrix,
    "approval_dirichlet": apprd.approval_dirichlet,
    "approval_gen_dirichlet": apprd.approval_gen_dirichlet,
    "euclidean": euc.euclidean_alloc_matrix,
    "indsep": paths.get_indsep_convex_utility_matrix,
    "consep": paths.get_consep_convex_utility_matrix,
    "indcon": paths.get_indcon_convex_utility_matrix,
    "conbcon": paths.get_conbcon_convex_utility_matrix,
    "bconsep": paths.get_bconsep_convex_utility_matrix,
    "wsepind": paths.get_wsepind_convex_utility_matrix,
    "sepwsep": paths.get_sepwsep_convex_utility_matrix,
    "bconwsep": paths.get_bconwsep_convex_utility_matrix,
    "uniform": basic.uniform_matrix,
    "expon": basic.expon_matrix,
    "block": basic.block_alloct_matrix
}


registered_features_of_alloct_matrix = {
    'pickiness': features.pickiness,
    'one_minus_pickiness': features.one_minus_pickiness,
    'diversity_of_demand': features.diversity_of_demand,
    'diversity_of_votes': features.diversity_of_votes,
    'diversity_of_votes_l2': features.diversity_of_votes_l2,
    "ex_envy_free": or_features.exists_envy_free,
    "ex_envy_free_time": or_features.exists_envy_free_time,
    "abs_envy": or_features.min_max_abs_envy,
    "abs_envy_time": or_features.min_max_abs_envy_time,
    "rel_envy": or_features.relative_envy,
    "rel_envy_time": or_features.relative_envy_time,
    "nash": or_features.nash,
    "nash_la": or_features.nash_lp,
    "nash_time": or_features.nash_time,
    "ex_envy_pareto": or_features.exists_envy_free_pareto,
    "ex_envy_pareto_time": or_features.exists_envy_free_pareto_time,
    "ex_mms": or_features.exists_mms,
    "ex_mms_time": or_features.exists_mms_time,
    "price_of_envy_free": or_features.price_of_envy_freeness,
    "price_of_envy_free_time": or_features.price_of_envy_freeness_time,
    "price_of_envy_pareto": or_features.price_of_envy_pareto,
    "price_of_envy_pareto_time": or_features.price_of_envy_pareto_time,
    "max_soc_welf_scaled": or_features.max_social_wel_scaled,
    "abs_envies_sum_scaled": or_features.min_sum_max_abs_envy_scaled,
    "abs_envies_sum": or_features.min_sum_max_abs_envy,
    "max_soc_welf": or_features.max_social_wel,
    "lsvd": features.larg_svd,
    "slsvd": features.sec_larg_svd,
    "deviation": features.level_deviation,
    "min_demand": features.min_demand,
    "max_demand": features.max_demand,
    "effm": features.eff_m,
    "sminded": features.frac_sm,
    "density": features.density,
    "all_three": features.all_three,
    "pref_div": features.preference_diversity,
    "sum_pddivomp": features.sum_pref_demand_div_one_minus_picki,
    "a_prop_share": or_features.a_prop_share,
    "prop_share": or_features.exists_prop_share
}


def get_matr_for_culture(culture_id: str,
                         agents_count: int,
                         resources_count: int,
                         params: dict = None):
    # TODO: consider the params argument; do we want to use **kwargs instead?
    if params is None:
        params = {}

    logger.debug(f'Getting: {culture_id}')
    if generator := registered_cultures_of_alloct_matrix.get(culture_id, None):
        matrix = generator(agents_count, resources_count, **params)
        fractional_matrix = []
        for row in matrix:
          fractional_matrix.append(list(map(Fraction, row)))
        return fractional_matrix

    logger.warning(f'No such culture id: {culture_id}. ID returned')
    return [[1] + [0] * (resources_count - 1) for _ in range(agents_count)]
