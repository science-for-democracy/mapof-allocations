import os
import csv
import time
import copy

import mapel.allocations.core.logs as logs
logger = logs.get_logger(__name__)

import mapel.core.utils as utils
import mapel.allocations.cultures.misc as misc
from mapel.core.objects.Family import Family
from mapel.allocations.core.alloctask import AllocationTask
from mapel.allocations.core.alloctasklibrarian import AllocationTaskLibrarian
from mapel.core.utils import get_instance_id


class AllocationTaskFamily(Family):

  @classmethod
  def from_one_alloc_task(cls, alloc_task, family_id, **kwargs):
    return AllocationTaskFamily(family_id = family_id, single = True,
    ready_instances = [alloc_task], **kwargs)

  @classmethod
  def from_culture(cls, culture_id, family_id, agents_count, resources_count, **kwargs):
    return AllocationTaskFamily(family_id = family_id, culture_id = culture_id,
    agents_count = agents_count, resources_count = resources_count,**kwargs)

  def __init__(self,
             culture_id: str = None,
             family_id='none',
             params: dict = None,
             size: int = 1,
             label: str = "none",
             color: str = "black",
             alpha: float = 1.,
             ms: int = 20,
             show=True,
             marker='o',
             starting_from: int = 0,
             path: dict = None,
             single: bool = False,
             election_ids=None,
             ready_instances = [],
             agents_count = 0,
             resources_count = 0):

    super().__init__(culture_id=culture_id,
                     family_id=family_id,
                     params=params,
                     size=size,
                     label=label,
                     color=color,
                     alpha=alpha,
                     ms=ms,
                     show=show,
                     marker=marker,
                     starting_from=starting_from,
                     path=path,
                     single=single,
                     instance_ids=election_ids)
    self.agents_count = agents_count
    self.resources_count = resources_count
    self.allocation_tasks = [] + ready_instances
    self.instance_ids = [t.instance_id for t in ready_instances]

  def prepare_family(self, experiment_id=None, is_exported=False,
                     store_points=False, aggregated=True):
    if self.allocation_tasks != []:
      return self.allocation_tasks

    instances = {}

    # This is a dirty hack which adds
    # unnecessary conditional on a culture name
    # In th efuture, there should be a possibility to also
    # define aggregate of the same cultures over multiple parameters
    # as an "automatic" family
    if self.culture_id == "collect_spliddit":
      basepath = self.params["basepath"]
      logger.debug(f"Collecting spliddit instaces from '{basepath}' ("
      f"{self.agents_count} agents and {self.resources_count} resources)")
      counter = 0
      for root, dirs, files in os.walk(basepath):
        if root != basepath:
          continue
        import random
        random.shuffle(files)
        for filename in files:
          if not filename.startswith(f"{self.agents_count}_{self.resources_count}_"):
            continue
          logger.info(f"Collecting {filename}")
          instance_filename  = os.path.join(root, filename)
          instance_id = get_instance_id(self.single, self.family_id, counter)
          instance = AllocationTask.from_splidditfile(instance_id,
          self.agents_count, self.resources_count, self.culture_id, instance_filename)
          instances[instance_id] = instance
          counter += 1
          if counter >= self.size:
              break
        if counter >= self.size:
            break
    elif self.culture_id == "collect_instances":
      max_instances = self.size
      basepath = self.params["basepath"]
      ext = self.params["ext"]
      logger.debug(f"Collecting mapel instaces from '{basepath}' ("
      f"{self.agents_count} agents and {self.resources_count} resources)")
      counter = 0
      for root, dirs, files in os.walk(basepath):
        if root != basepath:
          continue
        import random
        random.shuffle(files)
        for filename in files:
          if counter == max_instances:
            logger.info(f"Acheived the limit of {max_instances} loaded!")
            break
          if not filename.endswith(f".{ext}"):
            continue
          logger.info(f"Collecting {filename}")
          instance_filename  = os.path.join(root, filename)
          instance_id = get_instance_id(self.single, self.family_id, counter)

          try:
            utility_matrix = \
            misc.from_mapel_allocation_instance(self.agents_count, self.
                                                resources_count, instance_filename)
          except ValueError as e:
            logger.debug(f"File {filename} ommited due to incompatible agents"
                         " and/or resources counts.")
            continue
          instance = AllocationTask.from_matrix(utility_matrix, instance_id, self.culture_id)
          #A dirty hack to have a path
          instance.path = instance_filename 
          instances[instance_id] = instance
          counter += 1
    else:
      for j in range(self.size):
        instance_id = get_instance_id(self.single, self.family_id, j)
        instance = AllocationTask.from_culture(instance_id, culture_id=self.culture_id,
                                             agents_count = self.agents_count,
                                             resources_count =
                                             self.resources_count,
                                             label=self.label, params =
                                             self.params
                                             )
        instances[instance_id] = instance

    if is_exported:
      for instance in instances.values():
        lib = AllocationTaskLibrarian()
        filename = instance.__dict__.get("path", None)
        custom_line = None
        if filename:
          with open(filename, "r") as instancefile:
            lines = [line.strip() for line in instancefile]
            custom_line = f"{lines[-2]}\n{lines[-1]}"
        lib.write(instance, os.path.join("experiments", experiment_id,
                                         "instances"), custom_line)

    self.instance_ids = instances.keys()

    return instances

  def __getattr__(self, attr):
      if attr == 'election_ids':
          return self.instance_ids
      else:
          return self.__dict__[attr]

  def __setattr__(self, name, value):
      if name == "election_ids":
          return setattr(self, 'instance_ids', value)
      else:
          self.__dict__[name] = value




