import multiprocessing
import time
import importlib
import logging
from multiprocessing import Process, Queue, Pool
from mapmulti.agent.messagen import reconstructor

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

    def agent_start(self, agent):
        """
        Function that send task to agent
        :param agent: agent name
        :return: flag that task accomplished
        """
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger("process-%r" % (agent.name))
        logger.info('Agent {0} start planning'.format(agent.name))
        saved = agent.search_solution()
        if saved:
            logger.info('Agent {0} finish planning'.format(agent.name))
            self.finished = True
        return agent.name +' finished'

    def server_start(self, port, amount_agents, q):
        import socket
        serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        serversocket.bind(('', port))
        serversocket.listen(10)

        agents_socket = []

        while True:
            # waiting plans from agents
            (clientsocket, address) = serversocket.accept()
            agents_socket.append(clientsocket)
            solution = clientsocket.recv(1024)
            solution = solution.decode()

            if solution:
                self.solution.append(solution)
            else:
                logging.info("Solution is not found by agents")
            print('connected:', address)

            if len(self.solution) == amount_agents:
                keeper = action_keeper(self.solution)
                agent, self.solution = keeper.auction()
                # send best solution forward to agents
                for sock in agents_socket:
                    sock.send(self.solution.encode('utf-8'))
            else:
                continue
            break
        clientsocket.close()

        q.put(self.solution)
        return self.solution


    def manage_agents(self):
        """
        # Create a pool of workers (1 per agent) and wait for their plans.
        # Each agent has its own socket, which allows it take and send messages.
        :return:
        """
        clagents = []
        port = 9097
        for agent in self.agents:
            class_ = getattr(importlib.import_module(self.agpath), self.agtype)
            workman = class_()
            workman.multinitialize(agent, self.agents, self.problem, self.backward)
            port += 1
            clagents.append([workman, port])
        for current_agent in clagents:
            others = [[agent[0].name, agent[1]] for agent in clagents if not agent is current_agent]
            current_agent.insert(2, others)

        multiprocessing.set_start_method('spawn')
        q = Queue()
        p = Process(target=self.server_start, args=(port-len(clagents), len(clagents), q, ))
        p.start()
        pool = Pool(processes=len(clagents)) # make a pool with agents
        multiple_results = [pool.apply_async(self.agent_start, (agent, port, others)) for agent, port, others in
                            clagents]
        if self.solution:
            return self.solution
        else:
            time.sleep(1)

        pool.close()
        pool.join()

        return q.get()


class action_keeper():
    def __init__(self, solutions):
        self.solutions = solutions


    def auction(self):
        plans = {}
        auct = {}
        maxim = 1
        for sol in self.solutions:
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

















