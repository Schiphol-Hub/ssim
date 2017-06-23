from ssim.ssim import _parse_slotfile


def test_parsing_regressions(parsing_regressions):

    for slot_data in parsing_regressions:

        slots, header, footer = _parse_slotfile(slot_data['raw_data'])
        slots = list(slots)

        assert slots == slot_data['slots']
