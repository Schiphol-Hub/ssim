# TODO: create AD indicator, multiple flights out of turnaround flights, arrival / departure / both to rows transformation
# TODO: port aircraft and seat configuration parsing for sim
# TODO: testing of expanding
# TODO: fix bad midnight
# TODO: read_csv

import logging
import re
from datetime import datetime, timedelta, date
from dateutil.rrule import rrule, WEEKLY
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))
from regexes import regexes

logging.basicConfig(format="[%(asctime)s] %(levelname)s: %(message)s", level=logging.DEBUG)

year_adjustment = {
    "S": {
        "JAN": 1,
        "FEB": 1,
        "MAR": 0,
        "APR": 0,
        "MAY": 0,
        "JUN": 0,
        "JUL": 0,
        "AUG": 0,
        "SEP": 0,
        "OCT": 0,
        "NOV": 0,
        "DEC": 0,
    },
    "W": {
        "JAN": 1,
        "FEB": 1,
        "MAR": 1,
        "APR": 1,
        "MAY": 1,
        "JUN": 1,
        "JUL": 1,
        "AUG": 1,
        "SEP": 1,
        "OCT": 0,
        "NOV": 0,
        "DEC": 0,
    },
}

infinity_indicators = ["00XXX00"]  # indicates that something should run until start/end of season


def find_season_dates(season):
    # type: (str) -> (str, str)
    """
    Get first and last dat eof Iata Season

    Parameters
    ----------.
    season: string, indicating IATA season  (W17, S23). Note that W17 starts 
    in October 2016

    Returns
    -------
    tuple of dates, indicating first and last day of season
    """

    if season[0] == "W":
        march_year = 2000 + int(season[1:3]) + 1
        march_extra_day = 0
        october_extra_day = 1
    elif season[0] == "S":
        march_year = 2000 + int(season[1:3])
        march_extra_day = 1
        october_extra_day = 0
    else:
        raise ValueError('Season should be like "S17" or "W12" rather than ' + season)
    october_year = 2000 + int(season[1:3])

    october_day = date(october_year, 10, 29)
    while october_day.isoweekday() != (6 + october_extra_day):
        october_day -= timedelta(days=1)

    march_day = date(march_year, 3, 30)
    while march_day.isoweekday() != (6 + march_extra_day):
        march_day -= timedelta(days=1)

    if season[0] == "W":
        first_day = october_day
        last_day = march_day
    else:
        first_day = march_day
        last_day = october_day

    season_dates = []
    while first_day <= last_day:
        season_dates.append(first_day)
        first_day += timedelta(days=1)

    return season_dates[0], season_dates[-1]


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
        if d[key] == "":
            d[key] = None
    return d


