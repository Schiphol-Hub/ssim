import re
from datetime import datetime, timedelta
from dateutil.rrule import rrule, WEEKLY

# For email parsing see: emailregex.com
header_pattern = (
    '^(?P<file_type>SCR|SIR)\s*\n'
    '/{0,1}(?P<email>[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+){0,1}\n{0,1}'
    '(?P<season>\w+)\s*\n'
    '(?P<export_date>\w+)\s*\n'
    '(?P<origin>\w+)\n'
    '(REYT/\n){0,1}'
)
footer_pattern = (
    '(?P<special_information>SI [A-Za-z0-9 ()\.:=]+)\n'
    '(?P<general_information>GI [A-Za-z0-9 ()\.:=]+)\n*$'
)

return_row_pattern = (
    '(?P<action_code>[A-Z])'
    '(?P<arrival_flight_prefix>[A-Z]{2,3})'
    '(?P<arrival_flight_suffix>\d+[A-Z]*)'
    '\s'
    '(?P<departure_flight_prefix>[A-Z]{2,3})'
    '(?P<departure_flight_suffix>\d+[A-Z]*)'
    '\s'
    '(?P<start_date_of_operation>\d{2}[A-Z]{3})'
    '(?P<end_date_of_operation>\d{2}[A-Z]{3})'
    '\s'
    '(?P<days_of_operation>\d{7})'
    '\s'
    '(?P<seat_number>\d{3})'
    '(?P<aircraft_type_3_letter>\w{3})'
    '\s'
    '(?P<origin_of_flight>[A-Z]{3})'
    '(?P<scheduled_time_of_arrival_utc>\d{4})'
    '\s'
    '(?P<scheduled_time_of_departure_utc>\d{4})'
    '(?P<overnight_indicator>[0-6])*'
    '(?P<destination_of_flight>[A-Z]{3})'
    '\s'
    '(?P<arrival_type_of_flight>[A-Z])'
    '(?P<arrival_frequency_rate>\d){0,1}'
    '(?P<departure_type_of_flight>[A-Z])'
    '(?P<departure_frequency_rate>\d){0,1}'
    '\n*'
)

departure_row_pattern = (
    '(?P<action_code>[A-Z])'
    '\s'
    '(?P<departure_flight_prefix>[A-Z]{2,3})'
    '(?P<departure_flight_suffix>\d+[A-Z]*)'
    '\s'
    '(?P<start_date_of_operation>\d{2}[A-Z]{3})'
    '(?P<end_date_of_operation>\d{2}[A-Z]{3})'
    '\s'
    '(?P<days_of_operation>\d{7})'
    '\s'
    '(?P<seat_number>\d{3})'
    '(?P<aircraft_type_3_letter>\w{3})'
    '\s'
    '(?P<scheduled_time_of_departure_utc>\d{4})'
    '(?P<destination_of_flight>[A-Z]{3})'
    '\s'
    '(?P<departure_type_of_flight>[A-Z])'
    '(?P<departure_frequency_rate>\d){0,1}'
    '\n*'
)

arrival_row_pattern = (
    '(?P<action_code>[A-Z])'
    '(?P<arrival_flight_prefix>[A-Z]{2,3})'
    '(?P<arrival_flight_suffix>\d+[A-Z]*)'
    '\s'
    '(?P<start_date_of_operation>\d{2}[A-Z]{3})'
    '(?P<end_date_of_operation>\d{2}[A-Z]{3})'
    '\s'
    '(?P<days_of_operation>\d{7})'
    '\s'
    '(?P<seat_number>\d{3})'
    '(?P<aircraft_type_3_letter>\w{3})'
    '\s'
    '(?P<origin_of_flight>[A-Z]{3})'
    '(?P<scheduled_time_of_arrival_utc>\d{4})'
    '\s'
    '(?P<arrival_type_of_flight>[A-Z])'
    '(?P<arrival_frequency_rate>\d){0,1}'
    '\n*'
)

arrival_row_pattern_nl = (
    '(?P<action_code>[A-Z])'
    '(?P<arrival_flight_prefix>[A-Z]{2,3})'
    '(?P<arrival_flight_suffix>\d+[A-Z]*)'
    '\s'
    '(?P<start_date_of_operation>\d{2}[A-Z]{3})'
    '(?P<end_date_of_operation>\d{2}[A-Z]{3}|)'
    '\s'
    '(?P<days_of_operation>\d{7}|)'
    '\s{0,1}'
    '(?P<seat_number>\d{3})'
    '(?P<aircraft_type_3_letter>\w{3})'
    '\s'
    '(?P<previous_stop_of_flight>[A-Z]{3})'
    '(?P<origin_of_flight>[A-Z]{3})'
    '(?P<scheduled_time_of_arrival_utc>\d{4})'
    '\s'
    '(?P<arrival_type_of_flight>[A-Z])'
    '(?P<arrival_frequency_rate>\d){0,1}'
)

