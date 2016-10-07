"""
Production rules.
"""

import collections
import inspect

import pyactr.declarative as declarative
import pyactr.goals as goals
import pyactr.vision as vision
import pyactr.motor as motor
import pyactr.utilities as utilities
from pyactr.utilities import ACTRError

Event = utilities.Event

roundtime = utilities.roundtime

class Productions(collections.UserDict):
    """
    Production rules.
    """
    
    __rules_info = collections.namedtuple("rules_info", "rule utility reward selecting_time")

    _undefinedrulecounter = 0
        
    def __init__(self, *rules):
        self._rules = {}
        for rule in rules:
            print(rule)
            try:    
                utility_position = len(inspect.getargspec(rule).args)-inspect.getargspec(rule).args.index('utility')
                print(inspect.getargspec(rule).args)
            except ValueError:
                utility = 0
            else:
                utility = inspect.getargspec(rule).defaults[0-utility_position]
            try:    
                reward_position = len(inspect.getargspec(rule).args)-inspect.getargspec(rule).args.index('reward')
            except ValueError:
                reward = None
            else:
                reward = inspect.getargspec(rule).defaults[0-reward_position]
            self.update({rule.__name__: {"rule": rule, "utility": utility, "reward": reward}})

    def __contains__(self, elem):
        return elem in self._rules

    def __iter__(self):
        for elem in self._rules:
            yield elem

    def __len__(self):
        return len(self._rules)

    def __getitem__(self, key):
        return self._rules[key]
    
    def __delitem__(self, key):
        del self._rules[key]

    def __repr__(self):
        txt = ''
        for rulename in self._rules:
            production = self[rulename]["rule"]()
            utility = self[rulename]["utility"]
            reward = self[rulename]["reward"]
            txt += rulename + ":\n" '{}\n==>\n{}\n'.format(next(production), next(production))
            if utility:
                txt += "Utility: {}\n".format(utility)
            if reward:
                txt += "Reward: {}\n".format(reward)
        return txt

    def __setitem__(self, key, value):
        if isinstance(value, collections.MutableMapping):
            self._rules[key] = {"rule": value["rule"], "utility": value.get("utility", 0), "reward": value.get("reward", None), "selecting_time": value.get("selecting_time", [])}
        else:
            self._rules[key] = {"rule": value, "utility": 0, "reward": 0, "selecting_time": []}



