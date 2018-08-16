# -*- coding: utf-8 -*-
"""
Created on Mon Mar 12 16:09:38 2018

@author: ramon
"""

from ssim.ssim import _explode_aircraft_configuration_string


def test_explode_aircraft_configuration_string(aircraft_configuration_strings):
    for aircraft_configuration_string in aircraft_configuration_strings:
        assert (
            _explode_aircraft_configuration_string(aircraft_configuration_string["string"])
            == aircraft_configuration_string["aircraft_configuration"]
        )
