import csv
import ssim
import argparse

parser = argparse.ArgumentParser(description='Converts a slotfile to CSV.')
parser.add_argument('-i', help='Input slotfile filename', type=str, metavar='input filename', required=True)
parser.add_argument('-o', help='Output csv filename', type=str, metavar='output filename', required=True)
args = parser.parse_args()
input_file = args.i
output_file = args.o


def main():

    slots, _, _ = ssim.read(input_file)
    flights = ssim.expand_slots(slots)

    keys = flights[0].keys()

    with open(output_file, 'w') as csvfile:
        dict_writer = csv.DictWriter(csvfile, keys, restval='')
        dict_writer.writeheader()
        dict_writer.writerows(flights)

if __name__ == "__main__":
    main()