departure_row_pattern_nl = (
    '(?P<action_code>[A-Z])'
    '\s'
    '(?P<departure_flight_prefix>[A-Z]{2,3})'
    '(?P<departure_flight_suffix>\d+[A-Z]*)'
    '\s'
    '(?P<start_date_of_operation>\d{2}[A-Z]{3})'
    '(?P<end_date_of_operation>\d{2}[A-Z]{3}|)'
    '\s'
    '(?P<days_of_operation>\d{7}|)'
    '\s{0,1}'
    '(?P<seat_number>\d{3})'
    '(?P<aircraft_type_3_letter>\w{3})'
    '\s'
    '(?P<scheduled_time_of_departure_utc>\d{4})'
    '(?P<next_stop_of_flight>[A-Z]{3})'
    '(?P<destination_of_flight>[A-Z]{3})'
    '\s'
    '(?P<departure_type_of_flight>[A-Z])'
    '(?P<departure_frequency_rate>\d){0,1}'
)

row_patterns = [re.compile(arrival_row_pattern),
                re.compile(departure_row_pattern),
                re.compile(return_row_pattern),
                re.compile(arrival_row_pattern_nl),
                re.compile(departure_row_pattern_nl)]


def _add_year(dt):
    return datetime(dt.year + 1, dt.month, dt.day)


def _parse_slotfile(text):
    """
    Parses a ssim message and returns it as a dicts.

    Parameters
    ----------.
    text : string

    Returns
    -------
    parsed_rows: list of dicts, describing rows of a slotfile.
    header: dict, describing the header of the slotfile.
    footer: dict, describing the footer of the slotfile.
    """

    header_match = re.search(header_pattern, text)
    footer_match = re.search(footer_pattern, text)

    header = header_match.groupdict()

    try:
        footer = footer_match.groupdict()
    except Exception:
        footer = {}
        pass

    try:
        rows = text[header_match.end():footer_match.start()].splitlines()
    except Exception:
        rows = text[header_match.end():].splitlines()
        pass


    parsed_rows = []

    for row in rows:
        for row_pattern in row_patterns:
            try:
                parsed_rows.append(re.search(row_pattern, row).groupdict())
            except Exception:
                pass

    return parsed_rows, header, footer


def _process_slots(slots, header, year_prefix='20'):
    """
    Processes parsed ssim messages to insert the correct start
    and end dates.

    Parameters
    ----------.
    slots : list of dicts, describing rows of a slotfile.
    header: dict, describing the header of the slotfile.
    year_prefix: string, defining the century of the flight.

    Returns
    -------
    processed_slots: list of dicts, describing exact slots of a slotfile.
    """

    year = year_prefix + header['season'][1:]
    season = header['season'][0]
    processed_slots = []

    for slot in slots:
        if slot['end_date_of_operation'] == '':
            slot['end_date_of_operation'] = slot['start_date_of_operation']

        slot['start_date_of_operation'] = \
            datetime.strptime(slot['start_date_of_operation'] + year, '%d%b%Y')
        slot['end_date_of_operation'] = \
            datetime.strptime(slot['end_date_of_operation'] + year, '%d%b%Y')

        if season == 'W':
            if slot['end_date_of_operation'].month < 6:
                slot['end_date_of_operation'] = _add_year(slot['end_date_of_operation'])

                if slot['start_date_of_operation'].month < 6:
                    slot['start_date_of_operation'] = _add_year(slot['start_date_of_operation'])

        slot['start_date_of_operation'] = slot['start_date_of_operation'].strftime('%Y-%m-%d')
        slot['end_date_of_operation'] = slot['end_date_of_operation'].strftime('%Y-%m-%d')

        processed_slots.append(slot)

    return processed_slots


def _update_dict(d, entry):
    new_d = d.copy()
    new_d.update(entry)
    return new_d


