"""
Environment used for ACT-R model.
"""

import pyactr.utilities as utilities
    
roundtime = utilities.roundtime

class Environment(object):
    """
    Environment module for ACT-R. Shows whatever is seen on screen at the moment, allows interaction with ACT-R module.
    """


    Event = utilities.Event
    _ENV = utilities._ENV
    
    run_time = 1
    trigger = None
    obj = None

    def __init__(self):
        self.text = []

    def output(self, obj, trigger=None):
        """
        Outputs obj in environment. Trigger specifies to what the environment should respond (e.g., what key press).
        """
        self.trigger = trigger
        self.obj = obj
        print("OUTPUT ON SCREEN")
        print(self.obj)
        print("END OF OUTPUT")


