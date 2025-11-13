import mapel.allocations.core.logs as logs
logger = logs.get_logger(__name__)
import numpy as np
import itertools

import mapel.core.matchings as matchings
import mapel.core.inner_distances as inner_distances


def fast_distance(left_task, right_task, *args, **kwargs):
    logger.debug("Computing single fast distance")
    cost_table = get_matching_cost_table(left_task, right_task, inner_distances.l1)
    #print(cost_table)
    t = matchings.solve_matching_vectors(cost_table)
    #print(float(t[0]))
    #print("---")
    return t

def fast_distance_ell2(left_task, right_task, *args, **kwargs):
    logger.debug("Computing single fast distance")
    cost_table = get_matching_cost_table(left_task, right_task, inner_distances.l2)
    #print(cost_table)
    t = matchings.solve_matching_vectors(cost_table)
    #print(float(t[0]))
    #print("---")
    return t



def get_matching_cost_table(left_task, right_task, inner_dist):
    """ Return: Cost table """

    vectors_1 = convert_to_vectors(left_task)
    #print(vectors_1)
    vectors_2 = convert_to_vectors(right_task)
    #print(vectors_2)
    size = left_task.resources_count
    return [[float(inner_dist(vectors_1[i], vectors_2[j])) for i in range(size)] for j in range(size)]


def convert_to_vectors(task):
    vectors = np.zeros([task.resources_count, task.agents_count])
    utility_matrix = np.array(task.utility_matrix)
    for i in range(task.resources_count):
        vectors[i] = sorted(utility_matrix[:, i])
    return vectors


def match_items(matrix1, matrix2):
  # Calculate the sum of each column (i.e., total support for each item) for both matrices
  total_support1 = np.sum(matrix1, axis=0)
  total_support2 = np.sum(matrix2, axis=0)

  # Get the sorted indices (in descending order of total support)
  sorted_indices1 = np.argsort(-total_support1)
  sorted_indices2 = np.argsort(-total_support2)

  # Create a list of tuples to match items based on their sorted position
  matched_items = list(zip(sorted_indices1, sorted_indices2))

  return matched_items

def calculate_agent_distance(agent1, agent2, matched_items):
  # Calculate the distance based on matched items
  distance = 0
  for item1, item2 in matched_items:
    distance += abs(agent1[item1] - agent2[item2])
  return distance


def create_cost_table(matrix1, matrix2, matched_items):
  matrix1 = np.array(matrix1)
  matrix2 = np.array(matrix2)
  num_agents1 = matrix1.shape[0]
  num_agents2 = matrix2.shape[0]
  cost_table = np.zeros((num_agents1, num_agents2))

  for i in range(num_agents1):
    for j in range(num_agents2):
      cost_table[i, j] = calculate_agent_distance(matrix1[i], matrix2[j], matched_items)

  return cost_table


def mixed_distance(left_task, right_task, *args, **kwargs):
  matching = match_items(left_task.utility_matrix, right_task.utility_matrix)
  cost_table = create_cost_table(left_task.utility_matrix, right_task.utility_matrix, matching)
  return matchings.solve_matching_vectors(cost_table)
