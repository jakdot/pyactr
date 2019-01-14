"""
Chunks
"""

import collections
import re
import random
import warnings
import numbers

import pyactr.utilities as utilities
from pyactr.utilities import ACTRError

def chunktype(cls_name, field_names, defaults=None):
    """
    Creates type chunk. Works like namedtuple.

    For example:
    >>> chunktype('chunktype_example0', 'value')

    :param field_names: an iterable or a string of slot names separated by spaces
    :param defaults: default values for the slots, given as an iterable, counting from the last element
    """
    if cls_name in utilities.SPECIALCHUNKTYPES and field_names != utilities.SPECIALCHUNKTYPES[cls_name]:
        raise ACTRError("You cannot redefine slots of the chunk type '%s'; you can only use the slots '%s'" % (cls_name, utilities.SPECIALCHUNKTYPES[cls_name]))

    try:
        field_names = field_names.replace(',', ' ').split()
    except AttributeError:  # no .replace or .split
        pass  # assume it's already a sequence of identifiers
    field_names = tuple(sorted(name + "_" for name in field_names))
    for each in field_names:
        if each == "ISA" or each == "isa":
            raise ACTRError("You cannot use the slot 'isa' in your chunk. That slot is used to define chunktypes.")
    try:
        Chunk._chunktypes.update({cls_name:collections.namedtuple(cls_name, field_names, defaults=defaults)}) #chunktypes are not returned; they are stored as Chunk class attribute
    except TypeError:
        Chunk._chunktypes.update({cls_name:collections.namedtuple(cls_name, field_names)}) #chunktypes are not returned; they are stored as Chunk class attribute

