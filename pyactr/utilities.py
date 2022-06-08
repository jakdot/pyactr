"""
Helper functions used by ACT-R modules.
"""

import collections
import collections.abc
import re
import math
import warnings

import numpy as np
import pyparsing as pp


#for querying buffers

_BUSY = "busy"
_FREE = "free"
_ERROR = "error"

#special characters for chunks

ACTRVARIABLE = "="
ACTRVARIABLER = "\=" #used for regex
ACTRVALUE = "!"
ACTRVALUER = "\!" #used for regex
ACTRNEG = "~"
ACTRNEGR = "\~" #used for regex
ACTRRETRIEVE = "+"
ACTRRETRIEVER = "\+" #used for regex

MANUAL = "_manual"
VISUAL = "_visual"
VISUALLOCATION = "_visuallocation"

EMPTYVALUE = None

VarvalClass = collections.namedtuple("_variablesvalues", "values, variables, negvalues, negvariables")

def varval_repr(self):
    """
    This is a function used for string representation of VarvalClass.
    """
    temp = self
    y = ""
    if temp.values:
        y = "".join([y, str(temp.values)])
    if temp.variables:
        y = "".join([y, "=", str(temp.variables)])
    if temp.negvalues:
        if not isinstance(temp.negvalues, str):
            for each in temp.negvalues:
                y = "".join([y, "~", str(each)])
        else:
            y = "".join([y, "~", str(temp.negvalues)])
    if temp.negvariables:
        if not isinstance(temp.negvariables, str):
            for each in temp.negvariables:
                y = "".join([y, "~=", str(each)])
        else:
            y = "".join([y, "~=", str(temp[key])])
    return y

VarvalClass.__repr__ = varval_repr

SPECIALCHUNKTYPES = {MANUAL: "cmd, key", VISUAL: "cmd, value, color, screen_pos", VISUALLOCATION: "screen_x, screen_y, color, value"}

#[{"test": {"position": (300, 170)}, "X": {"position": (300, 170)}}]

#special values for cmd in MANUAL

CMDMANUAL = set([EMPTYVALUE, str(EMPTYVALUE), "press_key"])
CMDPRESSKEY = "press_key"

#special values for cmd in VISUAL

CMDVISUAL = set([EMPTYVALUE, str(EMPTYVALUE), "move_attention", "clear"])
CMDMOVEATTENTION = "move_attention"
CMDCLEAR = "clear"

#special character for visual chunks

VISIONSMALLER = "<" # smaller than
VISIONGREATER = ">" # greater than
VISIONLOWEST = "lowest" #
VISIONHIGHEST = "highest" #
VISIONCLOSEST = "closest" # closest is absolute
VISIONONEWAYCLOSEST = "onewayclosest" # onewayclosest is closest in one direction (x or y)

#for Events

Event = collections.namedtuple('Event', 'time proc action')

#for rules

_UNKNOWN = "UNKNOWN"
_PROCEDURAL = "PROCEDURAL"
_EMPTY = ""
_ENV = "ENVIRONMENT"

_RHSCONVENTIONS = {"?": "extra_test", "=": "modify", "+": "retrieveorset",\
        "!": "execute", "~": "clear", "@": "overwrite", "*": "modify_request"}
_RHSCONVENTIONS_REVERSED = {v: k for k, v in _RHSCONVENTIONS.items()}

_LHSCONVENTIONS = {"=": "test", "?": "query"}
_LHSCONVENTIONS_REVERSED = {v: k for k, v in _LHSCONVENTIONS.items()}

_INTERRUPTIBLE = {"retrieveorset", "modify_request"}

def roundtime(time):
    """
    Round time to tenths of a millisecond.
    """
    return round(time, 4)

##############class for ACT-R Exceptions##############

class ACTRError(Exception):
    """
    Exception specific to ACT-R.
    """

#############utilities for chunks######################################

