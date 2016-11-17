"""
Environment used for ACT-R model.
"""

import collections
import warnings

import pyactr.utilities as utilities
import pyactr.chunks as chunks

class Environment(object):
    """
    Environment module for ACT-R. Shows whatever is seen on screen at the moment, allows interaction with ACT-R model (vision and motor modules).
    """

    Event = utilities.Event
    _ENV = utilities._ENV

    def __init__(self, size=(640, 360), simulated_display_resolution=(1366, 768), simulated_screen_size=(50, 28), viewing_distance=50, focus_position=None):
        self.gui = True
        self.size = size
        if focus_position and len(focus_position) != 2:
            raise utilities.ACTRError("Focus position of the environemnt must be an iterable with 2 values.")
        if not focus_position:
            focus_position = (size[0]/2, size[1]/2)
        
        self.current_focus = list(focus_position)

        self.stimuli = None
        self.triggers = None
        self.times = None
        
        #below - used for interaction with vision and motor
        self.stimulus = None
        self.trigger = None
        self.simulated_display_resolution = simulated_display_resolution
        self.simulated_screen_size = simulated_screen_size
        self.viewing_distance = viewing_distance

    def roundtime(self, time):
        """
        Returns rounded time.
        """
        return utilities.roundtime(time)

    def environment_process(self, stimuli=None, triggers=None, times=1, start_time=0):
        """
        Example of environment process. Text appears, changes/disappers after run_time runs out.
        """
        #make all arguments iterables if they are not yet
        if isinstance(stimuli, str) or isinstance(stimuli, collections.Mapping) or not isinstance(stimuli, collections.Iterable):
            stimuli = [stimuli]
        for idx in range(len(stimuli)):
            if isinstance(stimuli[idx], collections.Mapping):
                for each in stimuli[idx]:
                    if not isinstance(stimuli[idx][each], collections.Mapping): #stimuli[idx][each] encodes position etc.
                        raise utilities.ACTRError("Arguments of stimuli, if any, must be dictionaries, e.g.,: [{'stimulus1-0time': {'text': 'hi', 'position': (0, 0)}, 'stimulus2-0time': {'text': 'you', 'position': (10, 10)}}, {'stimulus3-latertime': {'text': 'new', 'position': (0, 0)}}] etc. Currently, you have this: '%s'" %stimuli[idx])
            else:
                stimuli[idx] = {stimuli[idx]: {'position': (320, 180)}} #default position - 0,0
        if isinstance(triggers, str) or not isinstance(triggers, collections.Iterable):
            triggers = [triggers]
        if isinstance(times, str) or not isinstance(times, collections.Iterable):
            times = [times]
        #sanity checks - each arg must match in length, or an argument must be of length 1 (2 for positions)
        if len(stimuli) != len(triggers):
            if len(stimuli) == 1:
                stimuli = stimuli * len(triggers)
            elif len(triggers) == 1:
                triggers = triggers * len(stimuli)
            else:
                raise utilities.ACTRError("In environment, stimuli must be the same length as triggers or one of the two must be of length 1")
        if len(stimuli) != len(times):
            if len(times) == 1:
                times = times * len(stimuli)
            else:
                raise utilities.ACTRError("In environment, times must be the same length as stimuli or times must be of length 1")
        self.stimuli = stimuli
        try:
            self.triggers = [x.upper() for x in triggers]
        except AttributeError:
            raise utilities.ACTRError("Triggers are not strings; currently nothing else than strings are allowed as triggers in environment")
        self.times = times
        time = start_time
        yield self.Event(self.roundtime(time), self._ENV, "STARTING ENVIRONMENT") #yield Event; Event has three positions - time, process, in this case, ENVIRONMENT (specified in self._ENV) and description of action
        for idx, stimulus in enumerate(self.stimuli): #run through elems, print them, yield a corresponding event
            self.run_time = self.times[idx] #current run_time
            time = time + self.run_time
            self.trigger = self.triggers[idx] #current trigger
            self.output(stimulus) #output on environment
            yield self.Event(self.roundtime(time), self._ENV, "PRINTED NEW STIMULUS")

    def output(self, stimulus):
        """
        Outputs obj in environment.
        """
        self.stimulus = stimulus
        #this part is visual re-encoding - encode new info in your current focus
        #TODO - check that the new stimulus is different from the last one; do stuffing visuallocation

        if not self.gui:
            print("****Environment:", self.stimulus)

