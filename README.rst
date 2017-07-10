SSIM parser
===========


Introduction
------------
IATA SSIM (Standard Schedules Information Manual) file parser is a tool to read the standard IATA file format.

Alpha warning: please note this software is under active development. See the issue guidelines below if you encounter bugs.

Installation
------------

.. code-block:: bash

    pip install ssim

Usage example
-------------

Using in command line:

.. code-block:: bash

    ssim -i slotfile_example.SCR -o flights.csv

Using with python:

.. code-block:: python

    import ssim

    slots, header, footer = ssim.read('slotfile_example.SCR')
    flights = ssim.expand_slots(slots)

If using pandas then:

.. code-block:: python

    import pandas as pd
    flights_df = pd.DataFrame(flights)


Issue guidelines
----------------

In case you encounter bugs please submit a new `issue`_ on github. Please list the reported error and data used that will help us reconstruct it. This will help us reproduce and resolve the bug.

Contributors
-------

Rok.Mihevc_
Ramon.Van.Schaik
Howard.Riddiough
Kevin.Haagen

License
-------

Uses the `GPLv3`_ license.

.. _GPLv3: https://opensource.org/licenses/GPL-3.0
.. _Rok.Mihevc: https://rok.github.io
.. _issue: https://github.com/Schiphol-Hub/ssim/issues/new