def stringsplitting(info, empty=True):
    """
    Split info into variables, negative variables, values and negative values. Used in chunks. Info is a string, e.g., '=x~=y!2'. This is a depreciated approach.
    """
    varval = {"variables": set(), "values": set(), "negvariables": set(), "negvalues": set()}
    #assume it's a string
    varval["variables"] = set(re.findall("".join(["(?<=", "(?<!", ACTRNEGR, ")", ACTRVARIABLER, ").*?(?=$|", ACTRNEGR, "|", ACTRVALUER, "|", ACTRVARIABLER, ")"]), info))
    varval["values"] = set(re.findall("".join(["(?<=", "(?<!", ACTRNEGR, ")", ACTRVALUER, ").*?(?=$|", ACTRNEGR, "|", ACTRVALUER, "|", ACTRVARIABLER, ")"]), info))
    varval["negvariables"] = set(re.findall("".join(["(?<=", ACTRNEGR, ACTRVARIABLER, ").*?(?=$|", ACTRNEGR, "|", ACTRVALUER, "|", ACTRVARIABLER, ")"]), info))
    varval["negvalues"] = set(re.findall("".join(["(?<=", ACTRNEGR,  ACTRVALUER, ").*?(?=$|", ACTRNEGR, "|", ACTRVALUER, "|", ACTRVARIABLER, ")"]), info))
    if not any(varval.values()):
        varval["values"] = set([info]) #varval empty -> only values present

    if len(set(varval["values"])) > 1:
        raise ACTRError("Any slot must have at most one value, there is more than one value in this slot")
    if len(set(varval["variables"])) > 1:
        raise ACTRError("Any slot must have at most one variable, there is more than one variable in this slot")

    return varval

def splitting(info):
    """
    Split info into variables, negative variables, values and negative values. 

    """
    if info == EMPTYVALUE:
        info = VarvalClass(variables=None, values=None, negvariables=(), negvalues=())
    return info

def get_similarity(d, val1, val2, mismatch_penalty=1):
    """
    Get similarity for partial matching.
    """
    dis = d.get(tuple((val2, val1)), -mismatch_penalty) #-1 is the default value
    return dis

def getchunk():
    """
    Using pyparsing, create chunk reader for chunk strings.
    """
    slot = pp.Word("".join([pp.alphas, "_"]), "".join([pp.alphanums, "_"]))
    special_value = pp.Group(pp.oneOf([ACTRVARIABLE, "".join([ACTRNEG, ACTRVARIABLE]), ACTRNEG, VISIONGREATER, VISIONSMALLER, "".join([VISIONGREATER, ACTRVARIABLE]), "".join([VISIONSMALLER, ACTRVARIABLE])])\
            + pp.Word("".join([pp.alphanums, "_", '"', "'"])))
    strvalue = pp.QuotedString('"', unquoteResults=False)
    strvalue2 = pp.QuotedString("'", unquoteResults=False)
    varvalue = pp.Word("".join([pp.alphanums, "_", "\:", "\|", "\.", ",", "%", "&", "\$", "`", "\*", "-"]))
    value = varvalue | special_value | strvalue | strvalue2
    chunk_reader = pp.OneOrMore(pp.Group(slot + value))
    return chunk_reader

def make_chunkparts_without_varconflicts(chunkpart, rule_name, variables):
    """
    Make a chunk avoiding any variable names used in actrvariables. The function uses rule_name for naming, if possible.
    """
    varval = splitting(chunkpart)
    temp_var = None
    if varval.variables:
        new_name = "".join([str(varval.variables), "__rule__", rule_name])
        if "".join(["=", new_name]) in variables:
            raise ACTRError("A name clash appeared when trying to compile two rules. Try to rename variables in the rule '%s'" %rule_name)
        else:
            temp_var = new_name
    temp_negvar = set()
    for x in varval.negvariables:
        new_name = "".join([str(x), "__rule__", rule_name])
        if "".join(["=", "new_name"]) in variables:
            raise ACTRError("A name clash appeared when trying to compile two rules. Try to rename variables in the rule '%s'" %rule_name)
        else:
            temp_negvar.add(new_name)
    new_varval = VarvalClass(variables=temp_var, values=varval.values, negvariables=tuple(temp_negvar), negvalues=varval.negvalues)

    return new_varval

