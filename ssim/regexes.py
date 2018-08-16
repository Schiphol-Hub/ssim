# For SIR specifications see: SIR Message Specifications in chapter 6.5 of Standard Schedules Information Manual (2011)
# For SIM specifications see: see chapter 7.5 of Standard Schedules Information Manual (2011)

import re

record_1 = (
    "(?P<record_type>1)"
    "(?P<title_of_contents>.{34})"
    "(?P<spare_0>.{5})"
    "(?P<number_of_seasons>.{1})"
    "(?P<spare_1>.{150})"
    "(?P<data_set_serial_number>.{3})"
    "(?P<record_serial_number>.{6})"
)
record_2 = (
    "(?P<record_type>2)"
    "(?P<time_mode>.{1})"
    "(?P<airline_designator>.{3})"
    "(?P<spare_0>.{5})"
    "(?P<season>.{3})"
    "(?P<spare_1>.{1})"
    "(?P<period_of_schedule_validity_from>.{7})"
    "(?P<period_of_schedule_validity_to>.{7})"
    "(?P<creation_date>.{7})"
    "(?P<title_of_data>.{29})"
    "(?P<release_date>.{7})"
    "(?P<schedule_status>.{1})"
    "(?P<creator_reference>.{35})"
    "(?P<duplicate_airline_designator_marker>.{1})"
    "(?P<general_information>.{61})"
    "(?P<in_flight_service_information>.{19})"
    "(?P<electronic_ticketing_information>.{2})"
    "(?P<creation_time>.{4})"
    "(?P<record_serial_number>.{6})"
)

record_3 = (
    "(?P<record_type>3)"
    "(?P<operational_suffix>.{1})"
    "(?P<airline_designator>.{3})"
    "(?P<flight_number>.{4})"
    "(?P<itinerary_variation_identifier>.{2})"
    "(?P<leg_sequence_number>.{2})"
    "(?P<service_type>.{1})"
    "(?P<period_of_operation_from>.{7})"
    "(?P<period_of_operation_to>.{7})"
    "(?P<days_of_operation>.{7})"
    "(?P<frequency_rate>.{1})"
    "(?P<departure_station>.{3})"
    "(?P<scheduled_time_of_passenger_departure>.{4})"
    "(?P<scheduled_time_of_aircraft_departure>.{4})"
    "(?P<utc_local_time_variation_departure>.{5})"
    "(?P<passenger_terminal_departure>.{2})"
    "(?P<arrival_station>.{3})"
    "(?P<scheduled_time_of_aircraft_arrival>.{4})"
    "(?P<scheduled_time_of_passenger_arrival>.{4})"
    "(?P<utc_local_time_variation_arrival>.{5})"
    "(?P<passenger_terminal_arrival>.{2})"
    "(?P<aircraft_type>.{3})"
    "(?P<passenger_reservations_booking_designator>.{20})"
    "(?P<passenger_reservations_booking_modifier>.{5})"
    "(?P<meal_service_note>.{10})"
    "(?P<joint_operation_airline_designators>.{9})"
    "(?P<minimum_connecting_time_international_domestic_status>.{2})"
    "(?P<secure_flight_indicator>.{1})"
    "(?P<spare_0>.{5})"
    "(?P<itinerary_variation_identifier_overflow>.{1})"
    "(?P<aircraft_owner>.{3})"
    "(?P<cockpit_crew_employer>.{3})"
    "(?P<cabin_crew_employer>.{3})"
    "(?P<airline_designator_>.{3})"
    "(?P<flight_number_>.{4})"
    "(?P<aircraft_rotation_layover>.{1})"
    "(?P<operational_suffix_>.{1})"
    "(?P<spare_1>.{1})"
    "(?P<flight_transit_layover>.{1})"
    "(?P<operating_airline_disclosure>.{1})"
    "(?P<traffic_restriction_code>.{11})"
    "(?P<traffic_restriction_code_leg_overflow_indicator>.{1})"
    "(?P<spare_2>.{11})"
    "(?P<aircraft_configuration_version>.{20})"
    "(?P<date_variation>.{2})"
    "(?P<record_serial_number>.{6})"
)

record_4 = (
    "(?P<record_type>4)"
    "(?P<operational_suffix>.{1})"
    "(?P<airline_designator>.{3})"
    "(?P<flight_number>.{4})"
    "(?P<itinerary_variation_identifier>.{2})"
    "(?P<leg_sequence_number>.{2})"
    "(?P<service_type>.{1})"
    "(?P<spare_0>.{13})"
    "(?P<itinerary_variation_identifier_overflow>.{1})"
    "(?P<board_point_indicator>.{1})"
    "(?P<off_point_indicator>.{1})"
    "(?P<data_element_identifier>.{3})"
    "(?P<board_point>.{3})"
    "(?P<off_point>.{3})"
    "(?P<data>.{155})"
    "(?P<record_serial_number>.{6})"
)

record_5 = (
    "(?P<record_type>5)"
    "(?P<spare_0>.{1})"
    "(?P<airline_designator>.{3})"
    "(?P<release_date>.{7})"
    "(?P<spare_1>.{175})"
    "(?P<serial_number_check_reference>.{6})"
    "(?P<continuation_end_code>.{1})"
    "(?P<record_serial_number>.{6})"
)

