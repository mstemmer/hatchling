# create class to control config, inc_program and timing.
# serve to controller process via queue
from multiprocessing import Process, Queue
import time

class BroodLord():

    def __init__(self, inc_program, q_prog):
        self.q_prog = q_prog
        self.inc_program = inc_program
        self.set_program()

            # p_param = 179.6
            # i_param = 88
            # d_param = 22

    def set_program(self):
        # while True:
        self.q_prog.put([55, 37]) # set humidity , temperature # 100, 1 , 0 worked best so far
            # print('Putting prog')
        # time.sleep(300)
        #
        # self.q_prog.put([55, 37])
        # time.sleep(20)