def _expand(record, date_format="%d%b%y", season=None):
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

    if "days_of_operation" in record and record["days_of_operation"] is not None:
        days_of_operation = re.sub("\s|0", "", record["days_of_operation"])
        days_of_operation = [int(weekday) - 1 for weekday in days_of_operation]
    else:
        days_of_operation = range(0, 7)

    if "frequency_rate" in record and record["frequency_rate"] is not None:
        frequency_rate = record["frequency_rate"].strip()
        if frequency_rate == "":
            frequency_rate = "1"
    else:
        frequency_rate = "1"

    frequency_rate = int(frequency_rate)

    # if 00XXX00, use start/end of season instead
    period_of_operation_from = record["period_of_operation_from"]
    if period_of_operation_from in infinity_indicators:
        if season:
            period_of_operation_from = find_season_dates(season)[0]
        else:
            raise ValueError(
                "Found infinity indicator "
                + period_of_operation_from
                + " in file, but no season specified. Pleas sepcify season. \n"
                + record["raw"]
            )
    else:
        period_of_operation_from = datetime.strptime(period_of_operation_from, date_format)

    period_of_operation_to = record["period_of_operation_to"]
    if period_of_operation_to in infinity_indicators:
        if season:
            period_of_operation_to = find_season_dates(season)[-1]
        else:
            raise ValueError(
                "Found infinity indicator "
                + period_of_operation_to
                + " in file, but no season specified. Pleas sepcify season. \n"
                + record["raw"]
            )
    else:
        period_of_operation_to = datetime.strptime(period_of_operation_to, date_format)

    dates = rrule(
        freq=WEEKLY,
        interval=frequency_rate,
        dtstart=period_of_operation_from,
        until=period_of_operation_to,
        byweekday=days_of_operation,
    )

    # if flight is overnight, add one day
    if "overnight_indicator" in record.keys() and record["overnight_indicator"]:
        td = timedelta(days=1)
    else:
        td = timedelta(days=0)

    records = [_merge_two_dicts(record, {"date": (x + td).strftime("%Y-%m-%d")}) for x in dates]

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
    record_2 = regexes["sim"]["record_2"].search(text).groupdict()
    record_3 = regexes["sim"]["record_3"].finditer(text)
    # record_4 = regexes['sim']['record_4'].finditer(text)
    # record_5 = regexes['sim']['record_5'].search(text).groupdict()

    flight_leg_records = list(map(lambda x: x.groupdict(), record_3))
    flight_leg_records = [_strip_dict_values(x) for x in flight_leg_records]

    if record_2["time_mode"] == "U":
        [
            x.update({"scheduled_time_of_aircraft_arrival": x["scheduled_time_of_aircraft_arrival"] + "+0000"})
            for x in flight_leg_records
        ]
        [
            x.update({"scheduled_time_of_passenger_arrival": x["scheduled_time_of_passenger_arrival"] + "+0000"})
            for x in flight_leg_records
        ]
        [
            x.update({"scheduled_time_of_aircraft_departure": x["scheduled_time_of_aircraft_departure"] + "+0000"})
            for x in flight_leg_records
        ]
        [
            x.update({"scheduled_time_of_passenger_departure": x["scheduled_time_of_passenger_departure"] + "+0000"})
            for x in flight_leg_records
        ]

    elif record_2["time_mode"] == "L":
        [
            x.update(
                {
                    "scheduled_time_of_aircraft_arrival": x["scheduled_time_of_aircraft_arrival"]
                    + x["utc_local_time_variation_arrival"]
                }
            )
            for x in flight_leg_records
        ]
        [
            x.update(
                {
                    "scheduled_time_of_passenger_arrival": x["scheduled_time_of_passenger_arrival"]
                    + x["utc_local_time_variation_arrival"]
                }
            )
            for x in flight_leg_records
        ]
        [
            x.update(
                {
                    "scheduled_time_of_aircraft_departure": x["scheduled_time_of_aircraft_departure"]
                    + x["utc_local_time_variation_departure"]
                }
            )
            for x in flight_leg_records
        ]
        [
            x.update(
                {
                    "scheduled_time_of_passenger_departure": x["scheduled_time_of_passenger_departure"]
                    + x["utc_local_time_variation_departure"]
                }
            )
            for x in flight_leg_records
        ]

    # segment_data_records = list(map(lambda x: x.groupdict(), record_4))

    return flight_leg_records


def _attach_year_sir(record, year, season, from_key="period_of_operation_from", to_key="period_of_operation_to"):
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

    arr = regexes["sir"]["arr"].finditer(text)
    dep = regexes["sir"]["dep"].finditer(text)
    arrdep = regexes["sir"]["arrdep"].finditer(text)

    header = regexes["sir"]["header"].search(text).groupdict()
    season = header["season"][0]
    year = int(header["season"][1:])

    flight_leg_records = list(arr) + list(dep) + list(arrdep)
    flight_leg_records = list(map(lambda x: x.groupdict(), flight_leg_records))

    flight_leg_records = [_attach_year_sir(x, year, season) for x in flight_leg_records]

    return flight_leg_records


