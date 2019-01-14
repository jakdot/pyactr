pyactr
------

Python package to create and run ACT-R cognitive models.

The package supports symbolic and subsymbolic processes in ACT-R and it covers all basic cases of ACT-R modeling, including features that are not often implemented outside of the official Lisp ACT-R software.

The package should allow you to run any ACT-R model. If you need an ACT-R feature that's missing in the package, please let me know.

Significant changes might still occur in the near future.

Installing pyactr
-----------------

The best way to install pyactr is to run pip:

pip3 install pyactr

You can also clone this package and in the root folder, run:

python setup.py install

Requirements
------------

pyactr requires Python3 (>=3.3), numpy, simpy and pyparsing.

You might also consider getting tkinter if you want to see visual output on how ACT-R models interact with environment. But this is not necessary to run any models.

A note on Python3.3
-------------------

pyactr works with Python3.3 but some packages that it is dependent on dropped support for Python3.3. If you want to use pyactr with Python3.3 you must install numpy version 1.11.3 or lower. simpy is also planning to drop support of Python3.3 in future versions (as of January 2019).

Getting started
---------------

Go to https://github.com/jakdot/pyactr/wiki for a short intro into ACT-R and pyactr.

More documentation
------------------

More documents are on https://github.com/jakdot/pyactr. In particular, check:

1. the folder docs for discussion of ACT-R and pyactr. The book in the folder is currently incomplete, only the first few chapters are available. Examples in the excerpt are geared towards (psycho)linguists.

2. the folder tutorials for many examples of ACT-R models. Most of those models are translated from Lisp ACT-R, so if you are familiar with that it should be easy to understand these.

Modifying pyactr
----------------

To ensure that modifications do not break the current code, run unittests in pyactr/tests/.
