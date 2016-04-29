"""
Vision module. Just basic.
"""

import collections

import pyactr.chunks as chunks
import pyactr.utilities as utilities
import pyactr.buffers as buffers

class Visual(buffers.Buffer):
    """
    Visual buffer. Sees whatever is in environment.
    """


    _VISAUTOBUFFERING = utilities._VISAUTOBUFFERING

    def __init__(self, env=None, default_harvest=None):
        self.environment = env
        self.auto_buffer = None #place for automatic buffering
        buffers.Buffer.__init__(self, default_harvest, None)

    def add(self, elem, time=0, harvest=None):
        """
        Clears current buffer (into a memory) and adds a new chunk. Decl. memory is either specified as default_harvets, when Visual is initialized, or it can be specified as the argument of harvest.
        """
        self.clear(time, harvest)
        super().add(elem)

    def automatic_buffering(self):
        """
        Automatically buffers if there is something new in environment.
        """
        new_chunk = chunks.Chunk("_visual", object=self.environment.obj) #creates new chunk
        if new_chunk != self.auto_buffer:
            self.auto_buffer = new_chunk
            self.state = self._VISAUTOBUFFERING
        
    def clear(self, time=0, harvest=None):
        """
        Clears buffer, adds cleared chunk into decl. memory. Decl. memory is either specified as default_harvest, when Visual is initialized, or it can be specified here as harvest.
        """
        if harvest != None:
            if self._data:
                harvest.add(self._data.pop(), time)
        else:
            if self._data:
                self.dm.add(self._data.pop(), time)

    def create(self, otherchunk, harvest=None, actrvariables=None):
        """
        Sets a chunk in vision based on what is on the screen.
        """
        new_chunk = chunks.Chunk("_visual", object=self.environment.obj) #creates new chunk
        self.auto_buffer = new_chunk #add the chunk into auto_buffer
        self.add(new_chunk, harvest) #put chunk using add - i.e., clear first, then add

    def test(self, state, inquiry):
        """
        Is current state busy/free/error?
        """
        if inquiry == self._VISAUTOBUFFERING:
            self.automatic_buffering()
        return getattr(self, state) == inquiry
