# TODO: create AD indicator, multiple flights out of turnaround flights, arrival / departure / both to rows transformation
# TODO: port aircraft and seat configuration parsing for sim
# TODO: testing of expanding
# TODO: fix bad midnight
# TODO: read_csv

import logging
import re
from datetime import datetime
from dateutil.rrule import rrule, WEEKLY
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))
from regexes import regexes

logging.basicConfig(format='[%(asctime)s] %(levelname)s: %(message)s', level=logging.DEBUG)

year_adjustment = {
    'S': {'JAN': 1, 'FEB': 1, 'MAR': 0, 'APR': 0, 'MAY': 0, 'JUN': 0,
          'JUL': 0, 'AUG': 0, 'SEP': 0, 'OCT': 0, 'NOV': 0, 'DEC': 0},
    'W': {'JAN': 1, 'FEB': 1, 'MAR': 1, 'APR': 1, 'MAY': 1, 'JUN': 1,
          'JUL': 1, 'AUG': 1, 'SEP': 1, 'OCT': 0, 'NOV': 0, 'DEC': 0}
}


def _flatten(l):
    return [item for sublist in l for item in sublist]


def _merge_two_dicts(x, y):
    z = x.copy()
    z.update(y)
    return z


def _strip_dict_values(d):
    d = d.copy()
    for key, value in d.items():
        d[key] = value.strip()
        if d[key] == '':
            d[key] = None
    return d


def _expand(record, date_format='%d%b%y'):
    """
    Expands records into individual flights.

    Parameters
    ----------.
    record: dict, description of a record.
    date_format: string

    Returns
    -------
    records: list of dicts, representing flights described by the record.
    """

    if 'days_of_operation' in record and record['days_of_operation'] is not None:
        days_of_operation = re.sub('\s|0', '', record['days_of_operation'])
        days_of_operation = [int(weekday) - 1 for weekday in days_of_operation]
    else:
        days_of_operation = range(1, 8)

    if 'frequency_rate' in record and record['frequency_rate'] is not None:
        frequency_rate = record['frequency_rate'].strip()
        if frequency_rate == '':
            frequency_rate = '1'
    else:
        frequency_rate = '1'

    frequency_rate = int(frequency_rate)

    dates = rrule(freq=WEEKLY,
                  interval=frequency_rate,
                  dtstart=datetime.strptime(record['period_of_operation_from'], date_format),
                  until=datetime.strptime(record['period_of_operation_to'], date_format),
                  byweekday=days_of_operation)

    records = [_merge_two_dicts(record, {'date': x.strftime('%Y-%m-%d')}) for x in dates]

    return records


def _parse_sim(text):
    """
    Parses a SIM message and returns it as a list of dicts describing flight leg records.

    Parameters
    ----------.
    :type text: string

    Returns
    -------
    text: list of dicts, describing rows of a slotfile.
    header: dict, describing the header of the slotfile.
    footer: dict, describing the footer of the slotfile.
    """

    # record_1 = regexes['sim']['record_1'].search(text).groupdict()
    # record_2 = regexes['sim']['record_2'].search(text).groupdict()
    record_3 = regexes['sim']['record_3'].finditer(text)
    # record_4 = regexes['sim']['record_4'].finditer(text)
    # record_5 = regexes['sim']['record_5'].search(text).groupdict()

    # time_mode = record_2['time_mode']
    flight_leg_records = list(map(lambda x: x.groupdict(), record_3))
    flight_leg_records = [_strip_dict_values(x) for x in flight_leg_records]
    # segment_data_records = list(map(lambda x: x.groupdict(), record_4))

    return flight_leg_records


def _attach_year_sir(record, year, season,
                     from_key='period_of_operation_from', to_key='period_of_operation_to'):
    """
    This function adds year to dates from SIR message records.
    It also adjusts year - e.g. if the record is dated 2nd February in Winter 17 season the actual date
    is 2018-02-02.

    :param record: dictionary describing a record
    :param year: year of the season the record belongs to
    :param season: season e.g.: Winter or Summer
    :param from_key: dictionary key describing start of operation date
    :param to_key: dictionary key describing end of operation date
    :return: record: record with modified dates
    """

    record = record.copy()

    if record[to_key] is None:
        record[to_key] = record[from_key]

    from_month = record[from_key][2:]
    to_month = record[to_key][2:]
    record[from_key] = record[from_key] + str(year + year_adjustment[season][from_month])
    record[to_key] = record[to_key] + str(year + year_adjustment[season][to_month])

    return record


def _parse_sir(text):
    """
    Parses a SIR message and returns it as a list of dicts describing flight leg records.

    Parameters
    ----------.
    :type text: string

    Returns
    -------
    flight_leg_records: list of dicts describing flight leg records.
    """

    arr = regexes['sir']['arr'].finditer(text)
    dep = regexes['sir']['dep'].finditer(text)
    arrdep = regexes['sir']['arrdep'].finditer(text)

    header = regexes['sir']['header'].search(text).groupdict()
    season = header['season'][0]
    year = int(header['season'][1:])

    flight_leg_records = list(arr) + list(dep) + list(arrdep)
    flight_leg_records = list(map(lambda x: x.groupdict(), flight_leg_records))

    flight_leg_records = [_attach_year_sir(x, year, season) for x in flight_leg_records]

    return flight_leg_records


