"""
Goals.
"""

import pyactr.chunks as chunks
import pyactr.utilities as utilities
from pyactr.utilities import ACTRError
import pyactr.buffers as buffers

class Goal(buffers.Buffer):
    """
    Goal buffer module.
    """

    def __init__(self, data=None, default_harvest=None, delay=0):
        buffers.Buffer.__init__(self, default_harvest, data)
        self.delay = delay

    @property
    def delay(self):
        """
        Delay (in s) to create chunks in the goal buffer.
        """
        return self.__delay

    @delay.setter
    def delay(self, value):
        if value >= 0:
            self.__delay = value
        else:
            raise ValueError('Delay in the goal buffer must be >= 0')

    @property
    def default_harvest(self):
        """
        Default harvest of goal buffer.
        """
        return self.dm

    @default_harvest.setter
    def default_harvest(self, value):
        try:
            self.dm = value
        except ValueError:
            raise ACTRError('The default harvest set in the goal buffer is not a possible declarative memory')

    def add(self, elem, time=0, harvest=None):
        """
        If the buffer has a chunk, it clears current buffer (into the memory associated with the goal buffer). It adds a new chunk, specified as elem. Decl. memory is either specified as default_harvest, when Goal is initialized, or it can be specified as harvest.

        Neither time nor harvest currently affect the behavior of the goal buffer.
        """
        super().add(elem)
        
    def clear(self, time=0, harvest=None):
        """
        Clear buffer, add the cleared chunk into decl. memory. Decl. memory is either specified as default_harvest, when Goal is initialized, or it can be specified as harvest here.
        """
        if harvest != None:
            if self._data:
                harvest.add(self._data.pop(), time)
        else:
            if self._data:
                self.dm.add(self._data.pop(), time)


    def copy(self, harvest=None):
        """
        Copy the buffer. Unlike other buffers, this one does not copy the memory that is used for its harvest. This is because goal buffer will always share the memory to which it harvests with another retrieval buffer. You have to specify harvest (that is, which declarative memory should harvest the buffer) if you want clearing to work in the copied buffer.
        """
        if harvest == None:
            harvest = self.dm
        copy_goal = Goal(self._data.copy(), harvest)
        return copy_goal
    
    def test(self, state, inquiry):
        """
        Is current state busy/free/error?
        """
        return getattr(self, state) == inquiry

    def retrieve(self, otherchunk, actrvariables=None):
        """
        Retrieve a chunk. This is not possible in goal buffer, so an error is raised.
        """
        raise utilities.ACTRError("An attempt to retrieve from goal in the chunk '%s'; retrieving from goal is not possible" % otherchunk)


    def create(self, otherchunk, harvest=None, actrvariables=None):
        """
        Create (aka set) a chunk in goal buffer.
        """
        try:
            mod_attr_val = {x[0]: utilities.check_bound_vars(actrvariables, x[1]) for x in otherchunk.removeunused()} #creates dict of attr-val pairs according to otherchunk
        except utilities.ACTRError as arg:
            raise utilities.ACTRError("Setting the buffer using the chunk '%s' is impossible; %s" % (otherchunk, arg))

        new_chunk = chunks.Chunk(otherchunk.typename, **mod_attr_val) #creates new chunk

        self.add(new_chunk, 0, harvest) #put chunk using add


