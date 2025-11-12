import itertools
import os
import csv
import ast
import time

from matplotlib import pyplot as plt
from scipy.stats import stats
from tqdm import tqdm
import numpy as np
from matplotlib.patches import Polygon, Wedge

import mapel.allocations.core.logs as logs

logger = logs.get_logger(__name__)
from mapel.core.objects.Experiment import Experiment
from mapel.allocations.essentials import AllocationTaskFamily
from mapel.allocations.core.alloctask import AllocationTask
from mapel.core.utils import get_instance_id, make_folder_if_do_not_exist
from mapel.core.persistence.experiment_exports import export_feature_to_file
import mapel.allocations.metrics.surveying as surveying
from mapel.allocations.core.pot import registered_features_of_alloct_matrix
from mapel.core.printing import _add_textual, basic_coloring, basic_coloring_with_shading, _basic_background, _saveas_tex

class AllocationExperiment(Experiment):
    @classmethod
    def prepare_offline_experiment(cls, experiment_id, **kwargs):
        experiment = AllocationExperiment(is_exported=True, experiment_id=
        experiment_id, **kwargs)
        if experiment.check_if_experiment_exists():
            logger.warning(f"Experiment {experiment_id} already exists. The "
                           "structure is assumed to be correct")
        else:
            experiment.create_structure()
        return experiment

    def __init__(self, experiment_id, **kwargs):
        if experiment_id:
            self.all_exps_location = os.path.join(os.getcwd(), "experiments")
            self.exp_location = os.path.join(self.all_exps_location, experiment_id)
            self.map_csv_path = os.path.join(self.exp_location, "map.csv")
        super().__init__(experiment_id=experiment_id,
                         **kwargs)
        self.instance_type = "allocation"

    def create_structure(self) -> None:
        logger.debug(f"Experiment's {self.experiment_id} structure created in "
                     f"{self.exp_location}")
        os.makedirs(self.all_exps_location, exist_ok=True)
        os.makedirs(self.exp_location, exist_ok=True)

        internal_dirs = [
            "distances",
            "features",
            "coordinates",
            "instances",
            "matrices"
        ]

        for internal_dir in internal_dirs:
            path = os.path.join(self.exp_location, internal_dir)
            os.makedirs(path, exist_ok=True)

    def check_if_experiment_exists(self):
        return os.path.isfile(self.map_csv_path)

    def import_controllers(self):
        """ Import controllers from a file """
        families = {}

        if not os.path.isfile(self.map_csv_path):
            raise ValueError(f"{self.map_csv_path} does not exist!")
        with open(self.map_csv_path, 'r') as file_:

            header = [h.strip() for h in file_.readline().split(';')]
            reader = csv.DictReader(filter(lambda row: row[0] != "#", file_), fieldnames=header,
                                    delimiter=';')

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
                    if marker == "none":
                        continue

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
                                                                        color=color, alpha=alpha,
                                                                        show=show,
                                                                        size=size, marker=marker,
                                                                        starting_from=starting_from,
                                                                        agents_count=
                                                                        agents_count,
                                                                        resources_count=
                                                                        resources_count,
                                                                        single=single)
                starting_from += size

            #    all_num_candidates.append(num_candidates)
            #    all_num_voters.append(num_voters)

            # check_if_all_equal(all_num_candidates, 'num_candidates')
            # check_if_all_equal(all_num_voters, 'num_voters')

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
                is_exported=self.is_exported,
                experiment_id=self.experiment_id,
                store_points=store_points,
                aggregated=aggregated)

            for instance_id in new_instances:
                self.instances[instance_id] = new_instances[instance_id]

    def add_instances_to_experiment(self):
        instances = {}

        for family_id in self.families:
            logger.debug(f"Reading in family: {family_id}")
            single = self.families[family_id].single

            ids = []
            instances_count = self.families[family_id].size

            for j in range(instances_count):
                instance_id = get_instance_id(single, family_id, j)
                logger.debug(f"Reading in instance: {instance_id}")

                # The hack continued
                try:
                    instance = AllocationTask.from_file(instance_id,
                                                        self.experiment_id)
                except ValueError:
                  logger.debug(f"Error reading in {instance_id}. Stopped processing family {family_id}.")
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
                   family=None) -> list:

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

    def compute_distances(self, distance_id, self_distances=True):
        matchings = {instance_id: {} for instance_id in self.instances}
        distances = {instance_id: {} for instance_id in self.instances}
        times = {instance_id: {} for instance_id in self.instances}

        ids = []
        for i, instance_1 in enumerate(self.instances):
            for j, instance_2 in enumerate(self.instances):
                if i < j or (i == j and self_distances):
                    ids.append((instance_1, instance_2))

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

        if self.is_exported:
            self._store_distances_to_file(distance_id, self.distances, self.times,
                                          self_distances)

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
        registered_features_of_alloct_matrix[name] = function

    def compute_feature(self, feature_id: str = None, feature_params=None, **kwargs) -> dict:

        if feature_params is None:
            feature_params = {}

        feature_dict = {'value': {}}

        for instance_id in tqdm(self.instances):
            instance = self.instances[instance_id]

            value = registered_features_of_alloct_matrix[feature_id](instance)

            feature_dict['value'][instance_id] = value

        if self.is_exported:
            feature_long_id = feature_id
            export_feature_to_file(self, feature_id, feature_dict, f"{feature_id}")

        self.features[feature_id] = feature_dict
        return feature_dict

    def print_correlation_between_features(self,
                                           feature_id_1=None,
                                           feature_id_2=None,
                                           title=None, all=False, my_list=None,
                                           s=12, alpha=0.25, color='purple',
                                           title_size=24, label_size=20, ticks_size=10,
                                           saveas=None,
                                           show=False):

        all_features = {}

        all_features[feature_id_1] = self.import_feature(feature_id=feature_id_1)
        all_features[feature_id_2] = self.import_feature(feature_id=feature_id_2)

        names = list(all_features.keys())

        nice = {
            'spearman': 'Spearman',
            'l1-mutual_attraction': '$\ell_1$ Mutual Attraction',
            'hamming': "Hamming",
            "jaccard": "Jaccard",
            'discrete': 'Discrete',
            'swap': 'Swap',
            'emd-bordawise': "EMD-Bordawise",
            'emd-positionwise': 'EMD-Positionwise',
            'l1-positionwise': "$\ell_1$-Positionwise",
            'l1-pairwise': "$\ell_1$-Pairwise",
        }

        def normalize(name):
            return {
                'spearman': 1.,
                'l1-mutual_attraction': 1.,
                'emd-positionwise': 1.,
            }.get(name)

        for name_1, name_2 in itertools.combinations(names, 2):

            values_x = []
            values_y = []
            for e1 in all_features[name_1]:
                values_x.append(all_features[name_1][e1])
                values_y.append(all_features[name_2][e1])

            fig = plt.figure(figsize=[6.4, 4.8])
            plt.gcf().subplots_adjust(left=0.2)
            plt.gcf().subplots_adjust(bottom=0.2)
            ax = fig.add_subplot()
            ax.scatter(values_x, values_y, s=s, alpha=alpha, color=color)

            PCC = round(stats.pearsonr(values_x, values_y)[0], 3)
            print('PCC', PCC)

            plt.xlim(left=0)
            plt.ylim(bottom=0)

            plt.xticks(fontsize=ticks_size)
            plt.yticks(fontsize=ticks_size)

            plt.xlabel(nice.get(name_1, name_1), size=label_size)
            plt.ylabel(nice.get(name_2, name_2), size=label_size)

            if title:
                plt.title(title, size=title_size)

            plt.axis('equal')

            path = f'images/correlation'
            is_exist = os.path.exists(path)

            if not is_exist:
                os.makedirs(path)

            if saveas is None:
                saveas = f'corr_{name_1}_{name_2}'
            plt.savefig(f'images/correlation/{saveas}', pad_inches=1)
            if show:
                plt.show()

