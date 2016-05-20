"""
Motor module. Just basic.
"""

import collections

import pyactr.chunks as chunks
import pyactr.utilities as utilities
import pyactr.buffers as buffers

class Motor(buffers.Buffer):
    """
    Motor buffer. Only pressing keys possible, no time calculated (productions use defaults instead).
    """

    def __init__(self):
        buffers.Buffer.__init__(self, None, None)
        self.preparation = self._FREE
        self.processor = self._FREE
        self.execution = self._FREE

    def test(self, state, inquiry):
        """
        Is current state/preparation etc. busy or free?
        """
        return getattr(self, state) == inquiry

    def add(self, elem):
        """
        Tries to add a chunk. This is illegal for motor buffer.
        """
        raise AttributeError("Attempt to add an element to motor buffer. This is not possible.")

    def create(self, otherchunk, actrvariables=None):
        """
        Creates (aka sets) a chunk for manual control. The chunk is returned (and could be used by device or external environment).
        """
        if otherchunk.typename != "_manual":
            raise TypeError("Motor buffer accepts only chunk '_manual'")
        try:
            mod_attr_val = {x[0]: utilities.check_bound_vars(actrvariables, x[1]) for x in otherchunk.removeunused()} #creates dict of attr-val pairs according to otherchunk
        except utilities.ACTRError as arg:
            raise utilities.ACTRError("The chunk '%s' is not defined correctly; %s" % (otherchunk, arg))

        new_chunk = chunks.Chunk(otherchunk.typename, **mod_attr_val) #creates new chunk

        return new_chunk

