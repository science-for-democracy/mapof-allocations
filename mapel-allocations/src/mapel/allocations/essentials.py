import os
import csv
import time
import copy

import mapel.core.logs as logs
logger = logs.get_logger(__name__)

import mapel.core.utils as utils

from mapel.core.objects.Family import Family
from mapel.allocations.core.alloctask import AllocationTask, AllocationTaskLibrarian
import mapel.allocations.metrics.surveying as surveying
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

  def prepare_family(self, experiment_id=None, store=None,
                     store_points=False, aggregated=True):
    if self.allocation_tasks != []:
      return self.allocation_tasks

    instances = {}
    for j in range(self.size):
      instance_id = get_instance_id(self.single, self.family_id, j)
      instance = AllocationTask.from_culture(instance_id, culture_id=self.culture_id,
                                           agents_count = self.agents_count,
                                           resources_count =
                                           self.resources_count, label=self.label
                                           )
      instances[instance_id] = instance
      if store:
       lib = AllocationTaskLibrarian()
       lib.write(instance, os.path.join("experiments", experiment_id, "instances"))

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




