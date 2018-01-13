"""
General class on buffers.
"""

import collections

import pyactr.chunks as chunks
import pyactr.utilities as utilities

class Buffer(collections.MutableSet):
    """
    Buffer module.
    """

    _BUSY = utilities._BUSY
    _FREE = utilities._FREE
    _ERROR = utilities._ERROR

    def __init__(self, dm=None, data=None):
        self.dm = dm
        self.state = self._FREE #set here but state of buffer instances controlled in productions
        if data == None:
            self._data = set([])
        else:
            self._data = data
        assert len(self) <= 1, "Buffer can carry at most one element"

    @property
    def dm(self):
        """
        Default harvest of goal buffer.
        """
        return self.__dm

    @dm.setter
    def dm(self, value):
        if isinstance(value, collections.MutableMapping) or not value:
            self.__dm = value
        else:
            raise ValueError('The attempted dm value cannot be set; it is not a possible declarative memory')

    def __contains__(self, elem):
        return elem in self._data

    def __iter__(self):
        for elem in self._data:
            yield elem

    def __len__(self):
        return len(self._data)

    def __repr__(self):
        return repr(self._data)

    def add(self, elem):
        """
        Add a chunk into the buffer.

        elem must be a chunk.
        """
        self._data = set()
        
        if isinstance(elem, chunks.Chunk):
            self._data.add(elem)
        else:
            raise TypeError("Only chunks can be added to Buffer")

    def discard(self, elem):
        """
        Discard an element without clearing it into a memory.
        """
        self._data.discard(elem)
    
    def show(self, attr):
        """
        Print the content of the buffer.
        """
        if self._data:
            chunk = self._data.copy().pop()
        else:
            chunk = None
        try:
            print(" ".join([str(attr), str(getattr(chunk, attr))]))
        except AttributeError:
            print(attr)

    def test_buffer(self, inquiry):
        """
        Is buffer full/empty?
        """
        if self._data:
            if inquiry == "full": return True
        else:
            if inquiry == "empty": return True
        return False

    def modify(self, otherchunk, actrvariables=None):
        """
        Modify the chunk in Buffer according to the info in otherchunk.
        """
        if actrvariables == None:
            actrvariables = {}
        elem = self._data.pop()
        try:
            mod_attr_val = {x[0]: utilities.check_bound_vars(actrvariables, x[1]) for x in otherchunk.removeunused()} #creates dict of attr-val pairs according to otherchunk
        except utilities.ACTRError as arg:
            raise utilities.ACTRError("The modification by the chunk '%s is impossible; %s" % (otherchunk, arg))
        elem_attr_val = {x[0]: x[1] for x in elem}
        elem_attr_val.update(mod_attr_val) #updates original chunk with attr-val from otherchunk
        mod_chunk = chunks.Chunk(otherchunk.typename, **elem_attr_val) #creates new chunk

        self._data.add(mod_chunk) #put chunk directly into buffer
