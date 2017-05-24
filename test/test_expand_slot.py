from ssim.ssim import _expand_slot


def test_expand_slot(expanding_slots):

    assert _expand_slot(expanding_slots['slot']) == expanding_slots['flights']
