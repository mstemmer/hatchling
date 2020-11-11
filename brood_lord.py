# create class to control config, inc_program and timing.
# serve to controller process via queue
from multiprocessing import Process, Queue
import time

class BroodLord():

    def __init__(self, inc_program, q_prog):
        self.q_prog = q_prog
        self.inc_program = inc_program
        self.set_program()



    def set_program(self):
        while True:
            self.q_prog.put([55, 22])
            # print('Putting prog')
            time.sleep(20)

            self.q_prog.put([40, 15])
            time.sleep(20)