def _uniformize_sim_as_sir(slot, iata_airport):
    # type: (dict, str) -> list
    """
    Processes a SIM from the perspective of an airport.

    Parameters
    ----------.
    :param iata_airport: str, three letters, indicating name of airport.
    :return row: dict, describing aircraft configuration.
    """
    assert type(iata_airport) is str, "iata_airport is not an integer: %r" % iata_airport
    assert len(iata_airport) == 3, "iata_airport is not exactly three characters: %r" % iata_airport
    assert iata_airport.upper() == iata_airport, "iata_airport is all capital letters: %r" % iata_airport
    uniform_slots = []

    # it's very hard to see if a flight is overnight. In case time of dep is
    # higher than time of arr, it is likely to arrive overnight
    overnight_indicator_arrival = False
    if slot["arrival_station"] and slot["departure_station"]:
        if slot["scheduled_time_of_aircraft_arrival"] < slot["scheduled_time_of_aircraft_departure"]:
            overnight_indicator_arrival = True

    seats = _explode_aircraft_configuration_string(slot["aircraft_configuration_version"], slot["raw"])
    if slot["arrival_station"] == iata_airport:
        uniform_slots.append(
            {
                "ad": "A",
                "action_code": "H",
                "additional_schedule_information": None,
                "aircraft_type": slot["aircraft_type"],
                "airline_designator": slot["airline_designator"],
                "flight_number": slot["flight_number"],
                "operational_suffix": slot["operational_suffix"],
                "service_type": slot["service_type"],
                "days_of_operation": slot["days_of_operation"],
                "frequency_rate": slot["frequency_rate"],
                "seats": seats["seats"] if "seats" in seats.keys() else None,
                "second_station": slot["departure_station"],
                "period_of_operation_from": slot["period_of_operation_from"],
                "period_of_operation_to": slot["period_of_operation_to"],
                "station": slot["departure_station"],
                "raw": slot["raw"],
                "scheduled_time": slot["scheduled_time_of_aircraft_arrival"],
                "overnight_indicator": overnight_indicator_arrival,
            }
        )

    if slot["departure_station"] == iata_airport:
        uniform_slots.append(
            {
                "ad": "D",
                "action_code": "H",
                "additional_schedule_information": None,
                "aircraft_type": slot["aircraft_type"],
                "days_of_operation": slot["days_of_operation"],
                "airline_designator": slot["airline_designator"],
                "flight_number": slot["flight_number"],
                "operational_suffix": slot["operational_suffix"],
                "service_type": slot["service_type"],
                "second_station": slot["arrival_station"],
                "frequency_rate": slot["frequency_rate"],
                "station": slot["arrival_station"],
                "seats": seats["seats"] if "seats" in seats.keys() else None,
                "period_of_operation_from": slot["period_of_operation_from"],
                "period_of_operation_to": slot["period_of_operation_to"],
                "raw": slot["raw"],
                "scheduled_time": slot["scheduled_time_of_aircraft_departure"],
                "overnight_indicator": False,
            }
        )

    return uniform_slots


def _uniformize_sir(slot):
    uniform_slots = []

    if "arrival_airline_designator" in slot:
        uniform_slots.append(
            {
                "ad": "A",
                "action_code": slot["action_code"],
                "additional_schedule_information": slot["additional_schedule_information"],
                "aircraft_type": slot["aircraft_type"],
                "airline_designator": slot["arrival_airline_designator"],
                "flight_number": slot["arrival_flight_number"],
                "operational_suffix": slot["arrival_operational_suffix"],
                "service_type": slot["arrival_service_type"],
                "days_of_operation": slot["days_of_operation"],
                "frequency_rate": slot["frequency_rate"],
                "seats": int(slot["seats"]) if slot["seats"].isdigit() else slot["seats"],
                "second_station": slot["origin_station"],
                "period_of_operation_from": slot["period_of_operation_from"],
                "period_of_operation_to": slot["period_of_operation_to"],
                "station": slot["previous_station"],
                "raw": slot["raw"],
                "scheduled_time": slot["scheduled_time_of_arrival_utc"],
            }
        )

    if "departure_airline_designator" in slot:
        uniform_slots.append(
            {
                "ad": "D",
                "action_code": slot["action_code"],
                "additional_schedule_information": slot["additional_schedule_information"],
                "aircraft_type": slot["aircraft_type"],
                "days_of_operation": slot["days_of_operation"],
                "airline_designator": slot["departure_airline_designator"],
                "flight_number": slot["departure_flight_number"],
                "operational_suffix": slot["departure_operational_suffix"],
                "service_type": slot["departure_service_type"],
                "second_station": slot["destination_station"],
                "frequency_rate": slot["frequency_rate"],
                "station": slot["next_station"],
                "seats": int(slot["seats"]) if slot["seats"].isdigit() else slot["seats"],
                "period_of_operation_from": slot["period_of_operation_from"],
                "period_of_operation_to": slot["period_of_operation_to"],
                "raw": slot["raw"],
                "scheduled_time": slot["scheduled_time_of_departure_utc"],
            }
        )

    return uniform_slots


