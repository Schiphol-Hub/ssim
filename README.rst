SSIM parser
===========


Introduction
------------
IATA SSIM (Standard Schedules Information Manual) file parser is a tool to read the standard IATA file format.


Usage example
-------------

.. code-block:: python

    import ssim

    slots, header, footer = ssim.read('slotfile_example.SCR')
    flights = ssim.expand_slots(slots)


Authors
-------

Rok.Mihevc_

License
-------

Uses the `GPLv3`_ license.

.. _GPLv3: https://opensource.org/licenses/GPL-3.0
.. _Rok.Mihevc: https://rok.github.io
