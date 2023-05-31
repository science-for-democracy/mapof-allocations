from fractions import Fraction
import os

import mapel.allocations.core.logs as logs

logger = logs.get_logger(__name__)
from mapel.core.objects.Instance import Instance
from mapel.core.utils import make_folder_if_do_not_exist
import mapel.allocations.core.pot as pot


class AllocationTask(Instance):
    """
  Represents a single allocation task; in other words, one instance of
  an allocation problem.
  """

    @classmethod
    def from_matrix(cls, utility_matrix, instance_id):
        """
      Constructs an instance from a utility matrix, which is a list of agent
      evaluation functions over all of the resources. Each evaluation function
      is a list of integers.
    """
        return AllocationTask(utility_matrix, None, instance_id)

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
        return librarian.read(instance_id, os.path.join("experiments",
                                                        experiment_id, "instances"))

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


class AllocationTaskLibrarian:
    def read(self, instance_id, location):
        path_to_file = os.path.join(location, instance_id + ".alt")
        logger.debug(f"Reading in from file: {path_to_file}")

        if not os.path.exists(path_to_file):
            raise ValueError(f"No file: {path_to_file}")

        with open(path_to_file, "r") as ffile:
            utility_matrix = None
            line_counter = 0
            for line in ffile:
                line = line.strip()
                if line.startswith("#"):
                    continue
                line_counter += 1
                if line_counter == 1:
                    agents_cnt, res_cnt = map(int, line.split(" "))
                    utility_matrix = []
                elif line != "":
                    fractions = line.split(" ")
                    fractions = list(map(Fraction, fractions))
                    utility_matrix.append(fractions)

        return AllocationTask.from_matrix(utility_matrix, instance_id)

    def write(self, allocation, location):
        self._prepare_location(location)
        path_to_file = os.path.join(location, f'{allocation.instance_id}.alt')

        logger.debug(f"Writing allocation task to: {path_to_file}")

        with open(path_to_file, "w") as ffile:
            agents_cnt = allocation.agents_count
            res_cnt = allocation.resources_count
            ffile.write(f"{agents_cnt} {res_cnt}\n")
            ffile.write("\n")
            for row in allocation.utility_matrix:
                for entry in row[:-1]:
                    ffile.write(f"{entry} ")
                ffile.write(f"{row[-1]}\n")
            ffile.write("\n")
            for row in allocation.utility_matrix:
                ffile.write("# ")
                outstr = "\t".join(map(str, [round(float(n), 5) for n in row]))
                ffile.write(f"{outstr}\n")

    def _prepare_location(self, location):
        make_folder_if_do_not_exist(location)