def make_chunkparts_with_new_vars(chunkpart, variable_dict, val_dict):
    """
    Make a chunk changing variable names according to variable_dict.
    """
    varval = splitting(chunkpart)
    temp_var = None
    temp_val = varval.values
    if varval.variables:
        if varval.variables not in val_dict:
            temp_var = variable_dict.setdefault(varval.variables, varval.variables)
        else:
            if varval.values:
                if val_dict[varval.variables] == varval.values:
                    pass
                else:
                    raise ACTRError("During the compilation, one slot received two different values, namely %s and %s; exiting" %(varval.values, val_dict[varval.variables]))
            else:
                temp_val = val_dict[varval.variables]
    temp_negvar = set()
    temp_negval = set(varval.negvalues)
    for x in varval.negvariables:
        if x not in val_dict:
            temp_negvar.add(variable_dict.setdefault(x, x))
        else:
            temp_negval.add(val_dict[x])

    new_varval = VarvalClass(variables=temp_var, values=temp_val, negvariables=tuple(temp_negvar), negvalues=tuple(temp_negval))

    return new_varval


def merge_chunkparts(chunkpart1, chunkpart2):
    """
    Merge two chunk parts.

    Chunk parts are merged as follows: chunkpart1 is used; info in chunkpart2 is added to chunkpart1
    """
    varval1 = splitting(chunkpart1)
    varval2 = splitting(chunkpart2)
    for x in varval1:
        if x:
            break
    else:
        varval1 = varval2

    new_varval = VarvalClass(variables=varval1.variables, values=varval1.values, negvariables=varval1.negvariables, negvalues=varval1.negvalues)

    return new_varval

#############utilities for rules######################################

def getrule():
    """
    Using pyparsing, get rule out of a string.
    """
    arrow = pp.Literal("==>")
    buff = pp.Word(pp.alphas, "".join([pp.alphanums, "_"]))
    special_valueLHS = pp.oneOf([x for x in _LHSCONVENTIONS.keys()])
    end_buffer = pp.Literal(">")
    special_valueRHS = pp.oneOf([x for x in _RHSCONVENTIONS.keys()])
    chunk = getchunk()
    rule_reader = pp.Group(pp.OneOrMore(pp.Group(special_valueLHS + buff + end_buffer + pp.Group(pp.Optional(chunk))))) + arrow + pp.Group(pp.OneOrMore(pp.Group(special_valueRHS + buff + end_buffer + pp.Group(pp.Optional(chunk)))))
    return rule_reader

def check_bound_vars(actrvariables, elem, negative_impossible=True):
    """
    Check that elem is a bound variable, or not a variable. If the test goes through, return elem.
    If negative_impossible is set to True, then having negative values (or neg. variables) raises an Error. This is needed if the goal buffer is set. Otherwise, negative values are returned.
    """
    result = None
    neg_result = set()
    varval = splitting(elem)
    for x in varval._fields:
        if x == "variables" and getattr(varval, x):
            var = getattr(varval, x)
            var = "".join([ACTRVARIABLE, var])
            try:
                temp_result = actrvariables[var]
            except KeyError:
                raise ACTRError("Object '%s' in the value '%s' is a variable that is not bound; this is illegal in ACT-R" % (var[1:], elem)) #is this correct? maybe in some special cases binding only in RHS should be allowed? If so this should be adjusted in productions.py
        elif x == "values" and getattr(varval, x):
            temp_result = getattr(varval, x)
        elif x == "negvalues" and getattr(varval, x):
            if negative_impossible:
                raise ACTRError("It is not allowed to define negative values or negative variables on the right hand side of some ACT-R rules, notably, the ones that do not search environment or memory; '%s' is illegal in this case" % elem)
            else:
                for neg in getattr(varval, x):
                    neg_result.add(neg)
        elif x == "negvariables" and getattr(varval, x):
            if negative_impossible:
                raise ACTRError("It is not allowed to define negative values or negative variables on the right hand side of some ACT-R rules, notably, the ones that do not search environment or memory; '%s' is illegal in this case" % elem)
            else:
                for neg in getattr(varval, x):
                    neg_var = neg
                    neg_var = "".join([ACTRVARIABLE, neg_var])
                    try:
                        neg_result.add(actrvariables[neg_var])
                    except KeyError:
                        raise ACTRError("Object '%s' in the value '%s' is a variable that is not bound; this is illegal in ACT-R" % (var[1:], elem)) #is this correct? maybe in some special cases binding only in RHS should be allowed? If so this should be adjusted in productions.py
        if result and temp_result in {VISIONGREATER, VISIONSMALLER} or result in {VISIONGREATER, VISIONSMALLER}:
            result = "".join(sorted([temp_result, result], reverse=True))
        elif result and temp_result != result:
            raise ACTRError("It looks like in '%s', one slot would have to carry two values at the same time; this is illegal in ACT-R" % elem)
        else:
            try:
                result = temp_result
            except UnboundLocalError: #temp_result wasn't used
                pass
    try:
        if temp_result:
            returned_tuple = VarvalClass(variables=None, values=result, negvariables=(), negvalues=tuple(neg_result))
        returned_tuple
    except UnboundLocalError: #temp_result was never used, which means that no values were defined
        returned_tuple = VarvalClass(variables=None, values=None, negvariables=(), negvalues=tuple(neg_result))
    return returned_tuple

