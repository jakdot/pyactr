"""
Testing the symbolic & subsymbolic part of the module.
Requires Python >= 3.3
"""

import unittest
import collections
import re
import warnings
import math

import simpy
import numpy as np

import pyactr.chunks as chunks

import pyactr.buffers as buffers
import pyactr.goals as goals
import pyactr.declarative as declarative
import pyactr.utilities as util

import pyactr as actr

import pyactr.tests.modeltests as modeltests

class TestChunks1(unittest.TestCase):
    """
    Testing chunk comparisons. Basic cases, inluding values None.
    """

    def setUp(self):
        chunks.chunktype("test", ("arg1", "arg2"))
        self.chunk = chunks.makechunk("01", "test", arg1="v1", arg2="v2")
        self.chunk2 = chunks.makechunk("c01", "test", arg1="v1")
        self.chunk3 = chunks.makechunk("01", "test", arg2="v2", arg1="v1")
        self.chunk4 = chunks.makechunk("01", "test", arg2="v5", arg1="v1")
        self.chunk5 = chunks.makechunk("ch05", "test", arg1="v1", arg2=None)

    def test_values(self):
        self.assertEqual(self.chunk.arg1.values, "v1")
        self.assertEqual(self.chunk.arg2.values, "v2")

    def test_chunks(self):
        self.assertTrue(self.chunk2 < self.chunk)
        self.assertFalse(self.chunk2 > self.chunk)
        self.assertTrue(self.chunk2 <= self.chunk)
        self.assertFalse(self.chunk2 >= self.chunk)
        self.assertFalse(self.chunk <= self.chunk2)
        self.assertTrue(self.chunk >= self.chunk2)
        self.assertTrue(self.chunk == self.chunk3)
        self.assertFalse(self.chunk == self.chunk2)
        self.assertFalse(self.chunk == self.chunk4)
        self.assertFalse(self.chunk2 == self.chunk3)
        self.assertFalse(self.chunk3 == self.chunk4)
        self.assertTrue(self.chunk3 <= self.chunk)
        self.assertFalse(self.chunk4 < self.chunk)
        self.assertTrue(self.chunk5 <= self.chunk2)
        self.assertFalse(self.chunk5 <= self.chunk)

class TestChunks2(unittest.TestCase):
    """
    Testing chunk comparisons. Testing negation.
    """

    def setUp(self):
        chunks.chunktype("test", ("arg1", "arg2"))
        self.chunk = chunks.makechunk("01", "test", arg1="v1", arg2="v2")
        self.chunk2 = chunks.makechunk("01", "test", arg1="~!v1")
        self.chunk3 = chunks.makechunk("01", "test", arg1="~!v2")
        chunks.chunktype("testnew", ("arg10", "arg20"))
        self.chunk4 = chunks.makechunk("", "testnew")
        self.chunk5 = chunks.makechunk("", "testnew", arg10="v5")
        self.chunk6 = chunks.makechunk("", "testnew", arg10="~None")

    def test_chunks(self):
        self.assertFalse(self.chunk2 < self.chunk)
        self.assertFalse(self.chunk2 <= self.chunk)
        self.assertTrue(self.chunk3 < self.chunk)
        self.assertTrue(self.chunk3 <= self.chunk)
        self.assertTrue(self.chunk4 <= self.chunk)
        self.assertFalse(self.chunk5 <= self.chunk)
        self.assertTrue(self.chunk4 <= self.chunk5)
        self.assertTrue(self.chunk4 <= self.chunk6)
        self.assertFalse(self.chunk6 <= self.chunk)

class TestChunks3(unittest.TestCase):
    """
    Testing chunks. Testing variables, and the combination of variables, negation and values.
    """

    def setUp(self):
        chunks.chunktype("test", ("arg1", "arg2"))
        self.chunk = chunks.makechunk("01", "test", arg1="v1", arg2="v2")
        self.chunk2 = chunks.makechunk("01", "test", arg1="=x")
        self.chunk3 = chunks.makechunk("01", "test", arg2="=x")
        self.chunk4 = chunks.makechunk("01", "test", arg2="~=x")
        self.chunk5 = chunks.makechunk("01", "test", arg2="~=x~=y")
        self.chunk6 = chunks.makechunk("01", "test", arg2="~=x=y")
        self.chunk7 = chunks.makechunk("01", "test", arg2="=x!v2")
        self.chunk8 = chunks.makechunk("01", "test", arg2="v2")
        self.chunk9 = chunks.makechunk("01", "test", arg2="~=y!v2")
        self.chunk10 = chunks.makechunk("01", "test", arg2="!v2=x")
        self.chunk11 = chunks.makechunk("01", "test", arg2="!v2~=y")
        self.chunk12 = chunks.makechunk("01", "test", arg1="~=x")
        self.chunk13 = chunks.makechunk("01", "test", arg1="~=x!v1")
        self.chunk20 = chunks.makechunk("01", "test", arg1="=one~=two~=three~!v2~!v4", arg2="!v2~=one=two~=five")
        self.chunk21 = chunks.makechunk("01", "test", arg1="=one~=two~=three~!v2~!v4", arg2="!v2=one~=three~=five")
        self.chunk22 = chunks.makechunk("01", "test", arg1="=one~=two~=three~!v2~!v4", arg2="!v2~=one~=two")
        self.chunk.boundvars = {"=x" : "v1", "=y" : "v5"}
        self.chunk2.boundvars = {"=x" : "v1", "=y" : "v5"}
        self.chunk3.boundvars = {"=x" : "v1", "=y" : "v5"}
        self.chunk4.boundvars = {"=x" : "v1", "=y" : "v5"}
        self.chunk5.boundvars = {"=x" : "v1", "=y" : "v5"}
        self.chunk6.boundvars = {"=x" : "v1", "=y" : "v5"}
        self.chunk7.boundvars = {"=x" : "v1", "=y" : "v5"}
        self.chunk8.boundvars = {"=x" : "v1", "=y" : "v5"}
        self.chunk9.boundvars = {"=x" : "v1", "=y" : "v5"}
        self.chunk10.boundvars = {"=x" : "v1", "=y" : "v5"}
        self.chunk11.boundvars = {"=x" : "v1", "=y" : "v5"}
        self.chunk12.boundvars = {"=x" : "v1", "=y" : "v5"}
        self.chunk13.boundvars = {"=x" : "v1", "=y" : "v5"}
        self.chunk20.boundvars = {"~=one" : {"v2", "v3", "v5"}, "=two": "v2", "~=three": {"v1", "v4"}, "=five": "v5"}
        self.chunk21.boundvars = {"~=one" : {"v2", "v3", "v5"}, "=two": "v2", "~=three": {"v1", "v4"}, "=five": "v5"}
        self.chunk22.boundvars = {"~=one" : {"v2", "v3", "v5"}, "=two": "v2", "~=three": {"v1", "v4"}, "=five": "v5"}

    def test_chunks(self):
        self.assertTrue(self.chunk2 < self.chunk)
        self.assertTrue(self.chunk2 <= self.chunk)
        self.assertFalse(self.chunk3 < self.chunk)
        self.assertTrue(self.chunk4 < self.chunk)
        self.assertTrue(self.chunk5 < self.chunk)
        self.assertFalse(self.chunk6 < self.chunk)
        self.assertFalse(self.chunk7 < self.chunk)
        self.assertTrue(self.chunk8 < self.chunk)
        self.assertTrue(self.chunk9 < self.chunk)
        self.assertFalse(self.chunk10 < self.chunk)
        self.assertTrue(self.chunk11 < self.chunk)
        self.assertFalse(self.chunk12 < self.chunk)
        self.assertFalse(self.chunk13 < self.chunk)
        self.assertTrue(self.chunk20 <= self.chunk)
        self.assertEqual(self.chunk20.boundvars, {"=one": "v1", "~=one" : {"v2", "v3", "v5"}, "~=two": {"v1"}, "=two": "v2", "~=three": {"v1", "v4"}, "=five": "v5", "~=five": {"v2"}})
        self.assertFalse(self.chunk21 <= self.chunk)
        self.assertFalse(self.chunk22 <= self.chunk)

