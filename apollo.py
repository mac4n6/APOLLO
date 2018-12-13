#!/usr/bin/python
'''
Copyright (c) 2018, Station X Labs, LLC
All rights reserved.
Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:
	* Redistributions of source code must retain the above copyright
	  notice, this list of conditions and the following disclaimer.
	* Redistributions in binary form must reproduce the above copyright
	  notice, this list of conditions and the following disclaimer in the
	  documentation and/or other materials provided with the distribution.
	* Neither the name of the Station X Labs, LLC nor the
	  names of its contributors may be used to endorse or promote products
	  derived from this software without specific prior written permission.
THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL STATION X LABS, LLC BE LIABLE FOR ANY
DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
'''

import sqlite3
from time import gmtime, localtime, strftime
import csv
import sys
import argparse
from argparse import RawTextHelpFormatter
import os
from ConfigParser import RawConfigParser
from collections import OrderedDict

def parse_module_definition(mod_info):
	print "Parsing Modules..."

	database_names = set()
	for mod_def, mod_data in mod_info.items():
		mod_name = mod_def
		parser = RawConfigParser()
		parser.read(mod_def)

		query_name = parser.get('Query Metadata', 'QUERY_NAME')
		database_name = parser.get('Database Metadata', 'DATABASE')
		activity = parser.get('Query Metadata', 'ACTIVITY')
		key_timestamp = parser.get('Query Metadata', 'KEY_TIMESTAMP')
		sql_query = parser.get('SQL Query', 'QUERY')

		database_names.add(database_name)
		mod_info[mod_def] = [query_name, database_name, activity, key_timestamp, sql_query]
	
	print "Parsing: ", len(mod_info), " modules."

	print "Searching for database files..."
	for root, dirs, filenames in os.walk(data_dir):
		for f in filenames:
			if f in database_names:
				for mod_def, mod_data in mod_info.items():
					if mod_data[1] == f:
						mod_info[mod_def].append(os.path.join(root,f))

	for mod_def, mod_data in mod_info.items():
		print mod_def, ":",  len(mod_data)-5, "databases."

		run_module(mod_def,mod_data[0],mod_data[5:],mod_data[2],mod_data[3],mod_data[4])

def run_module(mod_name,query_name,database_names,activity,key_timestamp,sql_query):

	for db in database_names:
		print "\tExecuting module on: " + db
		conn = sqlite3.connect(db)
		with conn:
			conn.row_factory = sqlite3.Row
			cur = conn.cursor()

		try:
			sql = sql_query
			cur.execute(sql)
			rows = cur.fetchall()

			headers = []
			for x in cur.description:
				headers.append(x[0])

			for row in rows:
				col_row = OrderedDict()
				col_row = (OrderedDict(zip(headers,row)))

				data_stuff = ""

				for k,v in col_row.iteritems():

					if isinstance(v,str):
						data = "[" + str(k) + ": " + str(v) + "] "
					elif isinstance(v,unicode):
						data = "[" + str(k) + ": " + v.encode('utf8').decode('utf8') + "] "
					elif isinstance(v,int):
						data = "[" + str(k) + ": " + str(v) + "] "
					else:
						data = "[" + str(k) + ": " + str(v) + "] "

					data_stuff = data_stuff + data

				if args.output == 'csv':
					loccsv.writerow([col_row[key_timestamp],activity, data_stuff,db,mod_name])
				elif args.output == 'sql':
					key = col_row[key_timestamp]
					cw.execute("INSERT INTO APOLLO (Key, Activity, Output, Database, Module) VALUES (?, ?, ?, ?, ?)",(key, activity, data_stuff, db, mod_name))

		except:
			print "\t***ERROR***: Could not parse database ["+ db +"]. Often this is due to file permissions, or changes in the database schema."		

if __name__ == "__main__":

	parser = argparse.ArgumentParser(description="\
	Apple Pattern of Life Lazy Outputter (APoLLO)\
	\n\nVery lazy parser to extract pattern-of-life data from SQLite databases on iOS/macOS datasets (though really any SQLite database if you make a configuration file and provide it the proper metadata details.\
	\n\nOutputs include SQLite Database or CSV.\
	\n\n\tVersion: BETA 12122018 - TESTING PURPOSES ONLY, SERIOUSLY.\
	\n\tUpdated: 12/12/2018\
	\n\tAuthor: Sarah Edwards | @iamevltwin | mac4n6.com\
	\n\tAdded Efficiency: Sam Alptekin of @sjc_CyberCrimes"
		, prog='apollo.py'
		, formatter_class=RawTextHelpFormatter)
	parser.add_argument('-output', choices=['sql','csv'], action="store", help="sql=SQLite or csv=CSV")
	parser.add_argument('modules_directory')
	parser.add_argument('data_dir_to_analyze')

	args = parser.parse_args()

	global output_type
	output_type = None

	global csvfile
	global loccsv

	mod_dir = args.modules_directory
	data_dir = args.data_dir_to_analyze
	
	if args.output == 'csv':

		with open('apollo.csv', 'wb') as csvfile:
			loccsv = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
			loccsv.writerow(['Timestamp','Activity', 'Output','Database','Module'])

			mod_info = {}

			for root, dirs, filenames in os.walk(mod_dir):
				for f in filenames: 
					if f.endswith(".txt"):
						mod_def = os.path.join(root,f) 
						fread = open(mod_def,'r')
						contents = fread.read()
						if "[Database Metadata]" in contents:
							mod_info[mod_def] = []

			parse_module_definition(mod_def)

			print "\n===> Lazily outputted to CSV file: apollo.csv\n"

	if args.output == 'sql':

		if os.path.isfile("apollo.db"):
			os.remove("apollo.db")
		connw = sqlite3.connect('apollo.db')
		cw = connw.cursor()
		cw.execute("CREATE TABLE APOLLO(Key timestamp, Activity TEXT, Output TEXT, Database TEXT, Module TEXT)")
		
		mod_info = {}

		for root, dirs, filenames in os.walk(mod_dir):
			for f in filenames: 
				if f.endswith(".txt"):
					mod_def = os.path.join(root,f) 
					fread = open(mod_def,'r')
					contents = fread.read()
					if "[Database Metadata]" in contents:
						mod_info[mod_def] = []

		parse_module_definition(mod_info)

		connw.commit()

		print "\n===> Lazily outputted to SQLite file: apollo.db\n"
