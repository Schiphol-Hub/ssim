from ssim.ssim import _parse_slotfile


def test_parse_slotfile(slotfiles):

    for slot_data in slotfiles:

        slots, header, footer = _parse_slotfile(slot_data['raw_data'], year_prefix='20')

        assert slots == slot_data['slots']
        assert header == slot_data['header']
        assert footer == slot_data['footer']
