pyactr
------

Python package to create and run ACT-R cognitive models.

The package supports symbolic and subsymbolic processes in ACT-R and it covers most basic cases of ACT-R modeling. The only standard piece common in ACT-R modeling that is currently missing is production compilation. Furthermore, vision and motor modules are significantly simplified compared to the implementation of ACT-R in Lisp.

This is an early release of the package. Significant, radical changes might occur in the near future.

Installing pyactr
-----------------

Run python setup.py install (or python setup.py develop). Or put the subfolder pyactr/ in your Python path.

Requirements
------------

Requires Python3 (>=3.3), numpy, simpy and pyparsing.

Documentation
-------------

The folder docs/ discusses inner workings of pyactr, and presents several examples as to how ACT-R cognitive models should be written in pyactr. The folder tutorials/ has tutorial models taken from Lisp ACT-R. The folder examples_environment/ presents a few examples of environments that interact with ACT-R.

Modifying pyactr
----------------

To ensure that modifications do not break the code, run unittests in pyactr/tests/.
