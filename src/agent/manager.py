import multiprocessing
import os
import time
import importlib
import logging
from multiprocessing import Process, Queue, Pool, Pipe
from multiprocessing.util import log_to_stderr


def agent_activation(agpath, agtype, name, agents, problem, backward):
    #logger.info('Im inside')
    print('im inside')
    class_ = getattr(importlib.import_module(agpath), agtype)
    workman = class_()
    workman.multinitialize(name, agents, problem, backward)
    new_signs = workman.loadSWM()
    return str(new_signs)

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

    def agent_start(self, agent):
        """
        Function that send task to agent
        :param agent: agent name
        :return: flag that task accomplished
        """
        print('im inside')
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger("process-%r" % (agent.name))
        logger.info('Agent {0} start planning'.format(agent.name))
        saved = agent.search_solution()
        if saved:
            logger.info('Agent {0} finish planning'.format(agent.name))
            self.finished = True
        return agent.name +' finished'

    # def server_start(self, port, amount_agents, q):
    #     import socket
    #     serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #     serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    #     serversocket.bind(('', port))
    #     serversocket.listen(10)
    #
    #     agents_socket = []
    #
    #     while True:
    #         # waiting plans from agents
    #         (clientsocket, address) = serversocket.accept()
    #         agents_socket.append(clientsocket)
    #         solution = clientsocket.recv(1024)
    #         solution = solution.decode()
    #
    #         if solution:
    #             self.solution.append(solution)
    #         else:
    #             logging.info("Solution is not found by agents")
    #         print('connected:', address)
    #
    #         if len(self.solution) == amount_agents:
    #             keeper = action_keeper(self.solution)
    #             agent, self.solution = keeper.auction()
    #             # send best solution forward to agents
    #             for sock in agents_socket:
    #                 sock.send(self.solution.encode('utf-8'))
    #         else:
    #             continue
    #         break
    #     clientsocket.close()
    #
    #     q.put(self.solution)
    #     return self.solution


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



        with Pool(processes=len(self.agents)) as pool:
            multiple_results = [pool.apply_async(agent_activation, (self.agpath, self.agtype,ag, self.agents, self.problem, self.backward))
                                for ag in self.agents]
            print([el.get(True) for el in multiple_results])


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

        # def creator(data, q):
        #     """
        #     Creates data to be consumed and waits for the consumer
        #     to finish processing
        #     """
        #     print('Creating data and putting it on the queue')
        #     for item in data:
        #         q.put(item)
        #
        # def my_consumer(q):
        #     """
        #     Consumes some data and works on it
        #     In this case, all it does is double the input
        #     """
        #     while True:
        #         data = q.get()
        #         print('data found to be processed: {}'.format(data))
        #
        #         processed = data * 2
        #         print(processed)


#
# class action_keeper():
#     def __init__(self, solutions):
#         self.solutions = solutions
#
#
#     def auction(self):
#         plans = {}
#         auct = {}
#         maxim = 1
#         for sol in self.solutions:
#             agent, plan = reconstructor(sol)
#             plans[agent] = plan
#         for agent, plan in plans.items():
#             if not plan in auct:
#                 auct[plan] = 1
#             else:
#                 iter = auct[plan]
#                 auct[plan] = iter+1
#                 if iter+1 > maxim:
#                     maxim = iter+1
#
#         plan = [plan for plan, count in auct.items() if count==maxim][0]
#
#         agents = []
#         for agent, pl in plans.items():
#             if pl == plan:
#                 agents.append(agent)
#         return agents[0], plan

















