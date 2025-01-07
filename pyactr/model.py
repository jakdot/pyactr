"""
ACT-R Model.
"""

import pyparsing

from pyactr import chunks, declarative, goals, motor, productions, simulation, utilities, vision

class ACTRModel:
    """
    ACT-R model, running ACT-R simulations.

    model_parameters and their default values are:
    {"subsymbolic": False,
    "rule_firing": 0.05,
    "latency_factor": 0.1,
    "latency_exponent": 1.0,
    "decay": 0.5,
    "baselevel_learning": True,
    "optimized_learning": False,
    "instantaneous_noise" : 0,
    "retrieval_threshold" : 0,
    "buffer_spreading_activation" : {},
    "spreading_activation_restricted" : False,
    "strength_of_association": 0,
    "association_only_from_chunks": True,
    "partial_matching": False,
    "mismatch_penalty": 1,
    "activation_trace": False,
    "utility_noise": 0,
    "utility_learning": False,
    "utility_alpha": 0.2,
    "motor_prepared": False,
    "strict_harvesting": False,
    "production_compilation": False,
    "automatic_visual_search": True,
    "emma": True,
    "emma_noise": True,
    "emma_landing_site_noise": False,
    "eye_mvt_angle_parameter": 1,
    "eye_mvt_scaling_parameter": 0.01
    }

    environment has to be an instantiation of the class Environment.
    """

    MODEL_PARAMETERS = {"subsymbolic": False,
                "rule_firing": 0.05,
                "latency_factor": 0.1,
                "latency_exponent": 1.0,
                "decay": 0.5,
                "baselevel_learning": True,
                "optimized_learning": False,
                "instantaneous_noise" : 0,
                "retrieval_threshold" : 0,
                "buffer_spreading_activation" : {},
                "spreading_activation_restricted" : False,
                "strength_of_association": 0,
                "association_only_from_chunks": True,
                "partial_matching": False,
                "mismatch_penalty": 1,
                "activation_trace": False,
                "utility_noise": 0,
                "utility_learning": False,
                "utility_alpha": 0.2,
                "motor_prepared": False,
                "strict_harvesting": False,
                "production_compilation": False,
                "automatic_visual_search": True,
                "emma": True,
                "emma_noise": True,
                "emma_landing_site_noise": False,
                "eye_mvt_angle_parameter": 1, #in LispACT-R: 1
                "eye_mvt_scaling_parameter": 0.01, #in LispACT-R: 0.01, but dft rule firing -- 0.01
                }

    def __init__(self, environment=None, **model_parameters):

        self.chunktype = chunks.chunktype
        self.chunkstring = chunks.chunkstring

        self.visbuffers = {}

        start_goal = goals.Goal()
        self.goals = {"g": start_goal}

        self.__buffers = {"g": start_goal}

        start_retrieval = declarative.DecMemBuffer()
        self.retrievals = {"retrieval": start_retrieval}
        
        self.__buffers["retrieval"] = start_retrieval
        
        start_dm = declarative.DecMem()
        self.decmems = {"decmem": start_dm}

        self.productions = productions.Productions()
        self.__similarities = {}

        self.model_parameters = self.MODEL_PARAMETERS.copy()

        try:
            if not set(model_parameters.keys()).issubset(set(self.MODEL_PARAMETERS.keys())):
                params = set(model_parameters.keys()).difference(set(self.MODEL_PARAMETERS.keys()))
                allowed_params = set(self.MODEL_PARAMETERS.keys())
                raise utilities.ACTRError(f"Incorrect model parameter(s) {params}. The only possible model parameters are: '{allowed_params}'")
            self.model_parameters.update(model_parameters)
        except TypeError:
            pass

        self.__env = environment
    
    @property
    def retrieval(self):
        """
        Retrieval in the model.
        """
        if len(self.retrievals) == 1:
            return list(self.retrievals.values())[0]

        raise ValueError("Zero or more than 1 retrieval specified, unclear which one should be shown. Use ACTRModel.retrievals instead.")

    @retrieval.setter
    def retrieval(self, name):
        self.set_retrieval(name)

    @property
    def decmem(self):
        """
        Declarative memory in the model.
        """
        if len(self.decmems) == 1:
            return list(self.decmems.values())[0]

        raise ValueError("Zero or more than 1 declarative memory specified, unclear which one should be shown. Use ACTRModel.decmems instead.")
    
    @decmem.setter
    def decmem(self, data):
        self.set_decmem(data)

    def set_decmem(self, data=None):
        """
        Set declarative memory.
        """
        dm = declarative.DecMem(data)
        if len(self.decmems) > 1:
            self.decmems["".join(["decmem", str(len(self.decmems))])] = dm
        else:
            self.decmems["decmem"] = dm
        return dm

    @property
    def goal(self):
        """
        Goal buffer in the model.
        """
        if len(self.goals) == 1:
            return list(self.goals.values())[0]
        else:
            raise ValueError("Zero or more than 1 goal specified, unclear which one should be shown. Use ACTRModel.goals instead.")
    
    @goal.setter
    def goal(self, name):
        self.set_goal(name, 0)

    def set_retrieval(self, name):
        """
        Set retrieval.

        name: the name by which the retrieval buffer is referred to in production rules.
        """
        if not isinstance(name, str):
            raise ValueError("Retrieval buffer can be only set with a string, the name of the retrieval buffer.")
        dmb = declarative.DecMemBuffer()
        self.__buffers[name] = dmb
        self.retrievals[name] = dmb
        return dmb

    def set_goal(self, name, delay=0):
        """
        Set goal buffer. delay specifies the delay of setting a chunk in the buffer.

        name: the name by which the goal buffer is referred to in production rules.
        """
        if not isinstance(name, str):
            raise ValueError("Goal buffer can be only set with a string, the name of the goal buffer.")
        g = goals.Goal(delay=delay)
        self.__buffers[name] = g
        self.goals[name] = g
        return g

    def visualBuffer(self, name_visual, name_visual_location, default_harvest=None, finst=4):
        """
        Create visual buffers for ACTRModel. Two buffers are present in vision: visual What buffer, called just visual buffer (encoding seen objects) and visual Where buffer, called visual_location buffer (encoding positions). Both are created and returned. Finst is relevant only for the visual location buffer.

        name_visual: the name by which the visual buffer isreferred to in production rules.
        name_visual_location: the name by which the visual_location buffer is referred to in production rules.

        """
        v1 = vision.Visual(self.__env, default_harvest)
        v2 = vision.VisualLocation(self.__env, default_harvest, finst)
        self.visbuffers[name_visual] = v1
        self.visbuffers[name_visual_location] = v2
        return v1, v2

    def set_productions(self, *rules):
        """
        Creates production rules out of functions. One or more functions can be inserted.
        """
        self.productions = productions.Productions(*rules)
        return self.productions

    def productionstring(self, name='', string='', utility=0, reward=None):
        """
        Create a production rule when given a string. The string is specified in the following form (as a string): LHS ==> RHS
        
        name: name of the production rule
        string: string specifying the production rule
        utility: utility of the rule (default: 0)
        reward: reward of the rule (default: None)

        The following example would be a rule that checks the buffer 'g' and if the buffer has value one, it will reset it to two:
        >>> ACTRModel().productionstring(name='example0', string='=g>\
                isa example\
                value one\
                ==>\
                =g>\
                isa example\
                value two')
        {'=g': example(value= one)}
        ==>
        {'=g': example(value= two)}
        """
        if not name:
            name = "unnamedrule" + productions.Productions._undefinedrulecounter
            productions.Productions._undefinedrulecounter += 1
        temp_dictRHS = {v: k for k, v in utilities._RHSCONVENTIONS.items()}
        temp_dictLHS = {v: k for k, v in utilities._LHSCONVENTIONS.items()}
        rule_reader = utilities.getrule()
        try:
            rule = rule_reader.parse_string(string, parse_all=True)
        except pyparsing.ParseException as e:
            raise utilities.ACTRError(f"The rule '{name}' could not be parsed. The following error was observed: {e}")
        lhs, rhs = {}, {}
        def func():
            for each in rule[0]:
                if each[0] == temp_dictLHS["query"]:
                    lhs[each[0]+each[1]] = {x[0]:x[1] for x in each[3]}
                else:
                    try:
                        type_chunk, chunk_dict = chunks.createchunkdict(each[3])
                    except utilities.ACTRError as e:
                        raise utilities.ACTRError(f"The rule string {name} is not defined correctly; {e}")
                    lhs[each[0]+each[1]] = chunks.makechunk("", type_chunk, **chunk_dict)
            yield lhs
            for each in rule[2]:
                if each[0] == temp_dictRHS["extra_test"]:
                    rhs[each[0]+each[1]] = {x[0]:x[1] for x in each[3]}
                elif each[0] == temp_dictRHS["clear"]:
                    rhs[each[0]+each[1]] = None
                elif each[0] == temp_dictRHS["execute"]:
                    rhs[each[0]+each[1]] = each[3]
                else:
                    try:
                        type_chunk, chunk_dict = chunks.createchunkdict(each[3])
                    except utilities.ACTRError as e:
                        raise utilities.ACTRError(f"The rule string {name} is not defined correctly; {e}")
                    rhs[each[0]+each[1]] = chunks.makechunk("", type_chunk, **chunk_dict)
            yield rhs
        self.productions.update({name: {"rule": func, "utility": utility, "reward": reward}})
        return self.productions[name]

    def set_similarities(self, chunk, otherchunk, value):
        """
        Set similarities between chunks. By default, different chunks have the value of -1.

        chunk and otherchunk are two chunks whose similarities are set. value must be a non-positive number.
        """
        if value > 0:
            raise utilities.ACTRError("Values in similarities must be 0 or smaller than 0")
        self.__similarities[tuple((chunk, otherchunk))] = value
        self.__similarities[tuple((otherchunk, chunk))] = value

    def simulation(self, realtime=False, trace=True, gui=True, initial_time=0, environment_process=None, **kwargs):
        """
        Prepare simulation of the model

        This does not run the simulation, it only returns the simulation object. The object can then be run using run(max_time) command.

        realtime: should the simulation be run in real time or not?
        trace: should the trace of the simulation be printed?
        gui: should the environment appear on a separate screen? (This requires tkinter.)
        initial_time: what is the starting time point of the simulation?
        environment_process: what environment process should the simulation use?
        The environment_process argument should be supplied with the method environment_process of the environment used in the model.
        kwargs are arguments that environment_process will be supplied with.
        """

        if len(self.decmems) == 1:
            for key in self.__buffers:
                self.__buffers[key].dm = self.decmem #if only one dm, let all buffers use it
        elif len([x for x in self.decmems.values() if x]) == 1:
            for key in self.__buffers:
                if not self.__buffers[key].dm:
                    self.__buffers[key].dm = self.decmem #if only one non-trivial dm, let buffers use it that do not have a dm specified

        decmem = {name: self.__buffers[name].dm for name in self.__buffers\
                if self.__buffers[name].dm != None} #dict of declarative memories used; more than 1 decmem might appear here

        self.__buffers["manual"] = motor.Motor() #adding motor buffer

        if self.__env:
            self.__env.initial_time = initial_time #set the initial time of the environment to be the same as simulation
            if self.visbuffers:
                self.__buffers.update(self.visbuffers)
            else:
                dm = list(decmem.values())[0]
                self.__buffers["visual"] = vision.Visual(self.__env, dm) #adding vision buffers
                self.__buffers["visual_location"] = vision.VisualLocation(self.__env, dm) #adding vision buffers
        
        self.productions.used_rulenames = {} # remove any previously stored rules for utility learning

        used_productions = productions.ProductionRules(self.productions, self.__buffers, decmem, self.model_parameters)

        chunks.Chunk._similarities = self.__similarities

        return simulation.Simulation(self.__env, realtime, trace, gui, self.__buffers, used_productions, initial_time, environment_process, **kwargs)
