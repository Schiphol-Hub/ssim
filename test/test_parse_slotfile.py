from ssim.ssim import _parse_slotfile


def test_parse_slotfile(slotfiles):

    for slot_data in slotfiles:

        slots, header, footer = _parse_slotfile(slot_data['raw_data'])

        assert header == slot_data['header']
        assert footer == slot_data['footer']

        for slot, parsed_slot in zip(slot_data['slots'], slots):
            assert slot == parsed_slot