def match(dict2, slotvals, name1, name2):
    """
    Match variables that happen to be tied to the same slots. This function is used in production compilation. dict2 is the LHS of the second rule, slotvals is the dictionary based on the output of the first rule.
    """
    def temp_func(temp_set, temp_val):
        """
        temp_func gets a set of variables and a value (possibly, None), and it returns two dicts.
        matched stores which variables will be substituted by which variable, valued stores which variables will be substituted by a value (if temp_val not empty).
        """
        if temp_val:
            valued.update({x: temp_val for x in temp_set})
        else:
            try:
                temp_var = sorted(temp_set, key=lambda x:len(x))[0]
            except IndexError:
                pass
            else:
                matched.update({x: temp_var for x in temp_set})
        return matched, valued

    matched = {}
    valued = {}
    temp_slotvals = slotvals.copy()
    for key in dict2:

        code = key[0]
        buff = key[1:]

        chunkdict2 = {}
                    
        renaming_set = set(_LHSCONVENTIONS.keys())
        renaming_set.update(_RHSCONVENTIONS.keys())
        renaming_set.difference_update({_RHSCONVENTIONS_REVERSED["execute"], _RHSCONVENTIONS_REVERSED["clear"], _RHSCONVENTIONS_REVERSED["extra_test"], _LHSCONVENTIONS_REVERSED["query"]}) #only renaming_set is kept; execute etc. cannot carry a variable, so no variable matching is needed

        if code in renaming_set:
            chunkdict2 = dict2.get(key)._asdict()
            try:
                chunkdict3 = temp_slotvals.pop(buff)
            except KeyError:
                chunkdict3 = chunkdict2

            if isinstance(chunkdict3, collections.abc.MutableSequence): #this is retrieval, it consists of mutable sequence -- 0=chunk description in the 1st rule; 1=retrieved chunk
                for elem in chunkdict2:
                    chunkpart2 = splitting(chunkdict2[elem])
                    try:
                        chunkpart3 = splitting(chunkdict3[0][elem])
                    except KeyError:
                        chunkpart3 = splitting(EMPTYVALUE)
                    try:
                        temp_val = getattr(chunkdict3[1], elem).values
                    except AttributeError:
                        temp_val = None
                    temp_set = set()
                    if chunkpart2.variables:
                        temp_set.update(set([chunkpart2.variables]))
                    if chunkpart3.variables:
                        temp_set.update(set([chunkpart3.variables]))
                    matched, valued = temp_func(temp_set, temp_val)
                slotvals.pop(buff) #info about retrieved element has been fully used, it can be discarded now
            else: #anything else but retrieval is here
                for elem in chunkdict2:
                    chunkpart2 = splitting(chunkdict2[elem])
                    try:
                        chunkpart3 = splitting(chunkdict3[elem])
                    except (KeyError, TypeError):
                        chunkpart3 = splitting(EMPTYVALUE)

                    temp_set = set()
                    if chunkpart2.variables:
                        temp_set.update(set([chunkpart2.variables]))
                    if chunkpart3.variables:
                        temp_set.update(set([chunkpart3.variables]))
                    temp_val, val2, val3 = None, None, None
                    if chunkpart2.values:
                        val2 = chunkpart2.values
                    if chunkpart3.values:
                        val3 = chunkpart3.values

                    if val2 and val3 and val2 != val3:
                        raise ACTRError("The values in rules '%s' and '%s' do not match, production compilation failed" % (name1, name2))
            
                    temp_val = val2 or val3

                    matched, valued = temp_func(temp_set, temp_val)

    return matched, valued
            


