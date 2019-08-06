import multiprocessing
import os
import time
import importlib
import logging
from multiprocessing import Process, Queue, Pool, Pipe
from multiprocessing.util import log_to_stderr


def agent_activation(agpath, agtype, name, agents, problem, backward, childpipe):
    #logger.info('Im inside')
    class_ = getattr(importlib.import_module(agpath), agtype)
    workman = class_()
    workman.multinitialize(name, agents, problem, backward)
    new_signs = workman.loadSWM()
    childpipe.send((name, new_signs))
    print(childpipe.recv())
    solution = workman.search_solution()
    print(solution)

    #return name, new_signs

class Manager:
    def __init__(self, agents, problem, agpath = 'mapmulti.agent.agent_search', agtype = 'MlAgent', backward = True):
        self.problem = problem
        self.solution = []
        self.finished = None
        self.agtype = agtype
        self.agpath = agpath
        self.ref = 1
        self.backward = backward
        self.agents = agents
        self.logger = log_to_stderr()
        self.logger.setLevel(logging.INFO)
    #
    # def agent_start(self, agent):
    #     """
    #     Function that send task to agent
    #     :param agent: agent name
    #     :return: flag that task accomplished
    #     """
    #     print('im inside')
    #     logging.basicConfig(level=logging.INFO)
    #     logger = logging.getLogger("process-%r" % (agent.name))
    #     logger.info('Agent {0} start planning'.format(agent.name))
    #     saved = agent.search_solution()
    #     if saved:
    #         logger.info('Agent {0} finish planning'.format(agent.name))
    #         self.finished = True
    #     return agent.name +' finished'

    def manage_agents(self):
        """
        Create a pool of workers (1 per agent) and wait for their plans.
        The first action is using multisets to find the major agent. There are several strategies - we use
        the strategy, when the major agent is agent with the biggest amount of knowledge about current task.
        It can be partial or full.
        """
        # agents_of_the_task = []
        #
        # for agent in self.agents:
        #     class_ = getattr(importlib.import_module(self.agpath), self.agtype)
        #     workman = class_()
        #     workman.multinitialize(agent, self.agents, self.problem, self.backward)
        #     q = Queue()
        #     agents_of_the_task.append([workman, q])
        # for current_agent in agents_of_the_task:
        #     others = [[agent[0].name, agent[1]] for agent in agents_of_the_task if not agent is current_agent]
        #     current_agent.insert(2, others)
        #
        # multiprocessing.set_start_method('spawn')
        # q = Queue()
        # p = Process(target=self.server_start, args=(port-len(clagents), len(clagents), q, ))
        # p.start()
        # pool = Pool(processes=len(clagents)) # make a pool with agents
        # multiple_results = [pool.apply_async(self.agent_start, (agent, port, others)) for agent, port, others in
        #                     clagents]
        # # multiple_results = [pool.apply_async(self.agent_start, (agent)) for agent, port, others in
        # #                     clagents]
        # if self.solution:
        #     return self.solution
        # else:
        #     time.sleep(1)
        #
        # pool.close()
        # pool.join()
        #
        # return q.get()

        # queue = Queue()
        # with Pool(processes=len(self.agents)) as pool:
        #     multiple_results = [pool.apply_async(agent_activation, (self.agpath, self.agtype,ag, self.agents, self.problem, self.backward, queue))
        #                         for ag in self.agents]
        #     gr_exp = [queue.get()]
        #
        #     group_experience = dict([el.get(True) for el in multiple_results])
        #     # Select the major (most experienced) agent
        #     most_exp = max(group_experience.values())
        #     major = [ag for ag, exp in group_experience if exp == most_exp][0]


        allProcesses = []

        for ag in self.agents:
            parent_conn, child_conn = Pipe()
            p = Process(target=agent_activation, args=(self.agpath, self.agtype,ag, self.agents, self.problem, self.backward, child_conn,))
            allProcesses.append((p, parent_conn))
            p.start()

        group_experience = []
        for pr, conn in allProcesses:
            group_experience.append((conn.recv(), conn))
        # Select the major (most experienced) agent
        most_exp = 0
        for info, _ in group_experience:
            if info[1] > most_exp:
                most_exp = info[1]

        major = [info[0] for info, conn in group_experience if info[1] == most_exp][0]

        # Create a queue for all agents to put their solutions.
        # Major agent will create an auction and send back the best solution.
        queue = Queue()
        for pr, conn in allProcesses:
            conn.send(major)

        for pr, conn in allProcesses:
            pr.join()





        # leader search.
        # 1. Create process for each agent
        # 2. Activate agent's class inside each process <<=== Incapsulate agent into the process
        # 3. All agents need a pipe - to send to the server availability experience (amount of simular to task signs in the exp)
        # 4. Agent with the highest amount of experience signs - become a major agent. <<== algo in separate function
        # 5. All agents plans separately and then send there plans to the queue, that is available to all proceses.
        # 6. The major agent create an auction to get the best plan and send it to all agents by pipes.
        # 7. All agents save the best plan

        #pool to find plan by each of the agent
        # pool = Pool(processes=len(agents_of_the_task))
        # result = pool.apply_async(self.agent_start, (25,))
        # print(result.get(timeout=1))


















