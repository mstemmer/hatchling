from multiprocessing import Process, Queue, set_start_method
import os

from brood.workers.controller import BroodController
from brood.workers.brood_lord import BroodLord
from brood.workers.stream_data import Output
from brood.logging_config import setup_logging_for_spawn


class SpawnHatchling():
    def __init__(self, config, inc_program, time_init, data_folder, log_file_path):
        # Use 'spawn' instead of 'fork' for multiprocessing
        # This creates fresh Python interpreters instead of forking,
        # which allows gpiozero to initialize properly in each process
        try:
            set_start_method('spawn', force=True)
        except RuntimeError:
            pass  # Already set

        # Store log file path for child processes
        self.log_file_path = log_file_path

        # init queues
        q_data = Queue()
        q_prog = Queue()

        #init processes
        p1 = Process(target=self.run_controller, args=(config, q_prog, q_data,) )
        p2 = Process(target=self.run_brood_lord, args=(config, inc_program, q_prog, time_init, ))
        p3 = Process(target=self.run_output, args=(config, q_data, time_init, data_folder, ))
        processes = [p1, p2, p3]

        for p in processes:
            p.start()

        for p in processes:
            p.join()

    def run_controller(self, config, q_prog, q_data):
        setup_logging_for_spawn(self.log_file_path)
        BroodController(config, q_prog, q_data)

    def run_brood_lord(self, config, inc_program, q_prog, time_init):
        setup_logging_for_spawn(self.log_file_path)
        BroodLord(config, inc_program, q_prog, time_init)

    def run_output(self, config, q_data, time_init, data_folder):
        setup_logging_for_spawn(self.log_file_path)
        Output(config, q_data, time_init, data_folder)
