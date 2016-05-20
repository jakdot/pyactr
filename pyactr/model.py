"""
ACT-R Model.
"""

import simpy
import warnings

import pyactr.chunks as chunks
import pyactr.goals as goals
import pyactr.productions as productions
import pyactr.declarative as declarative
import pyactr.motor as motor
import pyactr.vision as vision
from pyactr.utilities import ACTRError

class ACTRModel(object):
    """
    ACT-R model, running ACT-R simulations.
    """

    def __init__(self, environment=None, **kwargs):

        self.chunktype = chunks.chunktype
        self.Chunk = chunks.Chunk
        self.DecMem = declarative.DecMem
        self.__DMBuffers = {}
        self.__Goals = {}
        self._VisBuffers = {}
        self.__Productions = {}
        self.__Similarities = {}

        self.__interruptibles = {} #interruptible processes

        self.model_parameters = kwargs

        self.__env = environment

        #simulation values, accesible by user

        self.current_event = None

    def __printevent__(self, event):
        """
        Stores current event in self.current_event and prints event.
        """
        if event.action != self.__pr._UNKNOWN:
            self.current_event = event
            if self.__trace:
                print(event[0:3])
    
    def __printenv__(self, event, suppressed=True):
        """
        Prints environment event. By default, suppressed.
        """
        if event.action != self.__pr._UNKNOWN and not suppressed:
            print(event[0:3])
                
    def __activate__(self, event):
        """
        Triggers proc_activate, needed to activate procedural process.
        """
        if event.action != self.__pr._UNKNOWN and event.proc != self.__pr._PROCEDURAL:
            if not self.__proc_activate.triggered:
                self.__proc_activate.succeed()

    def __localprocess__(self, name, generator):
        """
        Triggers local process. name is the name of module. generator must only yield Events.
        """
        while True:
            event = next(generator)
            try:
                yield self.__simulation.timeout(event.time-self.__simulation.now)
            except simpy.Interrupt:
                break
            else:
                self.__printevent__(event)
                self.__activate__(event)
            try:
                if self.__env.trigger in self.__pr.env_interaction:
                    self.__environment_activate.succeed(value=tuple((self.__env.trigger, self.__pr.env_interaction)))
                self.__pr.env_interaction = set()
            except AttributeError:
                pass

    def __procprocessGenerator__(self):
        """
        Creates simulation process for procedural rules.
        """
        pro = self.__simulation.process(self.__localprocess__(self.__pr._PROCEDURAL, self.__pr.procedural_process(self.__simulation.now))) #create procedural process
        self.__procs_started = yield pro #run the process, keep its return value
        while True:

            try:
                self.__procs_started.remove(self.__pr._PROCEDURAL)
            except ValueError:
                yield self.__proc_activate #wait for proc_activate
            else:
                for proc in self.__procs_started:
                    name = proc[0]
                    if not self.__dict_extra_proc_activate[name].triggered:
                        if proc[1].__name__ in self.__pr._INTERRUPTIBLE:
                            self.__interruptibles[name] = proc[1] #add new process interruptibles if the process can be interrupted according to ACT-R
                        self.__dict_extra_proc_activate[name].succeed() #activate modules that were used if not active
                    else:
                        if name in self.__interruptibles and proc[1] != self.__interruptibles[name]:
                            self.__interruptibles[name] = proc[1]
                            self.__dict_extra_proc[name].interrupt() #otherwise, interrupt them
            for _ in range(3):
                yield self.__simulation.timeout(0) #move procedural process to the bottom; right now, this is a hack - it yields 0 timeout three times, so other processes get enough cycles to start etc.
            pro = self.__simulation.process(self.__localprocess__(self.__pr._PROCEDURAL, self.__pr.procedural_process(self.__simulation.now)))
            self.__procs_started = yield pro
            self.__proc_activate = self.__simulation.event() #start the event

    def __extraprocessGenerator__(self, name):
        """
        Creates simulation process for other rules.
        """
        while True:
            try:
                _ , proc = next(filter(lambda x:x[0] == name, self.__procs_started))
            except StopIteration:
                if name in self.__interruptibles:
                    self.__interruptibles.pop(name) #remove this process from interruptibles since it's finished
                yield self.__dict_extra_proc_activate[name]
                self.__dict_extra_proc_activate[name] = self.__simulation.event()
            else:
                self.__procs_started.remove((name, proc))
                if not self.__dict_extra_proc_activate[name].triggered:
                    self.__dict_extra_proc_activate[name].succeed() #activate modules that were used
                pro = self.__simulation.process(self.__localprocess__(name, proc))

                try:
                    cont = yield pro
                except simpy.Interrupt:
                    if not pro.triggered:
                        warnings.warn("Process in %s interupted" % name)
                        pro.interrupt() #interrupt process

                #if first extra process is followed by another process (returned as cont), do what follows; used only for motor
                else:
                    if cont:
                        pro = self.__simulation.process(self.__localprocess__(name, cont))
                        try:
                            yield pro
                        except simpy.Interrupt:
                            pass

    def __envprocess__(self, event):
        """
        Runs local environment process.
        """
        try:
            yield self.__simulation.timeout(event.time-self.__simulation.now)
        except simpy.Interrupt:
            pass
        else:
            self.__printenv__(event)
        finally:
            self.__activate__(event)

    def __envGenerator__(self, ep, **kwargs):
        """
        Creates simulation process for process in environment.
        """
        generator = ep(**kwargs)
        event = next(generator)
        while True:
            pro = self.__simulation.process(self.__envprocess__(event))
            yield pro | self.__environment_activate
            if self.__environment_activate.triggered:
                expected, triggered = self.__environment_activate.value
                self.__environment_activate = self.__simulation.event()
                pro.interrupt()
            try:
                event = generator.send(self.__simulation.now)
            except StopIteration:
                generator = None
            if not generator:
                break


    def dmBuffer(self, name, declarative_memory, data=None, finst=0):
        """
        Creates and returns declarative memory buffer for ACTRModel.
        """
        dmb = declarative.DecMemBuffer(declarative_memory, data, finst)
        self.__DMBuffers[name] = dmb
        return dmb

    def goal(self, name, data=None, default_harvest=None, set_delay=0):
        """
        Creates and returns goal buffer for ACTRModel.
        """
        g = goals.Goal(data, default_harvest, set_delay)
        self.__Goals[name] = g
        return g
    
    def visualBuffer(self, name, default_harvest=None):
        """
        Creates and returns goal buffer for ACTRModel.
        """
        v = vision.Visual(self.__env, default_harvest)
        self._VisBuffers[name] = v
        return v

    def productions(self, *rules):
        """
        Creates production rules out of functions. One or more functions can be inserted.
        """
        self.__Productions = productions.Productions(*rules)

    def set_similarities(self, chunk, otherchunk, value):
        """
        Sets similarities between chunks. By default, different chunks have the value of -1. This can be changed.
        """
        if value > 0:
            raise ACTRError("Values in similarities must be 0 or smaller than 0")
        self.__Similarities[tuple((chunk, otherchunk))] = value

    def simulation(self, realtime=False, trace=True, environment_process=None, **kwargs):
        """
        Returns a simpy environment whose simulation can be run with run(max_time) command.
        """
        buffers = {name: self.__DMBuffers[name] for name in self.__DMBuffers} #dict of buffers created
        buffers.update(self.__Goals)
        
        decmem = {name: buffers[name].dm for name in buffers if buffers[name].dm != None} #dict of declarative memories used

        if not decmem:
            decmem = {"default_dm": self.DecMem()}

        dict_rules = self.__Productions #dict of production rules used

        buffers["manual"] = motor.Motor() #adding motor buffer
        
        if self.__env:
            if self._VisBuffers:
                buffers.update(self._VisBuffers)
            else:
                dm = next(iter(decmem.values()))
                buffers["visual"] = vision.Visual(self.__env, dm) #adding vision buffer

        self.__pr = productions.ProductionRules(dict_rules, buffers, decmem, self.model_parameters)

        chunks.Chunk._similarities = self.__Similarities

        #creating simulation environment
        
        self.__simulation = simpy.Environment()
        if realtime:
            self.__simulation = simpy.RealtimeEnvironment()

        #setting trace

        self.__trace = trace

        self.__dict_extra_proc = {key: None for key in buffers}

        self.__simulation.process(self.__procprocessGenerator__())

        self.__dict_extra_proc_activate = {}

        for each in self.__dict_extra_proc:
            if each != self.__pr._PROCEDURAL:
                self.__dict_extra_proc[each] = self.__simulation.process(self.__extraprocessGenerator__(each)) #create simulation processes for all buffers, store them in dict_extra_proc
                self.__dict_extra_proc_activate[each] = self.__simulation.event() #create simulation events for all buffers that control simulation flow (they work as locks)
        
        self.__proc_activate = self.__simulation.event() #special event (lock) for procedural module
        
        self.__procs_started = [] #list of processes that are started as a result of production rules

        #activate environment process, if environment present
        if self.__env:
            self.__proc_environment = self.__simulation.process(self.__envGenerator__(ep=environment_process, **kwargs))
            self.__environment_activate = self.__simulation.event()
        
        return self.__simulation

    def show_time(self):
        """
        Returns current time in simulation.
        """
        try:
            t = self.__simulation.now
        except AttributeError:
            raise AttributeError("No simulation is running")
        else:
            return t

