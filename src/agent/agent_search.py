import logging
import time

from mapmulti.search.mapsearch import MapSearch
from mapcore.agent.agent_search import Agent
from mapmulti.agent.messagen import reconstructor
from mapcore.grounding.sign_task import Task
from mapcore.grounding import pddl_grounding

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
        self.task = None

    def loadSWM(self):
        """
        This method loads SWM and count the amount of usable experience
        :return: the amount of experience (in signs)
        """
        logging.info('Grounding start: {0}'.format(self.problem.name))
        signs = Task.load_signs(self.name)
        self.task = pddl_grounding.ground(self.problem, self.name, signs)
        logging.info('Grounding end: {0}'.format(self.problem.name))
        logging.info('{0} Signs created'.format(len(self.task.signs)))
        return len(self.task.signs) - len(signs)

    def search_solution(self):
        """
        This function is needed to synthesize all plans, choose the best one and
        save the experience.
        """
        # task = self.load_sw()
        logging.info('Search start: {0}, Start time: {1}'.format(self.task.name, time.clock()))
        search = MapSearch(self.task, self.backward)
        solutions = search.search_plan()
        self.solution = search.long_relations(solutions)
        if self.backward:
            self.solution = list(reversed(self.solution))
        file_name = self.task.save_signs(self.solution)
        if file_name:
            logging.info('Agent ' + self.name + ' finished all works')

class DecisionStrategies:
    def __init__(self, solutions):
        self.plans = solutions

    def auction(self):
        plans = {}
        auct = {}
        maxim = 1
        for sol in self.plans:
            agent, plan = reconstructor(sol)
            plans[agent] = plan
        for agent, plan in plans.items():
            if not plan in auct:
                auct[plan] = 1
            else:
                iter = auct[plan]
                auct[plan] = iter+1
                if iter+1 > maxim:
                    maxim = iter+1

        plan = [plan for plan, count in auct.items() if count==maxim][0]

        agents = []
        for agent, pl in plans.items():
            if pl == plan:
                agents.append(agent)
        return agents[0], plan

