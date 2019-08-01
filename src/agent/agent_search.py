import logging
import time

from mapcore.grounding import pddl_grounding
from mapcore.search.mapsearch import MapSearch
from mapcore.grounding.sign_task import Task
from mapcore.agent.agent_search import Agent

class MlAgent(Agent):
    def __init__(self):
        super().__init__()
        pass

    # Initialization
    def multinitialize(self, name, agents, problem, backward):
        """
        This function allows agent to be initialized. We do not use basic __init__ to let
        user choose a valid variant of agent.
        :param problem: problem
        :param ref: the dynamic value of plan clarification
        """
        self.name = name
        self.problem = problem
        self.solution = []
        self.final_solution = ''
        self.backward = backward
        self.others = {ag for ag in agents if ag != name}

    def search_solution(self):
        """
        This function is needed to synthesize all plans, choose the best one and
        save the experience.
        """
        task = self.load_sw()
        logging.info('Search start: {0}, Start time: {1}'.format(task.name, time.clock()))
        search = MapSearch(task, self.backward)
        solutions = search.search_plan()
        self.solution = search.long_relations(solutions)
        if self.backward:
            self.solution = list(reversed(self.solution))
        file_name = task.save_signs(self.solution)
        if file_name:
            logging.info('Agent ' + self.name + ' finished all works')

