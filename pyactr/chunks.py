"""
Chunks
"""

import collections
import re
import random
import warnings

import pyactr.utilities as utilities
from pyactr.utilities import ACTRError

def chunktype(cls_name, field_names, verbose=False):
    """
    Creates type chunk. Works like namedtuple.
    """
    if cls_name in utilities.SPECIALCHUNKTYPES and field_names != utilities.SPECIALCHUNKTYPES[cls_name]:
        raise ACTRError("You cannot redefine attributes of the chunk type '%s'; you can only use the attributes '%s'" % (cls_name, utilities.SPECIALCHUNKTYPES[cls_name]))

    try:
        field_names = field_names.replace(',', ' ').split()
    except AttributeError:  # no .replace or .split
        pass  # assume it's already a sequence of identifiers
    field_names = tuple(sorted(name + "_" for name in field_names))
    for each in field_names:
        if each == "ISA" or each == "isa":
            raise ACTRError("You cannot use the attribute 'isa' in your chunk. That attribute is used to define chunktypes.")
    
    Chunk._chunktypes.update({cls_name:collections.namedtuple(cls_name, field_names, verbose)}) #chunktypes are not returned; they are stored as Chunk class attribute

class Chunk(collections.Sequence):
    """
    ACT-R chunks. Based on namedtuple (tuple with dictionary-like properties).
    """

    class EmptyValue(object):
        """
        Empty values used in chunks. These are None values.
        """

        def __init__(self):
            self.value = None

        def __eq__(self, val):
            if val == None or val == "None":
                return True #Chunks make strings out of values; (this holds for everything but cases in which chunks themselves are values); so, None will be turned into a string as well, hence the equality
            else:
                return False

        def __hash__(self):
            return hash(None)

        def __repr__(self):
            return repr(None)

    _chunktypes = {}
    _undefinedchunktypecounter = 0
    _chunks = {}

    __emptyvalue = EmptyValue()

    _similarities = {} #dict of similarities between chunks

    def __init__(self, typename, **dictionary):
        self.typename = typename
        self.boundvars = {} #dict of bound variables

        kwargs = {}
        for key in dictionary:

            #change values (and values in a tuple) into string, when possible
            if not isinstance(dictionary[key], collections.Sequence):
                dictionary[key] = str(dictionary[key])

            elif type(dictionary[key]) == tuple:
                dictionary[key] = tuple(str(x) if not isinstance(dictionary[key], Chunk) else x for x in dictionary[key])

            #adding _ to minimize/avoid name clashes
            kwargs[key+"_"] = dictionary[key]
        try:
            for elem in self._chunktypes[typename]._fields:

                if elem not in kwargs:

                    kwargs[elem] = self.__emptyvalue #emptyvalues are explicitly added to attributes that were left out
                    dictionary[elem[:-1]] = self.__emptyvalue #emptyvalues are also added to attributes in the original dictionary (since this might be used for chunktype creation later)

            if set(self._chunktypes[typename]._fields) != set(kwargs.keys()):

                chunktype(typename, dictionary.keys())  #If there are more args than in the original chunktype, chunktype has to be created again, with slots for new attributes
                warnings.warn("Chunk type %s is extended with new attributes" % typename)

        except KeyError:

            chunktype(typename, dictionary.keys())  #If chunktype completely missing, it is created first
            warnings.warn("Chunk type %s was not defined; added automatically" % typename)

        finally:
            self.actrchunk = self._chunktypes[typename](**kwargs)

    def _asdict(self):
        """
        Creates a dictionary out of chunk.
        """
        temp_dict = self.actrchunk._asdict()
        dictionary = {re.sub("_$", "", key): temp_dict[key] for key in temp_dict}
        return dictionary

    def __eq__(self, otherchunk):
        if hash(self) == hash(otherchunk):
            return True
        else:
            return False

    def __getattr__(self, name):
        if hasattr(self.actrchunk, name + "_"):
            return getattr(self.actrchunk, name + "_")
        else:
            raise AttributeError("Chunk has no such attribute")

    def __getitem__(self, pos):
        return re.sub("_$", "", self.actrchunk._fields[pos]), self.actrchunk[pos]

    def __hash__(self):
        def func():
            for x in self.removeempty():
                varval = sorted(utilities.splitting(x[1]).items(), reverse=True) #(neg)values and (neg)variables have to be checked
                for idx in range(len(varval)):
                    for _ in range(len(varval[idx][1])):
                        value = varval[idx][1].pop()
                        if idx == 0 or idx == 2: #idx == 0 -> variables; idx == 2 -> negvariables
                            try:
                                varval[idx+1][1].add(self.boundvars[utilities.ACTRVARIABLE + value]) #add value based on a variable
                            except KeyError:
                                yield tuple([x[0], tuple([varval[idx][0], hash(value)])]) #get hash of variable if it is not bound
                        else:
                            yield tuple([x[0], tuple([varval[idx][0], hash(value)])]) #values get their hash directly
        return hash(tuple(func()))

    def __iter__(self):
        for x, y in zip(self.actrchunk._fields, self.actrchunk):
            yield re.sub("_$", "", x), y

    def __len__(self):
        return len(self.actrchunk)

    def __repr__(self):
        reprtxt = ""
        for x, y in self:
            try:
                if y.typename == utilities.VARVAL:
                    temp = y.removeunused()
                    y = ""
                    for elem in temp:
                        if elem[0] == "values":
                            y = "".join([y, str(elem[1])])
                        elif elem[0] == "negvalues":
                            if not isinstance(elem[1], str):
                                for each in elem[1]:
                                    y = "".join([y, "~", str(each)])
                            else:
                                y = "".join([y, "~", str(elem[1])])
                        elif elem[0] == "variables":
                            y = "".join([y, "=", str(elem[1])])
                        elif elem[0] == "negvariables":
                            if not isinstance(elem[1], str):
                                for each in elem[1]:
                                    y = "".join([y, "~=", str(each)])
                            else:
                                y = "".join([y, "~=", str(elem[1])])
            except AttributeError:
                if y == None:
                    y = ""
                pass
            if reprtxt:
                reprtxt = ", ".join([reprtxt, '%s= %s' % (x, y)])
            else:
                reprtxt = '%s= %s' % (x, y)
        return "".join([self.typename, "(", reprtxt, ")"])

    def __lt__(self, otherchunk):
        """
        Checks whether one chunk is proper part of another (given bound variables in boundvars).
        """
        if self == otherchunk:
            return False
        else:
            final_val = self.match(otherchunk)
        if final_val < 0:
            return False
        else:
            return True

    def __le__(self, otherchunk):
        """
        Checks whether one chunk is part of another (given boundvariables in boundvars).
        """
        if self == otherchunk:
            return True
        else:
            return self < otherchunk

    def match(self, otherchunk):
        """
        Checks partial match (given bound variables in boundvars).
        """
        similarity = 0
        if self == otherchunk:
            return similarity
        #below starts the check that self is proper part of otherchunk. __emptyvalue is ignored. 4 cases have to be checked separately, =x, ~=x, !1, ~!1. Also, variables and their values have to be saved in boundvars. When self is not part of otherchunk the loop adds to (dis)similarity.
        for x in self:

            try:
                matching_val = getattr(otherchunk.actrchunk, x[0] + "_") #get the value of attr
            except AttributeError:
                matching_val = None #if it is missing, it must be None

            try:
                if matching_val.typename == utilities.VARVAL:
                    matching_val = matching_val.values #the value might be written using _variablesvalues chunk; in that case, get it out
            except AttributeError:
                pass

            varval = utilities.splitting(x[1], empty=False)

            #checking variables, e.g., =x
            if varval["variables"] != self.__emptyvalue and varval["variables"]:
                #if matching_val == self.__emptyvalue:
                #    similarity -= 1 #these two lines would require that variables are matched only to existing values; uncomment if you want that
                for var in varval["variables"]:
                    for each in self.boundvars.get("~=" + var, set()):
                        if each == matching_val:
                            similarity += utilities.get_similarity(self._similarities, each, matching_val) #False if otherchunk's value among the values of ~=x
                    try:
                        if self.boundvars["=" + var] != matching_val:
                            similarity += utilities.get_similarity(self._similarities, self.boundvars["=" + var], matching_val) #False if =x does not match otherchunks' value
                    except KeyError:
                        self.boundvars.update({"=" + var: matching_val}) #if boundvars lack =x, update and proceed

            #checking negvariables, e.g., ~=x
            if varval["negvariables"] != self.__emptyvalue and varval["negvariables"]:
                for var in varval["negvariables"]:
                    try:
                        if self.boundvars["=" + var] == matching_val:
                            similarity += utilities.get_similarity(self._similarities, self.boundvars["=" + var], matching_val) #False if =x does not match otherchunks' value
                    except KeyError:
                        pass
                    self.boundvars.setdefault("~=" + var, set([])).add(matching_val)

            #checking values, e.g., 10 or !10

            if varval["values"]:
                val = varval["values"].pop()
                if val != None and val != matching_val: #None is the misssing value of the attribute
                    similarity += utilities.get_similarity(self._similarities, val, matching_val) 
            #checking negvalues, e.g., ~!10
            if varval["negvalues"]:
                for negval in varval["negvalues"]:
                    if negval == matching_val:
                       similarity += utilities.get_similarity(self._similarities, negval, matching_val)
        return similarity

    def removeempty(self):
        """
        Removes attribute-value pairs that have the value __emptyvalue. Careful! Returns a generator with attr-value pairs.
        """
        def func():
            for x in self:
                try:
                    if x[1].removeempty():
                        if x[1] != self.__emptyvalue:
                            yield x
                except AttributeError:
                    if x[1] != self.__emptyvalue:
                        yield x
        return tuple(func())

    def removeunused(self):
        """
        Removes values that were only added to fill in empty slots, using None. Careful! Returns a generator with attr-value pairs.
        """
        def func():
            for x in self:
                try:
                    if x[1].removeunused():
                        if x[1] != None:
                            yield x
                except AttributeError:
                    if x[1] != None:
                        yield x
        return tuple(func())
        #return (x for x in self if x[1] != None) old version

