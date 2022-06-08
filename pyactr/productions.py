"""
Production rules.
"""

import collections
import collections.abc
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

#TODO: production compilation -- in ProductionRules - currently slotvals ignore that maybe there was other modification to the buffer in the same RHS of the rule, this should be included

class Production(collections.UserDict):
    """
    Production rule.
    """

    def __init__(self, rule, utility, reward):
        self.rule = {}
        self.rule['rule'] = rule
        self.rule['utility'] = utility
        self.rule['reward'] = reward

        self.utility = utility
        self.reward = reward

    def __contains__(self, elem):
        return elem in self.rule

    def __iter__(self):
        for elem in self.rule:
            yield elem

    def __len__(self):
        return len(self.rule)

    def __getitem__(self, key):
        return self.rule[key]
    
    def __delitem__(self, key):
        del self.rule[key]

    def __repr__(self):
        txt = ''
        production = self["rule"]()
        utility = self["utility"]
        reward = self["reward"]
        txt += '{}\n==>\n{}'.format(next(production), next(production))
        if utility:
            txt += "\nUtility: {}\n".format(utility)
        if reward:
            txt += "Reward: {}\n".format(reward)
        return txt

    def __setitem__(self, key, value):
        assert key in {"rule", "utility", "reward"}, "The production can set only one of four values -- rule, utility, reward; you are using '%s'" %key
        self.rule[key] = value

