SSIM parser
===========


Introduction
------------
IATA SSIM (Standard Schedules Information Manual) file parser is a tool to read the standard IATA file format.

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

Contributors
-------

Rok.Mihevc_
Ramon.Van.Schaik
Howard Riddiough
Kevin Haagen

License
-------

Uses the `GPLv3`_ license.

.. _GPLv3: https://opensource.org/licenses/GPL-3.0
.. _Rok.Mihevc: https://rok.github.io
