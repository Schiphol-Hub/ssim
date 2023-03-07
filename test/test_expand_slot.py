from ssim.ssim import _expand, compress_flights, expand_slots


def test_expand_slot(expanding_slots):
    for slot in expanding_slots:
        assert _expand(slot["slot"]) == slot["flights"]


def test_roundtrip_slots(expanding_slots):
    for slot in expanding_slots:
        flights = expand_slots([slot["slot"]])

        assert slot["flights"] == flights
        assert slot["slot"] == compress_flights(flights)[0]
