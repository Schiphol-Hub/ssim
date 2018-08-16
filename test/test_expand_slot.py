from ssim.ssim import _expand


def test_expand_slot(expanding_slots):
    for slot in expanding_slots:
        assert _expand(slot["slot"]) == slot["flights"]
