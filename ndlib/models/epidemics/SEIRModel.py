from ..DiffusionModel import DiffusionModel
import numpy as np
import future

__author__ = ["Vincenzo Caproni", "Beatrice Caputo", "Ettore Puccetti", "Elisa Salatti"]
__license__ = "BSD-2-Clause"


class SEIRModel(DiffusionModel):

    def __init__(self, graph, seed=None):

        super(self.__class__, self).__init__(graph, seed)

        self.name = "SEIR"

        self.available_statuses = {
            "Susceptible": 0,
            "Exposed": 2,
            "Infected": 1,
            "Removed": 3
        }
        self.parameters = {
            "model": {
                "alpha": {
                    "descr": "Latent period",
                    "range": [0, 1],
                    "optional": False},
                "beta": {
                    "descr": "Infection rate",
                    "range": [0, 1],
                    "optional": False},
                "gamma": {
                    "descr": "Recovery rate",
                    "range": [0, 1],
                    "optional": False
                },
                "tp_rate": {
                    "descr": "Whether if the infection rate depends on the number of infected neighbors",
                    "range": [0, 1],
                    "optional": True,
                    "default": 1
                }
            },
            "nodes": {},
            "edges": {},
        }

        self.progress = {}

    def iteration(self, node_status=True):
        self.clean_initial_status(self.available_statuses.values())

        actual_status = {node: nstatus for node, nstatus in future.utils.iteritems(self.status)}

        if self.actual_iteration == 0:
            self.actual_iteration += 1
            delta, node_count, status_delta = self.status_delta(actual_status)
            if node_status:
                return {"iteration": 0, "status": actual_status.copy(),
                        "node_count": node_count.copy(), "status_delta": status_delta.copy()}
            else:
                return {"iteration": 0, "status": {},
                        "node_count": node_count.copy(), "status_delta": status_delta.copy()}

        for u in self.graph.nodes:

            u_status = self.status[u]
            eventp = np.random.random_sample()
            neighbors = self.graph.neighbors(u)
            if self.graph.directed:
                neighbors = self.graph.predecessors(u)

            if u_status == 0:  # Susceptible

                infected_neighbors = [v for v in neighbors if self.status[v] == 1]
                triggered = 1 if len(infected_neighbors) > 0 else 0

                if self.params['model']['tp_rate'] == 1:
                    if eventp < 1 - (1 - self.params['model']['beta']) ** len(infected_neighbors):
                        actual_status[u] = 2  # Exposed
                        self.progress[u] =  self.actual_iteration # save time of exposure t_e
                else:
                    if eventp < self.params['model']['beta'] * triggered:
                        actual_status[u] = 2  # Exposed
                        self.progress[u] =  self.actual_iteration # save time of exposure t_e

            elif u_status == 2:

                # apply prob. of infection, after (t - t_e) 
                if eventp < 1 - np.exp(- (self.actual_iteration - self.progress[u]) * self.params['model']['alpha']): 
                    actual_status[u] = 1  # Infected
                    self.progress[u] =  self.actual_iteration # save time of infection t_i
                # apply prob. of recovery, after (t - t_i)
            elif u_status == 1:
                if eventp < 1 - np.exp(- (self.actual_iteration - self.progress[u]) * self.params['model']['gamma']): 
                    actual_status[u] = 3  # Removed
                    del self.status[u]

        delta, node_count, status_delta = self.status_delta(actual_status)
        self.status = actual_status
        self.actual_iteration += 1

        if node_status:
            return {"iteration": self.actual_iteration - 1, "status": delta.copy(),
                    "node_count": node_count.copy(), "status_delta": status_delta.copy()}
        else:
            return {"iteration": self.actual_iteration - 1, "status": {},
                    "node_count": node_count.copy(), "status_delta": status_delta.copy()}
