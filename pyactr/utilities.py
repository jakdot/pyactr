"""
Helper functions used by ACT-R modules.
"""

import collections
import re
import math
import random

import numpy as np
import pyparsing as pp


#for querying buffers

_BUSY = "busy"
_FREE = "free"
_ERROR = "error"

#special charactes for chunks

ACTRVARIABLE = "="
ACTRVARIABLER = "\=" #used for regex
ACTRVALUE = "!"
ACTRVALUER = "\!" #used for regex
ACTRNEG = "~"
ACTRNEGR = "\~" #used for regex
ACTRRETRIEVE = "+"
ACTRRETRIEVER = "\+" #used for regex

MANUAL = "_manual"
VARVAL = "_variablesvalues"
VISUAL = "_visual"
VISUALLOCATION = "_visuallocation"

SPECIALCHUNKTYPES = {VARVAL: "variables, values, negvariables, negvalues", MANUAL: "cmd, key", VISUAL: "cmd, value, color, screen_pos", VISUALLOCATION: "screen_x, screen_y, color"}

#[{"test": {"position": (300, 170)}, "X": {"position": (300, 170)}}]

#special values for cmd in MANUAL

CMDMANUAL = set([None, "None", "press_key"])
CMDPRESSKEY = "press_key"

#special values for cmd in VISUAL

CMDVISUAL = set([None, "None", "move_attention"])
CMDMOVEATTENTION = "move_attention"

#special character for visual chunks

