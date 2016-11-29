"""
Testing the symbolic part of the module.
Requires Python >= 3.3
"""

import unittest
import collections
import re
import warnings

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
        self.chunk = chunks.Chunk("test", arg1="v1", arg2="v2")
        self.chunk2 = chunks.Chunk("test", arg1="v1")
        self.chunk3 = chunks.Chunk("test", arg2="v2", arg1="v1")
        self.chunk4 = chunks.Chunk("test", arg2="v5", arg1="v1")
        self.chunk5 = chunks.Chunk("test", arg1="v1", arg2=None)

    def test_values(self):
        self.assertEqual(self.chunk.arg1, "v1")
        self.assertEqual(self.chunk.arg2, "v2")
        with self.assertRaises(AttributeError):
            print(self.chunk.new)

    def test_items(self):
        self.assertTrue(("arg1", "v1") in self.chunk)
        self.assertTrue(("arg2", "v2") in self.chunk)
        self.assertFalse(("arg3", "v3") in self.chunk)

    def test_chunks(self):
        self.assertTrue(self.chunk2 < self.chunk)
        self.assertFalse(self.chunk2 > self.chunk)
        self.assertTrue(self.chunk2 <= self.chunk)
        self.assertFalse(self.chunk2 >= self.chunk)
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
        self.chunk = chunks.Chunk("test", arg1="v1", arg2="v2")
        self.chunk2 = chunks.Chunk("test", arg1="~!v1")
        self.chunk3 = chunks.Chunk("test", arg1="~!v2")

    def test_chunks(self):
        self.assertFalse(self.chunk2 < self.chunk)
        self.assertFalse(self.chunk2 <= self.chunk)
        self.assertTrue(self.chunk3 < self.chunk)
        self.assertTrue(self.chunk3 <= self.chunk)