class TestChunks4(unittest.TestCase):
    """
    Testing chunks. Testing variables, and the combination of variables, negation and values. Using the special namedtuple _variablesvalues
    """

    def setUp(self):
        chunks.chunktype("test", ("arg1", "arg2"))
        self.chunkvar1 = chunks.makechunk("01", "test", arg1=util.VarvalClass(values="v1", variables=None, negvalues=(), negvariables=()), arg2=util.VarvalClass(values="v2", variables=None, negvalues=(), negvariables=()))
        self.chunkvar2 = chunks.makechunk("01", "test", arg1=util.VarvalClass(values="v1", variables=None, negvalues=(), negvariables=()), arg2=util.VarvalClass(values="v2", variables=None, negvalues=(), negvariables=()))
        self.chunk = chunks.makechunk("01", "test", arg1="v1", arg2="v2")
        self.chunk2 = chunks.makechunk("01", "test", arg1=util.VarvalClass(values=None, variables='x', negvalues=(), negvariables=()))
        self.chunk3 = chunks.makechunk("01", "test", arg2=util.VarvalClass(values=None, variables='x', negvalues=(), negvariables=()))
        self.chunk4 = chunks.makechunk("01", "test", arg2=util.VarvalClass(values=None, negvariables=('x',), negvalues=(), variables=None))
        self.chunk5 = chunks.makechunk("01", "test", arg2=util.VarvalClass(values=None, negvariables=('x', 'y'), negvalues=(), variables=None))
        self.chunk6 = chunks.makechunk("01", "test", arg2=util.VarvalClass(values=None, negvariables=('x',), negvalues=(), variables='y'))
        self.chunk7 = chunks.makechunk("01", "test", arg2=util.VarvalClass(values='v2', negvariables=(), negvalues=(), variables='x'))
        self.chunk7e = chunks.makechunk("01", "test", arg2=util.VarvalClass(values='v12', negvariables=(), negvalues=(), variables='x'))
        self.chunk8 = chunks.makechunk("01", "test", arg2=util.VarvalClass(values='v2', negvariables=(), negvalues=(), variables=None))
        self.chunk9 = chunks.makechunk("01", "test", arg2=util.VarvalClass(values='v2', negvariables=("y",), negvalues=(), variables=None))
        self.chunk10 = chunks.makechunk("01", "test", arg2=util.VarvalClass(values='v2', negvariables=("y",), negvalues=(), variables='x'))
        self.chunk12 = chunks.makechunk("01", "test", arg1=util.VarvalClass(values=None, negvariables=("x",), negvalues=(), variables=None))
        self.chunk13 = chunks.makechunk("01", "test", arg1=util.VarvalClass(values='v1', negvariables=("x",), negvalues=(), variables=None))
        self.chunk20 = chunks.makechunk("01", "test", arg1=util.VarvalClass(values=None, negvariables=("two", "three"), negvalues=(), variables='one'), arg2=util.VarvalClass(values='v2', negvariables=("one", "five"), negvalues=(), variables='two'))
        self.chunk21 = chunks.makechunk("01", "test", arg1=util.VarvalClass(values=None, negvariables=("two", "three"), negvalues=('v2', 'v4'), variables='one'), arg2=util.VarvalClass(values='v2', negvariables=("three", "five"), negvalues=(), variables='one'))
        self.chunk22 = chunks.makechunk("01", "test", arg1=util.VarvalClass(values=None, negvariables=("two", "three"), negvalues=('v2', 'v4'), variables='one'), arg2=util.VarvalClass(values='v2', negvariables=("one", "two"), negvalues=(), variables=None))

        self.chunk.boundvars = {"=x" : "v1", "=y" : "v5"}
        self.chunk2.boundvars = {"=x" : "v1", "=y" : "v5"}
        self.chunk3.boundvars = {"=x" : "v1", "=y" : "v5"}
        self.chunk4.boundvars = {"=x" : "v1", "=y" : "v5"}
        self.chunk5.boundvars = {"=x" : "v1", "=y" : "v5"}
        self.chunk6.boundvars = {"=x" : "v1", "=y" : "v5"}
        self.chunk7.boundvars = {"=x" : "v1", "=y" : "v5"}
        self.chunk7e.boundvars = {"=x" : "v1", "=y" : "v5"}
        self.chunk8.boundvars = {"=x" : "v1", "=y" : "v5"}
        self.chunk9.boundvars = {"=x" : "v1", "=y" : "v5"}
        self.chunk10.boundvars = {"=x" : "v1", "=y" : "v5"}
        self.chunk12.boundvars = {"=x" : "v1", "=y" : "v5"}
        self.chunk13.boundvars = {"=x" : "v1", "=y" : "v5"}
        self.chunk20.boundvars = {"~=one" : {"v2", "v3", "v5"}, "=two": "v2", "~=three": {"v1", "v4"}, "=five": "v5"}
        self.chunk21.boundvars = {"~=one" : {"v2", "v3", "v5"}, "=two": "v2", "~=three": {"v1", "v4"}, "=five": "v5"}
        self.chunk22.boundvars = {"~=one" : {"v2", "v3", "v5"}, "=two": "v2", "~=three": {"v1", "v4"}, "=five": "v5"}

    def test_chunks(self):
        self.assertTrue(self.chunkvar1 == self.chunkvar2)
        self.assertTrue(self.chunk2 < self.chunk)
        self.assertTrue(self.chunk2 <= self.chunk)
        self.assertFalse(self.chunk3 < self.chunk)
        self.assertTrue(self.chunk4 < self.chunk)
        self.assertTrue(self.chunk5 < self.chunk)
        self.assertFalse(self.chunk6 < self.chunk)
        self.assertFalse(self.chunk7 < self.chunk)
        self.assertFalse(self.chunk7e < self.chunk)
        self.assertTrue(self.chunk8 < self.chunk)
        self.assertTrue(self.chunk9 < self.chunk)
        self.assertFalse(self.chunk10 < self.chunk)
        self.assertFalse(self.chunk12 < self.chunk)
        self.assertFalse(self.chunk13 < self.chunk)
        self.assertTrue(self.chunk20 <= self.chunk)
        self.assertEqual(self.chunk20.boundvars, {"=one": "v1", "~=one" : {"v2", "v3", "v5"}, "~=two": {"v1"}, "=two": "v2", "~=three": {"v1", "v4"}, "=five": "v5", "~=five": {"v2"}})
        self.assertFalse(self.chunk21 <= self.chunk)
        self.assertFalse(self.chunk22 <= self.chunk)

class Testchunkstring(unittest.TestCase):
    """
    Testing chunk comparisons using chunkstring. Basic cases.
    """

    def setUp(self):
        chunks.chunktype("test", ("arg1", "arg2"))
        self.chunk = chunks.chunkstring("c1", "isa test arg1 'v1' arg2 'v2'")
        self.chunk2 = chunks.chunkstring("c2", \
                "isa    test\
                arg1    'v1'\
                arg2    'v2'")
        self.chunk2p = chunks.chunkstring("c2p", \
                'isa    test\
                arg2    "v2"\
                arg1    "v1"')
        self.chunk2not = chunks.chunkstring("c2not", \
                'isa    test\
                arg2    "v1"\
                arg1    "v2"')
        self.chunk3 = chunks.makechunk("","test", arg1=util.VarvalClass(values='v1', negvariables=(), negvalues=(), variables=None), arg2=util.VarvalClass(values='v2', negvariables=(), negvalues=(), variables=None))
        self.chunk4 = chunks.makechunk("","test", arg1="v1", arg2="v2")
        self.chunk5 = chunks.chunkstring("c5", \
                "isa test\
                arg1 None\
                arg2 ~=x\
                arg2  =y")
        self.chunk5a = chunks.chunkstring("c5a",\
                "isa test\
                arg2 ~= x\
                arg2 = y")
        self.chunk6 = chunks.makechunk("","test", arg2="~=x=y")
        self.chunk6not = chunks.makechunk("","test", arg2="~=x")
        self.chunk6not2 = chunks.makechunk("","test", arg2="=y")
        self.chunk5.boundvars = {"=x" : "v1", "=y" : "v5"}
        self.chunk5a.boundvars = self.chunk5.boundvars
        self.chunk6.boundvars = self.chunk5.boundvars
        self.chunk6not.boundvars = self.chunk5.boundvars
        self.chunk6not2.boundvars = self.chunk5.boundvars

    def test_chunks(self):
        self.assertTrue(self.chunk3 == self.chunk4)
        self.assertTrue(self.chunk == self.chunk2)
        self.assertFalse(self.chunk2 == self.chunk2not)
        self.assertTrue(self.chunk2 == self.chunk2p)
        self.assertTrue(self.chunk == self.chunk3)
        self.assertTrue(self.chunk == self.chunk4)
        self.assertTrue(self.chunk2 == self.chunk4)
        self.assertTrue(self.chunk5 == self.chunk6)
        self.assertTrue(self.chunk5a == self.chunk6)
        self.assertFalse(self.chunk5a == self.chunk6not)
        self.assertFalse(self.chunk5a == self.chunk6not2)

class Testchunkstring2(unittest.TestCase):
    """
    Testing chunk comparisons using chunkstring. Advanced cases in which chunks embed chunks embed chunks.
    """

    def setUp(self):
        chunks.chunktype("newtest", ("arg1", "arg2"))
        chunks.chunktype("nexttest", ("a1", "a5"))
        self.chunk = chunks.chunkstring("c1", \
                "isa    newtest\
                arg2    'v2'\
                arg1    'v1'")
        self.chunk2 = chunks.chunkstring("c2", \
                "arg1    c1\
                newarg   10")
        self.chunk3 = chunks.chunkstring("c3", \
                "arg1    5\
                newarg   c1")
        self.chunk4 = chunks.chunkstring("c4", \
                "arg1    5\
                newarg   = x")
        self.chunk5 = chunks.chunkstring("c5", \
                "isa    nexttest\
                a1      'v7'\
                a5      c4")
        self.chunk6 = chunks.chunkstring("c6", \
                "isa    nexttest\
                a5      =x\
                a1      'v7'")
        chunks.chunktype("startcount", ("start", "count"))
        chunks.chunktype("countcount", ("first", "second"))
        self.chunk7 = chunks.chunkstring("c7", \
                "isa startcount\
                start =x\
                count None")
        self.chunk7super = chunks.chunkstring("c7s", \
                "isa startcount\
                start 2")
        self.chunk8 = chunks.chunkstring("c7s", \
                "isa startcount\
                start 2")
        self.chunk9 = chunks.chunkstring("c7s", \
                "isa startcount\
                start None")
        self.chunk10 = chunks.chunkstring("c10", \
                "isa countcount\
                first 2")
        self.chunk11 = chunks.chunkstring("c11", \
                "isa countcount\
                first 2\
                second 4")
        self.chunk12 = chunks.chunkstring("c12", \
                "isa countcount\
                first 3\
                first =zz")
        self.chunk13 = chunks.chunkstring("c13", \
                "isa countcount\
                first 3")
        self.chunk14 = chunks.chunkstring("c14", \
                "isa countcount\
                first None")
        self.chunk15 = chunks.chunkstring("c15", \
                "isa countcount\
                first =t\
                first 20")
        self.chunk16 = chunks.chunkstring("c16", \
                "isa countcount\
                first 20")
        self.chunk17 = chunks.chunkstring("c17", \
                "isa countcount\
                first ~=t\
                first ~=z\
                first =x")
        self.chunk18 = chunks.chunkstring("c18", \
                "isa countcount\
                first 20")
        self.chunk19 = chunks.chunkstring("c19", \
                "isa countcount\
                first =x\
                first ~None")
        chunks.chunktype("testchunkstring2type1", "arg1, newarg")
        chunks.chunktype("testchunkstring2type3", "a1, a5")
        self.chunkc2 = chunks.makechunk("", "testchunkstring2type1", arg1=self.chunk, newarg=10)
        self.chunkc3 = chunks.makechunk("", "testchunkstring2type1", newarg="=x", arg1=5)
        self.chunkc5 = chunks.makechunk("", "testchunkstring2type3", a1="v7", a5=self.chunk4)
        self.chunk4.boundvars = {"=x" : self.chunk, "=y" : "v5"}
        self.chunk3.boundvars = {"=x" : self.chunk, "=y" : "v5"}
        self.chunkc3.boundvars = {"=x" : self.chunk, "=y" : "v5"}
        self.chunk6.boundvars = {"=x" : self.chunk4}

    def test_chunks(self):
        self.assertFalse(self.chunk == self.chunk2)
        self.assertTrue(self.chunkc2 == self.chunk2)
        self.assertTrue(self.chunkc3 == self.chunk3)
        self.assertTrue(self.chunkc3 == self.chunk4)
        self.assertTrue(self.chunk5 == self.chunkc5)
        self.assertTrue(self.chunk6 == self.chunkc5)
        self.assertFalse(self.chunk7 == self.chunk7super)
        self.assertFalse(self.chunk7super <= self.chunk7)
        self.assertTrue(self.chunk7 <= self.chunk7super)
        self.assertTrue(self.chunk7 == self.chunk7super)
        self.assertFalse(self.chunk8 == self.chunk9)
        self.assertFalse(self.chunk8 <= self.chunk9)
        self.assertFalse(self.chunk9 <= self.chunk8)
        self.assertTrue(self.chunk10 <= self.chunk11)
        self.assertEqual(self.chunk12.boundvars, {})
        self.assertTrue(self.chunk12 <= self.chunk13)
        self.assertEqual(self.chunk12.boundvars, {'=zz': '3'})
        self.assertEqual(self.chunk15.boundvars, {})
        self.assertFalse(self.chunk15 == self.chunk16)
        self.assertTrue(self.chunk15 <= self.chunk16)
        self.assertTrue(self.chunk16 <= self.chunk15)
        self.assertEqual(self.chunk15.boundvars, {'=t': '20'})
        self.chunk17.boundvars = {"=z" : '20', "=t": '20'}
        self.assertFalse(self.chunk17 <= self.chunk18)
        self.chunk17.boundvars = {"=z" : '10', "=t": '20'}
        self.assertFalse(self.chunk17 <= self.chunk18)
        self.chunk17.boundvars = {"=z" : '20', "=t": '10'}
        self.assertFalse(self.chunk17 <= self.chunk18)
        self.chunk17.boundvars = {"=x" : '20', "=t": '20'}
        self.assertFalse(self.chunk17 <= self.chunk18)
        self.chunk17.boundvars = {"=x" : '20', "=z": '20'}
        self.assertFalse(self.chunk17 <= self.chunk18)
        self.chunk17.boundvars = {"=x" : '20', "=z": '18', "=t": '14'}
        self.assertTrue(self.chunk17 <= self.chunk18)
        self.assertFalse(self.chunk19 <= self.chunk7)


