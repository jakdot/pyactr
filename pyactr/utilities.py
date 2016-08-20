"""
Helper functions used by ACT-R modules.
"""

import collections
import re
import math
import numpy as np
import pyparsing as pp

#for querying buffers

_BUSY = "busy"
_FREE = "free"
_ERROR = "error"
_VISAUTOBUFFERING = "auto_buffering"

#for chunks

ACTRVARIABLE = "="
ACTRVARIABLER = "\=" #used for regex
ACTRVALUE = "!"
ACTRVALUER = "\!" #used for regex
ACTRNEG = "~"
ACTRNEGR = "\~" #used for regex
ACTRRETRIEVE = "+"
ACTRRETRIEVER = "\+" #used for regex

#special chunk that can be used in production rules
Varval = collections.namedtuple("_variablesvalues", "variables, values, negvariables, negvalues")

#for Events

Event = collections.namedtuple('Event', 'time proc action')

#for rules

_UNKNOWN = "UNKNOWN"
_PROCEDURAL = "PROCEDURAL"
_EMPTY = ""
_ENV = "ENVIRONMENT"

_RHSCONVENTIONS = {"?": "extra_test", "=": "modify", "+": "retrieveorset",\
        "!": "execute", "~": "clear", "@": "overwrite", "*": "modify_request"}
_LHSCONVENTIONS = {"=": "test", "?": "query"}
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

def splitting(info, empty=True):
    """
    Splitting info into variables, negative variables, values and negative values. Used in chunks.

    Info could either be a string, e.g., '=x~=y!2', or a special chunk 'variablesvalues', e.g., Chunk('_variablesvalues', variables='x', negvariables='y', values=2). Alternatively, info could consist only of a value.
    """
    varval = {"variables": set(), "values": set(), "negvariables": set(), "negvalues": set()}
    try: #assume it's a string
        varval["variables"] = set(re.findall("(?<="+"(?<!"+ACTRNEGR+")"+ ACTRVARIABLER+").*?(?=$|"+ACTRNEGR+"|"+ACTRVALUER+"|"+ACTRVARIABLER+")", info))
        varval["values"] = set(re.findall("(?<="+"(?<!"+ACTRNEGR+")"+ ACTRVALUER+").*?(?=$|"+ACTRNEGR+"|"+ACTRVALUER+"|"+ACTRVARIABLER+")", info))
        varval["negvariables"] = set(re.findall("(?<="+ACTRNEGR+ ACTRVARIABLER+").*?(?=$|"+ACTRNEGR+"|"+ACTRVALUER+"|"+ACTRVARIABLER+")", info))
        varval["negvalues"] = set(re.findall("(?<="+ACTRNEGR+ ACTRVALUER+").*?(?=$|"+ACTRNEGR+"|"+ACTRVALUER+"|"+ACTRVARIABLER+")", info))
    except TypeError:
        try: #assume it's a attr-val chunk
            if info.typename == "_variablesvalues":
                if empty:
                    subpart = info.removeempty()
                else:
                    subpart = info.removeunused()
                for x in subpart:
                    if isinstance(x[1], tuple) or isinstance(x[1], set):
                        varval[x[0]] = set(x[1]) #tuples and sets are iterated over and added to the set
                    else:
                        varval[x[0]] = set([x[1]]) #other elements (strings, chunks) are added as a whole
            else:
                varval["values"] = set([info]) #varval empty -> only a chunk present
        except AttributeError: #it's just values
            pass
    else:
        if not any(varval.values()):
            varval["values"] = set([info]) #varval empty -> only values present

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
    slot = pp.Word(pp.alphas + "_", pp.alphanums + "_")
    special_value = pp.Group(pp.oneOf([ACTRVARIABLE, ACTRNEG + ACTRVARIABLE, ACTRNEG])\
            + pp.Word(pp.alphanums + "_" + '"' + "'"))
    strvalue = pp.QuotedString('"', unquoteResults=False)
    strvalue2 = pp.QuotedString("'", unquoteResults=False)
    varvalue = pp.Word(pp.alphanums + "_")
    value = varvalue | special_value | strvalue | strvalue2
    chunk_reader = pp.OneOrMore(pp.Group(slot + value))
    return chunk_reader

#############utilities for rules######################################

def getrule():
    """
    Using pyparsing, get rule out of a string.
    """
    arrow = pp.Literal("==>")
    buff = pp.Word(pp.alphas, pp.alphanums + "_")
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
                var = ACTRVARIABLE + var
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
    Find chunks as values in slots in the chunk chunk.
    """
    return (x[1] for x in chunk if x[1] != None and not isinstance(x[1], str))

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

def retrieval_latency(activation, latency_factor):
    """
    Calculates base-level learning: B_i = ln(sum(t_j^{-decay})) for t_j = current_time - t for t in times.
    """
    return latency_factor*(math.exp(-activation))



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

