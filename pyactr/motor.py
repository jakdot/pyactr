"""
Motor module. Carries out key presses.
"""

import collections
import string

import pyactr.chunks as chunks
import pyactr.utilities as utilities
from pyactr.utilities import ACTRError
import pyactr.buffers as buffers

class Motor(buffers.Buffer):
    """
    Motor buffer. Only pressing keys possible.
    """

    LEFT_HAND = ("1", "2", "3", "4", "5", "Q", "W", "E", "R", "T", "A", "S", "D", "F", "G", "Z", "X", "C", "V", "B", "SPACE")
    RIGHT_HAND = ("6", "7", "8", "9", "0", "Y", "U", "I", "O", "P", "H", "J", "K", "L", "N", "M", "SPACE")
    PRESSING = ("A", "S", "D", "F", "J", "K", "L", "SPACE")
    SLOWEST = ("5", "6")
    OTHERS = ()
    _MANUAL = utilities.MANUAL

    TIME_PRESSES = {PRESSING: (0.15, 0.05, 0.01, 0.09), SLOWEST: (0.25, 0.05, 0.11, 0.16), OTHERS: (0.25, 0.05, 0.1, 0.15)} #numbers taken from the motor module of Lisp ACT-R models for all the standard keyboard keys; the numbers are: preparation, initiation, action, finishing movement

    def __init__(self):
        buffers.Buffer.__init__(self, None, None)
        self.preparation = self._FREE
        self.processor = self._FREE
        self.execution = self._FREE

        self.last_key = [None, 0] #the number says what the last key was and when the last press will be finished, so that the preparation of the next move can speed up if it is a similar key, and execution waits for the previous mvt (two mvts cannot be carried out at the same time, according to ACT-R motor module)

    def test(self, state, inquiry):
        """
        Is current state/preparation etc. busy or free?
        """
        return getattr(self, state) == inquiry

    def add(self, elem):
        """
        Adding a chunk. This is illegal for motor buffer.
        """
        raise AttributeError("Attempt to add an element to motor buffer. This is not possible.")

    def create(self, otherchunk, actrvariables=None):
        """
        Create (aka set) a chunk for manual control. The chunk is returned (and could be used by device or external environment).
        """
        if actrvariables == None:
            actrvariables = {}
        try:
            mod_attr_val = {x[0]: utilities.check_bound_vars(actrvariables, x[1]) for x in otherchunk.removeunused()} #creates dict of attr-val pairs according to otherchunk
        except ACTRError as arg:
            raise ACTRError("Setting the chunk '%s' in the manual buffer is impossible; %s" % (otherchunk, arg))

        new_chunk = chunks.Chunk(self._MANUAL, **mod_attr_val) #creates new chunk

        if new_chunk.cmd.values not in utilities.CMDMANUAL:
            raise ACTRError("Motor module received an invalid command: '%s'. The valid commands are: '%s'" % (new_chunk.cmd.values, utilities.CMDMANUAL))

        if new_chunk.cmd.values == utilities.CMDPRESSKEY:
            pressed_key = new_chunk.key.values.upper() #change key into upper case
            mod_attr_val["key"] = pressed_key
            new_chunk = chunks.Chunk(self._MANUAL, **mod_attr_val) #creates new chunk
        if pressed_key not in self.LEFT_HAND and new_chunk.key.values not in self.RIGHT_HAND:
            raise ACTRError("Motor module received an invalid key: %s" % pressed_key)

        return new_chunk

