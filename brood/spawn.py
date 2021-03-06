from multiprocessing import Process, Queue

from brood.workers.controller import BroodController
from brood.workers.brood_lord import BroodLord
from brood.workers.output import Output


class SpawnHatchling():
    def __init__(self, config, inc_program, time_init):

        # init queues
        q_data = Queue()
        q_prog = Queue()

        #init processes
        p1 = Process(target=self.run_controller, args=(config, q_prog, q_data,) )
        p2 = Process(target=self.run_brood_lord, args=(config, inc_program, q_prog, time_init, ))
        p3 = Process(target=self.run_output, args=(config, q_data, time_init, ))
        processes = [p1, p2, p3]

        for p in processes:
            p.start()

        for p in processes:
            p.join()

    def run_controller(self, config, q_prog, q_data):
        BroodController(config, q_prog, q_data)

    def run_brood_lord(self, config, inc_program, q_prog, time_init):
        BroodLord(config, inc_program, q_prog, time_init)

    def run_output(self, config, q_data, time_init):
        Output(config, q_data, time_init)
