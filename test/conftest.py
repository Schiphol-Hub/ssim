import pytest
import glob
import yaml


@pytest.fixture
def slotfiles():
    slotfiles_files = glob.glob('data/slots_*.yml')

    slotfiles = []
    for slotfile in slotfiles_files:
        with open(slotfile) as f:
            text = yaml.load(f.read())

        slotfiles.append(text)

    return slotfiles
