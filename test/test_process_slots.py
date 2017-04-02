from ssim.ssim import _process_slots


def test_process_slots(slotfiles):

    for slot_data in slotfiles:

        processed_slots = _process_slots(slot_data['slots'], slot_data['header'])

        for processed_slot, parsed_slot in zip(slot_data['processed_slots'], processed_slots):
            assert processed_slot == parsed_slot