def modify_utilities(time, reward, rulenames, rules, model_parameters):
    """
    Update rules with newly calculated utilities for rules whose firing led to reward.
    """
    for rulename in rulenames:
        for t in rulenames[rulename]:
            utility_time = time-t
            rules[rulename]["utility"] = round(rules[rulename]["utility"] + model_parameters["utility_alpha"]*(reward-utility_time-rules[rulename]["utility"]), 4)

def calculate_setting_time(updated):
    """
    Calculate time to set a chunk in a buffer.
    """
    try:
        val = updated.delay
    except AttributeError:
        val = 0
    return val

#############utilities for baselevel learning and noise######################################

def baselevel_learning(current_time, times, bll, decay, activation=None, optimized_learning=False):
    """
    Calculate base-level learning: B_i = ln(sum(t_j^{-decay})) for t_j = current_time - t for t in times.
    """
    if len(times) > 0:
        with warnings.catch_warnings(record=True):
            warnings.filterwarnings('error')
            if bll and not optimized_learning:
                try:
                    B = math.log(np.sum((current_time - times) ** (-decay)))
                #this part removes chunk storages that are stored at current time (blocking simultaneous retrieval)
                except RuntimeWarning:
                    temp_times = np.delete(times, times.argmax())
                    if len(temp_times) > 0:
                        B = math.log(np.sum((current_time - temp_times) ** (-decay)))
            elif bll:
                try:
                    B = math.log(len(times)/(1-decay)) - decay*math.log(current_time - np.max(times)) #calculating bll using optimized learning -- much faster since it's a single calculation
                #this part removes chunk storages that are stored at current time (blocking simultaneous retrieval)
                except RuntimeWarning:
                    temp_times = np.delete(times, times.argmax())
                    if len(temp_times) > 0:
                        B = math.log(len(times)/(1-decay)) - decay*math.log(current_time - np.max(temp_times)) #calculating bll using optimized learning -- much faster since it's a single calculation

    #add hard-coded activation
    if activation != None:
        try:
            B = math.log(math.exp(B) + math.exp(activation))
        except NameError:
            B = activation
    return B

def calculate_instantaneous_noise(instantaneous_noise):
    """
    Calculate noise, generated by logistic distribution with mean 0 and variance = ( pi^2/3 ) * s^2 where s = instantaneous_noise.
    """
    assert instantaneous_noise >= 0, "Instantaneous noise must be positive"
    if instantaneous_noise == 0:
        return 0
    else:
        return np.random.logistic(0, instantaneous_noise, 1)[0]

#############utilities for source activation######################################

def weigh_buffer(chunk, weight_k, only_chunks=True):
    """
    Calculate w_{kj}=w_k/n_k. You supply chunk and its activation w_k and it divides w_k by the number of chunks in w_k.
    """
    n_k = len(tuple(find_chunks(chunk, only_chunks).values()))
    if n_k == 0:
        weight_kj = 0
    else:
        weight_kj = weight_k/n_k
    return weight_kj

