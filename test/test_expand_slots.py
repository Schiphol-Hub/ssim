from ssim.ssim import expand_slots


def test_expand_slots(expanding_slots):

    assert expand_slots([expanding_slots['slot']]) == expanding_slots['flights']
