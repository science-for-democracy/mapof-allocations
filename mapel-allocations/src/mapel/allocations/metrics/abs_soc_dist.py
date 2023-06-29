import mapel.allocations.features.or_tools_features.wrapper as or_features_wrap
import mapel.allocations.metrics.features_singles_dist as sd


def abs_2soc_distance(left_task, right_task, *args, **kwargs):
    dif_soc, _ = sd.soc_scaled_distance(left_task, right_task)
    diff_abs, _ = sd.abs_distance(left_task, right_task)

    return diff_abs + 2 * dif_soc, None


def abs_soc_distance(left_task, right_task, *args, **kwargs):
    dif_soc, _ = sd.soc_scaled_distance(left_task, right_task)
    diff_abs, _ = sd.abs_distance(left_task, right_task)

    return diff_abs + dif_soc, None


def max_abs_2soc_distance(left_task, right_task, *args, **kwargs):
    dif_soc, _ = sd.soc_scaled_distance(left_task, right_task)
    diff_abs, _ = sd.abs_distance(left_task, right_task)

    return max(diff_abs, 2 * dif_soc), None


def sum_abs_2soc_distance(left_task, right_task, *args, **kwargs):
    dif_soc, _ = sd.soc_scaled_distance(left_task, right_task)

    labs_envy_sum = or_features_wrap.min_sum_max_abs_envy(left_task)
    labs_envy_sum = labs_envy_sum / left_task.agents_count
    rabs_envy_sum = or_features_wrap.min_sum_max_abs_envy(right_task)
    rabs_envy_sum = rabs_envy_sum / right_task.agents_count
    diff_abs = abs(labs_envy_sum - rabs_envy_sum)

    return diff_abs + 2 * dif_soc, None
