import mapel.allocations.core.logs as logs

logger = logs.get_logger(__name__)
import itertools
import numpy as np

RR_DEMO = False


def rr_distance_demo(left_task, right_task, *args, **kwargs):
    # logger.debug("Computing single rr distance")
    _validate(left_task, right_task)

    trials = 20
    n = left_task.agents_count

    min_dist = n * n
    min_perm = None

    ag_dict = {
        0: "a",
        1: "b",
        2: "c",
        3: "d",
        4: "e"
    }

    res_dict = {
        0: "P",
        1: "Q",
        2: "R",
        3: "S",
        4: "T"
    }

    def bprint(matrix,
               agents_dict=None,
               resources_dict=None):

        res_names = range(len(matrix[0]))
        if resources_dict:
            res_names = map(lambda x: resources_dict[x], res_names)
        header = "\t".join(map(str, res_names))
        print(f"\t {header}")
        for i in range(len(matrix)):
            rounded_vals = list(map(lambda x: round(float(x), 3), matrix[i]))
            one_line = ""
            for val in rounded_vals:
                one_line += f"{val}\t"
            ag_name = i
            if agents_dict:
                ag_name = str(agents_dict[ag_name])
            print(f"{ag_name}: \t {one_line}")

    print("\n")
    print("LEFT")
    bprint(left_task.utility_matrix)
    print("\n")
    print("RIGHT")
    bprint(right_task.utility_matrix, resources_dict=res_dict, agents_dict=ag_dict)
    print("\n")

    def print_agents_mapping(mapping):
        map_str = ", ".join(
            [f"{i} --> {ag_dict[j]}" for i, j in enumerate(mapping)]
        )
        print(map_str)

    def order_to_str(order, agents_mapping=None):
        order = " ".join(
            map(lambda x: ag_dict[agents_mapping[x]] if agents_mapping else str(x), order))
        return order

    # logger.debug("Permutations loop")
    counter = 0
    for agents_mapping in itertools.permutations(range(n)):
        counter += 1
        if counter < 21:
            continue
        # logger.debug(f"Agents mapping: {agents_mapping}:")
        # print("AGENTS MAPPING")
        # print_agents_mapping(agents_mapping)
        # input()
        distance = 0
        for t in range(trials):
            order = np.random.permutation(left_task.agents_count)
            #  print(f"Left order: {order_to_str(order)}")
            #  print(f"Right order: {order_to_str(order, agents_mapping)}")
            #  input()
            left_allocation = _allocate_round_robin(left_task, order)
            left_matrix = _compute_allocation_matrix(left_task, left_allocation)
            #  bprint(left_matrix)
            right_allocation = _allocate_round_robin(right_task, order, agents_mapping)
            right_matrix = _compute_allocation_matrix(right_task, right_allocation)
            #  bprint(right_matrix, ag_dict, ag_dict)
            #  input()
            for i in range(n):
                for j in range(n):
                    left = left_matrix[i][j]
                    right = right_matrix[agents_mapping[i]][agents_mapping[j]]
                    #      print(f"LEFT: (ag, ag) -> ({i}, {j}): {left}")
                    #      print(f"RIGHT: (ag, ag) -> ({ag_dict[agents_mapping[i]]}, {ag_dict[agents_mapping[j]]}): {right}")
                    distance += (left - right) ** 2
        #   logger.debug(f"Trial: {t}, left_matrix: {left_matrix}\n right_matrix: {right_matrix}\n dist: {distance}")
        # logger.debug(f"Distance: {min_dist}")
        distance = distance / trials
        if distance < min_dist:
            min_dist = distance
            min_perm = agents_mapping

    print(min_dist)
    return (min_dist, min_perm)


def rr_distance(left_task, right_task, *args, **kwargs):
    if RR_DEMO:
        return rr_distance_demo(left_task, right_task, *args, **kwargs)
    # logger.debug("Computing single rr distance")
    _validate(left_task, right_task)

    trials = 30
    n = left_task.agents_count

    min_dist = n * n
    min_perm = None

    # logger.debug("Permutations loop")
    for agents_mapping in itertools.permutations(range(n)):
        # logger.debug(f"Agents mapping: {agents_mapping}:")
        distance = 0
        for t in range(trials):
            order = np.random.permutation(left_task.agents_count)
            left_allocation = _allocate_round_robin(left_task, order)
            left_matrix = _compute_allocation_matrix(left_task, left_allocation)
            right_allocation = _allocate_round_robin(right_task, order, agents_mapping)
            right_matrix = _compute_allocation_matrix(right_task, right_allocation)
            for i in range(n):
                for j in range(n):
                    left_entry = left_matrix[i][j]
                    right_entry = right_matrix[agents_mapping[i]][agents_mapping[j]]
                    distance += (left_entry - right_entry) ** 2
        #   logger.debug(f"Trial: {t}, left_matrix: {left_matrix}\n right_matrix: {right_matrix}\n dist: {distance}")
        # logger.debug(f"Distance: {min_dist}")
        distance = distance / trials
        if distance < min_dist:
            min_dist = distance
            min_perm = agents_mapping

    return (min_dist, min_perm)


def _get_resource_mapping_costs(left_task, right_task, agents_mapping):
    """ Return: Cost table """
    cost_table = np.zeros([left_task.resources_count, left_task.resources_count])
    for left_res in range(left_task.resources_count):
        for right_res in range(right_task.resources_count):
            ell_one_dist = 0
            for left_agent in range(left_task.agents_count):
                right_agent = agents_mapping[left_agent]
                ell_one_diff = abs(left_task[left_agent][left_res] - \
                                   right_task[right_agent][right_res])
                ell_one_dist += ell_one_diff
            cost_table[left_res][right_res] = ell_one_dist
    return cost_table


def _allocate_round_robin(task, order, agents_mapping=None):
    m = task.resources_count
    n = task.agents_count
    allocation = [[] for _ in range(m)]
    allocated_res = set()
    for i in range(m):
        curr_agent = order[i % n]
        if agents_mapping:
            curr_agent = agents_mapping[curr_agent]
        agent_choice, choice_value = max(
            [res for res in enumerate(task[curr_agent]) if res[0] not in allocated_res],
            key=lambda res: res[1])
        allocated_res.add(agent_choice)
        allocation[curr_agent].append(agent_choice)
    return allocation


def _compute_allocation_matrix(task, allocation):
    n = task.agents_count
    valuation_matrix = np.zeros([n, n])
    for agent_1 in range(n):
        allocation_of_1 = allocation[agent_1]
        for agent_2 in range(n):
            value_by_2 = sum([task[agent_2][res] for res in allocation_of_1])
            valuation_matrix[agent_2][agent_1] = value_by_2
    return valuation_matrix


def _validate(left_task, right_task):
    if left_task.agents_count != right_task.agents_count:
        raise ValueError("Cannot compute round-robin distance between two tasks with different "
                         "counts of agents")
    if left_task.resources_count != right_task.resources_count:
        raise ValueError("Cannot compute round-robin distance between two tasks with different "
                         "counts of resources")
