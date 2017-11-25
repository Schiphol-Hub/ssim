from ssim.ssim import _parse_slotfile, _process_dates_sir, _process_dates_sim


def test_process_slots(slotfiles):

    for slot_data in slotfiles:

        slots, header, footer = _parse_slotfile(slot_data['raw_data'], year_prefix='20')

        # slots = [_process_dates_sir(x, slot_data['header']) for x in slots]

        # processed_slots, _ = _process_dates_sir(slots, slot_data['header'])

        # assert _process_dates_sir(slots[0], slot_data['header'])
        # for processed_slot, parsed_slot in zip(slot_data['processed_slots'], processed_slots):
        #     assert processed_slot == parsed_slot

        assert slots == slot_data['slots']
        # for processed_slot, parsed_slot in zip(slot_data['processed_slots'], processed_slots):
        #     assert processed_slot == parsed_slot