arrdep = (
    "\n(?P<action_code>[A-Z])"
    "(?P<arrival_airline_designator>[A-Z]{2,3}|[A-Z][0-9]|[0-9][A-Z]|[A-Z]+)"
    "(?P<arrival_flight_number>\d+)*"
    "(?P<arrival_operational_suffix>[A-Z]{1,2})*"
    "\s"
    "(?P<departure_airline_designator>[A-Z]{2,3}|[A-Z][0-9]|[0-9][A-Z]|[A-Z]+)"
    "(?P<departure_flight_number>\d+)*"
    "(?P<departure_operational_suffix>[A-Z]{1,2})*"
    "\s"
    "(?P<period_of_operation_from>\d{2}[A-Z]{3})"
    "(?P<period_of_operation_to>\d{2}[A-Z]{3}){0,1}"
    "\s"
    "(?P<days_of_operation>\d{7}){0,1}"
    "\s"
    "(?P<seats>\d{3})*"
    "(?P<aircraft_type>\w{3})"
    "\s"
    "(?P<origin_station>[A-Z0-9]{3}){0,1}"
    "(?P<previous_station>[A-Z0-9]{3})"
    "(?P<scheduled_time_of_arrival_utc>\d{4})*"
    "\s"
    "(?P<scheduled_time_of_departure_utc>\d{4})*"
    "(?P<overnight_indicator>[0-6]){0,1}"
    "(?P<next_station>[A-Z0-9]{3})"
    "(?P<destination_station>[A-Z0-9]{3}){0,1}"
    "\s"
    "(?P<arrival_service_type>[A-Z])"
    "(?P<departure_service_type>[A-Z])"
    "(?P<frequency_rate>\d){0,1}"
)

arr = (
    "\n(?P<action_code>[A-Z])"
    "(?P<arrival_airline_designator>[A-Z]{2,3}|[A-Z][0-9]|[0-9][A-Z]|\w{2}){0,1}"
    "(?P<arrival_flight_number>\d+[A-Z]*|\w+){0,1}"
    "(?P<arrival_operational_suffix>\w+){0,1}"
    "\s"
    "(?P<period_of_operation_from>\d{2}[A-Z]{3})"
    "(?P<period_of_operation_to>\d{2}[A-Z]{3}){0,1}"
    "\s"
    "("
    "(?P<days_of_operation>\d{7}){0,1}"
    "\s"
    "){0,1}"
    "(?P<seats>\d{3})*"
    "(?P<aircraft_type>\w{3})"
    "\s"
    "(?P<origin_station>[A-Z0-9]{3}){0,1}"
    "(?P<previous_station>[A-Z0-9]{3})"
    "(?P<scheduled_time_of_arrival_utc>\d{4})*"
    "\s"
    "(?P<arrival_service_type>[A-Z])"
    "(?P<frequency_rate>\d){0,1}"
)

dep = (
    "\n(?P<action_code>[A-Z])"
    "\s"
    "(?P<departure_airline_designator>[A-Z]{2,3}|[A-Z][0-9]|[0-9][A-Z]|\w{2]){0,1}"
    "(?P<departure_flight_number>\d+[A-Z]*|\w+){0,1}"
    "(?P<departure_operational_suffix>\w+){0,1}"
    "\s"
    "(?P<period_of_operation_from>\d{2}[A-Z]{3})"
    "(?P<period_of_operation_to>\d{2}[A-Z]{3}){0,1}"
    "\s"
    "("
    "(?P<days_of_operation>\d{7})"
    "\s"
    "){0,1}"
    "(?P<seats>\d{3})*"
    "(?P<aircraft_type>\w{3})"
    "\s"
    "(?P<scheduled_time_of_departure_utc>\d{4})*"
    "(?P<next_station>[A-Z0-9]{3})"
    "(?P<destination_station>[A-Z0-9]{3}){0,1}"
    "\s"
    "(?P<departure_service_type>[A-Z])"
    "(?P<frequency_rate>\d){0,1}"
)

sir_header = (
    "^(?P<file_type>SAL|SAQ|SCR|SHL|SIR|SMA|WCR|WIR)\n"
    "/(?P<creator_reference>.*)\n"
    "(?P<season>[SW][0-9]{2})\n"
    "(?P<day_of_message>[0-9]{2})(?P<month_of_message>[A-Z]{3})\n"
    "(?P<clearance_advice_airport>[A-Z]{3})\n"
    "(REYT/(?P<message_reference>.*)\n)?"  # this line is optional
)

additional_information = "(\n/\s(?P<additional_schedule_information>.*)\s/){0,1}"

t = "(?P<raw>{})"
regexes = {
    "sir": {
        "arr": re.compile(t.format(arr + additional_information)),
        "dep": re.compile(t.format(dep + additional_information)),
        "arrdep": re.compile(t.format(arrdep + additional_information)),
        "header": re.compile(t.format(sir_header)),
    },
    "sim": {
        "record_1": re.compile(t.format(record_1)),
        "record_2": re.compile(t.format(record_2)),
        "record_3": re.compile(t.format(record_3)),
        "record_4": re.compile(t.format(record_4)),
        "record_5": re.compile(t.format(record_5)),
    },
}
