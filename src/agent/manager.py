import importlib
import logging
from multiprocessing import Process,Pipe
from multiprocessing.util import log_to_stderr
from mapmulti.agent.agent_search import DecisionStrategies


def agent_activation(agpath, agtype, name, agents, problem, backward, TaskType, childpipe):
    # init agent
    class_ = getattr(importlib.import_module(agpath), agtype)
    workman = class_()
    workman.multinitialize(name, agents, problem, backward)
    # load SWM and calculate the amount of new signs
    if TaskType == 'mahddl':
        new_signs = workman.loadHierarchy()
    else:
        new_signs = workman.loadSWM()
    childpipe.send((name, new_signs))
    # load info about the major agent
    major_agent = childpipe.recv()
    # search solution and send it to major agent
    if TaskType == 'mahddl':
        solution = workman.bulid_hierarchy()
    else:
        solution = workman.search_solution()
    childpipe.send(solution)
    if name == major_agent:
        # receive solution and create an auction
        solutions = childpipe.recv()
        logging.info("Solutions received by major agent %s" % name)
        keeper = DecisionStrategies(solutions)
        # can be changed to any other strategy
        agents, solution = keeper.auction()
        # ask agents whose plan won to save their solutions, to other agents - save won agent solution (find in their plans the won plan).
        childpipe.send(solution)
    # Save solution
    solution_to_save = childpipe.recv()
    workman.save_solution(solution_to_save)


class Manager:
    def __init__(self, agents, problem, agpath = 'mapmulti.agent.agent_search', agtype = 'MlAgent', backward = False, TaskType = 'mapddl'):
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
        self.TaskType = TaskType

    def manage_agents(self):

        allProcesses = []

        for ag in self.agents:
            parent_conn, child_conn = Pipe()
            p = Process(target=agent_activation,
                        args=(self.agpath, self.agtype,ag, self.agents, self.problem, self.backward, self.TaskType, child_conn, ))
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

        # Send solutions to the major agent and receive final solution
        final_solution = None
        for info, conn in group_experience:
            if info[0] == major:
                conn.send(solutions)
                final_solution = conn.recv()
                break

        # Send final solution to all agents
        for info, conn in group_experience:
            conn.send(final_solution)

        for pr, conn in allProcesses:
            pr.join()



