def _expand_slot(slot):
    """
    Expands slot into individual flights.

    Parameters
    ----------.
    slot: dict, description of a slot.

    Returns
    -------
    slot: list of dicts, representing flights described by the slot.
    """

    weekdays = [int(weekday) - 1 for weekday in list(slot['days_of_operation'].replace('0', ''))]
    expanded_slot = []

    # Expand arriving flights
    try:
        arrival_slot = {
            'action_code': slot['action_code'],
            'ad': 'A',
            'prefix': slot['arrival_flight_prefix'],
            'suffix': slot['arrival_flight_suffix'],
            'aircraft_type_3_letter': slot['aircraft_type_3_letter'],
            'type_of_flight': slot['arrival_type_of_flight'],
            'destination': slot['origin_of_flight'],
            'seats': slot['seat_number']

        }
        arrival_start_date = \
            datetime.strptime(slot['start_date_of_operation'] + slot['scheduled_time_of_arrival_utc'], '%Y-%m-%d%H%M')
        arrival_end_date = \
            datetime.strptime(slot['end_date_of_operation'] + slot['scheduled_time_of_arrival_utc'], '%Y-%m-%d%H%M')

        if slot['arrival_frequency_rate']:
            dates = rrule(freq=WEEKLY, interval=int(slot['arrival_frequency_rate']),
                      dtstart=arrival_start_date, until=arrival_end_date, byweekday=weekdays)
        else:
            dates = rrule(freq=WEEKLY, dtstart=arrival_start_date, until=arrival_end_date, byweekday=weekdays)

        arrival_slot['flight_datetime'] = [x.strftime('%Y-%m-%d %H:%M') for x in dates]

        expanded_slot = expanded_slot + [arrival_slot]

    except Exception:
        pass

    # Expand departing flights
    try:
        departure_slot = {
            'action_code': slot['action_code'],
            'ad': 'D',
            'prefix': slot['departure_flight_prefix'],
            'suffix': slot['departure_flight_suffix'],
            'aircraft_type_3_letter': slot['aircraft_type_3_letter'],
            'type_of_flight': slot['departure_type_of_flight'],
            'destination': slot['destination_of_flight'],
            'seats': slot['seat_number']
        }
        if 'overnight_indicator' in slot:
            departure_start_date = \
                datetime.strptime(slot['start_date_of_operation'] + slot['scheduled_time_of_departure_utc'], '%Y-%m-%d%H%M') \
                + timedelta(days=int(slot['overnight_indicator']))
            departure_end_date = \
                datetime.strptime(slot['end_date_of_operation'] + slot['scheduled_time_of_departure_utc'], '%Y-%m-%d%H%M') \
                + timedelta(days=int(slot['overnight_indicator']))
        else:
            departure_start_date = \
                datetime.strptime(slot['start_date_of_operation'] + slot['scheduled_time_of_departure_utc'], '%Y-%m-%d%H%M')
            departure_end_date = \
                datetime.strptime(slot['end_date_of_operation'] + slot['scheduled_time_of_departure_utc'], '%Y-%m-%d%H%M')

        if slot['departure_frequency_rate']:
            dates = rrule(freq=WEEKLY, interval=int(slot['departure_frequency_rate']),
                      dtstart=departure_start_date, until=departure_end_date, byweekday=weekdays)
        else:
            dates = rrule(freq=WEEKLY, dtstart=departure_start_date, until=departure_end_date, byweekday=weekdays)

        departure_slot['flight_datetime'] = [x.strftime('%Y-%m-%d %H:%M') for x in dates]

        expanded_slot = expanded_slot + [departure_slot]

    except Exception:
        pass

    return expanded_slot


def read(slotfile, year_prefix='20'):
    """
    Parses and processes a valid ssim file.

    Parameters
    ----------.
    slotfile : path to a slotfile.
    year_prefix: string, defining the century of the flight.

    Returns
    -------
    slots: list of dicts, describing exact slots of a slotfile.
    header: dict, describing the header of the slotfile.
    footer: dict, describing the footer of the slotfile.
    """

    with open(slotfile) as f:
        text = f.read()

    slots, header, footer = _parse_slotfile(text)
    slots = _process_slots(slots, header, year_prefix)

    return slots, header, footer


def expand_slots(slots):
    """
    Expands a list of slots into flights.
    
    Parameters
    ----------.
    :param slots: list, a list of slot dicts.
    
    Returns
    -------
    :return: flights: list, a list of flight dicts.
    """

    flights = []

    for slot in slots:
        expanded_slot = _expand_slot(slot)
        flights = flights + \
                  [_update_dict(x, {'flight_datetime': f_dt}) for x in expanded_slot for f_dt in x['flight_datetime']]

    return flights
