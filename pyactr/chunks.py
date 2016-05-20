"""
Chunks
"""

import collections
import re
import warnings

import pyactr.utilities as utilities


def chunktype(cls_name, field_names, verbose=False):
    """
    Creates type chunk. Works like namedtuple.
    """
    try:
        field_names = field_names.replace(',', ' ').split()
    except AttributeError:  # no .replace or .split
        pass  # assume it's already a sequence of identifiers
    field_names = tuple(name + "_" for name in field_names)
    
    Chunk._chunktypes.update({cls_name:collections.namedtuple(cls_name, field_names, verbose)}) #chunktypes are not returned; they are stored as Chunk class attribute

class Chunk(collections.Sequence):
    """
    ACT-R chunks. Based off namedtuple (tuple with dictionary-like properties).
    """

    class EmptyValue(object):
        """
        Empty values used in chunks. These are None values.
        """

        def __init__(self):
                self.value = None

        def __eq__(self, val):
            if val == None or val == "None":
                return True #Chunks make strings out of values; this holds for everything but cases in which chunks themselves are values; so, None will be turned into a string as well, hence the equality
            else:
                return False

        def __hash__(self):
            return hash(None)

        def __repr__(self):
            return repr(None)

    _chunktypes = {}

    __emptyvalue = EmptyValue()

    __actrvariable = "?"
    __actrvariableR = "\?" #used for regex
    __actrvalue = "!"
    __actrvalueR = "\!" #used for regex
    __actrneg = "~"
    __actrnegR = "~" #used for regex

    __negactrvariable = "~"
    _similarities = {} #dict of similarities between chunks

    def __init__(self, typename, **dictionary):
        self.typename = typename
        self.boundvars = {} #dict of bound variables

        #chunk is created with an extra _ in keywords (to avoid problems when chunk attributes have names already assigned to other attributes)
        kwargs = {}
        for key in dictionary:

            #change values (and values in a tuple) into string, when possible
            if not isinstance(dictionary[key], collections.Sequence):
                dictionary[key] = str(dictionary[key])

            elif type(dictionary[key]) == tuple:
                dictionary[key] = tuple(str(x) if not isinstance(dictionary[key], Chunk) else x for x in dictionary[key])

            #adding _ to minimize/avoid attribute clashes
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
        return hash(tuple(self.removeempty()))

    def __iter__(self):
        for x, y in zip(self.actrchunk._fields, self.actrchunk):
            yield re.sub("_$", "", x), y

    def __len__(self):
        return len(self.actrchunk)

    def __repr__(self):
        reprtxt = ', '.join('%s=%s' % (re.sub("_$", "", name), getattr(self.actrchunk, name)) for name in self.actrchunk._fields)
        return self.typename + "(" + reprtxt + ")"


    def __removeemptyandvars__(self):
        """
        Removes attribute-value pairs that have the value __emptyvalue or a variable(s). Careful! Returns a generator with attr-value pairs.
        """
        return (x for x in self if x[1] != self.__emptyvalue and str(x[1])[0] != self.__actrvariable)
    
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
            return self.__lt__(otherchunk)

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
                matching_val = getattr(otherchunk.actrchunk, x[0] + "_")
            except AttributeError:
                matching_val = None

            varval = utilities.splitting(x[1])

            #checking variables, e.g., =x
            if varval["variables"]:
                if matching_val == self.__emptyvalue:
                    similarity -= 1
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
            if varval["negvariables"]:
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
                if val not in set([self.__emptyvalue]) and val != matching_val: #set membership distingushes emptyvalue and None
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
        return (x for x in self if x[1] != self.__emptyvalue)

    def removeunused(self):
        """
        Removes values that were only added to fill in empty slots, using None. Careful! Returns a generator with attr-value pairs.
        """
        return (x for x in self if x[1] != None)


#create special chunk for LHS
chunktype("_variablesvalues", "variables, values, negvariables, negvalues")

#create special chunk for Motor
chunktype("_manual", "cmd, key")

#create special chunk for Vision
chunktype("_visual", "object")
