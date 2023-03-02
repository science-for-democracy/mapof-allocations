import os
import csv
import ast
import time

import mapel.core.logs as logs
logger = logs.get_logger(__name__)
from mapel.core.objects.Experiment import Experiment
from mapel.allocations.essentials import AllocationTaskFamily
from mapel.allocations.core.alloctask import AllocationTask
from mapel.core.utils import get_instance_id, make_folder_if_do_not_exist
import mapel.allocations.metrics.surveying as surveying


class AllocationExperiment(Experiment):
    @classmethod
    def prepare_offline_experiment(cls, experiment_id, **kwargs):
      experiment = AllocationExperiment(store = True, experiment_id =
      experiment_id, **kwargs)
      if experiment.check_if_experiment_exists():
        logger.warning(f"Experiment {experiment_id} already exists. The "
        "structure is assumed to be correct")
      else:
        experiment.create_structure()
      return experiment

    def __init__(self, experiment_id, **kwargs):
        self.all_exps_location = os.path.join(os.getcwd(), "experiments")
        self.exp_location = os.path.join(self.all_exps_location, experiment_id)
        self.map_csv_path = os.path.join(self.exp_location, "map.csv")
        super().__init__(experiment_id = experiment_id, **kwargs)

    def create_structure(self) -> None:
        logger.debug(f"Experiment's {self.experiment_id} structure created in "
        f"{self.exp_location}")
        os.makedirs(self.all_exps_location, exist_ok = True)
        os.makedirs(self.exp_location, exist_ok = True)

        internal_dirs = [
          "distances",
          "features",
          "coordinates",
          "instances",
          "matrices"
        ]

        for internal_dir in internal_dirs:
          path = os.path.join(self.exp_location, internal_dir)
          os.makedirs(path, exist_ok = True)

    def check_if_experiment_exists(self):
      return os.path.isfile(self.map_csv_path)

    def import_controllers(self):
        """ Import controllers from a file """
        families = {}

        if not os.path.isfile(self.map_csv_path):
          raise ValueError(f"{self.map_csv_path} does not exist!")
        with open(self.map_csv_path, 'r') as file_:

            header = [h.strip() for h in file_.readline().split(';')]
            reader = csv.DictReader(file_, fieldnames=header, delimiter=';')

            all_num_candidates = []
            all_num_voters = []

            starting_from = 0
            for row in reader:

                culture_id = None
                color = None
                label = None
                params = None
                alpha = None
                size = None
                marker = None
                agents_count = None
                resources_count = None
                family_id = None
                show = True

                if 'culture_id' in row.keys():
                    culture_id = str(row['culture_id']).strip()

                if 'color' in row.keys():
                    color = str(row['color']).strip()

                if 'label' in row.keys():
                    label = str(row['label'])

                if 'family_id' in row.keys():
                    family_id = str(row['family_id'])

                if 'params' in row.keys():
                    params = ast.literal_eval(str(row['params']))

                if 'alpha' in row.keys():
                    alpha = float(row['alpha'])

                if 'size' in row.keys():
                    size = int(row['size'])

                if 'marker' in row.keys():
                    marker = str(row['marker']).strip()

                if val := row.get("agents_count", None):
                    agents_count = int(val)

                if val := row.get('resources_count', None):
                    resources_count = int(val)

                if 'path' in row.keys():
                    path = ast.literal_eval(str(row['path']))

                if 'show' in row.keys():
                    show = row['show'].strip() == 't'

                single = size == 1

                if not label:
                  label = family_id

                families[family_id] = AllocationTaskFamily.from_culture(culture_id=culture_id,
                                                     family_id=family_id,
                                                     params=params, label=label,
                                                     color=color, alpha=alpha, show=show,
                                                     size=size, marker=marker,
                                                     starting_from=starting_from,
                                                     agents_count =
                                                     agents_count,
                                                     resources_count =
                                                     resources_count,
                                                     single=single)
                starting_from += size

            #    all_num_candidates.append(num_candidates)
            #    all_num_voters.append(num_voters)

            #check_if_all_equal(all_num_candidates, 'num_candidates')
            #check_if_all_equal(all_num_voters, 'num_voters')

            self.num_families = len(families)
            self.num_instances = sum([families[family_id].size for family_id in families])
            self.main_order = [i for i in range(self.num_instances)]

        return families


    def prepare_instances(self, store_points=False, aggregated=True):

        self.store_points = store_points
        self.aggregated = aggregated

        if self.instances is None:
            self.instances = {}

        for family_id in self.families:
            logger.debug(f'Preparing: {family_id}')

            new_instances = self.families[family_id].prepare_family(
                store=self.store,
                experiment_id=self.experiment_id,
                store_points=store_points,
                aggregated=aggregated)

            for instance_id in new_instances:
                self.instances[instance_id] = new_instances[instance_id]



#    def prepare_matrices(self):
#        path = os.path.join(os.getcwd(), "experiments", self.experiment_id, "matrices")
#        for file_name in os.listdir(path):
#            os.remove(os.path.join(path, file_name))
#
#        for election_id in self.elections:
#            matrix = self.elections[election_id].votes_to_positionwise_matrix()
#            file_name = election_id + ".csv"
#            path = os.path.join(os.getcwd(), "experiments", self.experiment_id,
#                                "matrices", file_name)
#
#            with open(path, 'w', newline='') as csv_file:
#
#                writer = csv.writer(csv_file, delimiter=';')
#                header = [str(i) for i in range(self.elections[election_id].num_candidates)]
#                writer.writerow(header)
#                for row in matrix:
#                    writer.writerow(row)

    def add_instances_to_experiment(self):
        instances = {}

        for family_id in self.families:
          logger.debug(f"Reading in family: {family_id}")
          single = self.families[family_id].single


          ids = []
          instances_count = self.families[family_id].size
          # A hack for families of time unknown at the time of wriitn map.csv
          if instances_count == 0:
            instances_count = 999999999999
          for j in range(instances_count):
              instance_id = get_instance_id(single, family_id, j)
              logger.debug(f"Reading in instance: {instance_id}")

              # The hack continued
              try:
                instance = AllocationTask.from_file(instance_id,
                self.experiment_id)
              except ValueError:
                break

              instances[instance_id] = instance
              ids.append(str(instance_id))

          self.families[family_id].election_ids = ids

        return instances
