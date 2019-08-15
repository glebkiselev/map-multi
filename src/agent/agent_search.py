import logging
import time

from mapcore.agent.agent_search import Agent
from mapmulti.agent.messagen import reconstructor
from mapmulti.agent.messagen import Tmessage

class MlAgent(Agent):
    def __init__(self):
        super().__init__()
        pass

    # Initialization pddl agent
    def multinitialize(self, name, agents, problem, TaskType, backward):
        """
        This function allows agent to be initialized. We do not use basic __init__ to let
        user choose a valid variant of agent.
        :param problem: problem
        :param ref: the dynamic value of plan clarification
        """
        self.name = name
        self.problem = problem
        self.solution = []
        self.allsolutions = []
        self.backward = backward
        self.others = {ag for ag in agents if ag != name}
        self.task = None
        self.TaskType = TaskType

    def loadSWM(self):
        """
        This method loads SWM and count the amount of usable experience
        :return: the amount of experience (in signs)
        """
        from mapmulti.grounding.sign_task import Task
        from mapmulti.grounding import pddl_grounding
        logging.info('Grounding start: {0}'.format(self.problem.name))
        signs = Task.load_signs(self.name)
        self.task = pddl_grounding.ground(self.problem, self.name, signs)
        logging.info('Grounding end: {0}'.format(self.problem.name))
        logging.info('{0} Signs created'.format(len(self.task.signs)))
        if signs:
            return len(self.task.signs) - len(signs)
        else:
            return 0

    def loadHierarchy(self):
        """
        This method ground hddl task
        :return: 0 - if there are no experience or
        the amount of new grounded signs
        """
        from mapmulti.grounding.hddl_grounding import ground
        logging.info('HDDL grounding start: {0}'.format(self.problem['name']))
        self.task = ground(self.problem, self.name)
        logging.info('HDDL grounding end: {0}'.format(self.problem['name']))
        logging.info('{0} Signs created'.format(len(self.task.signs)))
        return 0

    def sol_to_acronim(self, solution):
        acronim = ''
        if solution[-1][1] == 'approve' or solution[-1][1] == 'broadcast':
            solution = solution[:-1]
        for act in solution:
            if act[3]:
                if act[3].name == 'I':
                    name = self.name
                else:
                    name = act[3].name
            else:
                name = self.name
            acronim += act[1] + ' ' + name + ';'
        return acronim


    def search_solution(self):
        """
        This function is needed to synthesize all plans, choose the best one and
        save the experience.
        """
        if self.TaskType == 'mahddl':
            from mapmulti.search.htnsearch import HTNSearch as Search
        else:
            from mapmulti.search.mapsearch import MapSearch as Search
        logging.info('Search start: {0}, Start time: {1} by agent: {2}'.format(self.task.name, time.clock(), self.name))
        if len(self.others) > 1:
            method = 'Broadcast'
            cm = self.task.signs[method].significances[1].copy('significance', 'meaning')
        elif len(self.others) == 1:
            method = 'Approve'
            cm = self.task.signs[method].significances[1].copy('significance', 'meaning')
        else:
            method = 'save_achievement'
            cm = None
        search = Search(self.task, self.backward)
        self.allsolutions = search.search_plan()
        self.solution = search.long_relations(self.allsolutions)
        if self.backward:
            self.solution = list(reversed(self.solution))
        sol_acronims = []
        for sol in self.allsolutions:
            acronim = self.sol_to_acronim(sol)
            sol_acronims.append(acronim)
        self.solution.append((self.task.signs[method].add_meaning(), method, cm, self.task.signs["I"]))

        mes = Tmessage(self.solution, self.name)
        message = getattr(mes, method.lower())()

        return message

    def save_solution(self, solution):
        solacr = ''
        for sol in solution.split(';')[:-1]:
            solacr+=sol.strip() + ';'
        for sol in self.allsolutions:
            acronim = self.sol_to_acronim(sol)
            if acronim == solacr:
                if self.backward:
                    sol = list(reversed(sol))
                file_name = self.task.save_signs(sol)
                if file_name:
                    logging.info('Agent ' + self.name + ' finished all works')
                break
        else:
            logging.info("Agent {0} can not find the right solution to save!")



class DecisionStrategies:
    def __init__(self, solutions):
        self.plans = solutions

    def auction(self):
        solutions = {}
        auct = {}
        maxim = 1
        for agent, sol in self.plans.items():
            _, plan = reconstructor(sol)
            clear_plan = ''
            for el in plan.strip().split(';')[:-2]:
                clear_plan+=el + ';'
            solutions[agent] = clear_plan
        for agent, plan in solutions.items():
            if not plan in auct:
                auct[plan] = 1
            else:
                iter = auct[plan]
                auct[plan] = iter+1
                if iter+1 > maxim:
                    maxim = iter+1

        plan = [plan for plan, count in auct.items() if count==maxim][0]

        agents = []
        for agent, pl in solutions.items():
            if pl == plan:
                agents.append(agent)
        return agents, plan