class TestBuffers(unittest.TestCase):
    """
    Testing goal and dm buffers. Testing creation of buffers, addition to buffers, clearing buffers.
    """

    def setUp(self):
        chunks.chunktype("origo", "x")
        chunks.chunktype("bufferchunk", "y")
        chunks.chunktype("goalchunk", "z")
        chunks.chunktype("finalchunk", "x")
        self.dm = declarative.DecMem({chunks.makechunk("", "origo", x=1): 0})
        self.b = declarative.DecMemBuffer(self.dm)
        self.g = goals.Goal()
        self.b.add(chunks.makechunk("", "bufferchunk", y=10))
        self.g.add(chunks.makechunk("", "goalchunk", z=10))
        self.g2 = goals.Goal(default_harvest=self.dm)
        self.g2.add(chunks.makechunk("", "finalchunk", x=-5))

    def test_buffers(self):
        warnings.filterwarnings(action="ignore", category=UserWarning)
        self.b.add(chunks.makechunk("", "bufferchunk", x=10))
        self.assertEqual(self.dm.keys(), {chunks.makechunk("", "origo", x=1), chunks.makechunk("", "bufferchunk", y=10)})
        self.g.clear(harvest=self.dm)
        self.g.add(chunks.makechunk("", "goalchunk", x=20), 0, self.dm)
        self.assertEqual(self.dm.keys(), {chunks.makechunk("", "origo", x=1), chunks.makechunk("", "bufferchunk", y=10), chunks.makechunk("", "goalchunk", z=10)})
        self.g2.clear(harvest=self.dm)
        self.g2.add(chunks.makechunk("", "finalchunk", x=30))
        self.assertEqual(self.dm.keys(), {chunks.makechunk("", "origo", x=1), chunks.makechunk("", "bufferchunk", y=10), chunks.makechunk("", "goalchunk", z=10), chunks.makechunk("", "finalchunk", x=-5)})

class TestCountModel(unittest.TestCase):
    """
    Testing Count model, the simplest model in Lisp ACT-R.
    """
    
    def setUp(self):
        counting = modeltests.Counting()
        self.test = counting.model
        self.test.productions(counting.start, counting.increment, counting.stop)
        self.sim = self.test.simulation(trace=False)


    def test_procedure(self):
        warnings.simplefilter("ignore")
        while True:
            self.sim.step()
            if self.sim.current_event:
                break
        self.assertEqual(self.sim.show_time(), 0)
        self.assertEqual(self.sim.current_event.proc, 'PROCEDURAL')
        self.assertEqual(self.sim.current_event.action, 'CONFLICT RESOLUTION')
        while True:
            self.sim.step()
            if self.sim.current_event.action == "RULE SELECTED: start":
                break
        self.assertEqual(self.sim.show_time(), 0)
        while True:
            self.sim.step()
            if self.sim.current_event.action == "RULE FIRED: start":
                break
        self.assertEqual(self.sim.show_time(), 0.05)
        while True:
            self.sim.step()
            if self.sim.current_event.proc == "retrieval":
                break
        self.assertEqual(self.sim.show_time(), 0.05)
        self.assertEqual(self.sim.current_event.action, 'START RETRIEVAL')
        while True:
            self.sim.step()
            if self.sim.current_event.action == "RETRIEVED: countOrder(first= 2, second= 3)":
                break
        self.assertEqual(self.sim.show_time(), 0.1)
        while True:
            self.sim.step()
            if self.sim.current_event.proc == "PROCEDURAL":
                break
        self.assertEqual(self.sim.show_time(), 0.1)
        self.assertEqual(self.sim.current_event.action, 'CONFLICT RESOLUTION')
        while True:
            self.sim.step()
            if self.sim.current_event.action == "RULE FIRED: increment":
                break
        self.assertEqual(self.sim.show_time(), 0.15)
        while True:
            self.sim.step()
            if self.sim.current_event.proc == "retrieval":
                break
        self.assertEqual(self.sim.current_event.action, 'START RETRIEVAL')
        self.assertEqual(self.sim.show_time(), 0.15)
        while True:
            self.sim.step()
            if self.sim.current_event.action == "RETRIEVED: countOrder(first= 3, second= 4)":
                break
        self.assertEqual(self.sim.show_time(), 0.2)
        while True:
            self.sim.step()
            if self.sim.current_event.action == "CONFLICT RESOLUTION":
                break
        self.assertEqual(self.sim.show_time(), 0.2)
        while True:
            self.sim.step()
            if self.sim.current_event.action == "RULE FIRED: increment":
                break
        self.assertEqual(self.sim.show_time(), 0.25)
        while True:
            self.sim.step()
            if self.sim.current_event.proc == "retrieval":
                break
        self.assertEqual(self.sim.current_event.action, 'START RETRIEVAL')
        self.assertEqual(self.sim.show_time(), 0.25)
        while True:
            self.sim.step()
            if self.sim.current_event.action == "RULE FIRED: stop":
                break
        self.assertEqual(self.sim.show_time(), 0.3)


class TestCountModelstring(unittest.TestCase):
    """
    Testing Count model, the simplest model in Lisp ACT-R (the string version).
    """
    
    def setUp(self):
        self.counting = modeltests.Counting_stringversion()
        self.test = self.counting.model
        self.sim = self.test.simulation(trace=False)

    def test_procedure(self):
        while True:
            self.sim.step()
            if self.sim.current_event:
                break
        self.assertEqual(self.sim.show_time(), 0)
        self.assertEqual(self.sim.current_event.proc, 'PROCEDURAL')
        self.assertEqual(self.sim.current_event.action, 'CONFLICT RESOLUTION')
        while True:
            self.sim.step()
            if self.sim.current_event.action == "RULE SELECTED: start":
                break
        self.assertEqual(self.sim.show_time(), 0)
        while True:
            self.sim.step()
            if self.sim.current_event.action == "RULE FIRED: start":
                break
        self.assertEqual(self.sim.show_time(), 0.05)
        while True:
            self.sim.step()
            if self.sim.current_event.proc == "retrieval":
                break
        self.assertEqual(self.sim.show_time(), 0.05)
        self.assertEqual(self.sim.current_event.action, 'START RETRIEVAL')
        while True:
            self.sim.step()
            if self.sim.current_event.action == "RETRIEVED: countOrder(first= 2, second= 3)":
                break
        self.assertEqual(self.sim.show_time(), 0.1)
        while True:
            self.sim.step()
            if self.sim.current_event.proc == "PROCEDURAL":
                break
        self.assertEqual(self.sim.show_time(), 0.1)
        self.assertEqual(self.sim.current_event.action, 'CONFLICT RESOLUTION')
        while True:
            self.sim.step()
            if self.sim.current_event.action == "RULE FIRED: increment":
                break
        self.assertEqual(self.sim.show_time(), 0.15)
        while True:
            self.sim.step()
            if self.sim.current_event.proc == "retrieval":
                break
        self.assertEqual(self.sim.current_event.action, 'START RETRIEVAL')
        self.assertEqual(self.sim.show_time(), 0.15)
        while True:
            self.sim.step()
            if self.sim.current_event.action == "RETRIEVED: countOrder(first= 3, second= 4)":
                break
        self.assertEqual(self.sim.show_time(), 0.2)
        while True:
            self.sim.step()
            if self.sim.current_event.action == "CONFLICT RESOLUTION":
                break
        self.assertEqual(self.sim.show_time(), 0.2)
        while True:
            self.sim.step()
            if self.sim.current_event.action == "RULE FIRED: increment":
                break
        self.assertEqual(self.sim.show_time(), 0.25)
        while True:
            self.sim.step()
            if self.sim.current_event.proc == "retrieval":
                break
        self.assertEqual(self.sim.current_event.action, 'START RETRIEVAL')
        self.assertEqual(self.sim.show_time(), 0.25)
        while True:
            self.sim.step()
            if self.sim.current_event.action == "RULE FIRED: stop":
                break
        self.assertEqual(self.sim.show_time(), 0.3)

