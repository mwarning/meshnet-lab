#!/usr/bin/env python3

import argparse
import time
import json
import math
import sys
import os
import csv


parser = argparse.ArgumentParser(
    description='Read a CSV file and combine <span> rows. For each selected column, an extra variance column is added. Other numerical columns are replaced by the mean.')
parser.add_argument('input', help='Input CSV file')
parser.add_argument('output', help='Output CSV file')
parser.add_argument('--span', type=int, required=True, help='Amount of consecutive rows to be combined into a mean value.')
parser.add_argument('--type', type=str, required=True, choices=['sd', 'se', 'vr'], help='Calculate a standard deviation, standard error or value range. Column title suffix is "_sd", "_se" or "_vr".')
parser.add_argument('--columns', nargs='+', required=True, help='Calculate a standard deviation. Column title prefix is "_sd".')

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

def calc_standard_deviation(values):
	mean = calc_mean(values)
	d = []
	for value in values:
		d.append((value - mean) * (value - mean))
	return math.sqrt((1.0 / (len(d) - 1)) * sum(d))

def calc_standard_error(values):
	return calc_standard_deviation(values) / math.sqrt(len(values))

def calc_value_range(values):
	min = None
	max = None
	for value in values:
		if min == None or min > value:
			min = value
		if max == None or max < value:
			max = value

	return abs(max - min)

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

def handle_rows(rows, columns, type):
	output_row = []
	for col in range(0, len(rows[0])):
		if (col + 1) in columns:
			values = get_row_list(rows, col)
			places = get_decimal_places(rows, col)
			output_row.append(format_float(calc_mean(values), places))
			if type == 'sd':
				output_row.append(format_float(calc_standard_deviation(values), places))
			elif type == 'se':
				output_row.append(format_float(calc_standard_error(values), places))
			elif type == 'vr':
				output_row.append(format_float(calc_value_range(values), places))
			else:
				print('unknown type: {}'.format(type))
				exit(1)
		elif is_float(rows[0][col]):
			# other columns that are numbers => average
			values = get_row_list(rows, col)
			places = get_decimal_places(rows, col)
			output_row.append(format_float(calc_mean(values), places))
		else:
			# other columns that are not numbers => take first value
			output_row.append(rows[0][col])

	return output_row

def handle_header(header, columns, type):
	output_header = []
	for col in range(0, len(header)):
		if (col + 1) in columns:
			output_header.append(header[col])
			output_header.append(header[col] + '_' + type)
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

dialect = None
output_header = None
output_rows = []

with open(args.input, 'r') as file:
	sample = file.readline()
	file.seek(0)

	dialect = csv.Sniffer().sniff(sample, delimiters=";,\t ")
	reader = csv.reader(file, dialect)

	if csv.Sniffer().has_header(sample):
		for line in reader:
			args.columns = translate_columns(line, args.columns)
			output_header = handle_header(line, args.columns, args.type)
			break
	else:
		args.columns = translate_columns([], args.columns)

	rows = []
	for line in reader:
		if len(rows) < args.span:
			rows.append(line)
		else:
			# process every <span> rows
			output_rows.append(handle_rows(rows, args.columns, args.type))
			rows = [line]

	if len(rows) == args.span:
		output_rows.append(handle_rows(rows, args.columns, args.type))
	elif len(rows) != 0:
		print("Warning: {} lines left => skipped".format(len(rows)))


with open(args.output, 'w') as file:
	writer = csv.writer(file, dialect)

	if output_header is not None:
		writer.writerow(output_header)

	for row in output_rows:
		writer.writerow(row)
