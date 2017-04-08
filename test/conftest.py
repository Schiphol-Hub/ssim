import pytest
from glob import glob
import yaml


@pytest.fixture
def slotfiles():
    slotfiles_files = glob('test/data/slots_*.yml')

    slotfile_list = []
    for slotfile in slotfiles_files:
        with open(slotfile) as f:
            text = yaml.load(f.read())

        slotfile_list.append(text)

    return slotfile_list


@pytest.fixture
def expanding_slots():
    with open('test/data/expanding_slots.yml') as f:
        slots = yaml.load(f.read())

    return slots
