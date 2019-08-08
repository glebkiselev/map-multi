import importlib
import logging
from multiprocessing import Process,Pipe
from multiprocessing.util import log_to_stderr
from mapmulti.agent.agent_search import DecisionStrategies


def agent_activation(agpath, agtype, name, agents, problem, backward, childpipe):

    class_ = getattr(importlib.import_module(agpath), agtype)
    workman = class_()
    workman.multinitialize(name, agents, problem, backward)
    new_signs = workman.loadSWM()
    childpipe.send((name, new_signs))
    major_agent = childpipe.recv()
    solution = workman.search_solution()
    childpipe.send(solution)
    if name == major_agent:
        solutions = childpipe.recv()
        logging.info("Solutions received by major agent %s" % name)
        keeper = DecisionStrategies(solutions)
        # can be changed to any other strategy
        agents, solution = keeper.auction()
        # ask agents whose plan won to save their solutions, to other agents - save won agent solution (find in their plans the won plan).
        print(agents)

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

    def manage_agents(self):

        allProcesses = []

        for ag in self.agents:
            parent_conn, child_conn = Pipe()

            p = Process(target=agent_activation,
                        args=(self.agpath, self.agtype,ag, self.agents, self.problem, self.backward, child_conn, ))
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

        # Major agent will create an auction and send back the best solution.
        for pr, conn in allProcesses:
            conn.send(major)

        solutions = {}
        # Receive solutions
        for info, conn in group_experience:
            solutions[info[0]] = conn.recv()

        # Send solutions to the major agent
        for info, conn in group_experience:
            if info[0] == major:
                conn.send(solutions)
                break
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


















