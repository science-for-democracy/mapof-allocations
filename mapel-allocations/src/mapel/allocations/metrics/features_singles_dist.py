import mapel.allocations.features.or_tools_features.wrapper as or_features_wrap


def abs_distance(left_task, right_task, *args, **kwargs):
    labs_envy = or_features_wrap.min_max_abs_envy(left_task)
    rabs_envy = or_features_wrap.min_max_abs_envy(right_task)
    diff_abs = abs(labs_envy - rabs_envy)
    return diff_abs, None


def soc_scaled_distance(left_task, right_task, *args, **kwargs):
    l_max_social_welfare_s = or_features_wrap.max_social_wel_scaled(left_task)
    r_max_social_welfare_s = or_features_wrap.max_social_wel_scaled(right_task)

    return abs(l_max_social_welfare_s - r_max_social_welfare_s), None