class TestAdditionModel(unittest.TestCase):
    """
    Testing Addition model. This includes multiple retrievals, interplay of retrievals and rule selection.
    """
    
    def setUp(self):
        addition = modeltests.Addition()
        self.test = addition.model
        self.sim = self.test.simulation(trace=False)

    def test_procedure(self):
        warnings.simplefilter("ignore")
        while True:
            self.sim.step()
            if self.sim.current_event:
                break
        self.assertEqual(self.sim.show_time(), 0)
        self.assertEqual(self.sim.current_event.proc, 'PROCEDURAL')
        self.assertEqual(self.sim.current_event.action, 'CONFLICT RESOLUTION')
        while True:
            self.sim.step()
            if self.sim.current_event.action == "RULE SELECTED: initAddition":
                break
        self.assertEqual(self.sim.show_time(), 0)
        while True:
            self.sim.step()
            if self.sim.current_event.action == "RULE FIRED: initAddition":
                break
        self.assertEqual(self.sim.show_time(), 0.05)
        while True:
            self.sim.step()
            if self.sim.current_event.proc == "retrieval":
                break
        self.assertEqual(self.sim.show_time(), 0.05)
        self.assertEqual(self.sim.current_event.action, 'START RETRIEVAL')
        while True:
            self.sim.step()
            if self.sim.current_event.action == "RETRIEVED: countOrder(first= 5, second= 6)":
                break
        self.assertEqual(self.sim.show_time(), 0.1)
        while True:
            self.sim.step()
            if self.sim.current_event.proc == "PROCEDURAL":
                break
        self.assertEqual(self.sim.show_time(), 0.1)
        self.assertEqual(self.sim.current_event.action, 'CONFLICT RESOLUTION')
        while True:
            self.sim.step()
            if self.sim.current_event.action == "RULE FIRED: incrementSum":
                break
        self.assertEqual(self.sim.show_time(), 0.15)
        while True:
            self.sim.step()
            if self.sim.current_event.proc == "retrieval":
                break
        self.assertEqual(self.sim.current_event.action, 'START RETRIEVAL')
        self.assertEqual(self.sim.show_time(), 0.15)
        while True:
            self.sim.step()
            if self.sim.current_event.action == "RETRIEVED: countOrder(first= 0, second= 1)":
                break
        self.assertEqual(self.sim.show_time(), 0.2)
        while True:
            self.sim.step()
            if self.sim.current_event.action == "CONFLICT RESOLUTION":
                break
        self.assertEqual(self.sim.show_time(), 0.2)
        while True:
            self.sim.step()
            if self.sim.current_event.action == "RULE FIRED: incrementCount":
                break
        self.assertEqual(self.sim.show_time(), 0.25)
        while True:
            self.sim.step()
            if self.sim.current_event.proc == "retrieval":
                break
        self.assertEqual(self.sim.current_event.action, 'START RETRIEVAL')
        self.assertEqual(self.sim.show_time(), 0.25)
        while True:
            self.sim.step()
            if self.sim.current_event.action == "RETRIEVED: countOrder(first= 6, second= 7)":
                break
        self.assertEqual(self.sim.show_time(), 0.3)
        while True:
            self.sim.step()
            if self.sim.current_event.action == "CONFLICT RESOLUTION":
                break
        self.assertEqual(self.sim.show_time(), 0.3)
        while True:
            self.sim.step()
            if self.sim.current_event.action == "RULE FIRED: incrementSum":
                break
        self.assertEqual(self.sim.show_time(), 0.35)
        while True:
            self.sim.step()
            if self.sim.current_event.proc == "retrieval":
                break
        self.assertEqual(self.sim.current_event.action, 'START RETRIEVAL')
        self.assertEqual(self.sim.show_time(), 0.35)
        while True:
            self.sim.step()
            if self.sim.current_event.action == "RETRIEVED: countOrder(first= 1, second= 2)":
                break
        self.assertEqual(self.sim.show_time(), 0.4)
        while True:
            self.sim.step()
            if self.sim.current_event.action == "CONFLICT RESOLUTION":
                break
        self.assertEqual(self.sim.show_time(), 0.4)
        while True:
            self.sim.step()
            if self.sim.current_event.action == "RULE FIRED: incrementCount":
                break
        self.assertEqual(self.sim.show_time(), 0.45)
        while True:
            self.sim.step()
            if self.sim.current_event.action == "RULE FIRED: terminateAddition":
                break
        self.assertEqual(self.sim.show_time(), 0.5)
        

class TestModel1(unittest.TestCase):
    """
    Testing Model1, on properties of buffers (retrieving, querying, clearing).
    """
    
    def setUp(self):
        m1 = modeltests.Model1()
        self.test = m1.model
        self.sim = self.test.simulation(trace=False)

    def test_procedure(self):
        warnings.simplefilter("ignore")
        while True:
            self.sim.step()
            if self.sim.current_event:
                break
        while True:
            self.sim.step()
            if self.sim.current_event.proc == "retrieval":
                break
        self.assertEqual(self.sim.show_time(), 0.05)
        self.assertEqual(self.sim.current_event.action, 'START RETRIEVAL')
        while True:
            self.sim.step()
            if self.sim.current_event.action == "RULE FIRED: increment":
                break
        self.assertEqual(self.sim.show_time(), 0.15)
        while True:
            self.sim.step()
            if self.sim.current_event.action == "RULE FIRED: increment":
                break
        self.assertEqual(self.sim.show_time(), 0.25)
        while True:
            self.sim.step()
            if self.sim.current_event.action == "RULE FIRED: stop":
                break
        self.assertEqual(self.sim.show_time(), 0.35)

class TestModel2(unittest.TestCase):
    """
    Testing Model2, on properties of buffer (retrieving, buffer modifications, clearing - checking that cleared chunks end up correctly represented in dm).
    """
    
    def setUp(self):
        self.m2 = modeltests.Model2(strict_harvesting=True)
        self.test = self.m2.model
        self.test.productions(self.m2.start, self.m2.switch, self.m2.clear)
        self.sim = self.test.simulation(trace=False)


    def test_procedure(self):
        warnings.simplefilter("ignore")
        while True:
            self.sim.step()
            if self.sim.current_event:
                break
        while True:
            self.sim.step()
            if self.sim.current_event.action == "CLEARED" and self.sim.current_event.proc == "g":
                break
        self.assertEqual(self.sim.show_time(), 0.15)
        self.assertEqual(self.m2.dm, declarative.DecMem({chunks.makechunk("","twoVars", x=10, y=20): np.array([0.0]), chunks.makechunk("","reverse", x=10, y=10): np.array([0.15])}))
        while True:
            self.sim.step()
            if self.sim.current_event.action == "CLEARED" and self.sim.current_event.proc == "retrieval":
                break
        self.assertEqual(self.sim.show_time(), 0.2)
        self.assertEqual(self.m2.dm, {chunks.makechunk("","twoVars", x=10, y=20): np.array([0.0]), chunks.makechunk("","twoVars", x=20, y=10): np.array([0.2]), chunks.makechunk("","reverse", x=10, y=10): np.array([0.15])})


class TestModel3(unittest.TestCase):
    """
    Testing Model3, on properties of buffer (retrieving, buffer modifications, clearing - checking that cleared chunks end up correctly represented in dm). This is like Model2 but it works with optional buffers.
    """
    
    def setUp(self):
        self.m3 = modeltests.Model3(strict_harvesting=True)
        self.dm = self.m3.dm
        self.test = self.m3.model
        self.test.productions(self.m3.start, self.m3.switch, self.m3.clear)
        self.sim = self.test.simulation(trace=False)


    def test_procedure(self):
        warnings.simplefilter("ignore")
        while True:
            self.sim.step()
            if self.sim.current_event:
                break
        while True:
            self.sim.step()
            if self.sim.current_event.action == "CLEARED" and self.sim.current_event.proc == "g":
                break
        self.assertEqual(self.sim.show_time(), 0.15)
        while True:
            self.sim.step()
            if self.sim.current_event.action == "CLEARED" and self.sim.current_event.proc == "retrieval":
                break
        self.assertEqual(self.sim.show_time(), 0.2)
        self.assertEqual(self.sim._Simulation__pr.dm, {'retrieval': {chunks.makechunk("","twoVars", x=10, y=20): np.array([0.0]), chunks.makechunk("","twoVars", x=20, y=10): np.array([0.2]), chunks.makechunk("","reverse", x=10, y=10): np.array([0.15])}, 'g': {chunks.makechunk("","twoVars", x=10, y=20): np.array([0.0]), chunks.makechunk("","twoVars", x=20, y=10): np.array([0.2]), chunks.makechunk("","reverse", x=10, y=10): np.array([0.15])}})
        self.assertEqual(self.m3.dm, {chunks.makechunk("","twoVars", x=10, y=20): np.array([0.0]), chunks.makechunk("","twoVars", x=20, y=10): np.array([0.2]), chunks.makechunk("","reverse", x=10, y=10): np.array([0.15])})
        self.assertTrue(self.sim._Simulation__pr.dm['retrieval'] is self.sim._Simulation__pr.dm['g'])

class TestMotorModel(unittest.TestCase):
    """
    Testing MotorModel, on properties of motor.
    """
    
    def setUp(self):
        mm = modeltests.MotorModel()
        self.test = mm.model
        self.test.productions(mm.start, mm.go_on, mm.finish)
        self.sim = self.test.simulation(trace=False)

    def test_procedure(self):
        warnings.simplefilter("ignore")
        while True:
            self.sim.step()
            if self.sim.current_event:
                break
        while True:
            self.sim.step()
            if self.sim.current_event.proc == "manual":
                break
        self.assertEqual(self.sim.show_time(), 0.05)
        self.assertEqual(self.sim.current_event.action, 'COMMAND: press_key')
        while True:
            self.sim.step()
            if self.sim.current_event.proc != "manual":
                break
        while True:
            self.sim.step()
            if self.sim.current_event.proc == "manual":
                break
        self.assertEqual(self.sim.show_time(), 0.1)
        self.assertEqual(self.sim.current_event.action, 'COMMAND: press_key')
        while True:
            self.sim.step()
            if self.sim.current_event.action == "RULE FIRED: finish":
                break
        self.assertEqual(self.sim.show_time(), 0.4)
        while True:
            self.sim.step()
            if self.sim.current_event.action == "KEY PRESSED: B":
                break
        self.assertEqual(self.sim.show_time(), 0.5)
        while True:
            self.sim.step()
            if self.sim.current_event.action == "KEY PRESSED: C":
                break
        self.assertEqual(self.sim.show_time(), 0.8)