def _uniformize_sir(slot):
    uniform_slots = []

    if 'arrival_airline_designator' in slot:
        uniform_slots.append({
            'ad': 'A',
            'action_code': slot['action_code'],
            'additional_schedule_information': slot['additional_schedule_information'],
            'aircraft_type': slot['aircraft_type'],
            'airline_designator': slot['arrival_airline_designator'],
            'flight_number': slot['arrival_flight_number'],
            'operational_suffix': slot['arrival_operational_suffix'],
            'service_type': slot['arrival_service_type'],
            'days_of_operation': slot['days_of_operation'],
            'frequency_rate': slot['frequency_rate'],
            'number_of_seats': slot['number_of_seats'],
            'second_station': slot['origin_station'],
            'period_of_operation_from': slot['period_of_operation_from'],
            'period_of_operation_to': slot['period_of_operation_to'],
            'station': slot['previous_station'],
            'raw': slot['raw'],
            'scheduled_time': slot['scheduled_time_of_arrival']})

    if 'departure_airline_designator' in slot:
        uniform_slots.append({
            'ad': 'D',
            'action_code': slot['action_code'],
            'additional_schedule_information': slot['additional_schedule_information'],
            'aircraft_type': slot['aircraft_type'],
            'days_of_operation': slot['days_of_operation'],
            'airline_designator': slot['departure_airline_designator'],
            'flight_number': slot['departure_flight_number'],
            'operational_suffix': slot['departure_operational_suffix'],
            'service_type': slot['departure_service_type'],
            'second_station': slot['destination_station'],
            'frequency_rate': slot['frequency_rate'],
            'station': slot['next_station'],
            'number_of_seats': slot['number_of_seats'],
            'period_of_operation_from': slot['period_of_operation_from'],
            'period_of_operation_to': slot['period_of_operation_to'],
            'raw': slot['raw'],
            'scheduled_time': slot['scheduled_time_of_departure']})

    return uniform_slots