class TestChunks3(unittest.TestCase):
    """
    Testing chunks. Testing variables, and the combination of variables, negation and values.
    """

    def setUp(self):
        chunks.chunktype("test", ("arg1", "arg2"))
        self.chunk = chunks.Chunk("test", arg1="v1", arg2="v2")
        self.chunk2 = chunks.Chunk("test", arg1="=x")
        self.chunk3 = chunks.Chunk("test", arg2="=x")
        self.chunk4 = chunks.Chunk("test", arg2="~=x")
        self.chunk5 = chunks.Chunk("test", arg2="~=x~=y")
        self.chunk6 = chunks.Chunk("test", arg2="~=x=y")
        self.chunk7 = chunks.Chunk("test", arg2="=x!v2")
        self.chunk8 = chunks.Chunk("test", arg2="v2")
        self.chunk9 = chunks.Chunk("test", arg2="~=y!v2")
        self.chunk10 = chunks.Chunk("test", arg2="!v2=x")
        self.chunk11 = chunks.Chunk("test", arg2="!v2~=y")
        self.chunk12 = chunks.Chunk("test", arg1="~=x")
        self.chunk13 = chunks.Chunk("test", arg1="~=x!v1")
        self.chunk20 = chunks.Chunk("test", arg1="=one~=two~=three~!v2~!v4", arg2="!v2~=one=two~=five")
        self.chunk21 = chunks.Chunk("test", arg1="=one~=two~=three~!v2~!v4", arg2="!v2=one~=three~=five")
        self.chunk22 = chunks.Chunk("test", arg1="=one~=two~=three~!v2~!v4", arg2="!v2~=one~=two")
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
    Testing chunks. Testing variables, and the combination of variables, negation and values. Using the special chunk _variablesvalues
    """

    def setUp(self):
        chunks.chunktype("test", ("arg1", "arg2"))
        self.chunkvar1 = chunks.Chunk("test", arg1=chunks.Chunk("_variablesvalues", values="v1", variables=None), arg2=chunks.Chunk("_variablesvalues", values="v2"))
        self.chunkvar2 = chunks.Chunk("test", arg1=chunks.Chunk("_variablesvalues", values="v1"), arg2=chunks.Chunk("_variablesvalues", values="v2"))
        self.chunk = chunks.Chunk("test", arg1="v1", arg2="v2")
        self.chunk2 = chunks.Chunk("test", arg1=chunks.Chunk("_variablesvalues", variables="x"))
        self.chunk2e = chunks.Chunk("test", arg1=chunks.Chunk("_variablesvalues", variables=tuple(("x",))))
        self.chunk3 = chunks.Chunk("test", arg2=chunks.Chunk("_variablesvalues", variables="x"))
        self.chunk3e = chunks.Chunk("test", arg2=chunks.Chunk("_variablesvalues", variables=tuple(("x",))))
        self.chunk4 = chunks.Chunk("test", arg2=chunks.Chunk("_variablesvalues", negvariables="x"))
        self.chunk4e = chunks.Chunk("test", arg2=chunks.Chunk("_variablesvalues", negvariables=tuple(("x",))))
        self.chunk5 = chunks.Chunk("test", arg2=chunks.Chunk("_variablesvalues", negvariables=tuple(("x", "y"))))
        self.chunk6 = chunks.Chunk("test", arg2=chunks.Chunk("_variablesvalues", variables="y", negvariables="x"))
        self.chunk6e = chunks.Chunk("test", arg2=chunks.Chunk("_variablesvalues", variables=tuple(("y",)), negvariables=tuple(("x",))))
        self.chunk7 = chunks.Chunk("test", arg2=chunks.Chunk("_variablesvalues", variables="x", values="v2"))
        self.chunk7e = chunks.Chunk("test", arg2=chunks.Chunk("_variablesvalues", variables=tuple(("x",)), values=tuple(("v12",))))
        self.chunk8 = chunks.Chunk("test", arg2=chunks.Chunk("_variablesvalues", values="v2"))
        self.chunk8e = chunks.Chunk("test", arg2=chunks.Chunk("_variablesvalues", values=tuple(("v2",))))
        self.chunk9 = chunks.Chunk("test", arg2=chunks.Chunk("_variablesvalues", values="v2", negvariables="y"))
        self.chunk9e = chunks.Chunk("test", arg2=chunks.Chunk("_variablesvalues", values=tuple(("v2",)), negvariables=tuple(("y",))))
        self.chunk10 = chunks.Chunk("test", arg2=chunks.Chunk("_variablesvalues", values="v2", variables="x"))
        self.chunk10e = chunks.Chunk("test", arg2=chunks.Chunk("_variablesvalues", values=tuple(("v2",)), variables=tuple(("x",))))
        self.chunk12 = chunks.Chunk("test", arg1=chunks.Chunk("_variablesvalues", negvariables="x"))
        self.chunk13 = chunks.Chunk("test", arg1=chunks.Chunk("_variablesvalues", negvariables="x", values="v1"))
        self.chunk13e = chunks.Chunk("test", arg1=chunks.Chunk("_variablesvalues", negvariables=tuple(("x",)), values=tuple(("v1",))))
        self.chunk20 = chunks.Chunk("test", arg1=chunks.Chunk("_variablesvalues", variables="one", negvariables=tuple(("two", "three")), negvalues=tuple(("v2", "v4"))), arg2=chunks.Chunk("_variablesvalues", values="v2", variables="two", negvariables=tuple(("one", "five"))))
        self.chunk21 = chunks.Chunk("test", arg1=chunks.Chunk("_variablesvalues", variables="one", negvariables=tuple(("two", "three")), negvalues=tuple(("v2", "v4"))), arg2=chunks.Chunk("_variablesvalues", values="v2", variables="one", negvariables=tuple(("three", "five"))))
        self.chunk22 = chunks.Chunk("test", arg1=chunks.Chunk("_variablesvalues", variables="one", negvariables=tuple(("two", "three")), negvalues=tuple(("v2", "v4"))), arg2=chunks.Chunk("_variablesvalues", values="v2", negvariables=tuple(("one", "two"))))

        self.chunk.boundvars = {"=x" : "v1", "=y" : "v5"}
        self.chunk2.boundvars = {"=x" : "v1", "=y" : "v5"}
        self.chunk2e.boundvars = {"=x" : "v1", "=y" : "v5"}
        self.chunk3.boundvars = {"=x" : "v1", "=y" : "v5"}
        self.chunk3e.boundvars = {"=x" : "v1", "=y" : "v5"}
        self.chunk4.boundvars = {"=x" : "v1", "=y" : "v5"}
        self.chunk4e.boundvars = {"=x" : "v1", "=y" : "v5"}
        self.chunk5.boundvars = {"=x" : "v1", "=y" : "v5"}
        self.chunk6.boundvars = {"=x" : "v1", "=y" : "v5"}
        self.chunk6e.boundvars = {"=x" : "v1", "=y" : "v5"}
        self.chunk7.boundvars = {"=x" : "v1", "=y" : "v5"}
        self.chunk7e.boundvars = {"=x" : "v1", "=y" : "v5"}
        self.chunk8.boundvars = {"=x" : "v1", "=y" : "v5"}
        self.chunk8e.boundvars = {"=x" : "v1", "=y" : "v5"}
        self.chunk9.boundvars = {"=x" : "v1", "=y" : "v5"}
        self.chunk9e.boundvars = {"=x" : "v1", "=y" : "v5"}
        self.chunk10.boundvars = {"=x" : "v1", "=y" : "v5"}
        self.chunk12.boundvars = {"=x" : "v1", "=y" : "v5"}
        self.chunk13.boundvars = {"=x" : "v1", "=y" : "v5"}
        self.chunk13e.boundvars = {"=x" : "v1", "=y" : "v5"}
        self.chunk20.boundvars = {"~=one" : {"v2", "v3", "v5"}, "=two": "v2", "~=three": {"v1", "v4"}, "=five": "v5"}
        self.chunk21.boundvars = {"~=one" : {"v2", "v3", "v5"}, "=two": "v2", "~=three": {"v1", "v4"}, "=five": "v5"}
        self.chunk22.boundvars = {"~=one" : {"v2", "v3", "v5"}, "=two": "v2", "~=three": {"v1", "v4"}, "=five": "v5"}

    def test_chunks(self):
        self.assertTrue(self.chunkvar1 == self.chunkvar2)
        self.assertTrue(self.chunk2 < self.chunk)
        self.assertTrue(self.chunk2 <= self.chunk)
        self.assertTrue(self.chunk2e < self.chunk)
        self.assertFalse(self.chunk3 < self.chunk)
        self.assertFalse(self.chunk3e < self.chunk)
        self.assertTrue(self.chunk4 < self.chunk)
        self.assertTrue(self.chunk4e < self.chunk)
        self.assertTrue(self.chunk5 < self.chunk)
        self.assertFalse(self.chunk6 < self.chunk)
        self.assertFalse(self.chunk6e < self.chunk)
        self.assertFalse(self.chunk7 < self.chunk)
        self.assertFalse(self.chunk7e < self.chunk)
        self.assertTrue(self.chunk8 < self.chunk)
        self.assertTrue(self.chunk8e < self.chunk)
        self.assertTrue(self.chunk9 < self.chunk)
        self.assertTrue(self.chunk9e < self.chunk)
        self.assertFalse(self.chunk10 < self.chunk)
        self.assertFalse(self.chunk12 < self.chunk)
        self.assertFalse(self.chunk13 < self.chunk)
        self.assertFalse(self.chunk13e < self.chunk)
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
        self.chunk3 = chunks.Chunk("test", arg1=chunks.Chunk("_variablesvalues", values="v1"), arg2=chunks.Chunk("_variablesvalues", values="v2"))
        self.chunk4 = chunks.Chunk("test", arg1="v1", arg2="v2")
        self.chunk5 = chunks.chunkstring("c5", \
                "isa test\
                arg1 None\
                arg2 ~=x\
                arg2  =y")
        self.chunk5a = chunks.chunkstring("c5a",\
                "isa test\
                arg2 ~= x\
                arg2 = y")
        self.chunk6 = chunks.Chunk("test", arg2="~=x=y")
        self.chunk6not = chunks.Chunk("test", arg2="~=x")
        self.chunk6not2 = chunks.Chunk("test", arg2="=y")
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
        chunks.chunktype("countFrom", ("start", "count"))
        self.chunk7 = chunks.chunkstring("c7", \
                "isa countFrom\
                start =x\
                count None")
        self.chunk7super = chunks.chunkstring("c7s", \
                "isa countFrom\
                start 2")
        self.chunk8 = chunks.chunkstring("c7s", \
                "isa countFrom\
                start 2")
        self.chunk9 = chunks.chunkstring("c7s", \
                "isa countFrom\
                start None")
        self.chunk10 = chunks.chunkstring("c10", \
                "isa countOrder\
                first 2")
        self.chunk11 = chunks.chunkstring("c11", \
                "isa countOrder\
                first 2\
                second 4")
        self.chunk12 = chunks.chunkstring("c12", \
                "isa countOrder\
                first 3\
                first =zz")
        self.chunk13 = chunks.chunkstring("c13", \
                "isa countOrder\
                first 3")
        self.chunk14 = chunks.chunkstring("c14", \
                "isa countOrder\
                first None")

        self.chunkc2 = chunks.Chunk("testchunkstring2type1", arg1=self.chunk, newarg=10)
        self.chunkc3 = chunks.Chunk("testchunkstring2type1", newarg="=x", arg1=5)
        self.chunkc5 = chunks.Chunk("testchunkstring2type3", a1="v7", a5=self.chunk4)
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


class TestBuffers(unittest.TestCase):
    """
    Testing goal and dm buffers. Testing creation of buffers, addition to buffers, clearing buffers.
    """

    def setUp(self):
        self.dm = declarative.DecMem({chunks.Chunk("origo", x=1): 0})
        self.b = declarative.DecMemBuffer(self.dm)
        self.g = goals.Goal()
        self.b.add(chunks.Chunk("bufferchunk", y=10))
        self.g.add(chunks.Chunk("goalchunk", z=10))
        self.g2 = goals.Goal(default_harvest=self.dm)
        self.g2.add(chunks.Chunk("finalchunk", x=-5))

    def test_buffers(self):
        self.b.add(chunks.Chunk("newbufferchunk", x=10))
        self.assertEqual(self.dm.keys(), {chunks.Chunk("origo", x=1), chunks.Chunk("bufferchunk", y=10)})
        self.g.add(chunks.Chunk("newgoalchunk", x=20), 0, self.dm)
        self.assertEqual(self.dm.keys(), {chunks.Chunk("origo", x=1), chunks.Chunk("bufferchunk", y=10), chunks.Chunk("goalchunk", z=10)})
        self.g2.add(chunks.Chunk("newfinalchunk", x=30))
        self.assertEqual(self.dm.keys(), {chunks.Chunk("origo", x=1), chunks.Chunk("bufferchunk", y=10), chunks.Chunk("goalchunk", z=10), chunks.Chunk("finalchunk", x=-5)})

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
            if self.sim.current_event.action == "RETRIEVED: countOrder(first=2, second=3)":
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
            if self.sim.current_event.action == "RETRIEVED: countOrder(first=3, second=4)":
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
            if self.sim.current_event.action == "RETRIEVED: countOrder(first=2, second=3)":
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
            if self.sim.current_event.action == "RETRIEVED: countOrder(first=3, second=4)":
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
        self.test.productions(addition.initAddition, addition.terminateAddition, addition.incrementCount, addition.incrementSum)
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
            if self.sim.current_event.action == "RETRIEVED: countOrder(first=5, second=6)":
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
            if self.sim.current_event.action == "RETRIEVED: countOrder(first=0, second=1)":
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
            if self.sim.current_event.action == "RETRIEVED: countOrder(first=6, second=7)":
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
            if self.sim.current_event.action == "RETRIEVED: countOrder(first=1, second=2)":
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
        self.test.productions(m1.start, m1.increment, m1.stop)
        self.sim = self.test.simulation(trace=False)

    def test_procedure(self):
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
        while True:
            self.sim.step()
            if self.sim.current_event:
                break
        while True:
            self.sim.step()
            if self.sim.current_event.action == "CLEARED" and self.sim.current_event.proc == "g":
                break
        self.assertEqual(self.sim.show_time(), 0.15)
        self.assertEqual(self.m2.dm, declarative.DecMem({chunks.Chunk("twoVars", x=10, y=20): {0.0}, chunks.Chunk("reverse", x=10, y=10): {0.15}}))
        while True:
            self.sim.step()
            if self.sim.current_event.action == "CLEARED" and self.sim.current_event.proc == "retrieval":
                break
        self.assertEqual(self.sim.show_time(), 0.2)
        self.assertEqual(self.m2.dm, {chunks.Chunk("twoVars", x=10, y=20): {0.0}, chunks.Chunk("twoVars", x=20, y=10): {0.2}, chunks.Chunk("reverse", x=10, y=10): {0.15}})


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
        self.assertEqual(self.sim._Simulation__pr.dm, {'retrieval': {chunks.Chunk("twoVars", x=10, y=20): {0.0}, chunks.Chunk("twoVars", x=20, y=10): {0.2}, chunks.Chunk("reverse", x=10, y=10): {0.15}}, 'g': {chunks.Chunk("twoVars", x=10, y=20): {0.0}, chunks.Chunk("twoVars", x=20, y=10): {0.2}, chunks.Chunk("reverse", x=10, y=10): {0.15}}})
        self.assertEqual(self.m3.dm, {chunks.Chunk("twoVars", x=10, y=20): {0.0}, chunks.Chunk("twoVars", x=20, y=10): {0.2}, chunks.Chunk("reverse", x=10, y=10): {0.15}})
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
        self.sim = m.m.simulation(trace=False, gui=False, environment_process=environ.environment_process, stimuli=2*text, triggers=4*trigger,times=5, start_time=0)

    def test_procedure(self):
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
        self.assertIn(chunks.Chunk("pair", probe="bank", answer="0"), self.sim._Simulation__pr.dm['retrieval'].keys())
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
            if self.sim.current_event.action == "RETRIEVED: pair(answer=0, probe=bank)":
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
        self.assertSetEqual({cleared_time, keypressing_time}, self.sim._Simulation__pr.dm['retrieval'][chunks.Chunk("pair", probe="bank", answer="0")]) #keypressing_time relevant because at that point retrieval is cleared

class TestSourceActivation(unittest.TestCase):
    """
    Testing source activation.
    """

    def setUp(self):
        self.first = chunks.Chunk("first", x=2, y=5)
        self.second = chunks.Chunk("first", x=2, y=None)
        self.third = chunks.Chunk("first", x=2)
        self.fourth = chunks.Chunk("first", x=chunks.Chunk("tt"))
        self.fifth = chunks.Chunk("first", x=chunks.Chunk("t2", new=10))
        self.sixth = chunks.Chunk("first", x=chunks.Chunk("t2", x=10))
        self.seventh = chunks.Chunk("first", x=chunks.Chunk("tt"), y=chunks.Chunk("abc"))
        self.eighth = chunks.Chunk("first", x=chunks.Chunk("t2", new=10), y=chunks.Chunk("abc"))
        self.nineth = chunks.Chunk("first", x=chunks.Chunk("t2", x=10), y=chunks.Chunk("abc"))
        self.tenth = chunks.Chunk("first", x=chunks.Chunk("t2", x=10), y=chunks.Chunk("abc"), z=chunks.Chunk("d"))
        self.eleventh = chunks.Chunk("nnn", x=chunks.Chunk("t2", x=10), y=chunks.Chunk("abc"), z=chunks.Chunk("d"))

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

class TestSourceActivation2(unittest.TestCase):
    """
    Testing strength association.
    """

    def setUp(self):
        self.dm = declarative.DecMem({chunks.Chunk("one", x=chunks.Chunk("pres", pres="obama")): 0, chunks.Chunk("one", x=chunks.Chunk("pres", pres="bush")): 0, chunks.Chunk("two", y=chunks.Chunk("presidency_years", value=8), z=chunks.Chunk("pres", pres="bush")): 0})
        self.p = chunks.Chunk("pres", pres="obama")
        self.p2 = chunks.Chunk("pres", pres="bush")
        self.ret1 = chunks.Chunk("pres", pres="clinton")
        self.ret2 = chunks.Chunk("pres", pres="bush")
        self.ret3 = chunks.Chunk("pres", pres="obama")

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
        self.ch1 = chunks.Chunk("one", x=chunks.Chunk("pres", pres="obama"))
        self.ch2 = chunks.Chunk("one", x=chunks.Chunk("pres", pres="bush"))
        self.ch3 = chunks.Chunk("two", y=chunks.Chunk("presidency_years", value=8), z=chunks.Chunk("pres", pres="bush"))
        self.dm = declarative.DecMem({self.ch1: 0, self.ch2: 0, self.ch3: 0})
        self.g = goals.Goal()
        self.g.add(chunks.Chunk("finding_pres", person=chunks.Chunk("pres", pres="obama"), years="unknown"))
        self.g2 = goals.Goal()
        self.g2.add(chunks.Chunk("finding_pres", person=chunks.Chunk("pres", pres="bush"), years="unknown"))
        self.g3 = goals.Goal()
        self.g3.add(chunks.Chunk("finding_pres", person=chunks.Chunk("pres", pres="bush"), years=chunks.Chunk("presidency_years", value=8)))
        self.g4 = goals.Goal()
        self.g4.add(chunks.Chunk("finding_pres", person=chunks.Chunk("pres", pres="bush"), years=chunks.Chunk("presidency_years", value=5)))
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
        self.ch4 = chunks.Chunk("three", x=chunks.Chunk("pres", pres="bush"), xx=chunks.Chunk("pres", pres="bush"))
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




if __name__ == '__main__':
    unittest.main()