class TestBaseLevelLearning(unittest.TestCase):
    """
    Testing that Base Level learning works. Comparing the internal workings of bll with the hardcoded activation.
    """
    
    def setUp(self):

        d = 0.5

        self.model = actr.ACTRModel(subsymbolic=True, baselevel_learning=True, latency_factor=0.4, decay=d, retrieval_threshold=-2, instantaneous_noise=0)

        self.model.chunktype("countOrder", "first, second")

        temps = [-100, -50, -1]

        self.model.set_decmem({self.model.chunkstring(string="\
                isa countOrder\
                first 1\
                second 2"): np.array(temps)})

        self.model.chunktype("countFrom", ("start", "end", "count"))
        self.model.goal.add(self.model.chunkstring(string="\
                isa countFrom\
                start   1\
                end 2"))

        self.model.productionstring(name="start", string="""
                =g>
                isa countFrom
                start =x
                count None
                ==>
                =g>
                isa countFrom
                count =x
                +retrieval>
                isa countOrder
                first =x""")

        self.sim = self.model.simulation(trace=False, start_time=0)
        
        self.model2 = actr.ACTRModel(subsymbolic=True, baselevel_learning=True, latency_factor=0.4, decay=d, retrieval_threshold=-2, instantaneous_noise=0)

        self.model2.chunktype("countOrder", "first, second")

        self.model2.set_decmem({self.model2.chunkstring(string="\
                isa countOrder\
                first 1\
                second 2"): np.array([])})

        self.model2.decmem.activations.update({self.model2.chunkstring(string="\
                isa countOrder\
                first 1\
                second 2"): math.log(sum([(0.05-x)** (-d) for x in temps]))})

        self.model2.chunktype("countFrom", ("start", "end", "count"))
        self.model2.goal.add(self.model2.chunkstring(string="\
                isa countFrom\
                start   1\
                end 2"))

        self.model2.productionstring(name="start", string="""
                =g>
                isa countFrom
                start =x
                count None
                ==>
                =g>
                isa countFrom
                count =x
                +retrieval>
                isa countOrder
                first =x""")

        self.sim2 = self.model2.simulation(trace=False, start_time=0)

        temps = [-100, -1]

        self.model3 = actr.ACTRModel(subsymbolic=True, baselevel_learning=True, latency_factor=0.4, decay=d, retrieval_threshold=-2, instantaneous_noise=0)

        self.model3.chunktype("countOrder", "first, second")

        self.model3.set_decmem({self.model3.chunkstring(string="\
                isa countOrder\
                first 1\
                second 2"): np.array([-50])})

        self.model3.decmem.activations.update({self.model3.chunkstring(string="\
                isa countOrder\
                first 1\
                second 2"): math.log(sum([(0.05-x)** (-d) for x in temps]))})

        self.model3.chunktype("countFrom", ("start", "end", "count"))
        self.model3.goal.add(self.model3.chunkstring(string="\
                isa countFrom\
                start   1\
                end 2"))

        self.model3.productionstring(name="start", string="""
                =g>
                isa countFrom
                start =x
                count None
                ==>
                =g>
                isa countFrom
                count =x
                +retrieval>
                isa countOrder
                first =x""")

        self.sim3 = self.model3.simulation(trace=False, start_time=0)

    def test_procedure(self):
        warnings.simplefilter("ignore")
        while True:
            self.sim.step()
            if self.sim.current_event.action == "RULE FIRED: start":
                break
        self.assertEqual(self.sim.show_time(), 0.05)
        time0 = self.sim.show_time()
        while True:
            self.sim.step()
            if self.sim.current_event.action == "RETRIEVED: countOrder(first= 1, second= 2)":
                break
        comp_time = self.sim.show_time() - time0

        while True:
            self.sim2.step()
            if self.sim2.current_event.action == "RULE FIRED: start":
                break
        time0 = self.assertEqual(self.sim2.show_time(), 0.05)
        time0 = self.sim2.show_time()
        while True:
            self.sim2.step()
            if self.sim2.current_event.action == "RETRIEVED: countOrder(first= 1, second= 2)":
                break
        comp_time2 = self.sim2.show_time() - time0
        self.assertEqual(comp_time, comp_time2)

        while True:
            self.sim3.step()
            if self.sim3.current_event.action == "RULE FIRED: start":
                break
        time0 = self.assertEqual(self.sim3.show_time(), 0.05)
        time0 = self.sim3.show_time()
        while True:
            self.sim3.step()
            if self.sim3.current_event.action == "RETRIEVED: countOrder(first= 1, second= 2)":
                break
        comp_time3 = self.sim3.show_time() - time0
        self.assertEqual(comp_time3, comp_time2)

class TestBaseLevelLearningModel(unittest.TestCase):
    """
    Testing Paired model (from unit4) on: environment, vision, motor, base level learning.
    """
    
    def setUp(self):

        used_stim = {"bank": "0"}
        text = []
        for x in zip(used_stim.keys(), used_stim.values()):
            text.append({1: {'text': x[0], 'position': (1366, 0)}})
            text.append({1: {'text': x[1], 'position': (1366, 0)}})
        trigger = list(used_stim.values())

        environ = actr.Environment(size=(1366,768), focus_position=(0,0))
        
        m = modeltests.Paired(environ, subsymbolic=True, baselevel_learning=True, latency_factor=0.4, decay=0.5, retrieval_threshold=-2, instantaneous_noise=0, strict_harvesting=True, emma_noise=False, automatic_visual_search=False, eye_mvt_angle_parameter=1, eye_mvt_scaling_parameter=0.05)
        self.test = m.m
        self.sim = m.m.simulation(trace=False, gui=True, environment_process=environ.environment_process, stimuli=2*text, triggers=4*trigger,times=5, start_time=0)

    def test_procedure(self):
        warnings.simplefilter("ignore")
        while True:
            self.sim.step()
            if self.sim.current_event.proc == "visual_location":
                break
        self.assertEqual(self.sim.show_time(), 0.05)
        self.assertEqual(self.sim.current_event.action, "EXTRA TEST ADDED")
        while True:
            self.sim.step()
            if self.sim.current_event.action == "RULE FIRED: attend_probe":
                break
        self.assertEqual(self.sim.show_time(), 0.1)
        while True:
            self.sim.step()
            if self.sim.current_event.action[0:18] == "ENCODED VIS OBJECT":
                break
        self.assertEqual(self.sim.show_time(), 0.2097)
        self.sim.step()
        while True:
            self.sim.step()
            if self.sim.current_event.proc == "visual":
                break
        self.assertEqual(self.sim.show_time(), 0.235)
        self.assertEqual(self.sim.current_event.action, "PREPARATION TO SHIFT VISUAL ATTENTION COMPLETED")
        while True:
            self.sim.step()
            if self.sim.current_event.action == "START RETRIEVAL":
                break
        start_retrieval_time = self.sim.show_time()
        while True:
            self.sim.step()
            if self.sim.current_event.proc == "visual":
                break
        self.assertEqual(self.sim.show_time(), 0.395)
        self.assertEqual(self.sim.current_event.action, "SHIFT COMPLETE TO POSITION: [1366, 0]")
        while True:
            self.sim.step()
            if self.sim.current_event.action == "RETRIEVED: None":
                break
        failed_retrieval_time = self.sim.show_time()
        self.assertEqual(round(failed_retrieval_time-start_retrieval_time, 3), 2.956)
        while True:
            self.sim.step()
            if self.sim.current_event.action == "RULE SELECTED: associate":
                break
        self.assertEqual(self.sim.show_time(), 5.05)
        while True:
            self.sim.step()
            if self.sim.current_event.proc == "g2" and self.sim.current_event.action == "CLEARED":
                break
        cleared_time = self.sim.show_time()
        self.assertIn(chunks.makechunk("","pair", probe="bank", answer="0"), self.sim._Simulation__pr.dm['retrieval'].keys())
        while True:
            self.sim.step()
            if self.sim.current_event.action == "RULE SELECTED: read_probe":
                break
        self.assertEqual(self.sim.show_time(), 10.05)
        while True:
            self.sim.step()
            if self.sim.current_event.action == "START RETRIEVAL":
                break
        start_retrieval_time = self.sim.show_time()
        while True:
            self.sim.step()
            if self.sim.current_event.action == "RETRIEVED: pair(answer= 0, probe= bank)":
                break
        retrieved_time = self.sim.show_time()
        self.assertEqual(round(retrieved_time-start_retrieval_time, 3), 0.894)
        while True:
            self.sim.step()
            if re.findall("^COMMAND", self.sim.current_event.action):
                break
        keypressing_time = self.sim.show_time()
        while True:
            self.sim.step()
            if re.findall("^KEY", self.sim.current_event.action):
                break
        keyfinal_time = self.sim.show_time()
        self.assertEqual(round(keyfinal_time-keypressing_time, 3), 0.4)
        cleared_time2 = self.sim.show_time()
        np.testing.assert_array_equal(np.array([cleared_time, keypressing_time]), self.sim._Simulation__pr.dm['retrieval'][chunks.Chunk("pair", probe="bank", answer="0")]) #keypressing_time relevant because at that point retrieval is cleared

class TestSourceActivation(unittest.TestCase):
    """
    Testing source activation.
    """

    def setUp(self):
        actr.chunktype("tt", "y")
        actr.chunktype("t2", "new, x")
        actr.chunktype("d", "")
        actr.chunktype("abc", "")
        actr.chunktype("first", "x, y, z")
        actr.chunktype("nnn", "x, y, z")
        self.first = chunks.makechunk("","first", x=2, y=5)
        self.second = chunks.makechunk("","first", x=2, y=None)
        self.third = chunks.makechunk("","first", x=2)
        self.fourth = chunks.makechunk("","first", x=chunks.makechunk("","tt"))
        self.fifth = chunks.makechunk("","first", x=chunks.makechunk("","t2", new=10))
        self.sixth = chunks.makechunk("","first", x=chunks.makechunk("","t2", x=10))
        self.seventh = chunks.makechunk("","first", x=chunks.makechunk("","tt"), y=chunks.makechunk("","abc"))
        self.eighth = chunks.makechunk("","first", x=chunks.makechunk("","t2", new=10), y=chunks.makechunk("","abc"))
        self.nineth = chunks.makechunk("","first", x=chunks.makechunk("","t2", x=10), y=chunks.makechunk("","abc"))
        self.tenth = chunks.makechunk("","first", x=chunks.makechunk("","t2", x=10), y=chunks.makechunk("","abc"), z=chunks.makechunk("","d"))
        self.eleventh = chunks.makechunk("","nnn", x=chunks.makechunk("","t2", x=10), y=chunks.makechunk("","abc"), z=chunks.makechunk("","d"))
        self.twelve = chunks.chunkstring("","isa first x 2 y None")
        self.thirteenth = chunks.chunkstring("aaaa","isa first x 2 y 5")
        self.fourteenth = chunks.chunkstring("","isa first x aaaa y 5")
        self.fiveteenth = chunks.chunkstring("","isa first x =x x aaaa y 5")

    def test_chunks(self):
        self.assertEqual(util.weigh_buffer(self.first, 1), 0)
        self.assertEqual(util.weigh_buffer(self.second, 1), 0)
        self.assertEqual(util.weigh_buffer(self.third, 1), 0)
        self.assertEqual(util.weigh_buffer(self.fourth, 1), 1)
        self.assertEqual(util.weigh_buffer(self.fifth, 1), 1)
        self.assertEqual(util.weigh_buffer(self.sixth, 1), 1)
        self.assertEqual(util.weigh_buffer(self.seventh, 1), 0.5)
        self.assertEqual(util.weigh_buffer(self.eighth, 1), 0.5)
        self.assertEqual(util.weigh_buffer(self.nineth, 1), 0.5)
        self.assertEqual(util.weigh_buffer(self.tenth, 6), 2)
        self.assertEqual(util.weigh_buffer(self.eleventh, 6), 2)
        self.assertEqual(round(util.weigh_buffer(self.tenth, 1), 5), 0.33333)
        self.assertEqual(round(util.weigh_buffer(self.eleventh, 1), 5), 0.33333)
        self.assertEqual(util.weigh_buffer(self.twelve, 1), 0)
        self.assertEqual(util.weigh_buffer(self.thirteenth, 1), 0)
        self.assertEqual(util.weigh_buffer(self.fourteenth, 1), 1)
        self.assertEqual(util.weigh_buffer(self.fiveteenth, 1), 1)