VISIONSMALLER = "<" # smaller than and 
VISIONGREATER = ">" #
VISIONLOWEST = "lowest" #
VISIONHIGHEST = "highest" #
VISIONCLOSEST = "closest" #

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
    Rounds time to tenths of miliseconds.
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
    Splitting info into variables, negative variables, values and negative values. Used in chunks. Info is a string, e.g., '=x~=y!2'. This is a depreciated approach.
    """
    varval = {"variables": set(), "values": set(), "negvariables": set(), "negvalues": set()}
    #assume it's a string
    varval["variables"] = set(re.findall("".join(["(?<=", "(?<!", ACTRNEGR, ")", ACTRVARIABLER, ").*?(?=$|", ACTRNEGR, "|", ACTRVALUER, "|", ACTRVARIABLER, ")"]), info))
    varval["values"] = set(re.findall("".join(["(?<=", "(?<!", ACTRNEGR, ")", ACTRVALUER, ").*?(?=$|", ACTRNEGR, "|", ACTRVALUER, "|", ACTRVARIABLER, ")"]), info))
    varval["negvariables"] = set(re.findall("".join(["(?<=", ACTRNEGR, ACTRVARIABLER, ").*?(?=$|", ACTRNEGR, "|", ACTRVALUER, "|", ACTRVARIABLER, ")"]), info))
    varval["negvalues"] = set(re.findall("".join(["(?<=", ACTRNEGR,  ACTRVALUER, ").*?(?=$|", ACTRNEGR, "|", ACTRVALUER, "|", ACTRVARIABLER, ")"]), info))
    if not any(varval.values()):
        varval["values"] = set([info]) #varval empty -> only values present

    assert len(set(varval["values"])) <= 1, "Any attribute must have at most one value"

    return varval

def splitting(info, empty=True):
    """
    Splitting info into variables, negative variables, values and negative values. Used in chunks.

    Info could either be a string, e.g., '=x~=y!2', or a special chunk 'variablesvalues', e.g., Chunk('_variablesvalues', variables='x', negvariables='y', values=2). Alternatively, info could consist only of a value.
    """
    varval = {"variables": set(), "values": set(), "negvariables": set(), "negvalues": set()}
    try: #assume it's a attr-val chunk
        if info.typename == "_variablesvalues":
            if empty:
                subpart = info.removeempty()
            else:
                subpart = info.removeunused()
            for x in subpart:
                if isinstance(x[1], tuple):
                    varval[x[0]] = set(x[1]) #tuples are iterated over and added to the set
                else:
                    varval[x[0]] = set([x[1]]) #other elements (strings, chunks) are added as a whole
        else:
            varval["values"] = set([info]) #not varval -> only a chunk present
    except AttributeError: #it's just values; this could happen for None, which lacks any structure
        if empty:
            if info != 'None' and info != None:
                varval["values"] = set([info])
        else:
            if info != None:
                varval["values"] = set([info])

    assert len(set(varval["values"])) <= 1, "Any attribute must have at most one value"

    return varval

def get_similarity(d, val1, val2):
    """
    Gets similarity for partial matching.
    """
    dis = d.get(tuple((val2, val1)), -1) #-1 is the default value
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
    varvalue = pp.Word("".join([pp.alphanums, "_"]))
    value = varvalue | special_value | strvalue | strvalue2
    chunk_reader = pp.OneOrMore(pp.Group(slot + value))
    return chunk_reader

def make_chunkparts_without_varconflicts(chunkpart, rule_name, variables):
    """
    Makes a chunk avoiding any variable names used in actrvariables. Uses new_name for naming, if possible.
    """
    varval = splitting(chunkpart, empty=False)
    temp_var = set()
    for x in varval['variables']:
        new_name = "".join([str(x), "__rule__", rule_name])
        if "".join(["=", new_name]) in variables:
            raise ACTRError("A name clash appeared when trying to compile two rules. Try to rename variables in the rule '%s'" %rule_name)
        else:
            temp_var.add(new_name)
    temp_negvar = set()
    for x in varval['negvariables']:
        new_name = "".join([str(x), "__rule__", rule_name])
        if "".join(["=", "new_name"]) in variables:
            raise ACTRError("A name clash appeared when trying to compile two rules. Try to rename variables in the rule '%s'" %rule_name)
        else:
            temp_negvar.add(new_name)
    varval['negvariables'] = temp_negvar
    varval['variables'] = temp_var
    new_varval = {key: varval[key] for key in varval if varval[key]}

    for key in new_varval:
        if len(new_varval[key]) == 1:
            new_varval[key] = new_varval[key].pop()
        else:
            new_varval[key] = tuple(new_varval[key])

    return new_varval

def make_chunkparts_with_new_vars(chunkpart, variable_dict, val_dict):
    """
    Makes a chunk changing variable names according to variable_dict.
    """
    varval = splitting(chunkpart, empty=False)
    temp_set = set()
    for x in varval["variables"]:
        if x not in val_dict:
            temp_set.add(variable_dict.setdefault(x, x))
        else:
            varval["values"].add(val_dict[x])
    varval["variables"] = temp_set
    temp_set = set()
    for x in varval["negvariables"]:
        if x not in val_dict:
            temp_set.add(variable_dict.setdefault(x, x))
        else:
            varval["negvalues"].add(val_dict[x])
    varval["negvariables"] = temp_set

    new_varval = {key: varval[key] for key in varval if varval[key]}

    for key in new_varval:
        if len(new_varval[key]) == 1:
            new_varval[key] = new_varval[key].pop()
        else:
            new_varval[key] = tuple(new_varval[key])

    return new_varval


def merge_chunkparts(chunkpart1, chunkpart2):
    """
    Chunkparts are merged as follows: chunkpart1 is used; info in chunkpart2 is added to chunkpart1
    """
    varval1 = splitting(chunkpart1, empty=False)
    varval2 = splitting(chunkpart2, empty=False)
    for key in varval1:
        if varval1[key]:
            break
    else:
        varval1 = varval2

    new_varval = {key: varval1[key] for key in varval1 if varval1[key]}

    #for key in varval1:
    #    if varval2[key] and not varval1[key]:
    #        varval1[key] = varval2[key]

    #new_varval = {key: varval1[key] for key in varval1 if varval1[key]}

    for key in new_varval:
        if len(new_varval[key]) == 1:
            new_varval[key] = new_varval[key].pop()
        else:
            new_varval[key] = tuple(new_varval[key])

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

def check_bound_vars(actrvariables, elem):
    """
    Check that elem is a bound variable, or not a variable. If the test goes through, return elem.
    """
    result = None
    varval = splitting(elem)
    for x in varval:
        for _ in range(len(varval[x])):
            if x == "variables":
                var = str(varval[x].pop())
                var = "".join([ACTRVARIABLE, var])
                try:
                    temp_result = actrvariables[var]
                except KeyError:
                    raise ACTRError("Object '%s' in the value '%s' is a variable that is not bound; this is illegal in ACT-R" % (var[1:], elem)) #is this correct? maybe in some special cases binding only in RHS should be allowed? If so this should be adjusted in productions.py
            if x == "values":
                temp_result = varval[x].pop()
            if x == "negvariables" or x == "negvalues":
                raise ACTRError("It is not allowed to define negative values or negative variables on the right hand side of ACT-R rules; the object '%s' is illegal in ACT-R" % elem)
            if result and temp_result != result:
                raise ACTRError("It looks like in '%s', one slot would have to carry two values at the same time; this is illegal in ACT-R" % elem)
            else:
                result = temp_result
    return result

def match(dict2, slotvals, name1, name2):
    """
    Matches variables that happen to be tied to the same slots. This function is used in production compilation. dict2 is the LHS of the second rule, slotvals is the dictionary based on the output of the first rule.
    """
    def temp_func(temp_set, temp_val):
        """
        temp_func gets a set of variables and a value (possibly, None), and it returns two dicts.
        matched stores which variables will be substituted by which variable, valued stores which variables will be substituted by a value (if temp_val not empy).
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

            if isinstance(chunkdict3, collections.MutableSequence): #this is retrieval, it consists of mutable sequence -- 0=chunk description in the 1st rule; 1=retrieved chunk
                for elem in chunkdict2:
                    chunkpart2 = splitting(chunkdict2[elem], empty=False)
                    try:
                        chunkpart3 = splitting(chunkdict3[0][elem], empty=False)
                    except KeyError:
                        chunkpart3 = splitting(None)
                    try:
                        temp_val = getattr(chunkdict3[1], elem).values
                    except AttributeError:
                        temp_val = None
                    temp_set = set()
                    temp_set.update(chunkpart2["variables"])
                    temp_set.update(chunkpart3["variables"])
                    matched, valued = temp_func(temp_set, temp_val)
                slotvals.pop(buff) #info about retrieved element has been fully used, it can be discarded now
            else: #anything else but retrieval is here
                for elem in chunkdict2:
                    chunkpart2 = splitting(chunkdict2[elem], empty=False)
                    try:
                        chunkpart3 = splitting(chunkdict3[elem], empty=False)
                    except KeyError:
                        chunkpart3 = splitting(None)

                    temp_set = set()
                    temp_set.update(chunkpart2["variables"])
                    temp_set.update(chunkpart3["variables"])
                    temp_val, val2, val3 = None, None, None
                    if chunkpart2["values"]:
                        val2 = chunkpart2["values"].pop()
                    if chunkpart3["values"]:
                        val3 = chunkpart3["values"].pop()

                    if val2 and val3 and val2 != val3:
                        raise ACTRError("The values in rules '%s' and '%s' do not match, production compilation failed" % (name1, name2))
            
                    temp_val = val2 or val3

                    matched, valued = temp_func(temp_set, temp_val)

    return matched, valued
            


