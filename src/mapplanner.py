import logging
import os
from mapcore.mapplanner import MapPlanner as MPcore
from mapmulti.agent.manager import Manager
SOLUTION_FILE_SUFFIX = '.soln'

import platform

if platform.system() != 'Windows':
    delim = '/'
else:
    delim = '\\'

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("process-main")

class MapPlanner(MPcore):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        #self.domain, self.problem = self.find_domain(self.kwgs['path'], self.kwgs['task'])

    def find_domain(self, path, number):
        """
        Domain search function
        :param path: path to current task
        :param number: task number
        :return:
        """
        if self.TaskType == 'htn' or self.TaskType == 'mahddl':
            ext = '.hddl'
        else:
            ext = '.pddl'
        task = 'task' + number + ext
        domain = 'domain' + ext

        if not domain in os.listdir(path):
            domain2 = self.search_upper(path, domain)
            if not domain2:
                raise Exception('domain not found!')
            else:
                domain = domain2
        else:
            domain = path + domain
        if not task in os.listdir(path):
            raise Exception('task not found!')
        else:
            problem = path + task

        return domain, problem

    def action_agents(self, problem):
        agents = set()
        for _, action in problem.domain.actions.items():
            for ag in action.agents:
                for obj, type in problem.objects.items():
                    if type.name == ag:
                        agents.add(obj)
        return agents

    def search_multi(self):
        """
        multiagent plan search for clasically
        :return: the final solution. It is choosed from the set of all solutions, using auction
        """

        problem = self._parse(self.domain, self.problem)
        act_agents = self.action_agents(problem)
        logging.info('Agents found in actions: {0}'.format(len(act_agents)))
        agents = set()
        if problem.constraints:
            if len(act_agents):
                agents |= act_agents
            else:
                for constr in problem.constraints:
                    agents.add(constr)
                logging.info('Agents found in constraints: {0}'.format(len(agents)))
        elif act_agents:
            agents |= act_agents
        else:
            agents.add('I')
            logging.info('Only 1 agent plan')

        manager = Manager(agents, problem, self.agpath, backward=self.backward)
        solution = manager.manage_agents()
        return solution

    def search_mhddl(self):
        """
        classic HTN-based plan search. Multiagent version.
        :return: the final solution
        """
        from mapmulti.hddl.hddl_parser import maHDDLParser
        from mapcore.search.htnsearch import HTNSearch
        parser = maHDDLParser(self.domain, self.problem)
        logging.info('Parsing was finished...')
        logging.info('Parsing Domain {0}'.format(self.domain))
        domain = parser.ParseDomain(parser.domain)
        logging.info('Parsing Problem {0}'.format(self.problem))
        problem = parser.ParseProblem(parser.problem)
        logging.info('{0} Objects parsed'.format(len(problem['objects'])))
        logging.info('{0} Predicates parsed'.format(len(domain['predicates'])))
        logging.info('{0} Actions parsed'.format(len(domain['actions'])))
        logging.info('{0} Methods parsed'.format(len(domain['methods'])))
        problem.update(domain)

        # htn = HTNSearch(signs)
        # solution = htn.search_plan()

        #act_agents = self.action_agents(problem)
        agents = list(problem['constraints'].keys())
        import re
        problem_name = re.search('problem(.*)\)', parser.problem)
        problem_name = problem_name.group(1)
        problem['name'] = problem_name.strip()

        manager = Manager(agents, problem, self.agpath, TaskType=self.TaskType)
        solution = manager.manage_agents()
        return solution


    def search(self):
        if self.TaskType == 'classic':
            return self.search_classic()
        elif self.TaskType == 'htn':
            return self.search_htn()
        elif self.TaskType == 'mapddl':
            return self.search_multi()
        elif self.TaskType == 'mahddl':
            return self.search_mhddl()
        else:
            raise Exception('You are using multiagent lib without extensions. Tasks can be classic, htn or multi!!!')

