#!/usr/bin/env python3

import argparse
import time
import json
import math
import sys
import os
import csv


parser = argparse.ArgumentParser(
    description='Read a CSV file and combine <span> rows. For each selected column, an extra column is calculated. Other columns containing numerical values are replaced by the mean or by the first value otherwise.')
parser.add_argument('input', help='Input CSV file')
parser.add_argument('output', help='Output CSV file')
parser.add_argument('--span', type=int, required=True, help='Amount of consecutive rows to be combined into a mean value.')
parser.add_argument('--columns-sd', nargs='+', default=[], help='Calculate a standard deviation. Column title prefix is "_sd".')
parser.add_argument('--columns-se', nargs='+', default=[], help='Calculate a standard error. Column title prefix is "_se".')
parser.add_argument('--columns-range', nargs='+', default=[], help='Calculate the value range (|max - min|). Column title prefix is "_range".')
parser.add_argument('--columns-max', nargs='+', default=[], help='Calculate the maximum value. Column title prefix is "_max".')
parser.add_argument('--columns-min', nargs='+', default=[], help='Calculate the minimum value. Column title prefix is "_min".')

args = parser.parse_args()

def is_float(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

def is_int(s):
    try:
        int(s)
        return True
    except ValueError:
        return False

def calc_mean(values):
	return sum(values) / len(values)

def calc_value_min(values):
	min = None
	for value in values:
		if min == None or min > value:
			min = value
	return min

def calc_value_max(values):
	max = None
	for value in values:
		if max == None or max < value:
			max = value
	return max

def calc_standard_deviation(values):
	mean = calc_mean(values)
	d = []
	for value in values:
		d.append((value - mean) * (value - mean))
	return math.sqrt((1.0 / (len(d) - 1)) * sum(d))

def calc_standard_error(values):
	return calc_standard_deviation(values) / math.sqrt(len(values))

def calc_value_range(values):
	return abs(calc_value_max(values) - calc_value_min(values))

def get_row_list(lines, col):
	row = []
	for line in lines:
		row.append(float(line[col]))
	return row

'''
Get the maximum number of used decimal places, e.g.:
1 => 0
1.0 => 1
1.2, 1.23, 1.001 => 3
1.234 => 3
'''
def get_decimal_places(lines, col):
	def get_places(s):
		pos = s.find('.')
		return 0 if pos < 0 else (len(s) - pos - 1)

	max_places = 0
	for line in lines:
		places = get_places(line[col])
		max_places = max(max_places, places)

	return max_places

'''
Round a value to the given decimal places, e.g.:
1.0, 2 => 1.00
1.0, 1 => 1.0
1.0, 0 => 1
'''
def format_float(value, places):
	return str(round(value, places)).rstrip('0').rstrip('.')

def handle_rows(rows, mapping):
	output_row = []
	for col in range(0, len(rows[0])):
		if (col + 1) in mapping:
			values = get_row_list(rows, col)
			places = get_decimal_places(rows, col)
			output_row.append(format_float(calc_mean(values), places))
			for m in mapping[col + 1]:
				output_row.append(format_float(m['call'](values), places))
		elif is_float(rows[0][col]):
			# other columns that are numbers => average
			values = get_row_list(rows, col)
			places = get_decimal_places(rows, col)
			output_row.append(format_float(calc_mean(values), places))
		else:
			# other columns that are not numbers => take first value
			output_row.append(rows[0][col])

	return output_row

def handle_header(header, mapping):
	output_header = []
	for col in range(0, len(header)):
		if (col + 1) in mapping:
			output_header.append(header[col])
			for m in mapping[col + 1]:
				output_header.append(header[col] + '_' + m['suffix'])
		else:
			output_header.append(header[col])

	return output_header

'''
Translate column names to column index number using the CSV header
'''
def translate_columns(header, columns):
	translated = []
	for value in columns:
		idx = header.index(value)
		if idx < 0:
			if is_int(value):
				translated.append(int(value))
			else:
				print('Cannot find header: {}'.format(value))
				exit(1)
		else:
			# translated title name to column index
			translated.append(idx + 1)

	return translated

def create_colmap(header):
	def add_mappings(mapping, header, columns, method, suffix):
		def translate(arg):
			if arg in header:
				return (header.index(arg) + 1)

			if is_int(arg):
				return int(arg)
			else:
				print('Cannot find header: {}'.format(arg))
				exit(1)

		for arg in columns:
			col = translate(arg)
			if col in mapping:
				mapping[col].append({'call': method, 'suffix': suffix})
			else:
				mapping[col] = [{'call': method, 'suffix': suffix}]

	mapping = {}
	add_mappings(mapping, header, args.columns_se, calc_standard_error, 'se')
	add_mappings(mapping, header, args.columns_sd, calc_standard_deviation, 'sd')
	add_mappings(mapping, header, args.columns_range, calc_value_range, 'range')
	add_mappings(mapping, header, args.columns_max, calc_value_max, 'max')
	add_mappings(mapping, header, args.columns_min, calc_value_min, 'min')
	return mapping


dialect = None
output_header = None
output_rows = []
mapping = None

with open(args.input, 'r') as file:
	sample = file.readline()
	file.seek(0)

	dialect = csv.Sniffer().sniff(sample, delimiters=";,\t ")
	reader = csv.reader(file, dialect)

	if csv.Sniffer().has_header(sample):
		for line in reader:
			mapping = create_colmap(line)
			output_header = handle_header(line, mapping)
			break
	else:
		mapping = create_colmap([])

	rows = []
	for line in reader:
		if len(rows) < args.span:
			rows.append(line)
		else:
			# process every <span> rows
			output_rows.append(handle_rows(rows, mapping))
			rows = [line]

	if len(rows) == args.span:
		output_rows.append(handle_rows(rows, mapping))
	elif len(rows) != 0:
		print("Warning: {} lines left => skipped".format(len(rows)))


with open(args.output, 'w') as file:
	writer = csv.writer(file, dialect)

	if output_header is not None:
		writer.writerow(output_header)

	for row in output_rows:
		writer.writerow(row)