class ProductionRules(object):
    """
    Production knowledge.
    """

    _UNKNOWN = utilities._UNKNOWN
    _PROCEDURAL = utilities._PROCEDURAL
    _EMPTY = utilities._EMPTY
    _RHSCONVENTIONS = utilities._RHSCONVENTIONS
    _LHSCONVENTIONS = utilities._LHSCONVENTIONS
    _INTERRUPTIBLE = utilities._INTERRUPTIBLE

    def __init__(self, rules, buffers, dm, model_parameters = None):
        self.__actrvariables = {} #variables in a fired rule
        self.rules = rules #dict of production rules
        
        self.buffers = buffers #dict of buffers

        self.procs = [] #list of active processes

        self.extra_tests = {}
        
        self.dm = dm #list of (submodules of) memories

        self.env_interaction = set() #set interacting with environment (pressed keys)

        self.model_parameters = {"subsymbolic": False,
                "rule_firing": 0.05,
                "latency_factor": 0.1,
                "decay": 0.5,
                "baselevel_learning": True,
                "instantaneous_noise" : 0,
                "retrieval_threshold" : 0,
                "buffer_spreading_activation" : {},
                "strength_of_association": 0,
                "partial_matching": False,
                "activation_trace": False,
                "utility_noise": 0,
                "utility_learning": False,
                "utility_alpha": 0.2,
                "motor_preparation": 0.25,
                "motor_initiation": 0.05, #default
                "motor_execution": 0.1, #taken form LispACT-R ex. for pressing a key
                "motor_finish": 0.1, #taken from an example for pressing a key
                "strict_harvesting": False
                }
        try:
            assert set(model_parameters.keys()).issubset(set(self.model_parameters.keys())), "Incorrect model parameter(s) %s" % set(model_parameters.keys()).difference(set(self.model_parameters.keys()))
            self.model_parameters.update(model_parameters)
        except TypeError:
            pass


    def procedural_process(self, start_time=0):
        """
        Process that is carrying a production. Proceeds in steps: conflict resolution -> rule selection -> rule firing; or conflict resolution -> no rule found. Start_time specifies when production starts in discrete event simulation.
        """
        time = start_time

        self.procs.append(self._PROCEDURAL,)
        
        self.__actrvariables = {}
        yield Event(roundtime(time), self._PROCEDURAL, 'CONFLICT RESOLUTION')

        max_utility = float("-inf")
        used_rulename = None
        self.used_rulename = None

        for rulename in self.rules:
            self.used_rulename = rulename
            production = self.rules[rulename]["rule"]()
            utility = self.rules[rulename]["utility"]

            pro = next(production)

            if self.model_parameters["subsymbolic"]:
                inst_noise = utilities.calculate_instantanoues_noise(self.model_parameters["utility_noise"])
                utility += inst_noise
            if self.LHStest(pro) and max_utility <= utility:
                max_utility = utility
                used_rulename = rulename
        if used_rulename:
            self.used_rulename = used_rulename
            production = self.rules[used_rulename]["rule"]()
            self.rules[used_rulename]["selecting_time"].append(time)
            
            yield Event(roundtime(time), self._PROCEDURAL, 'RULE SELECTED: %s' % used_rulename)
            time = time + self.model_parameters["rule_firing"]
            yield Event(roundtime(time), self._PROCEDURAL, self._UNKNOWN)

            pro = next(production)

            if self.model_parameters["utility_learning"] and self.rules[used_rulename]["reward"] != None:
                utilities.modify_utilities(time, self.rules[used_rulename]["reward"], self.rules, self.model_parameters)


            yield Event(roundtime(time), self._PROCEDURAL, 'RULE FIRED: %s' % used_rulename)
            yield from self.update(next(production), time)
        else:
            self.procs.remove(self._PROCEDURAL,)
            yield Event(roundtime(time), self._PROCEDURAL, 'NO RULE FOUND')
        return self.procs #returns processes activated by PROCEDURAL

    def update(self, RHSdictionary, time):
        """
        Updates buffers (RHS of production rules).
        """
        temp_actrvariables = dict(self.__actrvariables)
        ordering_dict = {"!": 0, "?": 0, "=": 1, "@": 2, "*": 3, "+": 4, "~": 5}
        try:
            dictionary = collections.OrderedDict.fromkeys(sorted(RHSdictionary, key=lambda x:ordering_dict[x[0]]))
        except KeyError:
            raise ACTRError("The RHS rule '%s' is invalid; every condition in RHS rules must start with one of these signs: %s" % (self.used_rulename, list(self._RHSCONVENTIONS.keys())))
        dictionary.update(RHSdictionary)
        for key in dictionary:
            submodule_name = key[1:] #this is the name of updated submodule
            code = key[0] #this is what the key should do
            
            try:
                temp_actrvariables.pop("=" + submodule_name) #pop used submodule (needed for strict harvesting)
            except KeyError:
                pass
            updated = self.buffers[submodule_name]
            production = getattr(self, self._RHSCONVENTIONS[code])(submodule_name, updated, dictionary[key], self.__actrvariables, time)

            if production.__name__ in self._INTERRUPTIBLE:
                self.procs.append((submodule_name, production)) 
            else:
                yield from production #this either moves production on to modify, retrieve etc. (see RHSCONVENTIONS for the list), or it appends that process to the processes that have to be done as an extra process by model, i.e., not directly by productions (distinction made as in ACT-R)

        #this last part is strict harvesting
        if self.model_parameters["strict_harvesting"]:
            for key in temp_actrvariables:
                submodule_name = key[1:]
                if submodule_name in self.buffers:
                    self.procs.append((submodule_name, self.clear(submodule_name, self.buffers[submodule_name], None, self.__actrvariables, time)))

    def extra_test(self, name, tested, test, temp_actrvariables, time):
        """
        Adding an extra test to a buffer.
        """
        self.extra_tests[name] = test
        yield Event(roundtime(time), name, "EXTRA TEST ADDED")

    def clear(self, name, cleared, optional, temp_actrvariables, time):
        """
        Clears a buffer.
        """
        try:
            cleared.clear(time) #clear the buffer; works for decl. mem. buffers (tied to a specific decl. mem)
        except AttributeError: #unless it fails because the cleared chunk cannot be added anywhere
            if len(self.dm) == 1:
                cleared.clear(time, list(self.dm.values())[0]) #if there is only one memory, add the chunk there
            elif optional:
                    cleared.clear(time, self.dm[optional]) #if not, optional must specify memory where chunk should be added
            else:
                try:
                    cleared.clear(time, self.dm[name]) #if nothing else works, check whether buffer instance was bound to a decl. mem by user
                except KeyError:
                    raise ACTRError("It is not specified to what memory the buffer %s should be cleared" % name)
        yield Event(roundtime(time), name, "CLEARED")


    def execute(self, name, executed, executecommand, temp_actrvariables, time):
        """
        Executes a command.
        """
        try:
            getattr(executed, executecommand[0])(*executecommand[1])
        except TypeError:
            getattr(executed, executecommand[0])(executecommand[1])
        yield Event(roundtime(time), name, "EXECUTED")

    def modify(self, name, modified, otherchunk, temp_actrvariables, time):
        """
        Modifies a buffer chunk.
        """
        modified.modify(otherchunk, temp_actrvariables) #time variable is currently not used - needed if modification would cost time
        yield Event(roundtime(time), name, "MODIFIED")

    def modify_request(self, name, modified, otherchunk, temp_actrvariables, time):
        """
        Modifies a buffer chunk.
        """
        modified.state = modified._BUSY
        extra_time = utilities.calculate_setting_time(updated, self.model_parameters)
        time += extra_time
        yield Event(roundtime(time), name, self._UNKNOWN)
        modified.state = modifed._FREE
        modified.modify(otherchunk, temp_actrvariables)
        yield Event(roundtime(time), name, "MODIFIED")

    def overwrite(self, name, updated, otherchunk, temp_actrvariables, time):
        """
        Overwrites a buffer.
        """
        updated.state = updated._BUSY
        extra_time = utilities.calculate_setting_time(updated, self.model_parameters)
        time += extra_time
        yield Event(roundtime(time), name, self._UNKNOWN)
        updated.create(otherchunk, list(self.dm.values())[0], temp_actrvariables)
        created_elem = list(updated)[0]
        updated.state = updated._FREE
        yield Event(roundtime(time), name, "WROTE A CHUNK: %s" % created_elem)

    def retrieveorset(self, name, updated, otherchunk, temp_actrvariables, time):
        """
        Decides whether a buffer should be set (for buffers that are not attached to any dm, i.e., Goal or Motor or Vision) or should trigger retrieval.
        """
        updated.state = updated._BUSY
        if isinstance(updated, goals.Goal):
            yield from self.clear(name, updated, otherchunk, temp_actrvariables, time)
            extra_time = utilities.calculate_setting_time(updated, self.model_parameters)
            time += extra_time
            yield Event(roundtime(time), name, self._UNKNOWN)
            updated.create(otherchunk, list(self.dm.values())[0], temp_actrvariables)
            created_elem = list(updated)[0]
            updated.state = updated._FREE
            yield Event(roundtime(time), name, "CREATED A CHUNK: %s" % created_elem)
        elif isinstance(updated, vision.Visual) :
            yield from self.clear(name, updated, otherchunk, temp_actrvariables, time)
            extra_time = utilities.calculate_setting_time(updated, self.model_parameters)
            time += 0.05 #50 ms to create chunk in vision
            yield Event(roundtime(time), name, self._UNKNOWN)
            updated.create(otherchunk, list(self.dm.values())[0], temp_actrvariables)
            updated.state = updated._FREE
            yield Event(roundtime(time), name, "ATTENDED TO OBJECT") 
        elif isinstance(updated, motor.Motor):
            ret = yield from self.motorset(name, updated, otherchunk, temp_actrvariables, time)
            return ret #motor action returns value, namely, its continuation method
        else:
            yield from self.retrieve(name, updated, otherchunk, temp_actrvariables, time)

    def retrieve(self, name, retrieval, otherchunk, temp_actrvariables, time):
        """
        Carries out retrieval. 
        """
        #starting process
        yield Event(roundtime(time), name, 'START RETRIEVAL')
        retrieved_elem, extra_time = retrieval.retrieve(time, otherchunk, temp_actrvariables, self.buffers, self.extra_tests.get(name, {}), self.model_parameters)
        time += extra_time
        yield Event(roundtime(time), name, self._UNKNOWN)
        if retrieved_elem:
            retrieval.add(retrieved_elem, time)
            retrieval.state = retrieval._FREE
            yield Event(roundtime(time), name, 'CLEARED')
        else:
            retrieval.state = retrieval._ERROR
        yield Event(roundtime(time), name, 'RETRIEVED: %s' % retrieved_elem)

    def motorset(self, name, motorbuffer, otherchunk, temp_actrvariables, time):
        """
        Carries out preparation of motor action. 
        """
        if self.model_parameters["motor_preparation"]:
            preparation = self.model_parameters["motor_preparation"] #taken from ACT-R example for pressing keys, nothing else implemented (manual, sec. Motor Module)
        else:
            preparation = 0 #if nothing needs to be prepared (i.e., a repeated mvt), preparation defaults to 0
                
        newchunk = motorbuffer.create(otherchunk, temp_actrvariables)

        motorbuffer.state = motorbuffer._BUSY

        yield Event(roundtime(time), name, 'COMMAND: %s' % newchunk.cmd)
        motorbuffer.preparation = motorbuffer._BUSY
        
        time += preparation
        
        yield Event(roundtime(time), name, 'PREPARATION COMPLETE')

        return self.motorcontinue(name, motorbuffer, newchunk, temp_actrvariables, time)

    def motorcontinue(self, name, motorbuffer, otherchunk, temp_actrvariables, time):
        """
        Carries out the rest of motor action. Motor action is split in two because of assumption in ACT-R that the two parts can act independently of each other.
        """
        initiation = self.model_parameters["motor_initiation"] 
        execution = self.model_parameters["motor_execution"] 
        movement_finish = self.model_parameters["motor_finish"] 
        
        motorbuffer.preparation = motorbuffer._FREE
        motorbuffer.processor = motorbuffer._BUSY
        
        time += initiation
        
        yield Event(roundtime(time), name, 'INITIATION COMPLETE')
        motorbuffer.processor = motorbuffer._FREE
        motorbuffer.execution = motorbuffer._BUSY
        
        time += execution

        yield Event(roundtime(time), name, 'KEY PRESSED: %s' % otherchunk.key)
        self.env_interaction.add(otherchunk.key)
        motorbuffer.state = motorbuffer._FREE
        motorbuffer.execution = motorbuffer._FREE
        
        time += movement_finish

        yield Event(roundtime(time), name, 'MOVEMENT FINISHED')
        self.env_interaction.discard(otherchunk.key)

    def LHStest(self, dictionary):
        """
        Tests rules in LHS of production rules.
        """
        temp_actrvariables = dict(self.__actrvariables)
        for key in dictionary:
            submodule_name = key[1:] #this is the module
            code = key[0] #this is what the module should do; standardly, query, i.e., ?, or test, =
            if code not in self._LHSCONVENTIONS:
                raise ACTRError("The LHS rule '%s' is invalid; every condition in LHS rules must start with one of these signs: %s" % (self.used_rulename, list(self._LHSCONVENTIONS.keys())))
            result = getattr(self, self._LHSCONVENTIONS[code])(submodule_name, self.buffers.get(submodule_name), dictionary[key], temp_actrvariables)
            if not result[0]:
                return False
            else:
                temp_actrvariables.update(result[1])
        self.__actrvariables = temp_actrvariables
        return True

    def test(self, submodule_name, tested, testchunk, temp_actrvariables):
        """
        Tests the content of a buffer.
        """
        if not tested:
            return False, None

        for chunk in tested:
            testchunk.boundvars = dict(temp_actrvariables)

            if testchunk <= chunk:
                temp_actrvariables = dict(testchunk.boundvars)
                temp_actrvariables["=" + submodule_name] = list(self.buffers[submodule_name])[0]
                #print("VARS CONSIDERED:", temp_actrvariables) #for debugging
                return True, temp_actrvariables
            else:
                return False, None

    def query(self, submodule_name, tested, testdict, temp_actrvariables):
        """
        Queries a buffer.
        """
        for each in testdict:
            if each == 'buffer' and not tested.test_buffer(testdict.get(each)):
                return False, dict(temp_actrvariables)

            if each != 'buffer' and not tested.test(each, testdict.get(each)):
                return False, dict(temp_actrvariables)

        return True, dict(temp_actrvariables)