def modify_utilities(time, reward, rules, model_parameters):
    """
    Returns a new dict of rules, updated with newly calculated utilites for rules whose firing led to reward.
    """
    for rulename in rules:
        if rules[rulename]["selecting_time"] != []:
            for t in rules[rulename]["selecting_time"]:
                utility_time = time-t
                rules[rulename]["utility"] = round(rules[rulename]["utility"] + model_parameters["utility_alpha"]*(reward-utility_time-rules[rulename]["utility"]), 4)
            rules[rulename]["selecting_time"] = []

def calculate_setting_time(updated, model_parameters):
    """
    Calculates time to set a chunk in a buffer.
    """
    try:
        val = updated.set_delay
    except AttributeError:
        val = 0
    return val

#############utilities for baselevel learning and noise######################################

def baselevel_learning(current_time, times, bll, decay):
    """
    Calculates base-level learning: B_i = ln(sum(t_j^{-decay})) for t_j = current_time - t for t in times.
    """
    B = 0
    if bll:
        B = math.log(sum((current_time - x) ** (-decay) for x in times))
    return B

def calculate_instantanoues_noise(instantaneous_noise):
    """
    Calculates noise, generated by logistic distribution with mean 0 and variance = ( pi^2/3 ) * s^2 where s = instantaneous_noise.
    """
    assert instantaneous_noise >= 0, "Instantaneous noise must be positive"
    if instantaneous_noise == 0:
        return 0
    else:
        return np.random.logistic(0, instantaneous_noise, 1)[0]

#############utilities for source activation######################################