class TestSourceActivation2(unittest.TestCase):
    """
    Testing strength association.
    """

    def setUp(self):
        actr.chunktype("pres", "pres")
        actr.chunktype("finding_pres", "person")
        actr.chunktype("presidency_years", "value")
        self.dm = declarative.DecMem({chunks.makechunk("","one", x=chunks.makechunk("","pres", pres="obama")): 0, chunks.makechunk("","one", x=chunks.makechunk("","pres", pres="bush")): 0, chunks.makechunk("","two", y=chunks.makechunk("","presidency_years", value=8), z=chunks.makechunk("","pres", pres="bush")): 0})
        self.p = chunks.makechunk("","pres", pres="obama")
        self.p2 = chunks.makechunk("","pres", pres="bush")
        self.ret1 = chunks.makechunk("","pres", pres="clinton")
        self.ret2 = chunks.makechunk("","pres", pres="bush")
        self.ret3 = chunks.makechunk("","pres", pres="obama")

    def test_chunks(self):
        self.assertEqual(util.calculate_strength_association(self.p, self.ret1, self.dm, 4), 0)
        self.assertEqual(util.calculate_strength_association(self.p, self.ret2, self.dm, 4), 0)
        self.assertEqual(round(util.calculate_strength_association(self.p2, self.ret2, self.dm, 4), 6), 2.901388)
        self.assertEqual(round(util.calculate_strength_association(self.p, self.ret3, self.dm, 4), 6), 3.306853)

class TestSourceActivation3(unittest.TestCase):
    """
    Testing spreading activation.
    """

    def setUp(self):
        actr.chunktype("pres", "pres")
        actr.chunktype("finding_pres", "person, years")
        actr.chunktype("presidency_years", "value")
        actr.chunktype("one", "x")
        actr.chunktype("two", "y, z")
        self.ch1 = chunks.makechunk("", "one", x=chunks.makechunk("", "pres", pres="obama"))
        self.ch2 = chunks.makechunk("", "one", x=chunks.makechunk("", "pres", pres="bush"))
        self.ch3 = chunks.makechunk("", "two", y=chunks.makechunk("", "presidency_years", value=8), z=chunks.makechunk("","pres", pres="bush"))
        self.dm = declarative.DecMem({self.ch1: 0, self.ch2: 0, self.ch3: 0})
        self.g = goals.Goal()
        self.g.add(chunks.makechunk("","finding_pres", person=chunks.makechunk("","pres", pres="obama"), years="unknown"))
        self.g2 = goals.Goal()
        self.g2.add(chunks.makechunk("","finding_pres", person=chunks.makechunk("","pres", pres="bush"), years="unknown"))
        self.g3 = goals.Goal()
        self.g3.add(chunks.makechunk("","finding_pres", person=chunks.makechunk("","pres", pres="bush"), years=chunks.makechunk("","presidency_years", value=8)))
        self.g4 = goals.Goal()
        self.g4.add(chunks.makechunk("","finding_pres", person=chunks.makechunk("","pres", pres="bush"), years=chunks.makechunk("","presidency_years", value=5)))
        self.buffers = {"g": self.g, "g2": self.g2, "g3": self.g3, "g4": self.g4}

    def test_chunks(self):
        self.assertEqual(round(util.spreading_activation(self.ch1, self.buffers, self.dm, {"g": 1}, 2), 6), 1.306853)
        self.assertEqual(round(util.spreading_activation(self.ch2, self.buffers, self.dm, {"g": 1}, 2), 6), 0)
        self.assertEqual(round(util.spreading_activation(self.ch1, self.buffers, self.dm, {"g2": 1}, 2), 6), 0)
        self.assertEqual(round(util.spreading_activation(self.ch2, self.buffers, self.dm, {"g2": 1}, 2), 6), 0.901388)
        self.assertEqual(round(util.spreading_activation(self.ch3, self.buffers, self.dm, {"g2": 1}, 2), 6), 0.901388)
        self.assertEqual(round(util.spreading_activation(self.ch1, self.buffers, self.dm, {"g3": 1}, 2), 6), 0)
        self.assertEqual(round(util.spreading_activation(self.ch2, self.buffers, self.dm, {"g3": 1}, 2), 6), 0.450694)
        self.assertEqual(round(util.spreading_activation(self.ch3, self.buffers, self.dm, {"g3": 1}, 2), 6), 1.10412)
        self.assertEqual(round(util.spreading_activation(self.ch3, self.buffers, self.dm, {"g2": 1, "g3": 1}, 2), 6), 2.005508)
        self.ch4 = chunks.makechunk("","three", x=chunks.makechunk("","pres", pres="bush"), xx=chunks.makechunk("","pres", pres="bush"))
        self.dm.add(self.ch4)
        self.assertEqual(round(util.spreading_activation(self.ch4, self.buffers, self.dm, {"g2": 1}, 2), 6), 1.083709)

class TestSourceActivation4(unittest.TestCase):
    """
    Testing strength association using chunkstring.
    """

    def setUp(self):
        actr.chunktype("pres", "pres")
        actr.chunktype("finding_pres", "person")
        actr.chunktype("presidency_years", "value")
        self.dm = declarative.DecMem({chunks.makechunk("","one", x=chunks.makechunk("","pres", pres="obama")): 0, chunks.makechunk("","one", x=chunks.makechunk("","pres", pres="bush")): 0, chunks.makechunk("","two", y=chunks.makechunk("","presidency_years", value=8), z=chunks.makechunk("","pres", pres="bush")): 0})
        self.p = chunks.chunkstring(name="", string="isa pres pres obama")
        self.p2 = chunks.chunkstring(name="", string="isa pres pres bush")
        self.ret1 = chunks.chunkstring(name="", string="isa pres pres clinton")
        self.ret2 = chunks.chunkstring(name="", string="isa pres pres bush")
        self.ret3 = chunks.chunkstring(name="", string="isa pres pres obama")

    def test_chunks(self):
        self.assertEqual(util.calculate_strength_association(self.p, self.ret1, self.dm, 4), 0)
        self.assertEqual(util.calculate_strength_association(self.p, self.ret2, self.dm, 4), 0)
        self.assertEqual(round(util.calculate_strength_association(self.p2, self.ret2, self.dm, 4), 6), 2.901388)
        self.assertEqual(round(util.calculate_strength_association(self.p, self.ret3, self.dm, 4), 6), 3.306853)

class TestSourceActivation5(unittest.TestCase):
    """
    Testing strength association using chunkstring.
    """

    def setUp(self):
        actr.chunktype("pres", "pres")
        actr.chunktype("finding_pres", "person")
        actr.chunktype("presidency_years", "value")
        self.proob = chunks.makechunk("proob","pres", pres="obama")
        self.proob2 = chunks.makechunk("proob2","pres", pres="clinton")
        self.dm = declarative.DecMem({chunks.chunkstring("","isa one x proob"): 0, chunks.makechunk("","one", x=chunks.chunkstring("","isa pres pres bush")): 0, chunks.makechunk("","two", y=chunks.makechunk("","presidency_years", value=8), z=chunks.makechunk("","pres", pres="bush")): 0, chunks.makechunk("", "two", y=self.proob2, z=self.proob2): 0})
        self.p = chunks.chunkstring(name="", string="isa pres pres obama")
        self.p2 = chunks.chunkstring(name="", string="isa pres pres bush")
        self.ret1 = chunks.chunkstring(name="", string="isa pres pres clinton")
        self.ret2 = chunks.chunkstring(name="", string="isa pres pres bush")
        self.ret3 = chunks.chunkstring(name="", string="isa pres pres obama")

    def test_chunks(self):
        self.assertEqual(util.calculate_strength_association(self.p, self.ret1, self.dm, 4), 0)
        self.assertEqual(util.calculate_strength_association(self.p, self.ret2, self.dm, 4), 0)
        self.assertEqual(round(util.calculate_strength_association(self.p2, self.ret2, self.dm, 4), 6), 2.901388)
        self.assertEqual(round(util.calculate_strength_association(self.p, self.ret3, self.dm, 4), 6), 3.306853)
        self.assertEqual(round(util.calculate_strength_association(self.proob2, self.ret1, self.dm, 4), 6), 2.901388)

class TestSourceActivation6(unittest.TestCase):
    """
    Testing spreading activation using chunkstring.
    """

    def setUp(self):
        actr.chunktype("pres", "pres")
        actr.chunktype("finding_pres", "person, years")
        actr.chunktype("presidency_years", "value")
        actr.chunktype("one", "x")
        actr.chunktype("two", "y, z")
        chunks.chunkstring("proob", "isa pres pres obama")
        self.ch1 = chunks.chunkstring("", "isa one x proob")
        self.ch2 = chunks.makechunk("", "one", x=chunks.chunkstring("", "isa pres pres bush"))
        self.ch3d = chunks.makechunk("", "two", y=chunks.makechunk("", "presidency_years", value=8), z=chunks.makechunk("","pres", pres="bush"))
        self.ch5 = chunks.chunkstring("", "isa pres pres clinton")
        chunks.makechunk("val8", "presidency_years", value=8)
        chunks.makechunk("presbush","pres", pres="bush")
        self.ch3 = chunks.chunkstring("", "isa two y val8 z presbush")
        self.dm = declarative.DecMem({self.ch1: 0, self.ch2: 0, self.ch3d: 0, self.ch5: 0})
        self.g = goals.Goal()
        self.g.add(chunks.makechunk("","finding_pres", person=chunks.makechunk("","pres", pres="obama"), years="unknown"))
        self.g2 = goals.Goal()
        self.g2.add(chunks.chunkstring("","isa finding_pres person presbush years unknown"))
        self.g3 = goals.Goal()
        self.g3.add(chunks.makechunk("","finding_pres", person=chunks.makechunk("","pres", pres="bush"), years=chunks.makechunk("","presidency_years", value=8)))
        self.g4 = goals.Goal()
        self.g4.add(chunks.makechunk("","finding_pres", person=chunks.makechunk("","pres", pres="bush"), years=chunks.makechunk("","presidency_years", value=5)))
        self.g5 = goals.Goal()
        self.g5.add(chunks.chunkstring("","isa pres pres clinton"))
        self.buffers = {"g": self.g, "g2": self.g2, "g3": self.g3, "g4": self.g4, "g5": self.g5}

    def test_chunks(self):
        self.assertEqual(round(util.spreading_activation(self.ch1, self.buffers, self.dm, {"g": 1}, 2), 6), 1.306853)
        self.assertEqual(round(util.spreading_activation(self.ch2, self.buffers, self.dm, {"g": 1}, 2), 6), 0)
        self.assertEqual(round(util.spreading_activation(self.ch1, self.buffers, self.dm, {"g2": 1}, 2), 6), 0)
        self.assertEqual(round(util.spreading_activation(self.ch2, self.buffers, self.dm, {"g2": 1}, 2), 6), 0.901388)
        self.assertEqual(round(util.spreading_activation(self.ch3, self.buffers, self.dm, {"g2": 1}, 2), 6), 0.901388)
        self.assertEqual(round(util.spreading_activation(self.ch1, self.buffers, self.dm, {"g3": 1}, 2), 6), 0)
        self.assertEqual(round(util.spreading_activation(self.ch2, self.buffers, self.dm, {"g3": 1}, 2), 6), 0.450694)
        self.assertEqual(round(util.spreading_activation(self.ch3, self.buffers, self.dm, {"g3": 1}, 2), 6), 1.10412)
        self.assertEqual(round(util.spreading_activation(self.ch3, self.buffers, self.dm, {"g2": 1, "g3": 1}, 2), 6), 2.005508)
        self.assertEqual(round(util.spreading_activation(self.ch5, self.buffers, self.dm, {"g5": 1}, 2), 6), 0)
        self.ch4 = chunks.makechunk("","three", x=chunks.makechunk("","pres", pres="bush"), xx=chunks.makechunk("","pres", pres="bush"))
        self.dm.add(self.ch4)
        self.assertEqual(round(util.spreading_activation(self.ch4, self.buffers, self.dm, {"g2": 1}, 2), 6), 1.083709)