class Chunk(collections.Sequence):
    """
    ACT-R chunks. Based on namedtuple (tuple with dictionary-like properties).

    For example:
    >>> Chunk('chunktype_example0', value='one')
    chunktype_example0(value= one)
    """

    class EmptyValue(object):
        """
        Empty values used in chunks. These are None values.
        """

        def __init__(self):
            self.value = utilities.EMPTYVALUE

        def __eq__(self, val):
            if val == utilities.EMPTYVALUE or val == str(utilities.EMPTYVALUE):
                return True #Chunks make strings out of values; (this holds for everything but cases in which chunks themselves are values); so, None will be turned into a string as well, hence the equality
            else:
                return False

        def __hash__(self):
            return hash(self.value)

        def __repr__(self):
            return repr(self.value)

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

            #change values (and values in a tuple) into string, when possible (when the value is not another chunk)
            if isinstance(dictionary[key], Chunk):
                dictionary[key] = utilities.VarvalClass(variables=None, values=dictionary[key], negvariables=(), negvalues=())

            elif isinstance(dictionary[key], utilities.VarvalClass):
                for x in dictionary[key]._fields:
                    if x in {"values", "variables"} and not isinstance(getattr(dictionary[key], x), str) and getattr(dictionary[key], x) != self.__emptyvalue and not isinstance(getattr(dictionary[key], x), Chunk):
                        raise TypeError("Values and variables must be strings, chunks or empty (None)")

                    elif x in {"negvariables", "negvalues"} and (not isinstance(getattr(dictionary[key], x), collections.abc.Sequence) or isinstance(getattr(dictionary[key], x), collections.abc.MutableSequence)):
                        raise TypeError("Negvalues and negvariables must be tuples")

            elif (isinstance(dictionary[key], collections.abc.Iterable) and not isinstance(dictionary[key], str)) or not isinstance(dictionary[key], collections.abc.Hashable):
                raise ValueError("The value of a chunk slot must be hashable and not iterable; you are using an illegal type for the value of the chunk slot %s, namely %s" % (key, type(dictionary[key])))

            else:
                #create namedtuple varval and split dictionary[key] into variables, values, negvariables, negvalues
                try:
                    temp_dict = utilities.stringsplitting(str(dictionary[key]))
                except utilities.ACTRError as e:
                    raise utilities.ACTRError("The chunk %s is not defined correctly; %s" %(dictionary[key], e))
                loop_dict = temp_dict.copy()
                for x in loop_dict:
                    if x == "negvariables" or x == "negvalues":
                        val = tuple(temp_dict[x])
                    else:
                        try:
                            val = temp_dict[x].pop()
                        except KeyError:
                            val = None
                    temp_dict[x] = val
                dictionary[key] = utilities.VarvalClass(**temp_dict)

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

        self.__empty = None #this will store what the chunk looks like without empty values (the values will be stored on the first call of the relevant function)
        self.__unused = None #this will store what the chunk looks like without unused values
        self.__hash = None, self.boundvars.copy() #this will store the hash along with variables (hash changes if some variables are resolved)

    def _asdict(self):
        """
        Create a dictionary out of chunk.
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
        if self.__hash[0] and self.boundvars == self.__hash[1]:
            return self.__hash[0]
        def hash_func():
            for x in self.removeempty():
                varval = utilities.splitting(x[1])
                temp_varval = {"values": set(), "negvalues": set()}
                for key in ["variables", "negvariables"]:
                    if getattr(varval, key):
                        for value in getattr(varval, key):
                            try:
                                temp_varval[re.sub("variables", "values", key)].add(self.boundvars[utilities.ACTRVARIABLE + value]) #add (neg)value based on the (neg)variable
                            except KeyError:
                                if x[0]:
                                    yield tuple([x[0], tuple([key, hash(value)])]) #get hash of variable if it is not bound
                                else:
                                    yield tuple([key, hash(value)])
                for key in ["values", "negvalues"]:
                    if key == "values" and getattr(varval, key) != self.__emptyvalue:
                        temp_varval[key].update(set([getattr(varval, key)]))
                    elif key == "negvalues":
                        temp_varval[key].update(set(getattr(varval, key)))
                    if temp_varval[key]:
                        for value in temp_varval[key]:
                            if x[0]:
                                yield tuple([x[0], tuple([key, hash(value)])]) #values get their hash directly
                            else:
                                yield tuple([key, hash(value)])

        self.__hash = hash(tuple(hash_func())), self.boundvars.copy() #store the hash along with the vars used to calculate it, so it doesnt need to be recalculated
        return self.__hash[0]

    def __iter__(self):
        for x, y in zip(self.actrchunk._fields, self.actrchunk):
            yield re.sub("_$", "", x), y

    def __len__(self):
        return len(self.actrchunk)

    def __repr__(self):
        reprtxt = ""
        for x, y in self:
            if isinstance(y, utilities.VarvalClass):
                y = str(y)
            elif isinstance(y, self.EmptyValue):
                y = ""
            if reprtxt:
                reprtxt = ", ".join([reprtxt, '%s= %s' % (x, y)])
            elif x:
                reprtxt = '%s= %s' % (x, y)
            else:
                reprtxt = '%s' % y
        return "".join([self.typename, "(", reprtxt, ")"])

    def __lt__(self, otherchunk):
        """
        Check whether one chunk is proper part of another (given bound variables in boundvars).
        """
        return not self == otherchunk and self.match(otherchunk, partialmatching=False)

    def __le__(self, otherchunk):
        """
        Check whether one chunk is part of another (given boundvariables in boundvars).
        """
        return self == otherchunk or self.match(otherchunk, partialmatching=False) #actually, the second disjunct should be enough -- TODO: check why it fails in some cases; this might be important for partial matching

    def match(self, otherchunk, partialmatching, mismatch_penalty=1):
        """
        Check partial match (given bound variables in boundvars).
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

            if isinstance(matching_val, utilities.VarvalClass):
                matching_val = matching_val.values #the value might be written using _variablesvalues namedtuple; in that case, get it out
            varval = utilities.splitting(x[1])

            #checking variables, e.g., =x
            if varval.variables:
                #if matching_val == self.__emptyvalue:
                #    similarity -= 1 #these two lines would require that variables are matched only to existing values; uncomment if you want that
                    var = varval.variables
                    for each in self.boundvars.get("~=" + var, set()):
                        if each == matching_val:
                            if partialmatching:
                                similarity += utilities.get_similarity(self._similarities, each, matching_val, mismatch_penalty) #False if otherchunk's value among the values of ~=x
                            else:
                                return False
                    try:
                        if self.boundvars["=" + var] != matching_val:
                            if partialmatching:
                                similarity += utilities.get_similarity(self._similarities, self.boundvars["=" + var], matching_val, mismatch_penalty) #False if =x does not match otherchunks' value
                            else:
                                return False
                    except KeyError:
                        self.boundvars.update({"=" + var: matching_val}) #if boundvars lack =x, update and proceed

            #checking negvariables, e.g., ~=x
            if varval.negvariables:
                for var in varval.negvariables:
                    try:
                        if self.boundvars["=" + var] == matching_val:
                            if partialmatching:
                                similarity += utilities.get_similarity(self._similarities, self.boundvars["=" + var], matching_val, mismatch_penalty) #False if =x does not match otherchunks' value
                            else:
                                return False
                    except KeyError:
                        pass
                    self.boundvars.setdefault("~=" + var, set([])).add(matching_val)

            #checking values, e.g., 10 or !10

            if varval.values:
                val = varval.values
                if val != None and val != matching_val: #None is the misssing value of the attribute
                    if partialmatching:
                        similarity += utilities.get_similarity(self._similarities, val, matching_val, mismatch_penalty) 
                    else:
                        return False
            #checking negvalues, e.g., ~!10
            if varval.negvalues:
                for negval in varval.negvalues:
                    if negval == matching_val or (negval in {self.__emptyvalue, 'None'} and matching_val == self.__emptyvalue):
                        if partialmatching:
                            similarity += utilities.get_similarity(self._similarities, negval, matching_val, mismatch_penalty)
                        else:
                            return False
        if partialmatching:
            return similarity
        else:
            return True

    def removeempty(self):
        """
        Remove slot-value pairs that have the value __emptyvalue, that is, None and 'None'.
        
        Be careful! This returns a tuple with slot-value pairs.
        """
        def emptying_func():
            for x in self:
                try:
                    if x[1].removeempty():
                        if x[1] != self.__emptyvalue:
                            yield x
                except AttributeError:
                    try:
                        if x[1].values != self.__emptyvalue or x[1].variables or x[1].negvariables or x[1].negvalues:
                            yield x
                    except AttributeError:
                        pass
        if not self.__empty:
            self.__empty = tuple(emptying_func())
        return self.__empty

    def removeunused(self):
        """
        Remove values that were only added to fill in empty slots, using None. 
        
        Be careful! This returns a generator with slot-value pairs.
        """
        def unusing_func():
            for x in self:
                try:
                    if x[1].removeunused():
                        if x[1] != utilities.EMPTYVALUE:
                            yield x
                except AttributeError:
                    try:
                        if x[1].values != utilities.EMPTYVALUE or x[1].variables or x[1].negvariables or x[1].negvalues:
                            yield x
                    except AttributeError:
                        pass
        if not self.__unused:
            self.__unused = tuple(unusing_func())
        return self.__unused