def _uniformize_sim(s):
    uniform_slots = []

    if s['scheduled_time_of_aircraft_departure']:
        uniform_slots.append({
            'ad': 'D',
            'raw': s['raw'],
            'record_type': s['record_type'],
            'operational_suffix': s['operational_suffix'],
            'airline_designator': s['airline_designator'],
            'flight_number': s['flight_number'],
            'itinerary_variation_identifier': s['itinerary_variation_identifier'],
            'leg_sequence_number': s['leg_sequence_number'],
            'service_type': s['service_type'],
            'period_of_operation_from': s['period_of_operation_from'],
            'period_of_operation_to': s['period_of_operation_to'],
            'days_of_operation': s['days_of_operation'],
            'frequency_rate': s['frequency_rate'],
            'departure_station': s['departure_station'],
            'scheduled_time_of_passenger_departure': s['scheduled_time_of_passenger_departure'],
            'scheduled_time_of_aircraft_departure': s['scheduled_time_of_aircraft_departure'],
            'utc_local_time_variation_departure': s['utc_local_time_variation_departure'],
            'passenger_terminal_departure': s['passenger_terminal_departure'],
            'arrival_station': s['arrival_station'],
            'scheduled_time_of_aircraft_arrival': s['scheduled_time_of_aircraft_arrival'],
            'scheduled_time_of_passenger_arrival': s['scheduled_time_of_passenger_arrival'],
            'utc_local_time_variation_arrival': s['utc_local_time_variation_arrival'],
            'passenger_terminal_arrival': s['passenger_terminal_arrival'],
            'aircraft_type': s['aircraft_type'],
            'passenger_reservations_booking_designator': s['passenger_reservations_booking_designator'],
            'passenger_reservations_booking_modifier': s['passenger_reservations_booking_modifier'],
            'meal_service_note': s['meal_service_note'],
            'joint_operation_airline_designators': s['joint_operation_airline_designators'],
            'minimum_connecting_time_international_domestic_status': s[
                'minimum_connecting_time_international_domestic_status'],
            'secure_flight_indicator': s['secure_flight_indicator'],
            'spare_0': s['spare_0'],
            'itinerary_variation_identifier_overflow': s['itinerary_variation_identifier_overflow'],
            'aircraft_owner': s['aircraft_owner'],
            'cockpit_crew_employer': s['cockpit_crew_employer'],
            'cabin_crew_employer': s['cabin_crew_employer'],
            'airline_designator_': s['airline_designator_'],
            'flight_number_': s['flight_number_'],
            'aircraft_rotation_layover': s['aircraft_rotation_layover'],
            'operational_suffix_': s['operational_suffix_'],
            'spare_1': s['spare_1'],
            'flight_transit_layover': s['flight_transit_layover'],
            'operating_airline_disclosure': s['operating_airline_disclosure'],
            'traffic_restriction_code': s['traffic_restriction_code'],
            'traffic_restriction_code_leg_overflow_indicator': s['traffic_restriction_code_leg_overflow_indicator'],
            'spare_2': s['spare_2'],
            'aircraft_configuration_version': s['aircraft_configuration_version'],
            'date_variation': s['date_variation'],
            'record_serial_number': s['record_serial_number']})

    if s['scheduled_time_of_aircraft_arrival']:
        uniform_slots.append({
            'ad': 'A',
            'raw': s['raw'],
            'record_type': s['record_type'],
            'operational_suffix': s['operational_suffix'],
            'airline_designator': s['airline_designator'],
            'flight_number': s['flight_number'],
            'itinerary_variation_identifier': s['itinerary_variation_identifier'],
            'leg_sequence_number': s['leg_sequence_number'],
            'service_type': s['service_type'],
            'period_of_operation_from': s['period_of_operation_from'],
            'period_of_operation_to': s['period_of_operation_to'],
            'days_of_operation': s['days_of_operation'],
            'frequency_rate': s['frequency_rate'],
            'departure_station': s['departure_station'],
            'scheduled_time_of_passenger_departure': s['scheduled_time_of_passenger_departure'],
            'scheduled_time_of_aircraft_departure': s['scheduled_time_of_aircraft_departure'],
            'utc_local_time_variation_departure': s['utc_local_time_variation_departure'],
            'passenger_terminal_departure': s['passenger_terminal_departure'],
            'arrival_station': s['arrival_station'],
            'scheduled_time_of_aircraft_arrival': s['scheduled_time_of_aircraft_arrival'],
            'scheduled_time_of_passenger_arrival': s['scheduled_time_of_passenger_arrival'],
            'utc_local_time_variation_arrival': s['utc_local_time_variation_arrival'],
            'passenger_terminal_arrival': s['passenger_terminal_arrival'],
            'aircraft_type': s['aircraft_type'],
            'passenger_reservations_booking_designator': s['passenger_reservations_booking_designator'],
            'passenger_reservations_booking_modifier': s['passenger_reservations_booking_modifier'],
            'meal_service_note': s['meal_service_note'],
            'joint_operation_airline_designators': s['joint_operation_airline_designators'],
            'minimum_connecting_time_international_domestic_status': s[
                'minimum_connecting_time_international_domestic_status'],
            'secure_flight_indicator': s['secure_flight_indicator'],
            'spare_0': s['spare_0'],
            'itinerary_variation_identifier_overflow': s['itinerary_variation_identifier_overflow'],
            'aircraft_owner': s['aircraft_owner'],
            'cockpit_crew_employer': s['cockpit_crew_employer'],
            'cabin_crew_employer': s['cabin_crew_employer'],
            'airline_designator_': s['airline_designator_'],
            'flight_number_': s['flight_number_'],
            'aircraft_rotation_layover': s['aircraft_rotation_layover'],
            'operational_suffix_': s['operational_suffix_'],
            'spare_1': s['spare_1'],
            'flight_transit_layover': s['flight_transit_layover'],
            'operating_airline_disclosure': s['operating_airline_disclosure'],
            'traffic_restriction_code': s['traffic_restriction_code'],
            'traffic_restriction_code_leg_overflow_indicator': s['traffic_restriction_code_leg_overflow_indicator'],
            'spare_2': s['spare_2'],
            'aircraft_configuration_version': s['aircraft_configuration_version'],
            'date_variation': s['date_variation'],
            'record_serial_number': s['record_serial_number']})

    return uniform_slots


def read(file):
    """
    Reads, detects filetype, parses and processes a valid flight records file.

    Parameters
    ----------.
    file : path to a slotfile.

    Returns
    -------
    slots: list of dicts, describing exact slots of a slotfile.
    header: dict, describing the header of the slotfile.
    footer: dict, describing the footer of the slotfile.
    """

    with open(file, 'r') as f:
        text = f.read()

    slots = []

    if regexes['sir']['header'].match(text):
        logging.info('Reading and parsing SIR file: %s.' % file)
        slots = _parse_sir(text)
        slots = _flatten([_uniformize_sir(x) for x in slots])

    elif regexes['sim']['record_1'].match(text):
        logging.info('Reading and parsing SIM file: %s.' % file)
        slots = _parse_sim(text)
        slots = _flatten([_uniformize_sim(x) for x in slots])

    return slots


def expand_slots(slots):
    """
    Expands a list of slots into flights.

    Parameters
    ----------.
    :param slots: list, a list of slot dicts.

    Returns
    -------
    :return: flattened_flights: list, a list of flight dicts.
    """

    flights = map(_expand, slots)
    flattened_flights = _flatten(flights)

    logging.info('Expanded %i slots into %i flights.' % (len(slots), len(flattened_flights)))
    return flattened_flights
