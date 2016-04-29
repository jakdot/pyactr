"""
Environment used for ACT-R model.
"""

import collections

import pyactr.environment as env

class Environment(env.Environment): #subclass Environment
    """
    Example of environment used for ACT-R model. This model changes display based on trigger (run_time must be present, but it is set high to not play any role). You can run this in u2_motormodel in the folder tutorials.
    """

    def __init__(self):
        self.text = "b c d".split()
        self.run_time = 10

    def environment_process(self, start_time):
        """
        Example of environment process. Text appears, changes/disappers after run_time runs out.
        """
        time = start_time
        yield env.Event(env.roundtime(time), env._ENV, "STARTING ENVIRONMENT") #yield Event; Event has three positions - time, process, in this case, ENVIRONMENT (specified in env._ENV) and description of action; only time is crucial for correct running of the environment
        for letter in self.text: #run through letters, print them, yield a corresponding event
            self.output(letter, trigger=letter) #output on environment
            time = time + self.run_time
            yield env.Event(env.roundtime(time), env._ENV, "PRINTED LETTER %s" % letter)





