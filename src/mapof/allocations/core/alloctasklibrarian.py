import os
from fractions import Fraction

from mapof.core.utils import make_folder_if_do_not_exist
import mapof.allocations.core.logs as logs
logger = logs.get_logger(__name__)

class AllocationTaskLibrarian:

    @classmethod
    def read_utility_matrix(cls, path_to_file):
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
        return utility_matrix
        
    def read(self, path_to_file):
        logger.debug(f"Reading in from file: {path_to_file}")

        return AllocationTaskLibrarian.read_utility_matrix(path_to_file)

    def write(self, allocation, location, custom_suffix = None):
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
            if custom_suffix:
                ffile.write(custom_suffix)
                ffile.write("\n")

    def _prepare_location(self, location):
        make_folder_if_do_not_exist(location)