def find_chunks(chunk, only_chunks=True):
    """
    Find chunks as values in slots in the chunk 'chunk'.

    only_chunks specifies whether spreading activation only goes from chunks, or it can also go from actual values (strings).
    """
    chunk_dict = {}
    for x in chunk:
        try:
            val = splitting(x[1]).values
        except AttributeError:
            pass
        else:
            if val != EMPTYVALUE and val != str(EMPTYVALUE):
                if not only_chunks:
                    chunk_dict[x[0]] = val
                elif not isinstance(val, str):
                    chunk_dict[x[0]] = val
    return chunk_dict

def calculate_strength_association(chunk, otherchunk, dm, strength_of_association, restricted='', only_chunks=True):
    """
    Calculate S_{ji} = S - ln((1+slots_j)/slots_ij), where j=chunk, i=otherchunk

    restricted specifies the slot name to which calculation is restricted.
    """
    chunk_dict = find_chunks(otherchunk, only_chunks)
    slotvalues = chunk_dict.items()
    values = chunk_dict.values()
    if chunk != otherchunk and chunk not in values:
        return 0
    else:
        if restricted:
            if (restricted, chunk) in slotvalues:
                if (restricted, chunk) not in dm.restricted_number_chunks:
                    slots_j = 1
                    for each in dm:
                        for x in each:
                            if x[0] == restricted and splitting(x[1]).values and chunk == splitting(x[1]).values:
                                slots_j += 1
                    dm.restricted_number_chunks.update({(restricted, chunk): slots_j})
                else:
                    slots_j = dm.restricted_number_chunks[(restricted, chunk)]
            else:
                return 0
        else:
            slots_j = 1
            if chunk not in dm.unrestricted_number_chunks:
                for each in dm:
                    for x in each:
                        if splitting(x[1]).values and chunk == splitting(x[1]).values:
                            slots_j += 1
                dm.unrestricted_number_chunks.update({chunk: slots_j})
            else:
                slots_j = dm.unrestricted_number_chunks[chunk]
    slots_ij = list(values).count(chunk)
    return strength_of_association - math.log(slots_j/max(1, slots_ij))

def spreading_activation(chunk, buffers, dm, buffer_spreading_activation, strength, restricted=False, only_chunks=True):
    """
    Calculate spreading activation.

    restricted states whether spreading activation should be restricted only to chunk names that share the same slot names.
    """
    SA = 0
    for each in buffer_spreading_activation:
        try:
            otherchunk = list(buffers[each])[0]
        except IndexError:
            continue
        w_kj = weigh_buffer(otherchunk, buffer_spreading_activation[each], only_chunks)
        s_ji = 0
        for each in find_chunks(otherchunk, only_chunks).items():
            if restricted:
                s_ji += calculate_strength_association(each[1], chunk, dm, strength, each[0], only_chunks)
            else:
                s_ji += calculate_strength_association(each[1], chunk, dm, strength, only_chunks=only_chunks)

        SA += w_kj*s_ji
    return SA

##########utilities for subsymbolic retrieval, general###########

def retrieval_success(activation, threshold):
    """
    If retrieval is successful, return the element.
    """
    return True if activation >= threshold else False

def retrieval_latency(activation, latency_factor, latency_exponent):
    """
    Calculate retrieval latency.
    """
    return latency_factor*(math.exp(-activation*latency_exponent))

##########utilities for calculating visual angle in vision###########

#assuming SCREEN_SIZE (pixels) = 1366:768
#assuming SIZE (cms) = 50:28
#assuming DISTANCE (cms) = 50

def calculate_visual_angle(start_position, final_position, screen_size, simulated_screen_size, viewing_distance):
    """
    Calculate visual angle, needed for vision module.
    
    start_position is the current focus
    final position is where the focus should be shifted
    screen_size is the size of the environment in simulation
    simulated_display_resolution in pixels - e.g., 1366:768
    simulated_screen_size in cm - e.g., 50cm : 28cm
    viewing distance in cm - e.g., 50cm
    """
    start_position = list(start_position)
    final_position = list(final_position)
    start_position[0] = float(start_position[0])
    start_position[1] = float(start_position[1])
    final_position[0] = float(final_position[0])
    final_position[1] = float(final_position[1])
    x_axis = final_position[0] - start_position[0]
    y_axis = final_position[1] - start_position[1]
    distance_sqrd = sum((x_axis**2, y_axis ** 2))
    distance = math.sqrt(distance_sqrd) #distance in pxs
    pxpercm = float(screen_size[0])/float(simulated_screen_size[0])
    distance = distance / pxpercm #distance in cm
    return math.atan2(distance, viewing_distance) 