def _uniformize_sim(s):
    uniform_slots = []

    if s["scheduled_time_of_aircraft_departure"]:
        uniform_slots.append(
            {
                "ad": "D",
                "raw": s["raw"],
                "record_type": s["record_type"],
                "operational_suffix": s["operational_suffix"],
                "airline_designator": s["airline_designator"],
                "flight_number": s["flight_number"],
                "itinerary_variation_identifier": s["itinerary_variation_identifier"],
                "leg_sequence_number": s["leg_sequence_number"],
                "service_type": s["service_type"],
                "period_of_operation_from": s["period_of_operation_from"],
                "period_of_operation_to": s["period_of_operation_to"],
                "days_of_operation": s["days_of_operation"],
                "frequency_rate": s["frequency_rate"],
                "departure_station": s["departure_station"],
                "scheduled_time_of_passenger_departure": s["scheduled_time_of_passenger_departure"],
                "scheduled_time_of_aircraft_departure": s["scheduled_time_of_aircraft_departure"],
                "utc_local_time_variation_departure": s["utc_local_time_variation_departure"],
                "passenger_terminal_departure": s["passenger_terminal_departure"],
                "arrival_station": s["arrival_station"],
                "scheduled_time_of_aircraft_arrival": s["scheduled_time_of_aircraft_arrival"],
                "scheduled_time_of_passenger_arrival": s["scheduled_time_of_passenger_arrival"],
                "utc_local_time_variation_arrival": s["utc_local_time_variation_arrival"],
                "passenger_terminal_arrival": s["passenger_terminal_arrival"],
                "aircraft_type": s["aircraft_type"],
                "passenger_reservations_booking_designator": s["passenger_reservations_booking_designator"],
                "passenger_reservations_booking_modifier": s["passenger_reservations_booking_modifier"],
                "meal_service_note": s["meal_service_note"],
                "joint_operation_airline_designators": s["joint_operation_airline_designators"],
                "minimum_connecting_time_international_domestic_status": s[
                    "minimum_connecting_time_international_domestic_status"
                ],
                "secure_flight_indicator": s["secure_flight_indicator"],
                "spare_0": s["spare_0"],
                "itinerary_variation_identifier_overflow": s["itinerary_variation_identifier_overflow"],
                "aircraft_owner": s["aircraft_owner"],
                "cockpit_crew_employer": s["cockpit_crew_employer"],
                "cabin_crew_employer": s["cabin_crew_employer"],
                "airline_designator_": s["airline_designator_"],
                "flight_number_": s["flight_number_"],
                "aircraft_rotation_layover": s["aircraft_rotation_layover"],
                "operational_suffix_": s["operational_suffix_"],
                "spare_1": s["spare_1"],
                "flight_transit_layover": s["flight_transit_layover"],
                "operating_airline_disclosure": s["operating_airline_disclosure"],
                "traffic_restriction_code": s["traffic_restriction_code"],
                "traffic_restriction_code_leg_overflow_indicator": s["traffic_restriction_code_leg_overflow_indicator"],
                "spare_2": s["spare_2"],
                "aircraft_configuration_version": s["aircraft_configuration_version"],
                "date_variation": s["date_variation"],
                "record_serial_number": s["record_serial_number"],
            }
        )

    if s["scheduled_time_of_aircraft_arrival"]:
        uniform_slots.append(
            {
                "ad": "A",
                "raw": s["raw"],
                "record_type": s["record_type"],
                "operational_suffix": s["operational_suffix"],
                "airline_designator": s["airline_designator"],
                "flight_number": s["flight_number"],
                "itinerary_variation_identifier": s["itinerary_variation_identifier"],
                "leg_sequence_number": s["leg_sequence_number"],
                "service_type": s["service_type"],
                "period_of_operation_from": s["period_of_operation_from"],
                "period_of_operation_to": s["period_of_operation_to"],
                "days_of_operation": s["days_of_operation"],
                "frequency_rate": s["frequency_rate"],
                "departure_station": s["departure_station"],
                "scheduled_time_of_passenger_departure": s["scheduled_time_of_passenger_departure"],
                "scheduled_time_of_aircraft_departure": s["scheduled_time_of_aircraft_departure"],
                "utc_local_time_variation_departure": s["utc_local_time_variation_departure"],
                "passenger_terminal_departure": s["passenger_terminal_departure"],
                "arrival_station": s["arrival_station"],
                "scheduled_time_of_aircraft_arrival": s["scheduled_time_of_aircraft_arrival"],
                "scheduled_time_of_passenger_arrival": s["scheduled_time_of_passenger_arrival"],
                "utc_local_time_variation_arrival": s["utc_local_time_variation_arrival"],
                "passenger_terminal_arrival": s["passenger_terminal_arrival"],
                "aircraft_type": s["aircraft_type"],
                "passenger_reservations_booking_designator": s["passenger_reservations_booking_designator"],
                "passenger_reservations_booking_modifier": s["passenger_reservations_booking_modifier"],
                "meal_service_note": s["meal_service_note"],
                "joint_operation_airline_designators": s["joint_operation_airline_designators"],
                "minimum_connecting_time_international_domestic_status": s[
                    "minimum_connecting_time_international_domestic_status"
                ],
                "secure_flight_indicator": s["secure_flight_indicator"],
                "spare_0": s["spare_0"],
                "itinerary_variation_identifier_overflow": s["itinerary_variation_identifier_overflow"],
                "aircraft_owner": s["aircraft_owner"],
                "cockpit_crew_employer": s["cockpit_crew_employer"],
                "cabin_crew_employer": s["cabin_crew_employer"],
                "airline_designator_": s["airline_designator_"],
                "flight_number_": s["flight_number_"],
                "aircraft_rotation_layover": s["aircraft_rotation_layover"],
                "operational_suffix_": s["operational_suffix_"],
                "spare_1": s["spare_1"],
                "flight_transit_layover": s["flight_transit_layover"],
                "operating_airline_disclosure": s["operating_airline_disclosure"],
                "traffic_restriction_code": s["traffic_restriction_code"],
                "traffic_restriction_code_leg_overflow_indicator": s["traffic_restriction_code_leg_overflow_indicator"],
                "spare_2": s["spare_2"],
                "aircraft_configuration_version": s["aircraft_configuration_version"],
                "date_variation": s["date_variation"],
                "record_serial_number": s["record_serial_number"],
            }
        )

    for i in range(0, len(uniform_slots)):
        seats = _explode_aircraft_configuration_string(uniform_slots[i]["aircraft_configuration_version"], s["raw"])
        # uniform_slots[i] = {**seats,**uniform_slots[i]}
        uniform_slots[i] = _merge_two_dicts(seats, uniform_slots[i])

    return uniform_slots


