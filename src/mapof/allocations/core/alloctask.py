from fractions import Fraction
import os
import mapof.allocations.core.logs as logs
logger = logs.get_logger(__name__)
from mapof.core.objects.Instance import Instance
from mapof.allocations.core.alloctasklibrarian import AllocationTaskLibrarian
import mapof.allocations.core.pot as pot


class AllocationTask(Instance):
    """
  Represents a single allocation task; in other words, one instance of
  an allocation problem.
  """

    @classmethod
    def from_matrix(cls, utility_matrix, instance_id, culture_id = None, **kwargs):
        """
      Constructs an instance from a utility matrix, which is a list of agent
      evaluation functions over all of the resources. Each evaluation function
      is a list of integers.
    """
        return AllocationTask(utility_matrix, None, instance_id, culture_id,
                              *kwargs)

    @classmethod
    def from_splidditfile(cls, instance_id, agents_count, resources_count,
                          culture_id, fpath, **kwargs):
        utility_matrix = pot.get_matr_for_culture("from_spliddit", agents_count,
                                                  resources_count, {"path": fpath})
        return AllocationTask(utility_matrix, None, instance_id, culture_id,
                              **kwargs)

    @classmethod
    def from_culture(cls, instance_id, agents_count, resources_count, culture_id,
                     params={}, **kwargs):
        utility_matrix = pot.get_matr_for_culture(culture_id, agents_count,
                                                  resources_count, params)
        return AllocationTask(utility_matrix, None, instance_id, culture_id,
                              **kwargs)

    @classmethod
    def from_file(cls, instance_id, experiment_id, **kwargs):
        librarian = AllocationTaskLibrarian()
        path_to_file = os.path.join("experiments", experiment_id, "instances", instance_id + ".alt")
        utility_matrix = librarian.read(path_to_file)
        task = AllocationTask.from_matrix(utility_matrix, instance_id, None, **kwargs)
        # A hack to have the path always
        task.path = path_to_file
        return task

    def __init__(self, utility_matrix, experiment_id, instance_id,
                 culture_id=None, alpha=None, **kwargs):
        super().__init__(experiment_id, instance_id, culture_id=culture_id,
                         alpha=alpha)
        self._validate(utility_matrix)

        self.utility_matrix = utility_matrix
        self.agents_count = len(utility_matrix)
        self.resources_count = len(utility_matrix[0])
        self.votes = None

    def __getitem__(self, idx):
        return self.utility_matrix[idx]

    def _validate(self, utility_matrix):
        if type(utility_matrix) is not list:
            raise ValueError("Allocation task can only be constructed using list of "
                             "lists")
        if len(utility_matrix) == 0:
            raise ValueError("An empty allocation task is '[[]]' not '[]'")
        row_size = 0
        for row in utility_matrix:
            if row_size == 0:
                row_size = len(row)
            if type(row) is not list:
                raise ValueError("Allocation task can only be constructed using list of "
                                 "lists")
            if row_size != len(row):
                raise ValueError("Each row in an allocation task matrix must have the "
                                 "same number of entries")
            for val in row:
                if type(val) not in (float, int, Fraction):
                    raise ValueError("Each row in an allocation task matrix must be an "
                                     "int or float")


