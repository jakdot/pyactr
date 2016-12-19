pyactr
------

Python package to create and run ACT-R cognitive models.

The package supports symbolic and subsymbolic processes in ACT-R and it covers all basic cases of ACT-R modeling, including features that are not often implemented outside of the official Lisp ACT-R software.

The package should allow you to run any ACT-R model. If you need an ACT-R feature that's missing in the package, please let me know.

Significant changes might still occur in the near future.

Installing pyactr
-----------------

The best way to install this is to run pip:

pip3 install pyactr

You can also clone this package and in the root folder, run:

python setup.py install

Requirements
------------

Requires Python3 (>=3.3), numpy, simpy and pyparsing.

You might also consider getting tkinter if you want to see visual output on how ACT-R models interact with environment. But this is not necessary to run any models.

Documentation
-------------

Documentation is on https://github.com/jakdot/pyactr. In particular, check:

1. the folder docs for discussion of ACT-R and pyactr. Examples are geared towards (psycho)linguists, but discussion on models should be accessible to anyone.

2. the folder tutorials for many examples of ACT-R models. Most of those models are translated from Lisp ACT-R, so if you are familiar with that it should be easy to understand these.

Modifying pyactr
----------------

To ensure that modifications do not break the current code, run unittests in pyactr/tests/.