#special chunk that can be used in production rules
for key in utilities.SPECIALCHUNKTYPES:
    chunktype(key, utilities.SPECIALCHUNKTYPES[key])

def createchunkdict(chunk):
    """
    Create typename and chunkdict from pyparsed list.
    """
    sp_dict = {utilities.ACTRVARIABLE: "variables", utilities.ACTRNEG: "negvalues", utilities.ACTRNEG + utilities.ACTRVARIABLE: "negvariables", utilities.ACTRVALUE: "values", utilities.ACTRNEG + utilities.ACTRVALUE: "negvalues"}
    chunk_dict = {}
    for elem in chunk:
        temp_dict = chunk_dict.get(elem[0], utilities.VarvalClass(variables=set(), values=set(), negvariables=set(), negvalues=set())._asdict())

        for idx in range(1, len(elem)):
            try:
                if elem[idx][0][0] == utilities.VISIONGREATER or elem[idx][0][0] == utilities.VISIONSMALLER: #this checks special visual conditions on greater/smaller than
                    if elem[idx][0][-1] == utilities.ACTRVARIABLE:
                        temp_dict['variables'].add(elem[idx][1])
                        update_val = elem[idx][0][0]
                    else:
                        update_val = elem[idx][0] + elem[idx][1]
                        #here fix
                    updating = 'values'
                elif elem[idx][1][0] == "'" or elem[idx][1][0] == '"':
                    updating = sp_dict[elem[idx][0]]
                    update_val = elem[idx][1][1:-1]
                else:
                    updating = sp_dict[elem[idx][0]]
                    update_val = elem[idx][1]

            except (KeyError, IndexError) as err: #indexerror --> only a string is present; keyerror: the first element in elem[idx] is not a special symbol (in sp)
                if elem[idx][0] == "'" or elem[idx][0] == '"':
                    update_val = elem[idx][1:-1]
                else:
                    #check if the string is an existing chunk in the database of chunks
                    try:
                        update_val = Chunk._chunks[elem[idx]]
                    #if not, save it as a string
                    except KeyError:
                        update_val = elem[idx]
                updating = 'values'
            finally:
                temp_dict[updating].add(update_val)

        chunk_dict[elem[0]] = temp_dict

    for key in chunk_dict:
        chunk_dict[key]["negvalues"] = tuple(chunk_dict[key]["negvalues"])
        chunk_dict[key]["negvariables"] = tuple(chunk_dict[key]["negvariables"])
        for x in ["values", "variables"]:
            if len(chunk_dict[key][x]) > 1:
                raise utilities.ACTRError("Any slot must have fewer than two %s, there is more than one in this slot" %x)
            elif len(chunk_dict[key][x]) == 1:
                chunk_dict[key][x] = chunk_dict[key][x].pop()
            else:
                chunk_dict[key][x] = None
        chunk_dict[key] = utilities.VarvalClass(**chunk_dict[key])
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
    Create a chunk.

    Three values can be specified:
    
    (i) the name of the chunk (the name could be used if the chunk appears as a value of other chunks or production rules)
    (ii) its type
    (ii) slot-value pairs.

    For example:
    >>> makechunk(nameofchunk='example0', typename='chunktype_example0', value='one')
    chunktype_example0(value= one)

    This creates a chunk of type chunk1, which has one slot (value) and the value of that slot is one.
    """
    if not nameofchunk:
        nameofchunk = "unnamedchunk"
    if not typename:
        typename = "undefined" + str(Chunk._undefinedchunktypecounter)
        Chunk._undefinedchunktypecounter += 1
    for key in dictionary:
        if isinstance(dictionary[key], Chunk):
            pass
        elif isinstance(dictionary[key], utilities.VarvalClass):
            pass
        else:
            try:
                temp_dict = utilities.stringsplitting(str(dictionary[key]))
            except utilities.ACTRError as e:
                raise utilities.ACTRError("The chunk value %s is not defined correctly; %s" %(dictionary[key], e))
            loop_dict = temp_dict.copy()
            for x in loop_dict:
                if x == "negvariables" or x == "negvalues":
                    val = tuple(temp_dict[x])
                else:
                    try:
                        val = temp_dict[x].pop()
                    except KeyError:
                        val = None
                temp_dict[x] = val
            dictionary[key] = utilities.VarvalClass(**temp_dict)

    created_chunk = Chunk(typename, **dictionary)
    created_chunk._chunks[nameofchunk] = created_chunk
    return created_chunk

def chunkstring(name='', string=''):
    """
    Create a chunk when given a string. The string is specified in the form: slot value slot value (arbitrary number of slot-value pairs can be used). isa-slot is used as the type of chunk. If no isa-slot is provided, chunk is assigned an 'undefined' type.

    For example:
    >>> chunkstring(name="example0", string='isa chunktype_example0 value one')
    chunktype_example0(value= one)
    """
    chunk_reader = utilities.getchunk()
    chunk = chunk_reader.parseString(string, parseAll=True)
    try:
        type_chunk, chunk_dict = createchunkdict(chunk)
    except utilities.ACTRError as e:
        raise utilities.ACTRError("The chunk string %s is not defined correctly; %s" %(string, e))

    created_chunk = makechunk(name, type_chunk, **chunk_dict)
    return created_chunk