class TestProductionUtilities(unittest.TestCase):
    """
    Testing utilities and rewards.
    """
    
    def setUp(self):
        mm = modeltests.Utilities(subsymbolic=True, utility_noise=10, utility_learning=True)
        self.test = mm.m
        self.test.productions(mm.one, mm.two, mm.three)
        self.sim = self.test.simulation(trace=False)

    def test_procedure(self):
        ut_one = 1      
        ut_two = 5
        times_two = []
        times_one = []
        time = -1
        while True:
            self.sim.step()
            if self.sim.current_event:
                break
        while True:
            self.sim.step()
            if self.sim.current_event.action == "RULE SELECTED: two" and time != self.sim.show_time():
                self.sim.current_event = actr.productions.Event(self.sim.current_event.time, self.sim.current_event.proc, "deleted")
                time = self.sim.show_time()
                times_two.append(time)
            if self.sim.current_event.action == "RULE SELECTED: one" and time != self.sim.show_time():
                self.sim.current_event = actr.productions.Event(self.sim.current_event.time, self.sim.current_event.proc, "deleted")
                time = self.sim.show_time()
                times_one.append(time)
            if self.sim.current_event.action == "RULE FIRED: three" and time != self.sim.show_time():
                time = self.sim.show_time()
                break
        for idx in range(len(times_one)):
            times_one[idx] = time-times_one[idx]
        for idx in range(len(times_two)):
            times_two[idx] = time-times_two[idx]
        utility_one = ut_one
        for idx in range(len(times_one)):
            utility_one = utility_one + 0.2*(10-times_one[idx]-utility_one)
        utility_two = ut_two
        for idx in range(len(times_two)):
            utility_two = utility_two + 0.2*(10-times_two[idx]-utility_two)
        self.assertEqual(self.test._ACTRModel__productions["one"]["utility"], round(utility_one, 4))

        self.assertEqual(self.test._ACTRModel__productions["two"]["utility"], round(utility_two, 4))

        self.assertEqual(self.test._ACTRModel__productions["three"]["utility"], 1.99)

class TestCompilation1(unittest.TestCase):
    """
    Testing production compilation.
    """
    
    def setUp(self):
        mm = modeltests.Compilation1(production_compilation=True)
        self.test = mm
        self.model = mm.m
        self.sim = self.model.simulation(trace=False)

    def test_procedure(self):
        while True:
            self.sim.step()
            if self.sim.current_event.action == "RULE CREATED: one and two":
                break
        new_rule = self.model._ACTRModel__productions["one and two"]["rule"]()

        pro = next(new_rule)

        self.assertSetEqual(set(pro), {"=g"})
        var1 = pro["=g"]._asdict()["starting"].variables
        var2 = pro["=g"]._asdict()["ending"].negvariables
        var3 = pro["=g"]._asdict()["ending"].variables
        self.assertTrue(var1 == var2[0])
        self.assertFalse(var1 == var3)
        
        pro = next(new_rule)
        
        self.assertSetEqual(set(pro), {"=g"})

        var21 = pro["=g"]._asdict()["starting"].variables
        var22 = pro["=g"]._asdict()["ending"].negvariables
        var23 = pro["=g"]._asdict()["ending"].variables
        val = pro["=g"]._asdict()["starting"].values
        self.assertTrue(var21 == None)
        self.assertTrue(var22 == ())
        self.assertFalse(var21 == var23)
        self.assertTrue(var1 == var23)
        self.assertEqual(val, '4')

class TestCompilation2(unittest.TestCase):
    """
    Testing production compilation.
    """
    
    def setUp(self):
        mm = modeltests.Compilation2(production_compilation=True)
        self.test = mm
        self.model = mm.m
        self.sim = self.model.simulation(trace=False)

    def test_procedure(self):
        while True:
            self.sim.step()
            if self.sim.current_event.action == "RULE CREATED: one and two":
                break
        new_rule = self.model._ACTRModel__productions["one and two"]["rule"]()

        pro = next(new_rule)

        self.assertSetEqual(set(pro), {"=g"})
        var1 = pro["=g"]._asdict()["starting"].variables
        var2 = pro["=g"]._asdict()["ending"].negvariables
        var3 = pro["=g"]._asdict()["ending"].variables
        self.assertTrue(var1 == var3)
        self.assertFalse(var1 == var2)
        
        pro = next(new_rule)
        
        self.assertSetEqual(set(pro), {"=g"})

        var21 = pro["=g"]._asdict()["starting"].variables
        var22 = pro["=g"]._asdict()["ending"].variables
        val21 = pro["=g"]._asdict()["starting"].values
        val22 = pro["=g"]._asdict()["ending"].values
        self.assertTrue(var21 == var22)
        self.assertTrue(val21 == val22)
        self.assertFalse(var21 == val21)
        self.assertEqual(val21, '4')
        self.assertEqual(val22, '4')

class TestCompilation3(unittest.TestCase):
    """
    Testing production compilation.
    """
    
    def setUp(self):
        mm = modeltests.Compilation3(production_compilation=True)
        self.test = mm
        self.model = mm.m
        self.sim = self.model.simulation(trace=False)

    def test_procedure(self):
        while True:
            self.sim.step()
            if self.sim.current_event.action == "RULE CREATED: one and two":
                break
        
        new_rule = self.model._ACTRModel__productions["one and two"]["rule"]()

        pro = next(new_rule)

        self.assertSetEqual(set(pro), {"=g"})
        var1 = pro["=g"]._asdict()["arg1"].variables
        var2 = pro["=g"]._asdict()["arg2"].variables
        var3 = pro["=g"]._asdict()["arg3"].variables
        var4 = pro["=g"]._asdict()["arg4"].variables
        val1 = pro["=g"]._asdict()["arg1"].values
        val2 = pro["=g"]._asdict()["arg2"].values
        val3 = pro["=g"]._asdict()["arg3"].values
        val4 = pro["=g"]._asdict()["arg4"].values
        self.assertEqual(var1, None)
        self.assertEqual(var2, 'v2')
        self.assertEqual(var3, 'v2')
        self.assertEqual(var4, 'v3')
        self.assertEqual(val1, '3')
        self.assertEqual(val2, None)
        self.assertEqual(val3, None)
        self.assertEqual(val4, None)
        
        pro = next(new_rule)
        
        self.assertSetEqual(set(pro), {"=g"})
        var1 = pro["=g"]._asdict()["arg1"].variables
        var2 = pro["=g"]._asdict()["arg2"].variables
        var3 = pro["=g"]._asdict()["arg3"].variables
        var4 = pro["=g"]._asdict()["arg4"].variables
        val1 = pro["=g"]._asdict()["arg1"].values
        val2 = pro["=g"]._asdict()["arg2"].values
        val3 = pro["=g"]._asdict()["arg3"].values
        val4 = pro["=g"]._asdict()["arg4"].values
        self.assertEqual(var1, 'v2')
        self.assertEqual(var2, 'v3')
        self.assertEqual(var3, 'v3')
        self.assertEqual(var4, 'v2')
        self.assertEqual(val1, None)
        self.assertEqual(val2, None)
        self.assertEqual(val3, None)
        self.assertEqual(val4, None)

class TestCompilation4(unittest.TestCase):
    """
    Testing production compilation. Testing queries & empty values.
    """
    
    def setUp(self):
        mm = modeltests.Compilation4(production_compilation=True)
        self.test = mm
        self.model = mm.m
        self.sim = self.model.simulation(trace=False)

    def test_procedure(self):

        while True:
            try:
                self.sim.step()
            except simpy.core.EmptySchedule:
                break
            if self.sim.current_event.action == "RULE CREATED: one and two":
                break

        new_rule = self.model._ACTRModel__productions["one and two"]["rule"]()

        pro = next(new_rule)
        self.assertSetEqual(set(pro), {"=g", "?g"})
        self.assertDictEqual(pro["?g"], {'buffer': 'full', 'state': 'free'})
        
        self.model._ACTRModel__productions.pop("one")

        g_noncompiled = self.model.goal.copy()
        self.sim = self.model.simulation(trace=False)

        self.model.goal.add(actr.makechunk(nameofchunk="start", typename="goal", arg1=1, arg2=None, arg4=10))
        
        while True:
            self.sim.step()
            if self.sim.current_event.action == "RULE FIRED: one and two":
                break

        while True:
            self.sim.step()
            if self.sim.current_event.action == "CONFLICT RESOLUTION":
                break

        g_compiled = self.model.goal.copy()

        self.assertEqual(g_noncompiled, g_compiled)

        self.sim = self.model.simulation(trace=False)

        self.model.goal.add(actr.makechunk(nameofchunk="start", typename="goal", arg1=1, arg2=None, arg3=7, arg4=10))
        
        self.sim.step()
        self.assertEqual(self.sim.current_event.action, "CONFLICT RESOLUTION")
        self.sim.step()
        self.assertEqual(self.sim.current_event.action, "NO RULE FOUND")

class TestCompilation5(unittest.TestCase):
    """
    Testing production compilation.
    """
    
    def setUp(self):
        mm = modeltests.Compilation5(production_compilation=True)
        self.test = mm
        self.model = mm.m
        self.sim = self.model.simulation(trace=False)

    def test_procedure(self):
        while True:
            try:
                self.sim.step()
            except simpy.core.EmptySchedule:
                break
            if self.sim.current_event.action == "RULE CREATED: one and two":
                break
        new_rule = self.model._ACTRModel__productions["one and two"]["rule"]()

        pro = next(new_rule)
        self.assertSetEqual(set(pro), {"=g"})
        var1 = pro["=g"]._asdict()["starting"].variables
        var2 = pro["=g"]._asdict()["ending"].negvariables
        var3 = pro["=g"]._asdict()["ending"].variables
        val1 = pro["=g"]._asdict()["starting"].values
        self.assertEqual(var1, 'x')
        self.assertEqual(var2, ('x',))
        self.assertEqual(var3, None)
        self.assertEqual(val1, None)
        
        pro = next(new_rule)

        self.assertSetEqual(set(pro), {"=g"})
        var1 = pro["=g"]._asdict()["starting"].variables
        var2 = pro["=g"]._asdict()["ending"].variables
        val1 = pro["=g"]._asdict()["starting"].values
        val2 = pro["=g"]._asdict()["ending"].values
        self.assertEqual(var1, None)
        self.assertEqual(var2, 'x')
        self.assertEqual(val1, '4')
        self.assertEqual(val2, None)
        
        self.model._ACTRModel__productions.pop("one")

        g_noncompiled = self.model.goal.copy()

        self.model.goal.add(actr.makechunk(nameofchunk="start", typename="state", starting=1, ending=3, position='start'))

        self.sim = self.model.simulation(trace=False)

        while True:
            self.sim.step()
            if self.sim.current_event.action == "RULE FIRED: one and two":
                break

        while True:
            self.sim.step()
            if self.sim.current_event.action == "CONFLICT RESOLUTION":
                break

        g_compiled = self.model.goal.copy()

        self.assertEqual(g_noncompiled, g_compiled)