def weigh_buffer(chunk, weight_k):
    """
    Calculates w_{kj}=w_k/n_k. That is, you supply chunk and its activation w_k and it divides w_k by the number of chunks in w_k.
    """
    n_k = len(tuple(find_chunks(chunk)))
    if n_k == 0:
        weight_kj = 0
    else:
        weight_kj = weight_k/n_k
    return weight_kj

def find_chunks(chunk):
    """
    Find chunks as values in slots in the chunk 'chunk'.
    """
    chunk_list = []
    for x in chunk:
        try:
            val = splitting(x[1])['values'].pop()
        except KeyError:
            pass
        else:
            if val != 'None' and not isinstance(val, str):
                chunk_list.append(val)
    return chunk_list

def calculate_strength_association(chunk, otherchunk, dm, strength_of_association):
    """
    Calculates S_{ji} = S - ln((1+slots_j)/slots_ij), where j=chunk, i=otherchunk
    """
    if chunk != otherchunk and chunk not in otherchunk._asdict().values():
        return 0
    else:
        slots_j = 0
        for each in dm:
            if chunk in set(x[1] for x in each):
                slots_j += list(x[1] for x in each).count(chunk)
    slots_ij = list(otherchunk._asdict().values()).count(chunk)
    return strength_of_association - math.log((1 + slots_j)/max(1, slots_ij))

def spreading_activation(chunk, buffers, dm, buffer_spreading_activation, strength):
    """
    Calculates spreading activation.
    """
    SA = 0
    for each in buffer_spreading_activation:
        otherchunk = list(buffers[each])[0]
        w_kj = weigh_buffer(otherchunk, buffer_spreading_activation[each])
        s_ji = 0
        for each in find_chunks(otherchunk):
            s_ji += calculate_strength_association(each, chunk, dm, strength)
        SA += w_kj*s_ji
    return SA

##########utilities for subsymbolic retrieval, general###########

def retrieval_success(activation, threshold):
    """
    If retrieval successful, return the element.
    """
    return True if activation >= threshold else False

def retrieval_latency(activation, latency_factor, latency_exponent):
    """
    Calculates retrieval latency.
    """
    return latency_factor*(math.exp(-activation*latency_exponent))

##########utilities for calculating visual angle in vision###########

#assuming SCREEN_SIZE (pixels) = 1366:768
#assuming SIZE (cms) = 50:28
#assuming DISTANCE (cms) = 50

def calculate_visual_angle(start_position, final_position, screen_size, simulated_screen_size, viewing_distance):
    """
    Calculates visual angle, needed for vision module. start_position is the current focus, final position is where the focus should be shifted. screen_size is the size of the environment in simulation, simulated_display_resolution in pixels - e.g., 1366:768, simulated_screen_size in cm - e.g., 50cm : 28cm, viewing distance in cm - e.g., 50cm
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
    return math.atan2(distance, viewing_distance) #50 cm distance

def calculate_distance(angle_degree, screen_size, simulated_screen_size, viewing_distance):
    """
    Calculates distance from start position that is at the border given the visual angle.
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

def calculate_delay_visual_attention(angle_distance, K, k, emma_noise, frequency=None):
    """
    Delay in visual attention using EMMA model: K*[-log frequency]*e^(k*distance). Distance is measured in degrees of visual angle.
    """
    if frequency:
        delay = K * (-math.log(float(frequency)))* math.exp(k*float(angle_distance))
    else:
        delay = K * math.exp(k*float(angle_distance))
    if emma_noise:
        return np.random.gamma(shape=9, scale=delay/9)
    else:
        return delay

def calculate_preparation_time(emma_noise):
    """
    Returns time to prepare eye mvt.
    """
    if emma_noise:
        return np.random.gamma(shape=9, scale=0.135/9)
    else:
        return 0.135

def calculate_execution_time(angle_distance, emma_noise):
    """
    Returns execution time for eye mvt. Angle_distance is in radians.
    """
    degree_distance = 180*angle_distance/math.pi
    execution_time = 0.07 + 0.002*degree_distance
    if emma_noise:
        return np.random.gamma(shape=9, scale=execution_time/9)
    else:
        return execution_time

def calculate_landing_site(position, angle_distance, emma_noise):
    """
    Returns time to prepare eye mvt.
    """
    position = list(position)
    position[0] = float(position[0])
    position[1] = float(position[1])
    degree_distance = 180*angle_distance/math.pi
    if emma_noise and degree_distance:
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

