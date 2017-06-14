import pytest
from glob import glob
import yaml
path_to_data = 'data/'

@pytest.fixture
def slotfiles():
    # slotfiles_files = glob(path_to_data + 'slots_*.yml')
    slotfiles_files = [
        'slots_austria.yml',
        'slots_belgium.yml',
        'slots_netherlands.yml'
    ]
    slotfile_list = []
    for slotfile in slotfiles_files:
        with open(path_to_data + slotfile) as f:
            text = yaml.load(f.read())

        slotfile_list.append(text)

    return slotfile_list


@pytest.fixture
def expanding_slots():
    with open(path_to_data + 'expanding_slots.yml') as f:
        slots = yaml.load(f.read())

    return slots


@pytest.fixture
def regressions():
    with open(path_to_data + 'regressions.yml') as f:
        slots = yaml.load(f.read())

    return slots
