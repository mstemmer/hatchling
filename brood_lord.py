# create class to control config, inc_program and timing.
# serve to controller process via queue
from multiprocessing import Process, Queue
import time


class BroodLord():

    def __init__(self, inc_program, q_prog, time_init):
        self.q_prog = q_prog
        self.inc_program = inc_program
        self.time_init = time_init
        print(time_init)
        # if species == 'chicken':
        #     self.inc_program = inc_program["chicken"]
        #


        # species = 'chicken'
        # if species == 'chicken':
        #     self.inc_program = inc_program['chicken']

        self.set_program()

            # p_param = 179.6
            # i_param = 88
            # d_param = 22

    def set_program(self):
        # while True:
        self.q_prog.put(self.inc_program["phase_1"]) # set humidity , temperature # 100, 1 , 0 worked best so far
            # print('Putting prog')
        # time.sleep(300)
        #
        # self.q_prog.put([55, 37])
        # time.sleep(20)