def read(file, iata_airport=None):
    """
    Reads, detects filetype, parses and processes a valid flight records file.

    Parameters
    ----------.
    file : path to a slotfile.
    airport_iata: 3 letter capital string indicating iata airport. If passed
    along with SIM file, it will return data from perspective of airport (as 
    SIR)

    Returns
    -------
    slots: list of dicts, describing exact slots of a slotfile.
    header: dict, describing the header of the slotfile.
    footer: dict, describing the footer of the slotfile.
    """

    with open(file, "r") as f:
        text = f.read()

    slots = []

    if regexes["sir"]["header"].match(text):
        logging.info("Reading and parsing SIR file: %s." % file)
        slots = _parse_sir(text)
        slots = _flatten([_uniformize_sir(x) for x in slots])

    elif regexes["sim"]["record_1"].match(text):
        if iata_airport:
            logging.info("Reading and parsing SIM file: %s." % file)
            slots = _parse_sim(text)
            slots = _flatten([_uniformize_sim_as_sir(x, iata_airport) for x in slots])

        else:
            logging.info("Reading and parsing SIM file: %s." % file)
            slots = _parse_sim(text)
            slots = _flatten([_uniformize_sim(x) for x in slots])

    return slots


def expand_slots(slots, season=None):
    """
    Expands a list of slots into flights.

    Parameters
    ----------.
    :param slots: list, a list of slot dicts.
    :param season: indication of season to import. SSIM files can contain 
    00XXX00 as date indicators, which means from beginning/until end of season.
    Argument is required and only used when file contains 00XXX00.

    Returns
    -------
    :return: flattened_flights: list, a list of flight dicts.
    """

    flights = [_expand(slot, season=season) for slot in slots]
    flattened_flights = _flatten(flights)

    logging.info("Expanded %i slots into %i flights." % (len(slots), len(flattened_flights)))
    return flattened_flights