#special chunk that can be used in production rules
for key in utilities.SPECIALCHUNKTYPES:
    chunktype(key, utilities.SPECIALCHUNKTYPES[key])

def createchunkdict(chunk):
    """
    Returns typename and chunkdict from pyparsed list.
    """
    sp_dict = {utilities.ACTRVARIABLE: "variables", utilities.ACTRNEG: "negvalues", utilities.ACTRNEG + utilities.ACTRVARIABLE: "negvariables", utilities.ACTRVALUE: "values", utilities.ACTRNEG + utilities.ACTRVALUE: "negvalues"}
    chunk_dict = {}
    for elem in chunk:
        temp_dict = chunk_dict.get(elem[0], Chunk(utilities.VARVAL))._asdict()

        if not temp_dict['negvalues'] or temp_dict['negvalues'] == Chunk.EmptyValue():
            temp_dict['negvalues'] = set()
        else:
            temp_dict["negvalues"] = set(temp_dict["negvalues"])
        if not temp_dict['negvariables'] or temp_dict['negvariables'] == Chunk.EmptyValue():
            temp_dict['negvariables'] = set() #these two can carry multiple values
        else:
            temp_dict["negvariables"] = set(temp_dict["negvariables"])
        for idx in range(1, len(elem)):
            try:
                if elem[idx][0] == utilities.VISIONGREATER or elem[idx][0] == utilities.VISIONSMALLER: #this checks special visual conditions on greater/smaller than
                    updating = 'values'
                    update_val = elem[idx][0] + elem[idx][1]
                elif elem[idx][1][0] == "'" or elem[idx][1][0] == '"':
                    updating = sp_dict[elem[idx][0]]
                    update_val = elem[idx][1][1:-1]
                else:
                    updating = sp_dict[elem[idx][0]]
                    update_val = elem[idx][1]

            except (KeyError, IndexError): #indexerror --> only a string is present; keyerror: the first element in elem[idx] is not a special symbol given above
                if elem[idx][0] == "'" or elem[idx][0] == '"':
                    update_val = elem[idx][1:-1]
                    updating = 'values'
                    temp_dict[updating] = update_val
                else:
                    updating = 'values'
                    try:
                        update_val = Chunk._chunks[elem[idx]]
                    except KeyError:
                        update_val = elem[idx]
            finally:
                if updating == "negvariables" or updating == "negvalues":
                    temp_dict[updating].add(update_val)
                else:
                    temp_dict[updating] = update_val
        
        if temp_dict["negvalues"]:
            temp_dict["negvalues"] = tuple(temp_dict["negvalues"])
        else:
            temp_dict["negvalues"] = None
        if temp_dict["negvariables"]:
            temp_dict["negvariables"] = tuple(temp_dict["negvariables"])
        else:
            temp_dict["negvariables"] = None

        temp_dict = {k: v for k, v in temp_dict.items() if v != None}
        chunk_dict[elem[0]] = Chunk(utilities.VARVAL, **temp_dict)
    type_chunk = ""
    try:
        type_chunk = chunk_dict.pop("isa").values #change this - any combination of capital/small letters
        type_chunk = chunk_dict.pop("ISA").values
        type_chunk = chunk_dict.pop("Isa").values
    except KeyError:
        pass
    return type_chunk, chunk_dict