def calculate_distance(angle_degree, screen_size, simulated_screen_size, viewing_distance):
    """
    Calculate distance from start position that is at the border given the visual angle.
    """
    angle = angle_degree*math.pi/180
    pxpercm = float(screen_size[0])/float(simulated_screen_size[0])
    return pxpercm*math.tan(angle) * viewing_distance

def calculate_pythagorian_distance(x, y):
    """
    x and y are 2D positions.
    """
    x = list(x)
    y = list(y)
    x[0] = float(x[0])
    x[1] = float(x[1])
    y[0] = float(y[0])
    y[1] = float(y[1])

    dist_sqrd = (x[0] - y[0]) ** 2 + (x[1] - y[1]) ** 2
    return math.sqrt(dist_sqrd)

def calculate_onedimensional_distance(x, y, horizontal=True):
    """
    x and y are 2D positions.
    
    horizontal checks whether we measure horizontal or vertical distance.
    """
    x = list(x)
    y = list(y)
    x[0] = float(x[0])
    x[1] = float(x[1])
    y[0] = float(y[0])
    y[1] = float(y[1])
    if horizontal:
        return abs(x[0] - y[0])
    else:
        return abs(x[1] - y[1])

def calculate_delay_visual_attention(angle_distance, K, k, emma_noise, vis_delay=None):
    """
    Delay in visual attention using EMMA model.
    
    Original formula: K*[-log frequency]*e^(k*distance). Simplified as: K * vis_delay * e^(k*distance).
    
    The modeller herself can decide how frequency should be hooked to delay via the parameter vis_delay.
    
    Distance is measured in degrees of visual angle.
    """
    if vis_delay:
        delay = K * float(vis_delay)* math.exp(k*float(angle_distance))
    else:
        delay = K * math.exp(k*float(angle_distance))
    if emma_noise:
        return np.random.gamma(shape=9, scale=delay/9)
    else:
        return delay

def calculate_preparation_time(emma_noise):
    """
    This function returns time to prepare eye mvt.
    """
    if emma_noise:
        return np.random.gamma(shape=9, scale=0.135/9)
    else:
        return 0.135

def calculate_execution_time(angle_distance, emma_noise):
    """
    This function returns execution time for eye mvt. Angle_distance is in radians.
    """
    degree_distance = 180*angle_distance/math.pi
    execution_time = 0.07 + 0.002*degree_distance
    if emma_noise:
        return np.random.gamma(shape=9, scale=execution_time/9)
    else:
        return execution_time


def calculate_landing_site(position, angle_distance, emma_landing_site_noise):
    """
    This function returns time to prepare eye mvt.
    """
    position = list(position)
    position[0] = float(position[0])
    position[1] = float(position[1])
    degree_distance = 180*angle_distance/math.pi
    if emma_landing_site_noise and degree_distance:
        cov_mat = [[0.1*degree_distance,0], [0,0.1*degree_distance]]
        return tuple(np.random.multivariate_normal(position, cov_mat))
    else:
        return tuple(position)

###########################################################
#########BELOW: CURRENTLY UNUSED FUNCTIONS#################
###########################################################


def splitting_submodules(string): #currently not used, maybe eventually !!!not used
    """
    Splitting info into variables and retrievals. Currently not used, but could be implemented for production rules.
    """
    variables = re.findall("(?<="+ ACTRVARIABLER+").*?(?=$)", string)
    retrievals = re.findall("(?<="+ ACTRRETRIEVER+").*?(?=$)", string)
    return {"variables": set(variables), "retrievals": set(retrievals)}