class Productions(collections.UserDict):
    """
    Production rules.
    """
    
    _undefinedrulecounter = 0

    __DFT_UTILITY = 0
    __DFT_REWARD = None
        
    def __init__(self, *rules):
        self.rules = {}
        for rule in rules:
            try:    
                utility_position = len(inspect.getargspec(rule).args)-inspect.getargspec(rule).args.index('utility')
            except ValueError:
                utility = self.__DFT_UTILITY
            else:
                utility = inspect.getargspec(rule).defaults[0-utility_position]
            try:    
                reward_position = len(inspect.getargspec(rule).args)-inspect.getargspec(rule).args.index('reward')
            except ValueError:
                reward = self.__DFT_REWARD
            else:
                reward = inspect.getargspec(rule).defaults[0-reward_position]
            self.update({rule.__name__: {'rule': rule, 'utility': utility, 'reward': reward}})

        self.used_rulenames = {} #the dictionary of used rulenames, needed for utility learning

    def __contains__(self, elem):
        return elem in self.rules

    def __iter__(self):
        for elem in self.rules:
            yield elem

    def __len__(self):
        return len(self.rules)

    def __getitem__(self, key):
        return self.rules.get(key)
    
    def __delitem__(self, key):
        del self.rules[key]

    def __repr__(self):
        txt = ''
        for rulename in self.rules:
            txt += rulename + '{}\n'.format(self.rules[rulename])
        return txt

    def __setitem__(self, key, value):
        if isinstance(value, collections.abc.MutableMapping):
            self.rules[key] = Production(**value)
        else:
            self.rules[key] = Production(rule=value["rule"], utility=self.__DFT_UTILITY, reward=self.__DFT_REWARD)

    def __collapse__(self, rule1, rule2, slotvals, retrieval):
        """
        Collapses 2 rules into 1.
        """
        def func():
            production1 = rule1['rule']()
            production2 = rule2['rule']()

            pro1 = next(production1).copy()
            pro2 = next(production2).copy()

            for key in pro1:

                code = key[0]
                buff = key[1:]

                #querying just kept
                if utilities._LHSCONVENTIONS[code] == "query":
                    continue

                #here below -- testing
                if key not in pro2:
                    continue

                pro2buff = pro2.pop(key)._asdict()
                
                pro1buff = pro1[key]._asdict()
                
                mod_attr_val = {}

                if buff in slotvals:
                    for slot in pro2buff:
                        try:
                            slotvals_slot = slotvals[buff][slot].removeunused()
                        except (KeyError, AttributeError, TypeError):
                            slotvals_slot = None
                        if not slotvals_slot:
                            varval = utilities.merge_chunkparts(pro1buff[slot], pro2buff[slot])
                            mod_attr_val[slot] = varval
                        else:
                            mod_attr_val[slot] = pro1buff[slot]
                elif buff == retrieval:
                    continue #test on retrieved elem from rule1 in rule2 is removed because no retrieval
                else:
                    for slot in pro2buff:
                        varval = utilities.merge_chunkparts(pro1buff[slot], pro2buff[slot])
                        mod_attr_val[slot] = varval

                new_chunk = chunks.Chunk(pro1[key].typename, **mod_attr_val)
                pro1[key] = new_chunk

            #test on pro2 here below -- buffers might be in pro2 that are missing in pro1
            for key in pro2:
                
                code = key[0]
                buff = key[1:]

                if utilities._LHSCONVENTIONS[code] == "query":
                    temp_production1 = rule1['rule']()
                    _, temp_testing = next(temp_production1), next(temp_production1)
                    for temp_key in temp_testing:
                        if utilities._RHSCONVENTIONS[temp_key[0]] != "modify" and utilities._RHSCONVENTIONS[temp_key[0]] != "extra_test" and temp_key[1:] == buff:
                            break
                    else:
                        pro1.setdefault(key, {}).update(pro2[key])
                    continue

                pro2buff = pro2[key]._asdict()
                
                mod_attr_val = {}
                
                if buff in slotvals:
                    for slot in pro2buff:
                        try:
                            slotvals_slot = slotvals[buff][slot].removeunused()
                        except (KeyError, AttributeError, TypeError):
                            slotvals_slot = None
                        if not slotvals_slot:
                            mod_attr_val[slot] = pro2buff[slot]
                elif buff == retrieval:
                    continue #test on retrieved elem from rule1 in rule2 is removed because no retrieval
                else:
                    mod_attr_val = pro2buff.copy()

                new_chunk = chunks.Chunk(pro2[key].typename, **mod_attr_val)
                pro1[key] = new_chunk

            yield pro1

            pro1 = next(production1).copy()
            pro2 = next(production2).copy()
            
            #anything in pro2 should go into action
            for key in pro2:

                code = key[0]
                buff = key[1:]

                if utilities._RHSCONVENTIONS[code] in {"execute", "clear", "extra_test"}:
                    continue
                
                if buff not in slotvals:
                    continue

                pro1buff = slotvals[buff]
                
                pro2buff = pro2[key]._asdict()

                mod_attr_val = {}
                
                for slot in pro2buff:
                    if pro1buff and slot in pro1buff:
                        varval = utilities.merge_chunkparts(pro2buff[slot], pro1buff[slot])
                        mod_attr_val[slot] = varval
                    else:
                        mod_attr_val[slot] = pro2buff[slot]

                new_chunk = chunks.Chunk(pro2[key].typename, **mod_attr_val)
                pro2[key] = new_chunk

            #actions in pro1 here below -- buffers might be in pro1 that are missing in pro2
            for key in pro1:
                
                code = key[0]
                buff = key[1:]
                
                for temp_key in pro2:
                    if temp_key[1:] == buff:
                        key = None
                        break

                if not key:
                    continue

                if buff == retrieval:
                    continue
                
                if utilities._RHSCONVENTIONS[code] in {"execute", "clear", "extra_test"}:
                    pro2[key] = pro1[key]
                    continue

                pro1buff = pro1[key]._asdict()
                
                mod_attr_val = {}
                for slot in pro1buff:
                    mod_attr_val[slot] = pro1buff[slot]

                new_chunk = chunks.Chunk(pro1[key].typename, **mod_attr_val)
                pro2[key] = new_chunk

            yield pro2

        return Production(rule=func, utility=self.__DFT_UTILITY, reward=self.__DFT_REWARD)

    def __rename__(self, name, variables):
        """
        Rename production, so that variable names do not clash. name is used to change the variable name to minimize clash. Returns the production with the new name.
        """
        def func():
            production = self[name]['rule']()
            for pro in production:
                for key in pro:
                    code = key[0]
                    buff = key[1:]

                    renaming_set = set(utilities._LHSCONVENTIONS.keys())
                    renaming_set.update(utilities._RHSCONVENTIONS.keys())
                    renaming_set.difference_update({utilities._RHSCONVENTIONS_REVERSED["execute"], utilities._RHSCONVENTIONS_REVERSED["clear"], utilities._RHSCONVENTIONS_REVERSED["extra_test"], utilities._LHSCONVENTIONS_REVERSED["query"]})

                    if code in renaming_set:
                        mod_attr_val = {}
                        for elem in pro[key]:
                            varval = utilities.make_chunkparts_without_varconflicts(elem[1], name, variables)
                            mod_attr_val[elem[0]] = varval
                        new_chunk = chunks.Chunk(pro[key].typename, **mod_attr_val)
                        pro[key] = new_chunk

                yield pro
                
        return Production(rule=func, utility=self.__DFT_UTILITY, reward=self.__DFT_REWARD) #Reward and utility are set at dft right now, simplified

    def __substitute__(self, rule, variable_dict, val_dict):
        """
        Substitutes variables in rule1 and rule2 according to the information in the dictionary variable_dict.
        """
        def func():
            production = rule['rule']()
            for pro in production:
                for key in pro:
                    code = key[0]
                    buff = key[1:]

                    renaming_set = set(utilities._LHSCONVENTIONS.keys())
                    renaming_set.update(utilities._RHSCONVENTIONS.keys())
                    renaming_set.difference_update({utilities._RHSCONVENTIONS_REVERSED["execute"], utilities._RHSCONVENTIONS_REVERSED["clear"], utilities._RHSCONVENTIONS_REVERSED["extra_test"], utilities._LHSCONVENTIONS_REVERSED["query"]})

                    if code in renaming_set:
                        mod_attr_val = {}
                        for elem in pro[key]:
                            varval = utilities.make_chunkparts_with_new_vars(elem[1], variable_dict, val_dict)
                            mod_attr_val[elem[0]] = varval
                        new_chunk = chunks.Chunk(pro[key].typename, **mod_attr_val)
                        pro[key] = new_chunk

                yield pro

        return Production(rule=func, utility=rule['utility'], reward=rule['reward'])

    def __check_valid_compilation__(self, rule_name1, rule_name2, buffers):
        """
        Check that production compilation is valid. There are several cases in which compilation is blocked because it would result in an unsafe rule (a rule that might differ in its output compared to the original rule1 and rule2 firing one after the other). The function returns True if the production compilation is unsafe and should be stopped.
        """
        production1 = self[rule_name1]['rule']()

        pro11 = next(production1)
        pro12 = next(production1)

        production2 = self[rule_name2]['rule']()

        pro21 = next(production2)
        pro22 = next(production2)

        for key in pro12:
            code = key[0]
            buff = key[1:]
            if code == utilities._RHSCONVENTIONS_REVERSED["retrieveorset"]:
                for key2 in pro22:
                    if key2[0] == utilities._RHSCONVENTIONS_REVERSED["retrieveorset"] and key2[1:] == buff and buff not in {x for x in buffers.keys() if isinstance(buffers[x], declarative.DecMemBuffer)}:
                        return True #both productions cannot retrieve/set a value in the same buffers (unless the buffer is retrieval)

                #Checking motor buffers: If the first production makes a request in this buffer then it is not possible to compose it with a second production if that production also makes a request in that buffer or queries the buffer for anything other than state busy.
                if buff in {x for x in buffers.keys() if isinstance(buffers[x], motor.Motor)}:
                    for key2 in pro22:
                        if key2[0] == utilities._RHSCONVENTIONS_REVERSED["retrieveorset"] and key2[1:] == buff:
                            return True
                    for key2 in pro21:
                        if key2[0] == utilities._LHSCONVENTIONS_REVERSED["query"] and key2[1:] == buff and pro21[key2] != {"state": "busy"}:
                            return True
                #Checking visual buffers: If the first production makes a request of one of these buffers then it is not possible to compose it with a second production if that production also makes a request in the same buffer or queries the buffer for anything other than state busy or tests that buffer.
                elif buff in {x for x in buffers.keys() if isinstance(buffers[x], vision.VisualLocation) or isinstance(buffers[x], vision.Visual)}:
                    for key2 in pro22:
                        if key2[0] == utilities._RHSCONVENTIONS_REVERSED["retrieveorset"] and key2[1:] == buff:
                            return True
                    for key2 in pro21:
                        if key2[0] == utilities._LHSCONVENTIONS_REVERSED["query"] and key2[1:] == buff and pro21[key2] != {"state": "busy"}:
                            return True
                        elif key2[0] == utilities._LHSCONVENTIONS_REVERSED["test"] and key2[1:] == buff:
                            return True
                elif buff in {x for x in buffers.keys() if isinstance(buffers[x], declarative.DecMemBuffer)}:
                    for key2 in pro21:
                        if key2[0] == utilities._LHSCONVENTIONS_REVERSED["query"] and key2[1:] == buff and pro21[key2] == {"state": "error"}:
                            return True

        return False

    def compile_rules(self, rule_name1, rule_name2, slotvals, buffers, model_parameters):
        """
        Rule compilation.
        """
        slotvals = slotvals.copy()

        stop = self.__check_valid_compilation__(rule_name1, rule_name2, buffers)
        if stop:
            return False, False

        #we have to get rid of =, ~= sign
        modified_actrvariables = set()

        #get out variables that should not be clashed
        retrieval = None
        for buff in slotvals:
            if slotvals[buff]:
                if isinstance(slotvals[buff], collections.abc.MutableSequence):
                    retrieval = buff #store which buffer carries retrieval info that can be discarded later
                    #if the retrieval is not gone at the end of rule_name2 -- do not compile!!! -- this catches one case in which rules should not be combined because they might yield unsafe results
                    if buffers[buff]:
                        return False, False
                else:
                    for slot in slotvals[buff]:
                        if slotvals[buff][slot] != None:
                            var = slotvals[buff][slot].variables
                            if var != None:
                                modified_actrvariables.add(var)

        new_2rule = self.__rename__(rule_name2, modified_actrvariables) #rename all variables in rule_name2 to avoid var clashes

        production2 = new_2rule['rule']()
        
        pro2 = next(production2)

        matched, valued = utilities.match(pro2, slotvals, rule_name1, rule_name2)

        new_1rule = self.__substitute__(self[rule_name1], matched, valued)
        
        new_2rule = self.__substitute__(new_2rule, matched, valued)

        for buff in slotvals:
            mod_attr_val = {}
            if slotvals[buff]:
                for elem in slotvals[buff]:
                    varval = utilities.make_chunkparts_with_new_vars(slotvals[buff][elem], matched, valued)
                    mod_attr_val[elem] = varval
                slotvals[buff] = mod_attr_val

        new_rule = self.__collapse__(new_1rule, new_2rule, slotvals, retrieval)
        
        idx = 0
        re_created = "CREATED"
        while True:
            if idx > 0:
                new_name = " ".join([str(rule_name1), "and", str(rule_name2), str(idx)])
            else:
                new_name = " ".join([str(rule_name1), "and", str(rule_name2)])
            if self.__getitem__(new_name):
                pr1 = self[new_name]["rule"]()
                pr2 = new_rule["rule"]()
                if next(pr1) == next(pr2) and next(pr1) == next(pr2):
                    re_created = "RE-CREATED"
                    if model_parameters["utility_learning"]:
                        self[new_name]["utility"] = round(self[new_name]["utility"] + model_parameters["utility_alpha"]*(self[rule_name1]["utility"]-self[new_name]["utility"]), 4)
                    break
                else:
                    idx += 1
            else:
                self[new_name] = new_rule
                break

        return new_name, re_created

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

    def __init__(self, rules, buffers, dm, model_parameters):
        self.__actrvariables = {} #variables in a fired rule
        self.rules = rules
        self.ordered_rulenames = sorted(rules.keys(), key=lambda x: rules[x]['utility'], reverse=True) #rulenames ordered by utilities -- this speeds up rule selection when utilities are used

        self.last_rule = None #used for production compilation
        self.last_rule_slotvals = {key: None for key in buffers} #slot-values after a production; used for production compilation
        self.current_slotvals = {key: None for key in buffers} #slot-values after a production; used for production compilation
        self.compile = [] #information for compilation

        self.buffers = buffers #dict of buffers

        self.procs = [] #list of active processes

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
        self.extra_tests = {}
        
        self.last_rule_slotvals = self.current_slotvals.copy()

        for rulename in self.ordered_rulenames:
            self.used_rulename = rulename
            production = self.rules[rulename]["rule"]()
            utility = self.rules[rulename]["utility"]

            pro = next(production)

            if self.model_parameters["subsymbolic"]:
                inst_noise = utilities.calculate_instantaneous_noise(self.model_parameters["utility_noise"])
                utility += inst_noise
            if max_utility <= utility and self.LHStest(pro, self.__actrvariables.copy()):
                max_utility = utility
                used_rulename = rulename
                if not self.model_parameters["subsymbolic"] or not self.model_parameters["utility_noise"]:
                    break #breaking after finding a rule, to speed up the process
        if used_rulename:
            self.used_rulename = used_rulename
            production = self.rules[used_rulename]["rule"]()
            self.rules.used_rulenames.setdefault(used_rulename, []).append(time)
            
            yield Event(roundtime(time), self._PROCEDURAL, 'RULE SELECTED: %s' % used_rulename)
            time = time + self.model_parameters["rule_firing"]
            yield Event(roundtime(time), self._PROCEDURAL, self._UNKNOWN)

            pro = next(production)

            if not self.LHStest(pro, self.__actrvariables.copy(), True):
                yield Event(roundtime(time), self._PROCEDURAL, 'RULE STOPPED FROM FIRING: %s' % used_rulename)
            else:
                if self.model_parameters["utility_learning"] and self.rules[used_rulename]["reward"] != None:
                    utilities.modify_utilities(time, self.rules[used_rulename]["reward"], self.rules.used_rulenames, self.rules, self.model_parameters)
                    self.rules.used_rulenames = {}
                compiled_rulename, re_created = self.compile_rules()
                self.compile = []
                if re_created:
                    yield Event(roundtime(time), self._PROCEDURAL, 'RULE %s: %s' % (re_created, compiled_rulename))
                self.current_slotvals = {key: None for key in self.buffers}
                yield Event(roundtime(time), self._PROCEDURAL, 'RULE FIRED: %s' % used_rulename)
                try:
                    yield from self.update(next(production), time)
                except utilities.ACTRError as e:
                    raise utilities.ACTRError("The following rule is not defined correctly according to ACT-R: '%s'. The following error occurred: %s" % (self.used_rulename, e))
                if self.last_rule and self.last_rule != used_rulename:
                    self.compile = [self.last_rule, used_rulename, self.last_rule_slotvals.copy()]
                    self.last_rule_slotvals = {key: None for key in self.buffers}

                self.last_rule = used_rulename
        else:
            self.procs.remove(self._PROCEDURAL,)
            yield Event(roundtime(time), self._PROCEDURAL, 'NO RULE FOUND')
        yield self.procs #yields processes activated by PROCEDURAL

    def compile_rules(self):
        """
        Compile two rules.
        """
        if self.model_parameters["production_compilation"] and self.compile:
            compiled_rulename, re_created = self.rules.compile_rules(self.compile[0], self.compile[1], self.compile[2], self.buffers, self.model_parameters)
            if compiled_rulename:
                self.ordered_rulenames.append(compiled_rulename)
            return compiled_rulename, re_created
        else:
            return None, None

    def update(self, RHSdictionary, time):
        """
        Update buffers (RHS of production rules).
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
        Add an extra test to a buffer.
        """
        tested.state = tested._BUSY
        self.extra_tests[name] = test
        tested.state = tested._FREE
        yield Event(roundtime(time), name, "EXTRA TEST ADDED")

    def clear(self, name, cleared, optional, temp_actrvariables, time, freeing=True):
        """
        Clear a buffer. The 'freeing' argument specifies whether the state should be considered FREE (if the rule is run alone) or not (if it is embedded in another rule).
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
        Execute a command.
        """
        executed.state = executed._BUSY
        for each in executecommand:
            try:
                getattr(executed, each[0])(*each[1])
            except TypeError:
                getattr(executed, each[0])(each[1])
        executed.state = executed._FREE
        yield Event(roundtime(time), name, "EXECUTED")

    def modify(self, name, modified, otherchunk, temp_actrvariables, time):
        """
        Modify a buffer chunk.
        """
        modified.state = modified._BUSY
        if self.model_parameters['production_compilation']:
            RHSdict = otherchunk._asdict()
            RHSdict = {item[0]: item[1] for item in RHSdict.items() if item[1] != chunks.Chunk.EmptyValue()} #delete None values, they will be copied from LHSdict
            production = self.rules[self.used_rulename]["rule"]()
            code = utilities._LHSCONVENTIONS_REVERSED["test"]
            try:
                slotvaldict = next(production)[code+name]._asdict()
            except KeyError:
                slotvaldict = {}
            finally:
                slotvaldict.update(RHSdict)
            self.current_slotvals[name] = slotvaldict

        modified.modify(otherchunk, temp_actrvariables) #time variable is currently not used - needed if modification would cost time
        modified.state = modified._FREE
        yield Event(roundtime(time), name, "MODIFIED")

    def modify_request(self, name, modified, otherchunk, temp_actrvariables, time):
        """
        Modify a buffer chunk. Unlike plain modify, this might add extra time to changing the chunk in the buffer.
        """
        modified.state = modified._BUSY
        extra_time = utilities.calculate_setting_time(updated)
        time += extra_time
        yield Event(roundtime(time), name, self._UNKNOWN)
        if self.model_parameters['production_compilation']:
            RHSdict = otherchunk._asdict()
            RHSdict = {item[0]: item[1] for item in RHSdict.items() if item[1] != chunks.Chunk.EmptyValue()} #delete None values, they will be copied from LHSdict
            production = self.rules[self.used_rulename]["rule"]()
            code = utilities._LHSCONVENTIONS_REVERSED["test"]
            try:
                slotvaldict = next(production)[code+name]._asdict()
            except KeyError:
                slotvaldict = {}
            finally:
                slotvaldict.update(RHSdict)
            self.current_slotvals[name] = slotvaldict

        modified.modify(otherchunk, temp_actrvariables)
        modified.state = modifed._FREE
        yield Event(roundtime(time), name, "MODIFIED")

    def overwrite(self, name, updated, otherchunk, temp_actrvariables, time):
        """
        Overwrite a buffer.
        """
        updated.state = updated._BUSY
        extra_time = utilities.calculate_setting_time(updated)
        time += extra_time
        yield Event(roundtime(time), name, self._UNKNOWN)
        if self.model_parameters['production_compilation']:
            RHSdict = otherchunk._asdict()
            RHSdict = {item[0]: item[1] for item in RHSdict.items()} 
            self.current_slotvals[name] = RHSdict

        updated.create(otherchunk, list(self.dm.values())[0], temp_actrvariables)

        created_elem = list(updated)[0]
        updated.state = updated._FREE
        yield Event(roundtime(time), name, "WROTE A CHUNK: %s" % str(created_elem))

    def visualencode(self, name, visualbuffer, chunk, temp_actrvariables, time, extra_time, site):
        """
        Encode a visual object.
        """
        visualbuffer.state = visualbuffer._BUSY
        time += extra_time
        visualbuffer.current_focus = site #use it if visual focus is fully attention-based (internal) and not based on eye position; site is the position of attention
        yield from self.clear(name, visualbuffer, None, temp_actrvariables, time, freeing=False)
        visualbuffer.add(chunk, time)
        visualbuffer.state = visualbuffer._FREE
        yield Event(roundtime(time), name, "ENCODED VIS OBJECT:'%s'" % str(chunk))

    def retrieveorset(self, name, updated, otherchunk, temp_actrvariables, time):
        """
        Find out whether a buffer should be set (for buffers that are not attached to any dm, i.e., Goal or Motor or Vision) or should trigger retrieval.
        """
        updated.state = updated._BUSY
        if isinstance(updated, goals.Goal):
            yield from self.clear(name, updated, otherchunk, temp_actrvariables, time, freeing=False)
            extra_time = utilities.calculate_setting_time(updated)
            time += extra_time
            yield Event(roundtime(time), name, self._UNKNOWN)
            if self.model_parameters['production_compilation']:
                RHSdict = otherchunk._asdict()
                RHSdict = {item[0]: item[1] for item in RHSdict.items()}
                self.current_slotvals[name] = RHSdict

            updated.create(otherchunk, list(self.dm.values())[0], temp_actrvariables)
            created_elem = list(updated)[0]
            updated.state = updated._FREE
            yield Event(roundtime(time), name, "CREATED A CHUNK: %s" % str(created_elem))
        elif isinstance(updated, vision.VisualLocation):
            extra_time = utilities.calculate_setting_time(updated)
            time += extra_time #0 ms to create chunk in location (pop-up effect)
            yield Event(roundtime(time), name, self._UNKNOWN)
            chunk, stim = updated.find(otherchunk, actrvariables=temp_actrvariables, extra_tests=self.extra_tests.get(name, {})) #extra_time currently ignored
            if chunk:
                yield from self.clear(name, updated, None, temp_actrvariables, time, freeing=False)
                updated.add(chunk, stim, time)
                updated.state = updated._FREE
            else:
                updated.state = updated._ERROR
            yield Event(roundtime(time), name, "ENCODED LOCATION:'%s'" % str(chunk))
        elif isinstance(updated, vision.Visual):
            mod_attr_val = {x[0]: utilities.check_bound_vars(temp_actrvariables, x[1]) for x in otherchunk.removeunused()}
            if (not mod_attr_val['cmd'].values) or mod_attr_val['cmd'].values not in utilities.CMDVISUAL:
                raise ACTRError("Visual module received no command or an invalid command: '%s'. The valid commands are: '%s'" % (mod_attr_val['cmd'].values, utilities.CMDVISUAL))
            if mod_attr_val['cmd'].values == utilities.CMDMOVEATTENTION:
                ret = yield from self.visualshift(name, updated, otherchunk, temp_actrvariables, time)
                yield ret #visual action returns value, namely, its continuation method
            elif mod_attr_val['cmd'].values == utilities.CMDCLEAR:
                updated.stop_automatic_buffering()
                updated.state = updated._FREE
                yield Event(roundtime(time), name, "VISUAL STOPPED FROM AUTOMATIC BUFFERING AT ITS CURRENT FOCUS")
        elif isinstance(updated, motor.Motor):
            ret = yield from self.motorset(name, updated, otherchunk, temp_actrvariables, time)
            yield ret #motor action returns value, namely, its continuation method
        else:
            yield from self.retrieve(name, updated, otherchunk, temp_actrvariables, time)

    def retrieve(self, name, retrieval, otherchunk, temp_actrvariables, time):
        """
        Carry out retrieval using the retrieval buffer. 
        """
        #starting process
        yield Event(roundtime(time), name, 'START RETRIEVAL')
        retrieved_elem, extra_time = retrieval.retrieve(time, otherchunk, temp_actrvariables, self.buffers, self.extra_tests.get(name, {}), self.model_parameters)
        time += extra_time
        yield Event(roundtime(time), name, self._UNKNOWN)
        if retrieved_elem:
            yield Event(roundtime(time), name, 'CLEARED')
            retrieval.add(retrieved_elem, time)
            retrieval.state = retrieval._FREE
        else:
            retrieval.state = retrieval._ERROR

        if self.model_parameters['production_compilation']:
            RHSdict = otherchunk._asdict()
            RHSdict = {item[0]: item[1] for item in RHSdict.items() if item[1] != chunks.Chunk.EmptyValue()} #delete None values
            self.current_slotvals[name] = [RHSdict, retrieved_elem]

        yield Event(roundtime(time), name, 'RETRIEVED: %s' % str(retrieved_elem))

    def automatic_search(self, name, visualbuffer, stim, time):
        """
        Automatic search of environment stim in the visual buffer. Automatic search is never found by production rules. Production rules are bypassed, this is called directly by simulation.
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
        Automatic buffering of environment stim in the visual buffer. Automatic buffering is never found by production rules. Production rules are bypassed, this is called directly by simulation.
        """
        visualbuffer.state = visualbuffer._BUSY
        visualbuffer.autoattending = visualbuffer._BUSY
        foveal_distance = utilities.calculate_distance(1, visualbuffer.environment.size, visualbuffer.environment.simulated_screen_size, visualbuffer.environment.viewing_distance)
        cf = tuple(visualbuffer.current_focus)
        newchunk = None
        encoding = 0
        for st in stim:
            if st['position'][0] > cf[0]-foveal_distance and st['position'][0] < cf[0]+foveal_distance and st['position'][1] > cf[1]-foveal_distance and st['position'][1] < cf[1]+foveal_distance:
                if (not visualbuffer) or list(visualbuffer)[0].value.values != st['text']: #automatic buffer only of there is sth to buffer
                    newchunk, encoding = visualbuffer.automatic_buffering(st, self.model_parameters)
        time += encoding
        yield Event(roundtime(time), name, self._UNKNOWN)
        visualbuffer.state = visualbuffer._FREE
        visualbuffer.autoattending = visualbuffer._FREE
        if newchunk:
            if visualbuffer:
                visualbuffer.modify(newchunk)
            else:
                visualbuffer.add(newchunk, time)
            yield Event(roundtime(time), name, 'AUTOMATIC BUFFERING: %s' % str(newchunk))

    def visualshift(self, name, visualbuffer, otherchunk, temp_actrvariables, time):
        """
        Carry out preparation of visual shift.
        """
        newchunk, extra_time, site = visualbuffer.shift(otherchunk, actrvariables=temp_actrvariables, model_parameters=self.model_parameters)

        encoding = extra_time[0]
        preparation = extra_time[1]
        execution = extra_time[2]

        visualbuffer.preparation = visualbuffer._BUSY
        visualbuffer.processor = visualbuffer._BUSY
        visualbuffer.state = visualbuffer._BUSY
        
        yield Event(roundtime(time), name, 'PREPARATION TO SHIFT VISUAL ATTENTION STARTED')

        if encoding <= preparation:
            yield from self.visualencode(name, visualbuffer, newchunk, temp_actrvariables, time, encoding, site)

        time += preparation
        
        yield Event(roundtime(time), name, 'PREPARATION TO SHIFT VISUAL ATTENTION COMPLETED')
        
        if encoding > preparation and encoding <= preparation+execution:
            yield from self.visualencode(name, visualbuffer, newchunk, temp_actrvariables, time-preparation, encoding, site)

        yield self.visualcontinue(name, visualbuffer, newchunk, temp_actrvariables, time, extra_time, site)

    def visualcontinue(self, name, visualbuffer, otherchunk, temp_actrvariables, time, extra_time, landing_site):
        """
        Carry out the rest of visual shift. Shift is split in two because of EMMA assumption that the two parts can act independently of each other.
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
        yield Event(roundtime(time), name, 'SHIFT COMPLETE TO POSITION: %s' % str(visualbuffer.current_focus))
        if encoding > preparation+execution:
            newchunk, extra_time, _ = visualbuffer.shift(otherchunk, actrvariables=temp_actrvariables, model_parameters=self.model_parameters)
            yield from self.visualencode(name, visualbuffer, otherchunk, temp_actrvariables, time, (1-((preparation+execution)/encoding))*extra_time[0], landing_site)
        visualbuffer.processor = visualbuffer._FREE
        visualbuffer.execution = visualbuffer._FREE
        visualbuffer.state = visualbuffer._FREE
        visualbuffer.attend_automatic = True
        #the following lines - if we think that automatic buffering should be repeated after being done with shift
        #if visualbuffer.attend_automatic:
        #    yield from self.automatic_buffering(name, visualbuffer, list(visualbuffer.environment.stimulus.values()), time)
    
    def motorset(self, name, motorbuffer, otherchunk, temp_actrvariables, time):
        """
        Carry out preparation of motor action. 
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

        yield Event(roundtime(time), name, 'COMMAND: %s' % str(newchunk.cmd))
        time += preparation
        
        yield Event(roundtime(time), name, 'PREPARATION COMPLETE')

        yield self.motorcontinue(name, motorbuffer, newchunk, temp_actrvariables, time, time_presses)

    def motorcontinue(self, name, motorbuffer, otherchunk, temp_actrvariables, time, time_presses):
        """
        Carry out the rest of motor action. Motor action is split in two because of ACT-R assumption that the two parts can act independently of each other.
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
        
        self.env_interaction.add(otherchunk.key.values)

        yield Event(roundtime(time), name, 'KEY PRESSED: %s' % str(otherchunk.key))
        
        time += movement_finish

        yield Event(roundtime(time), name, 'MOVEMENT FINISHED')
        
        self.env_interaction.discard(otherchunk.key)
        motorbuffer.state = motorbuffer._FREE
        motorbuffer.execution = motorbuffer._FREE
        motorbuffer.last_key[1] = 0

    def LHStest(self, dictionary, actrvariables, update=False):
        """
        Test rules in LHS of production rules. update specifies whether actrvariables should be updated (this does not happen when rules are tested, only when they are fired)
        """
        for key in dictionary:
            submodule_name = key[1:] #this is the module
            code = key[0] #this is what the module should do; standardly, query, i.e., ?, or test, =
            if code not in self._LHSCONVENTIONS:
                raise ACTRError("The LHS rule '%s' is invalid; every condition in LHS rules must start with one of these signs: %s" % (self.used_rulename, list(self._LHSCONVENTIONS.keys())))
            result = getattr(self, self._LHSCONVENTIONS[code])(submodule_name, self.buffers.get(submodule_name), dictionary[key], actrvariables)
            if not result[0]:
                return False
            else:
                actrvariables.update(result[1])
        if update:
            self.__actrvariables = actrvariables
        return True

    def test(self, submodule_name, tested, testchunk, temp_actrvariables):
        """
        Test the content of a buffer.

        What buffer - specified by tested.
        """
        if not tested:
            return False, None

        submodule_var = "".join(["=", submodule_name])

        if submodule_var in temp_actrvariables and list(self.buffers[submodule_name])[0] != temp_actrvariables[submodule_var]:
            return False, None

        for chunk in tested:
            testchunk.boundvars = dict(temp_actrvariables)

            if testchunk <= chunk:
                temp_actrvariables = dict(testchunk.boundvars)
                temp_actrvariables[submodule_var] = list(self.buffers[submodule_name])[0]
                return True, temp_actrvariables
            else:
                return False, None

    def query(self, submodule_name, tested, testdict, temp_actrvariables):
        """
        Query a buffer.

        What buffer - specified by tested.
        """
        for each in testdict:
            if each == 'buffer' and not tested.test_buffer(testdict.get(each)):
                return False, dict(temp_actrvariables)

            if each != 'buffer' and not tested.test(each, testdict.get(each)):
                return False, dict(temp_actrvariables)

        return True, dict(temp_actrvariables)