def makechunk(nameofchunk="", typename="", **dictionary):
    """
    Creates a chunk.
    """
    if not nameofchunk:
        nameofchunk = "unnamedchunk"
    if not typename:
        typename = "undefined" + str(Chunk._undefinedchunktypecounter)
        Chunk._undefinedchunktypecounter += 1
    for key in dictionary:
        #create varval if not created explicitly, i.e., if this chunk itself is not a varval
        if typename != utilities.VARVAL and not isinstance(dictionary[key], Chunk):
            temp_dict = utilities.stringsplitting(str(dictionary[key]))
            loop_dict = temp_dict.copy()
            for x in loop_dict:
                if loop_dict[x]:
                    if x == "negvariables" or x == "negvalues":
                        val = tuple(temp_dict[x])
                    else:
                        val = temp_dict[x].pop()
                    temp_dict[x] = val
                else:
                    temp_dict.pop(x) 
            dictionary[key] = Chunk(utilities.VARVAL, **temp_dict)

    created_chunk = Chunk(typename, **dictionary)
    created_chunk._chunks[nameofchunk] = created_chunk
    return created_chunk

def chunkstring(name='', string=''):
    """
    Returns a chunk when given a string. The string is specified in the form: slot value slot value (arbitrary number of slot-value pairs can be used). isa-slot is used as the type of chunk. If no isa-slot is provided, chunk is assigned an 'undefined' type.
    """
    chunk_reader = utilities.getchunk()
    chunk = chunk_reader.parseString(string, parseAll=True)
    type_chunk, chunk_dict = createchunkdict(chunk)
    created_chunk = makechunk(name, type_chunk, **chunk_dict)
    return created_chunk