def _explode_aircraft_configuration_string(aircraft_configuration_string, raw_line=""):
    # type: (str, str) -> dict
    """
    Explodes a string containing aircraft information to.

    Parameters
    ----------.
    :param aircraft_configuration_string: str, describing aircraft configuartion.
    :param raw_line: str, optinal for displaying original slot line in case of error
    :return row: dict, describing aircraft configuration.
    """

    # if none retunr empty dict
    if aircraft_configuration_string is None:
        return {}

    # if input is numeric only, assume that to be the total amount of seats
    if aircraft_configuration_string.isdigit():
        return {"seats": int(aircraft_configuration_string)}

    string_remainder = aircraft_configuration_string.rstrip()

    seat_class_designators = [
        "P",
        "F",
        "A",
        "J",
        "C",
        "D",
        "I",
        "Z",
        "W",
        "S",
        "Y",
        "B",
        "H",
        "K",
        "L",
        "M",
        "N",
        "Q",
        "T",
        "V",
        "X",
        "G",
        "U",
        "E",
        "O",
        "R",
    ]

    cargo_designators = ["LL", "PP"]  # unit load devices (containers)  # pallets

    integer_designators = {"seats": seat_class_designators, "cargo": cargo_designators}

    acv_info = {}

    # seat designator should be in fixed order according to standard
    for designator_type, designators in integer_designators.items():
        for designator in designators:
            if string_remainder.startswith(designator) and (  # only continue if string starts with designator and...
                len(designator) > 1
                or not (  # either have a multi length designator
                    (len(string_remainder) > 1 and string_remainder[1] == string_remainder[0])
                    or string_remainder.startswith("V V")
                )
            ):  #

                acv_info_key = designator_type + "_" + designator

                # for next iteration, remove designator from beginning of string
                string_remainder = string_remainder[len(designator):]

                # standard specifies that there may be an int following. If not return empty string (to later on destinguish from NaN if data gets put in a data frame)
                acv_info_val = ""
                acv_regex = re.search(r"^\d*", string_remainder).group()

                # if int found, add it to total and remove it from string to process as well
                if acv_regex:
                    acv_info_val = int(acv_regex)
                    if designator_type == "seats":
                        if designator_type in acv_info.keys():
                            acv_info[designator_type] += acv_info_val
                        else:
                            acv_info[designator_type] = acv_info_val

                    string_remainder = string_remainder[len(acv_regex):]

                # store found information
                acv_info[acv_info_key] = acv_info_val

    # remainer are general designators
    if string_remainder.startswith("BB"):
        acv_info["BB"] = ""

    # aircraft type
    if string_remainder.startswith("VV"):
        acv_info["VV"] = string_remainder[2:]
    elif string_remainder.startswith("V V"):  # aircraft type alt. Assuming it won't appear together with VV.
        acv_info["V V"] = string_remainder[3:]
    elif len(string_remainder.strip()):
        log_text = (
            "After trying to process aircraft configuration string, there should be no remainder. However, the following string remains in this instance: (%s)"
            % string_remainder
        )
        if raw_line:
            log_text += "\n Raw slot line: " + raw_line
        logging.warning(log_text)

    return acv_info
