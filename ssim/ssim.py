# TODO: fix bad midnight
# TODO: create AD indicator, multiple flights out of turnaround flights
# TODO: missing SIR records?
# TODO: add logging

import logging
import re
from datetime import datetime
from dateutil.rrule import rrule, WEEKLY
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))
from regexes import regexes

year_adjustment = {
    'S': {'JAN': 1, 'FEB': 1, 'MAR': 0, 'APR': 0, 'MAY': 0, 'JUN': 0,
          'JUL': 0, 'AUG': 0, 'SEP': 0, 'OCT': 0, 'NOV': 0, 'DEC': 0},
    'W': {'JAN': 1, 'FEB': 1, 'MAR': 1, 'APR': 1, 'MAY': 1, 'JUN': 1,
          'JUL': 1, 'AUG': 1, 'SEP': 1, 'OCT': 0, 'NOV': 0, 'DEC': 0}
}


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

    logging.info('Reading and parsing file: %s.' % file)
    with open(file, 'r') as f:
        text = f.read()

    slots = []

    if regexes['sir']['header'].match(text):
        print('sir', file)
        slots = _parse_sir(text)

    elif regexes['sim']['record_1'].match(text):
        print('sim', file)
        slots = _parse_sim(text)

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
    flattened_flights = [item for sublist in flights for item in sublist]

    logging.info('Expanded %i slots into %i flights.' % (len(slots), len(flattened_flights)))
    return flattened_flights