#
#    def set_default_num_candidates(self, num_candidates: int) -> None:
#        """ Set default number of candidates """
#        self.default_num_candidates = num_candidates
#
#    def set_default_num_voters(self, num_voters: int) -> None:
#        """ Set default number of voters """
#        self.default_num_voters = num_voters
#
#    def set_default_committee_size(self, committee_size: int) -> None:
#        """ Set default size of the committee """
#        self.default_committee_size = committee_size

#    def add_election(self, culture_id="none", params=None, label=None,
#                     color="black", alpha=1., show=True, marker='x', starting_from=0, size=1,
#                     num_candidates=None, num_voters=None, election_id=None):
#        """ Add election to the experiment """
#
#        if num_candidates is None:
#            num_candidates = self.default_num_candidates
#
#        if num_voters is None:
#            num_voters = self.default_num_voters
#
#        return self.add_family(culture_id=culture_id, params=params, size=size, label=label,
#                               color=color, alpha=alpha, show=show, marker=marker,
#                               starting_from=starting_from, family_id=election_id,
#                               num_candidates=num_candidates, num_voters=num_voters,
#                               single=True)

    def add_family(self, culture_id: str = "none", params: dict = None, size: int = 1,
                   label: str = None, color: str = "black", alpha: float = 1.,
                   show: bool = True, marker: str = 'o', starting_from: int = 0,
                   num_candidates: int = None, num_voters: int = None,
                   family_id: str = None, single: bool = False,
                   path: dict = None,
                   election_id: str = None, 
                   family = None) -> list:

        if family == None:
          raise NotImplementedError

        elif label is None:
            label = family.family_id

        if self.families == None:
          self.families = {}

        self.families[family.family_id] = family
        self.num_families = len(self.families)
        self.num_elections = sum([self.families[family_id].size for family_id in self.families])
        self.main_order = [i for i in range(self.num_elections)]

        new_instances = family.allocation_tasks

        for instance in new_instances:
            self.instances[instance.instance_id] = instance

        return [alloc_task.instance_id for alloc_task in family.allocation_tasks]


    def compute_distances(self, distance_id, self_distances = True):
        matchings = {instance_id: {} for instance_id in self.instances}
        distances = {instance_id: {} for instance_id in self.instances}
        times = {instance_id: {} for instance_id in self.instances}

        ids = []
        for i, instance_1 in enumerate(self.instances):
            for j, instance_2 in enumerate(self.instances):
                if i < j or (i == j and self_distances):
                    ids.append((instance_1, instance_2))
         
        from tqdm import tqdm
        with tqdm(total=len(ids)) as pbar:
          for left_task_id, right_task_id in ids:
            st_time = time.time() 
            distance, matching = \
            surveying.get_distance(self.instances[left_task_id],
            self.instances[right_task_id], distance_id) 
            distances[left_task_id][right_task_id] = distance
            matchings[left_task_id][right_task_id] = matching
            times[left_task_id][right_task_id] = time.time() - st_time
            pbar.update(1)

        logger.debug(f"Computed distances:\n{distances}")

        self.distances = distances
        self.times = times
        self.matchings = matchings

        if self.store:
          self._store_distances_to_file(distance_id, self.distances, self.times,
          self_distances )


    def _store_distances_to_file(self, distance_id, distances, times, self_distances):
        path_to_folder = os.path.join(os.getcwd(), "experiments", self.experiment_id, "distances")
        make_folder_if_do_not_exist(path_to_folder)
        path_to_file = os.path.join(path_to_folder, f'{distance_id}.csv')

        logger.debug(f"Storing distances in: {path_to_file}")

        with open(path_to_file, 'w', newline='') as csv_file:
            writer = csv.writer(csv_file, delimiter=';')
            writer.writerow(["instance_id_1", "instance_id_2", "distance", "time"])

            for i, instance_1 in enumerate(self.instances):
                for j, instance_2 in enumerate(self.instances):
                    if i < j or (i == j and self_distances):
                        distance = str(distances[instance_1][instance_2])
                        time_ = str(times[instance_1][instance_2])
                        writer.writerow([instance_1, instance_2, distance, time_])

        logger.debug(f"Distances stored!")

    def get_election_id_from_model_name(self, culture_id: str) -> str:
        for family_id in self.families:
            if self.families[family_id].culture_id == culture_id:
                return family_id

    def add_feature(self, name, function):
        self.features[name] = function

    def compute_feature(self, feature_id: str = None, feature_params=None,
                       printing=False, **kwargs) -> dict:

        if feature_params is None:
            feature_params = {}

        feature_dict = {'value': {}}

        for instance_id in self.instances:
            if printing:
                print(instance_id)
            instance = self.instances[instance_id]

            value = self.features[feature_id](instance)

            feature_dict['value'][instance_id] = value

        # if self.store:
        #     self._store_feature(feature_id, feature_long_id, feature_dict)

        self.features[feature_id] = feature_dict
        return feature_dict

