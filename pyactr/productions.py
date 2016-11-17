"""
Production rules.
"""

import collections
import inspect

import pyactr.declarative as declarative
import pyactr.chunks as chunks
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
            try:    
                utility_position = len(inspect.getargspec(rule).args)-inspect.getargspec(rule).args.index('utility')
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

        self.model_parameters = model_parameters


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
            
            if not self.LHStest(pro):
                yield Event(roundtime(time), self._PROCEDURAL, 'RULE STOPPED FROM FIRING: %s' % used_rulename)
            else:
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

            updated.state = updated._BUSY

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
        tested.state = tested._BUSY
        self.extra_tests[name] = test
        tested.state = tested._FREE
        yield Event(roundtime(time), name, "EXTRA TEST ADDED")

    def clear(self, name, cleared, optional, temp_actrvariables, time, freeing=True):
        """
        Clears a buffer. The 'freeing' argument specifies whether the state should be considered FREE (if the rule is run alone) or not (if it is embedded in another rule).
        """
        cleared.state = cleared._BUSY
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
        if freeing:
            cleared.state = cleared._FREE


    def execute(self, name, executed, executecommand, temp_actrvariables, time):
        """
        Executes a command.
        """
        executed.state = executed._BUSY
        try:
            getattr(executed, executecommand[0])(*executecommand[1])
        except TypeError:
            getattr(executed, executecommand[0])(executecommand[1])
        executed.state = executed._FREE
        yield Event(roundtime(time), name, "EXECUTED")

    def modify(self, name, modified, otherchunk, temp_actrvariables, time):
        """
        Modifies a buffer chunk.
        """
        modified.state = modified._BUSY
        modified.modify(otherchunk, temp_actrvariables) #time variable is currently not used - needed if modification would cost time
        modified.state = modified._FREE
        yield Event(roundtime(time), name, "MODIFIED")

    def modify_request(self, name, modified, otherchunk, temp_actrvariables, time):
        """
        Modifies a buffer chunk.
        """
        modified.state = modified._BUSY
        extra_time = utilities.calculate_setting_time(updated, self.model_parameters)
        time += extra_time
        yield Event(roundtime(time), name, self._UNKNOWN)
        modified.modify(otherchunk, temp_actrvariables)
        modified.state = modifed._FREE
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

    def visualencode(self, name, visualbuffer, chunk, temp_actrvariables, time, extra_time):
        """
        Encodes visual object.
        """
        visualbuffer.state = visualbuffer._BUSY
        time += extra_time
        yield from self.clear(name, visualbuffer, None, temp_actrvariables, time, freeing=False)
        visualbuffer.add(chunk, time)
        visualbuffer.state = visualbuffer._FREE
        yield Event(roundtime(time), name, "ENCODED VIS OBJECT:'%s'" %chunk) 

    def retrieveorset(self, name, updated, otherchunk, temp_actrvariables, time):
        """
        Decides whether a buffer should be set (for buffers that are not attached to any dm, i.e., Goal or Motor or Vision) or should trigger retrieval.
        """
        updated.state = updated._BUSY
        if isinstance(updated, goals.Goal):
            yield from self.clear(name, updated, otherchunk, temp_actrvariables, time, freeing=False)
            extra_time = utilities.calculate_setting_time(updated, self.model_parameters)
            time += extra_time
            yield Event(roundtime(time), name, self._UNKNOWN)
            updated.create(otherchunk, list(self.dm.values())[0], temp_actrvariables)
            created_elem = list(updated)[0]
            updated.state = updated._FREE
            yield Event(roundtime(time), name, "CREATED A CHUNK: %s" % created_elem)
        elif isinstance(updated, vision.VisualLocation):
            yield from self.clear(name, updated, None, temp_actrvariables, time, freeing=False)
            extra_time = utilities.calculate_setting_time(updated, self.model_parameters)
            time += extra_time #0 ms to create chunk in location (pop-up effect)
            yield Event(roundtime(time), name, self._UNKNOWN)
            chunk, stim = updated.find(otherchunk, actrvariables=temp_actrvariables, extra_tests=self.extra_tests.get(name, {})) #extra_time currently ignored
            if chunk:
                updated.add(chunk, stim, time)
                updated.state = updated._FREE
            else:
                updated.state = updated._ERROR
            yield Event(roundtime(time), name, "ENCODED LOCATION:'%s'" %chunk) 
        elif isinstance(updated, vision.Visual):
            ret = yield from self.visualshift(name, updated, otherchunk, temp_actrvariables, time)
            return ret #visual action returns value, namely, its continuation method
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

    def automatic_search(self, name, visualbuffer, stim, time):
        """
        Automatic buffering of environment stim in the visual buffer. This is not entered by production rules. Production rules are bypassed, this is called directly by simulation.
        """
        visualbuffer.state = visualbuffer._BUSY
        newchunk = None
        if self.model_parameters["automatic_visual_search"]:
            newchunk, stim = visualbuffer.automatic_search(stim)
        if newchunk:
            if visualbuffer:
                visualbuffer.modify(newchunk, stim)
            else:
                visualbuffer.add(newchunk, stim, time)
            yield Event(roundtime(time), name, 'ENCODED LOCATION: %s' %newchunk)
        else:
            yield Event(roundtime(time), name, self._UNKNOWN)

    def automatic_buffering(self, name, visualbuffer, stim, time):
        """
        Automatic buffering of environment stim in the visual buffer. This is not entered by production rules. Production rules are bypassed, this is called directly by simulation.
        """
        visualbuffer.state = visualbuffer._BUSY
        foveal_distance = utilities.calculate_distance(1, visualbuffer.environment.size, visualbuffer.environment.simulated_screen_size, visualbuffer.environment.viewing_distance)
        cf = tuple(visualbuffer.current_focus)
        newchunk = None
        encoding = 0
        for st in stim:
            if st['position'][0] > cf[0]-foveal_distance and st['position'][0] < cf[0]+foveal_distance and st['position'][1] > cf[1]-foveal_distance and st['position'][1] < cf[1]+foveal_distance:
                newchunk, encoding = visualbuffer.automatic_buffering(st, self.model_parameters)
        time += encoding
        yield Event(roundtime(time), name, self._UNKNOWN)
        visualbuffer.state = visualbuffer._FREE
        if newchunk:
            if visualbuffer:
                visualbuffer.modify(newchunk)
            else:
                visualbuffer.add(newchunk, time)
            yield Event(roundtime(time), name, 'AUTOMATIC BUFFERING: %s' %newchunk)

    def visualshift(self, name, visualbuffer, otherchunk, temp_actrvariables, time):
        """
        Carries out preparation of visual shift.
        """
        newchunk, extra_time, site = visualbuffer.shift(otherchunk, actrvariables=temp_actrvariables, model_parameters = self.model_parameters)

        encoding = extra_time[0]
        preparation = extra_time[1]
        execution = extra_time[2]

        visualbuffer.preparation = visualbuffer._BUSY
        visualbuffer.processor = visualbuffer._BUSY
        visualbuffer.state = visualbuffer._BUSY
        
        yield Event(roundtime(time), name, 'PREPARATION TO SHIFT VISUAL ATTENTION STARTED')

        if encoding <= preparation:
            yield from self.visualencode(name, visualbuffer, newchunk, temp_actrvariables, time, encoding)

        time += preparation
        
        yield Event(roundtime(time), name, 'PREPARATION TO SHIFT VISUAL ATTENTION COMPLETED')
        
        if encoding > preparation and encoding <= preparation+execution:
            yield from self.visualencode(name, visualbuffer, newchunk, temp_actrvariables, time-preparation, encoding)

        return self.visualcontinue(name, visualbuffer, newchunk, temp_actrvariables, time, extra_time, site)

    def visualcontinue(self, name, visualbuffer, otherchunk, temp_actrvariables, time, extra_time, landing_site):
        """
        Carries out the rest of visual shift. Shift is split in two because of EMMA assumption that the two parts can act independently of each other.
        """
        visualbuffer.preparation = visualbuffer._FREE
        visualbuffer.execution = visualbuffer._BUSY
        if visualbuffer.last_mvt > time:
            time = visualbuffer.last_mvt # if another move is executed, wait for that to finish before starting mvt execution

        encoding = extra_time[0]
        preparation = extra_time[1]
        execution = extra_time[2]
        
        visualbuffer.last_mvt = time + execution

        time += execution

        yield Event(roundtime(time), name, self._UNKNOWN)
        visualbuffer.move_eye(landing_site)
        yield Event(roundtime(time), name, 'SHIFT COMPLETE TO POSITION: %s' %visualbuffer.current_focus)
        if encoding > preparation+execution:
            newchunk, extra_time, _ = visualbuffer.shift(otherchunk, actrvariables=temp_actrvariables, model_parameters = self.model_parameters)
            yield from self.visualencode(name, visualbuffer, otherchunk, temp_actrvariables, time, (1-((preparation+execution)/encoding))*extra_time[0])
        visualbuffer.processor = visualbuffer._FREE
        visualbuffer.execution = visualbuffer._FREE

    def motorset(self, name, motorbuffer, otherchunk, temp_actrvariables, time):
        """
        Carries out preparation of motor action. 
        """
        newchunk = motorbuffer.create(otherchunk, temp_actrvariables)

        time_presses = None #used for time stamps of 4 phases of motor
        for elem in motorbuffer.TIME_PRESSES.keys():
            if newchunk.key in elem:
                time_presses = motorbuffer.TIME_PRESSES[elem]
        if not time_presses:
            time_presses = motorbuffer.TIME_PRESSES[()] #if not pressing or slowest, use default (short mvt)
        preparation = time_presses[0]

        #preparation can be modified if previous key was the same or similar -- see if-clauses below
        if newchunk.key == motorbuffer.last_key[0] or self.model_parameters["motor_prepared"]:
            self.model_parameters["motor_prepared"] = False #motor_prepared is only used for the 1st key press
            preparation = 0
        elif motorbuffer.last_key[0] and (newchunk.key in motorbuffer.PRESSING) == (motorbuffer.last_key[0] in motorbuffer.PRESSING):
            if (newchunk.key in motorbuffer.LEFT_HAND) == (motorbuffer.last_key[0] in motorbuffer.LEFT_HAND): 
                preparation -= 0.1 #the same hand, same mvt cuts down by 100 ms; Lisp ACT-R also has the same finger which cuts down by 150 ms; this is not currently implemented
            else:
                preparation -= 0.05 #a different hand, same mvt cuts down by 50 ms

        motorbuffer.state = motorbuffer._BUSY
        motorbuffer.preparation = motorbuffer._BUSY
        motorbuffer.processor = motorbuffer._BUSY

        yield Event(roundtime(time), name, 'COMMAND: %s' % newchunk.cmd)
        time += preparation
        
        yield Event(roundtime(time), name, 'PREPARATION COMPLETE')

        return self.motorcontinue(name, motorbuffer, newchunk, temp_actrvariables, time, time_presses)

    def motorcontinue(self, name, motorbuffer, otherchunk, temp_actrvariables, time, time_presses):
        """
        Carries out the rest of motor action. Motor action is split in two because of ACT-R assumption that the two parts can act independently of each other.
        """
        if motorbuffer.last_key[1]:
            time = motorbuffer.last_key[1] # if something else is being pressed, wait for that to finish before starting initializing etc.
        initiation = time_presses[1]
        execution = time_presses[2]
        movement_finish = time_presses[3]
        
        motorbuffer.preparation = motorbuffer._FREE
        motorbuffer.execution = motorbuffer._BUSY
        motorbuffer.last_key[0] = otherchunk.key
        
        time += initiation
        
        motorbuffer.last_key[1] = time + execution + movement_finish
        
        yield Event(roundtime(time), name, 'INITIATION COMPLETE')
        
        motorbuffer.processor = motorbuffer._FREE
        
        time += execution
        yield Event(roundtime(time), name, self._UNKNOWN)
        
        self.env_interaction.add(otherchunk.key)

        yield Event(roundtime(time), name, 'KEY PRESSED: %s' % otherchunk.key)
        
        time += movement_finish

        yield Event(roundtime(time), name, 'MOVEMENT FINISHED')
        
        self.env_interaction.discard(otherchunk.key)
        motorbuffer.state = motorbuffer._FREE
        motorbuffer.execution = motorbuffer._FREE
        motorbuffer.last_key[1] = 0

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

