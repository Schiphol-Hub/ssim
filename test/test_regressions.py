from ssim.ssim import _parse_slotfile


def test_regressions(regressions):

    for slot_data in regressions:

        slots, header, footer = _parse_slotfile(slot_data['raw_data'])
        slots = list(slots)

        assert slots == slot_data['slots']