class TestCompilation6(unittest.TestCase):
    """
    Testing production compilation.
    """
    
    def setUp(self):
        mm = modeltests.Compilation6(production_compilation=True, strict_harvesting=True)
        self.test = mm
        self.model = mm.m
        self.sim = self.model.simulation(trace=False)

    def test_procedure(self):
        while True:
            try:
                self.sim.step()
            except simpy.core.EmptySchedule:
                break
            if self.sim.current_event.action == "RULE CREATED: one and two":
                break
        
        new_rule = self.model._ACTRModel__productions["one and two"]["rule"]()

        pro = next(new_rule)

        self.assertSetEqual(set(pro), {"=g"})
        var1 = pro["=g"]._asdict()["arg1"].variables
        var2 = pro["=g"]._asdict()["arg2"].variables
        var3 = pro["=g"]._asdict()["arg3"].variables
        var4 = pro["=g"]._asdict()["arg4"].variables
        val1 = pro["=g"]._asdict()["arg1"].values
        val2 = pro["=g"]._asdict()["arg2"].values
        val3 = pro["=g"]._asdict()["arg3"].values
        val4 = pro["=g"]._asdict()["arg4"].values
        self.assertEqual(var1, None)
        self.assertEqual(var2, 'v2')
        self.assertEqual(var3, 'v2')
        self.assertEqual(var4, 'v3')
        self.assertEqual(val1, '3')
        self.assertEqual(val2, None)
        self.assertEqual(val3, None)
        self.assertEqual(val4, None)
        
        pro = next(new_rule)

        self.assertSetEqual(set(pro), {"=g"})
        var1 = pro["=g"]._asdict()["arg1"].variables
        var2 = pro["=g"]._asdict()["arg2"].variables
        var3 = pro["=g"]._asdict()["arg3"].variables
        var4 = pro["=g"]._asdict()["arg4"].variables
        val1 = pro["=g"]._asdict()["arg1"].values
        val2 = pro["=g"]._asdict()["arg2"].values
        val3 = pro["=g"]._asdict()["arg3"].values
        val4 = pro["=g"]._asdict()["arg4"].values
        self.assertEqual(var1, 'v2')
        self.assertEqual(var2, None)
        self.assertEqual(var3, 'v3')
        self.assertEqual(var4, 'v2')
        self.assertEqual(val1, None)
        self.assertEqual(val2, '5')
        self.assertEqual(val3, None)
        self.assertEqual(val4, None)

class TestCompilation7(unittest.TestCase):
    """
    Testing production compilation.
    """
    
    def setUp(self):
        mm = modeltests.Compilation7(production_compilation=True, strict_harvesting=False)
        self.test = mm
        self.model = mm.m
        self.sim = self.model.simulation(trace=False)

    def test_procedure(self):
        while True:
            try:
                self.sim.step()
            except simpy.core.EmptySchedule:
                break
            if self.sim.current_event.action == "RULE CREATED: one and two":
                break
        
        new_rule = self.model._ACTRModel__productions["one and two"]["rule"]()

        pro = next(new_rule)

        self.assertSetEqual(set(pro), {"=g"})
        var1 = pro["=g"]._asdict()["arg1"].variables
        var2 = pro["=g"]._asdict()["arg2"].variables
        var3 = pro["=g"]._asdict()["arg3"].variables
        var4 = pro["=g"]._asdict()["arg4"].variables
        val1 = pro["=g"]._asdict()["arg1"].values
        val2 = pro["=g"]._asdict()["arg2"].values
        val3 = pro["=g"]._asdict()["arg3"].values
        val4 = pro["=g"]._asdict()["arg4"].values
        self.assertEqual(var1, None)
        self.assertEqual(var2, 'v2')
        self.assertEqual(var3, 'v2')
        self.assertEqual(var4, 'v3')
        self.assertEqual(val1, '3')
        self.assertEqual(val2, None)
        self.assertEqual(val3, None)
        self.assertEqual(val4, None)
        
        pro = next(new_rule)

        self.assertSetEqual(set(pro), {"=g", "~retrieval"})
        var1 = pro["=g"]._asdict()["arg1"].variables
        var2 = pro["=g"]._asdict()["arg2"].variables
        var3 = pro["=g"]._asdict()["arg3"].variables
        var4 = pro["=g"]._asdict()["arg4"].variables
        val1 = pro["=g"]._asdict()["arg1"].values
        val2 = pro["=g"]._asdict()["arg2"].values
        val3 = pro["=g"]._asdict()["arg3"].values
        val4 = pro["=g"]._asdict()["arg4"].values
        self.assertEqual(var1, 'v2')
        self.assertEqual(var2, None)
        self.assertEqual(var3, 'v3')
        self.assertEqual(var4, 'v2')
        self.assertEqual(val1, None)
        self.assertEqual(val2, '5')
        self.assertEqual(val3, None)
        self.assertEqual(val4, None)

class TestCompilation8(unittest.TestCase):
    """
    Testing production compilation. Cases which should block compilaton
    """
    
    def setUp(self):
        mm = modeltests.Compilation8(production_compilation=True, strict_harvesting=False)
        self.test = mm
        self.model = mm.m
        self.model.productions(mm.start, mm.go_on, mm.still_go_on, mm.finish)
        self.sim = self.model.simulation(trace=False)

    def test_procedure(self):
        while True:
            try:
                self.sim.step()
            except simpy.core.EmptySchedule:
                break
            if self.sim.current_event.action == "RULE CREATED: go_on and still_go_on":
                break
        new_rule = self.model._ACTRModel__productions["go_on and still_go_on"]["rule"]()

        pro = next(new_rule)

        self.assertSetEqual(set(pro), {"=g"})
        pro = next(new_rule)

        self.assertSetEqual(set(pro), {"=g", "+manual"})

class TestCompilation9(unittest.TestCase):
    """
    Testing production compilation.
    """
    
    def setUp(self):
        mm = modeltests.Compilation9(production_compilation=True)
        self.test = mm
        self.model = mm.m
        self.sim = self.model.simulation(trace=False)

    def test_procedure(self):
        while True:
            try:
                self.sim.step()
            except simpy.core.EmptySchedule:
                break
            if self.sim.current_event.action == "RULE CREATED: one and two":
                break
        
        self.assertSetEqual(set(self.model._ACTRModel__productions), {"one", "two"})
        
class TestCompilation10(unittest.TestCase):
    """
    Testing production compilation.
    """
    
    def setUp(self):
        mm = modeltests.Compilation10(production_compilation=True, strict_harvesting=False)
        self.test = mm
        self.model = mm.m
        self.sim = self.model.simulation(trace=False)

    def test_procedure(self):
        while True:
            try:
                self.sim.step()
            except simpy.core.EmptySchedule:
                break
            if self.sim.current_event.action == "RULE CREATED: one and two":
                break
        
        self.assertSetEqual(set(self.model._ACTRModel__productions), {"one", "two"})

class TestCompilation11(unittest.TestCase):
    """
    Testing production compilation and utility learning.
    """
    
    def setUp(self):
        mm = modeltests.Compilation11(utility_learning=True,  production_compilation=True, utility_noise=1)
        self.test = mm
        self.model = mm.m
        self.sim = self.model.simulation(trace=False)

    def test_procedure(self):
        while True:
            self.sim.step()
            if self.sim.current_event.action == "RULE RE-CREATED: one and two":
                break
        new_rule = self.model._ACTRModel__productions["one and two"]
        new_rule2 = self.model._ACTRModel__productions.pop("two and one")
        u1 = 0 + 0.2*(10 - 0)
        self.assertEqual(new_rule["utility"], u1)
        self.assertEqual(new_rule2["utility"], 0)
        while True:
            self.sim.step()
            if self.sim.current_event.action == "RULE RE-CREATED: one and two":
                break
        u2 = u1 + 0.2*(10 - u1)
        self.model._ACTRModel__productions.pop("two and one")
        self.assertEqual(new_rule["utility"], u2)

class TestCompilation12(unittest.TestCase):
    """
    Testing production compilation.
    """
    
    def setUp(self):
        mm = modeltests.Compilation12(production_compilation=True)
        self.test = mm
        self.model = mm.m
        self.sim = self.model.simulation(trace=False)

    def test_procedure(self):
        while True:
            try:
                self.sim.step()
            except simpy.core.EmptySchedule:
                break
            if self.sim.current_event.action == "RULE CREATED: one and two":
                break

        new_rule = self.model._ACTRModel__productions["one and two"]["rule"]()

        pro = next(new_rule)
        self.assertSetEqual(set(pro), {"=g"})
        var1 = pro["=g"]._asdict()["starting"].variables
        var2 = pro["=g"]._asdict()["ending"].negvariables
        var3 = pro["=g"]._asdict()["ending"].variables
        val1 = pro["=g"]._asdict()["starting"].values
        self.assertEqual(var1, 'x')
        self.assertEqual(var2, ('x',))
        self.assertEqual(var3, None)
        self.assertEqual(val1, None)
        
        pro = next(new_rule)

        self.assertSetEqual(set(pro), {"=g"})
        var1 = pro["=g"]._asdict()["starting"].variables
        var2 = pro["=g"]._asdict()["ending"].variables
        val1 = pro["=g"]._asdict()["starting"].values
        val2 = pro["=g"]._asdict()["ending"].values
        val3 = pro["=g"]._asdict()["position"].values
        self.assertEqual(var1, None)
        self.assertEqual(var2, 'x')
        self.assertEqual(val1, 'None')
        self.assertEqual(val2, None)
        self.assertEqual(val3, 'completeend')
        
        self.model._ACTRModel__productions.pop("one")

        g_noncompiled = self.model.goal.copy()

        self.model.goal.add(actr.makechunk(nameofchunk="start", typename="state", starting=1, ending=3, position='start'))

        self.sim = self.model.simulation(trace=False)

        while True:
            self.sim.step()
            if self.sim.current_event.action == "RULE FIRED: one and two":
                break

        while True:
            self.sim.step()
            if self.sim.current_event.action == "CONFLICT RESOLUTION":
                break

        g_compiled = self.model.goal.copy()

        self.assertEqual(g_noncompiled, g_compiled)

if __name__ == '__main__':
    unittest.main()