def print_map_2d_features(experiment: Experiment,
    feat_name1: str,
    feat_name2: str,
    xlabel=None,
    shading=False,
    legend_pos=None,
    title_pos=None,
    textual=None,
    title=None,
    bbox_inches='tight',
    saveas=None,
    show=True,
    ms=20,
    tex=False,
    legend=True,
    dpi=250,
    title_size=16,
    textual_size=16,
    figsize=(6.4, 6.4),
    pad_inches=None) -> None:

    def shade_region(na, mi, ax):
        margin = 0.15
        inner_color = "white"
        outer_color = "whitesmoke"

        # Create circle and polygon patches
        circle = Wedge((0, 0), np.sqrt(na), 360, 90, color=inner_color, zorder=-2)
        polygon1 = Polygon(
            np.array(
                [[0, 0], [2 * np.sqrt(na / 2), 0], [np.sqrt(na / 2), np.sqrt(na / 2)]]
            ),
            closed=True,
            color=outer_color,
            zorder=-1,
        )

        polygon2 = Polygon(
            np.array(
                [
                    [0, 0],
                    [0, np.sqrt(na / mi)],
                    [np.sqrt(na), np.sqrt(na / mi)],
                    [np.sqrt(na), 0],
                ]
            ),
            closed=True,
            color=outer_color,
            zorder=-1,
        )
        
        polygon3 = Polygon(
            np.array(
                [
                    [-2 * margin, 0],
                    [-2 * margin, np.sqrt(na)],
                    [0, np.sqrt(na)],
                    [0, 0],
                ]
            ),
            closed=True,
            color=outer_color,
            zorder=-1,
        )
        ax.set_facecolor(outer_color)

        # Add patches to plot
        ax.add_patch(circle)
        ax.add_patch(polygon1)
        ax.add_patch(polygon2)
        ax.add_patch(polygon3)

        # Set limits and labels
        plt.xlim(-margin, np.sqrt(na / 2) + margin)
        plt.ylim(np.sqrt(na / mi) - margin, np.sqrt(na) + margin)
        plt.xlabel("σ₂")  # , fontsize=25)
        plt.ylabel("σ₁")  # , fontsize=25)

    experiment.compute_feature(feat_name1)
    experiment.compute_feature(feat_name2)
    all_feat1 = experiment.import_feature(feature_id=feat_name1)
    all_feat2 = experiment.import_feature(feature_id=feat_name2)
    experiment.coordinates = {}
    for i, v in all_feat1.items():
        experiment.coordinates[i] = [v, all_feat2[i]]
    
    if textual is None:
        textual = []

    experiment.compute_coordinates_by_families()

    fig = plt.figure(figsize=figsize)
    ax = fig.add_subplot()
    plt.axis('equal')

    if feat_name1 == "slsvd" and feat_name2 == "lsvd":
        # TODO Not nice...
        n = None
        m = None
        for family_info in experiment.families.values():
            n = family_info.agents_count
            m = family_info.resources_count
            break
        assert n is not None and m is not None
        shade_region(n, m, ax)
 
    _add_textual(experiment=experiment, textual=textual, ax=ax, size=textual_size)

    if shading:
        basic_coloring_with_shading(experiment=experiment, ax=ax, ms=ms)
    else:
        basic_coloring(experiment=experiment, ax=ax, dim=2, textual=textual, ms=ms)

    _basic_background(ax=ax, legend=legend, pad_inches=pad_inches,
                      saveas=saveas, xlabel=xlabel, bbox_inches=bbox_inches,
                      title=title, legend_pos=legend_pos, title_size=title_size,
                      title_pos=title_pos, dpi=dpi)
    
    if tex:
        _saveas_tex(saveas=saveas)
    if show:
        plt.show()
