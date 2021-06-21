'''
--------------------------------------------------------------------------------
      Copyright (c) 2018-2020 Sarah Edwards (Station X Labs, LLC, 
      @iamevltwin, mac4n6.com). All rights reserved.

      This software is provided "as is," without warranty of any kind,
      express or implied.  In no event shall the author or contributors
      be held liable for any damages arising in any way from the use of
      this software.

      The contents of this file are DUAL-LICENSED.  You may modify and/or
      redistribute this software according to the terms of one of the
      following two licenses (at your option):

      LICENSE 1 ("BSD-like with acknowledgment clause"):

      Permission is granted to anyone to use this software for any purpose,
      including commercial applications, and to alter it and redistribute
      it freely, subject to the following restrictions:

      1. Redistributions of source code must retain the above copyright
         notice, disclaimer, and this list of conditions.
      2. Redistributions in binary form must reproduce the above copyright
         notice, disclaimer, and this list of conditions in the documenta-
         tion and/or other materials provided with the distribution.
      3. All advertising, training, and documentation materials mentioning 
         features or use of this software must display the following 
         acknowledgment. Character-limited social media may abbreviate this 
         acknowledgment to include author and APOLLO name ie: "This new 
         feature brought to you by @iamevltwin's APOLLO". Please make an 
         effort credit the appropriate authors on specific APOLLO modules.
         The spirit of this clause is to give public acknowledgment to 
         researchers where credit is due.

            This product includes software developed by Sarah Edwards 
            (Station X Labs, LLC, @iamevltwin, mac4n6.com) and other 
            contributors as part of APOLLO (Apple Pattern of Life Lazy 
            Output'er). 


      LICENSE 2 (GNU GPL v3 or later):

      This file is part of APOLLO (Apple Pattern of Life Lazy Output'er).

      APOLLO is free software: you can redistribute it and/or modify
      it under the terms of the GNU General Public License as published by
      the Free Software Foundation, either version 3 of the License, or
      (at your option) any later version.

      APOLLO is distributed in the hope that it will be useful,
      but WITHOUT ANY WARRANTY; without even the implied warranty of
      MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
      GNU General Public License for more details.

      You should have received a copy of the GNU General Public License
      along with APOLLO.  If not, see <https://www.gnu.org/licenses/>.
--------------------------------------------------------------------------------
'''
import sqlite3
import csv
import argparse
from argparse import RawTextHelpFormatter
import os
import configparser
from collections import OrderedDict
import string
from simplekml import Kml, Style
import re
import shutil
import subprocess
import stat
import json
from zipfile import ZipFile
import fnmatch

def gathermacos(database_names):
	tempdir()
	ignore_dir.append(os.getcwd())
	print("...Searching for and copying databases into tmp_apollo...")
	for root, dirs, filenames in os.walk(data_dir,followlinks=False):
		if not any(ignored in root for ignored in ignore_dir):
			for f in filenames:
				for db in database_names:
					if db == "db":
						if re.search(rf'^{db}(-shm|-wal|$)',f):
							if not os.path.exists(os.getcwd() + "/tmp_apollo" + root):
								os.makedirs(os.getcwd() + "/tmp_apollo" + root)
							shutil.copyfile(os.path.join(root,f),os.getcwd() + "/tmp_apollo" + root +"/"+f)
					elif re.search(rf'^{db}(-shm|-wal|$)',f):
						if not os.path.exists(os.getcwd() + "/tmp_apollo" + root):
							os.makedirs(os.getcwd() + "/tmp_apollo" + root)
						shutil.copyfile(os.path.join(root,f),os.getcwd() + "/tmp_apollo" + root +"/"+f)
	chown_chmod()

def gatherios(database_names):

	tempdir()
	tmpdir = os.getcwd() + "/tmp_apollo"
	sshProcess = subprocess.Popen(['ssh', '-p', port, '-T', 'root@' + ip]
		, stdin=subprocess.PIPE
		, stdout=subprocess.PIPE
		, encoding='utf8')
	print("...Finding files on root@" + ip + ":" + port + " in " + data_dir)
	findcmd = "find " + data_dir + " -type f"
	out, err = sshProcess.communicate("find " + data_dir + " -type f")
	print("...Writing ios_files.txt...")
	with open(tmpdir +'/ios_files.txt', 'w') as file:
		file.write(out)

	if ignore_dir:
		with open(tmpdir +'/ios_files.txt', 'r') as file:
			lines = file.readlines()
		with open(tmpdir +'/ios_files.txt', "w") as file:
			for line in lines:
				if not any(ignored in line.strip("\n") for ignored in ignore_dir):
					file.write(line)

	print("...Searching for and copying databases into tmp_apollo...")
	with open(tmpdir +'/ios_files.txt', 'r') as file:
		lines = file.readlines()
		for line in lines:
			for f in database_names:
				splitline = line.rsplit("/",1)
				if splitline[1].startswith(f):
					if f == "db":
						pass
					else:
						line_escape = line.replace(" ", "\ ")
						output = tmpdir + splitline[0]
						if not os.path.exists(output):
							os.makedirs(output)
						server = 'root@'+ip+":"
						subprocess.Popen(['scp','-P'+port,'-T',server+line_escape,output]).wait()
	chown_chmod()

def gatherfromzip(database_names):
	
	tempdir()
	tmpdir = os.getcwd() + "/tmp_apollo"

	zip_file = ZipFile(data_dir)
	name_list = zip_file.namelist()
	
	for pattern in database_names:
		pattern = f'*{pattern}'
		for member in name_list:
			if fnmatch.fnmatch(member, pattern):
				try:
					extracted_path = zip_file.extract(member, path=tmpdir)
				except Exception as ex:
					member = member.lstrip("/")
					logfunc(f'Could not write file to filesystem, path was {member} ' + str(ex))

	zip_file.close()
	chown_chmod()
	
def tempdir():
	tmpdir = os.getcwd() + "/tmp_apollo"
	print("...Creating /tmp_apollo in: " + tmpdir)
	if not os.path.exists(tmpdir):
		os.makedirs(tmpdir)
	os.chown(tmpdir,os.stat(os.getcwd()).st_uid,os.stat(os.getcwd()).st_gid)

def chown_chmod():
	print("...chmod/chown all the things...")
	for root, dirs, filenames in os.walk(os.getcwd() + "/tmp_apollo"):
			for d in dirs:
				if os.access(os.path.join(root, d), os.R_OK) == False:
					os.chmod(os.path.join(root, d), stat.S_IRWXU)
				os.chown(os.path.join(root, d),os.stat(os.getcwd()).st_uid,os.stat(os.getcwd()).st_gid)
			for f in filenames:
				if os.access(os.path.join(root, f), os.R_OK) == False or os.access(os.path.join(root, f), os.W_OK) == False:
					os.chmod(os.path.join(root, f), stat.S_IRWXU)
				os.chown(os.path.join(root, f),os.stat(os.getcwd()).st_uid,os.stat(os.getcwd()).st_gid)

def extractdata(mod_info,database_names):
	print("\n==> Parsing", len(mod_info), "modules (Note: Some modules may be run on more than one database.)")
	count = 1
	modules = set()
	
	for item in sorted(mod_info):
		dbs = item.split('#')
		for mod in dbs:
			modules.add(dbs[0])
		print("\t[" + str(count) + "] " + str(dbs[0]) + " on " + str(dbs[1]) + ": "+ str(dbs[2]))
		count = count + 1

	print("\n==> Will lazily run APOLLO on " + str(len(modules)) + " unique modules and " + str(len(database_names))+ " unique databases.") 

	print("\n==> Searching for database files...this may take a hot minute...")
	print()
	for root, dirs, filenames in os.walk(data_dir):
		for f in filenames:
			if f in database_names:
				for mod_def, mod_data in mod_info.items():
					if mod_data:
						if mod_data[1] == f:
							mod_info[mod_def].append(os.path.join(root,f))

	for mod_def, mod_data in mod_info.items():
		mod_def_split = mod_def.split('#')
		if mod_data:
			print(mod_def_split[0] + " on " + mod_def_split[1] + " for [" + mod_def_split[2] + "]:", len(mod_data)-5, "databases.")
			run_module(mod_def,mod_data[0],mod_data[5:],mod_data[2],mod_data[3],mod_data[4])
			print()
		else:
			print(mod_def_split[0] + " on " + mod_def_split[1], ": Module not supported for version of data provided.")
			print()	

def run_module(mod_name,query_name,database_names,activity,key_timestamp,sql_query):

	global records
	global total_loc_records

	for db in database_names:
		print("\tExecuting module on: " + db)

		if args.k == True and "Location" in activity:
			kml = Kml()
			sharedstyle = Style()
			sharedstyle.iconstyle.color =  'ff0000ff'

		conn = sqlite3.connect(db)
		with conn:
			conn.row_factory = sqlite3.Row
			cur = conn.cursor()

		try: 
			try:
				sql = sql_query
				cur.execute(sql)
			except:
				print("\tSQL Query not supported for this version of the database.")
				
			try:
				rows = cur.fetchall()
			except:
				print("\t\tERROR: Cannot fetch query contents.")

			num_records = str(len(rows))
			print("\t\tNumber of Records: " + num_records)
			records = records + len(rows)

			headers = []
			for x in cur.description:
				headers.append(x[0])

			loc_records = 0

			for row in rows:
				col_row = OrderedDict()
				col_row = (OrderedDict(list(zip(headers,row))))

				data_stuff = ""
				for k,v in iter(col_row.items()):
					data = "[" + str(k) + ": " + str(v) + "] "

					try:
						data_stuff = data_stuff + data
					except:
						data_stuff = [x for x in data_stuff if x in string.printable]
						data_stuff = data_stuff + data
				
				if output == 'csv':
					key = col_row[key_timestamp]
					if "\n" in data_stuff:
							data_stuff = data_stuff.replace('\n',"<nl>")
					if "\r" in data_stuff:
							data_stuff = data_stuff.replace('\r',"<cr>")
					try:
						loccsv.writerow([key,activity,data_stuff,db,mod_name])
					except:
						loccsv.writerow([key,activity,data_stuff.encode('utf8'),db,mod_name])

				elif output == 'sql':
					key = col_row[key_timestamp]
					cw.execute("INSERT INTO APOLLO (Key, Activity, Output, Database, Module) VALUES (?, ?, ?, ?, ?)",(key, activity, data_stuff, db, mod_name))

				elif output == 'sql_json':			
					key = col_row[key_timestamp]
					cw.execute("INSERT INTO APOLLO (Key, Activity, Output, Database, Module) VALUES (?, ?, ?, ?, ?)",(key, activity, json.dumps(col_row, indent=4), db, mod_name))

				if len(rows) > 0:
					if args.k == True and "COORDINATES" in data_stuff:
						coords_search = re.search(r'COORDINATES: [\d\.\,\ \-]*',data_stuff)
						coords = coords_search.group(0).split(" ")

						point = kml.newpoint(name=key)
						point.description = ("Data: " + data_stuff)
						point.timestamp.when = key
						point.style = sharedstyle
						point.coords = [(coords[2],coords[1])]
						
						loc_records = loc_records + 1
						total_loc_records = total_loc_records + 1

			if loc_records:
				kmzfilename = query_name + ".kmz"
				print("\t\tNumber of Location Records: " + str(loc_records))
				print("\t\t===> Saving KMZ to " + kmzfilename + "...")
				kml.savekmz(kmzfilename)
		
		except:
			print("\t\tERROR: Problem with database. Could be unsupported.")

def parse_module_definition(mod_info):

	print("...Parsing Modules in..." + mod_dir)
	database_names = set()
	for root, dirs, filenames in os.walk(mod_dir):
		for f in filenames: 
			if f.endswith(".txt"):
				mod_def = os.path.join(root,f) 
				fread = open(mod_def,'r')
				contents = fread.read()

				parser = configparser.ConfigParser()
				parser.read(mod_def)

				mod_name = mod_def
				query_name = parser['Query Metadata']['QUERY_NAME']
				activity = parser['Query Metadata']['ACTIVITY']
				key_timestamp = parser['Query Metadata']['KEY_TIMESTAMP']
				databases = parser['Database Metadata']['DATABASE']
				database_name = databases.split(',')

				for database in database_name:
					database_names.add(database)

				for db in database_name:

					if subparser == 'extract':
						if version == 'yolo':
							for section in parser.sections():
								if "SQL Query" in section:
									sql_query = parser.items(section,'QUERY')
									for item in sql_query[0]:
										if "SELECT" in item:
											query = item
											uniquekey = mod_def + "#" + db + "#" + section
											mod_info[uniquekey] = [query_name, db, activity, key_timestamp, query]
						else:			
							for section in parser.sections():
								if version in re.split('[ ,]', section):
									sql_query = parser.items(section,'QUERY')
									for item in sql_query[0]:
										query = item
										uniquekey = mod_def + "#" + db + "#" + section
										mod_info[uniquekey] = [query_name, db, activity, key_timestamp, query]

	if subparser == 'extract': 
		extractdata(mod_info,database_names)
	elif subparser =='gather_macos':
		gathermacos(database_names)
	elif subparser == 'gather_ios': 
		gatherios(database_names)
	elif subparser == 'gather_from_zip': 
		gatherfromzip(database_names)
		
if __name__ == "__main__":

	parser = argparse.ArgumentParser(description="\
	Apple Pattern of Life Lazy Outputter (APOLLO)\
	\n\nVery lazy parser to extract pattern-of-life data from SQLite databases on iOS/macOS/Android/Windows datasets (though really any SQLite database if you make a configuration file and provide it the proper metadata details.\
	\n\nOutputs include SQLite Database (with JSON or '|' Delimited) or Tab Delimited CSV.\
	\n\nYolo! Meant to run on anything and everything, like a honey badger - it don't care. Can be used with multiple dumps of devices. It will run all queries in all modules with no regard for versioning. May lead to redundant data since it can run more than one similar query. Be careful with this option.\
	\n\tAuthor: Sarah Edwards | @iamevltwin | mac4n6.com"
		, prog='apollo.py'
		, formatter_class=RawTextHelpFormatter)

	apollo_version = "11182020"
	parser.add_argument('-v','--version'
		, action='version'
		, version='%(prog)s 1.4')
	
	subparsers = parser.add_subparsers(help='help for subcommand'
		, dest='subparser')

	gather_macos = subparsers.add_parser('gather_macos'
		, help='Gather Files from MacOS System')
	
	gather_from_zip = subparsers.add_parser('gather_from_zip'
		, help='Gather Files from Zip file')
	
	gather_ios = subparsers.add_parser('gather_ios'
		, help='Gather from Jailbroken iOS Device (IP/Port Required)')
	gather_ios.add_argument('--ip'
		, action="store"
		, help="IP Address/Domain of Jailbroken iOS Device"
		, required=True)
	gather_ios.add_argument('--port'
		, action="store"
		, help="SSH/SCP Port of Jailbroken iOS Device"
		, required=True)

	extract = subparsers.add_parser('extract'
		, help='Extract Data using APOLLO Modules')
	extract.add_argument('-o'
		, choices=['sql','csv','sql_json']
		, required=True
		, action="store"
		, help="Output: sql=SQLite or csv=CSV (required)")
	extract.add_argument('-p'
		, choices=['apple','android','windows','yolo']
		, default='apple'
		, action="store"
		, help="Platform: apple=iOS/macOS, Android, Windows or yolo (run on whatever")
	extract.add_argument('-v'
		, choices=['8','9','10','11','12','13','14','10.13','10.14','10.15','10.16', 'and9','and10','and11','win10_1803','win10_1809','win10_1903','win10_1909','yolo']
		, required=True
		, action="store"
		, help="OS Version (required). iOS=8-13, macOS=10.13-10.15, android 9-11, Windows 10 1803-1909")
	extract.add_argument('-k'
		, help="Additional KMZ Output for Location Data"
		, action="store_true")
	
	parser.add_argument('modules_directory'
		, help="Path to Modules Directory")
	parser.add_argument('data_path'
		, help="Path to Data Directory. It can be full file system dump or directory of extracted databases, it is recursive. For gathering files this is the top level directory to search for files.")
	parser.add_argument('--ignore'
		, action='append'
		, help='Ignore Path using Gather. Can be used more than once for different paths.')

	args = parser.parse_args()

	global csvfile
	global loccsv
	records = 0
	total_loc_records = 0

	print("\n--------------------------------------------------------------------------------------")
	print("APOLLO Modules Version: " + apollo_version)
	try: 
		subparser = args.subparser
		print("Action: " + subparser)
	except:
		pass
	try: 
		platform = args.p
		print("Platform: " + platform)
	except:
		pass
	try:
		version = args.v 
		print("Version: " + version)
	except:
		pass
	try:
		output = args.o 
		print("Output: " + output)
	except:
		pass
	try:
		data_dir = args.data_path
		print("Data Directory: " + data_dir)
	except:
		pass
	try:
		ignore_dir = args.ignore
		for ignore in ignore_dir:
			print("  Ignoring Directory: " + ignore)
	except:
		pass
	try:
		mod_dir = args.modules_directory
		print("Modules Directory: " + mod_dir)
	except:
		pass
	try:
		port = args.port
		ip = args.ip
		print('Jailbroken Device IP/Domain: ' + ip)
		print('Jailbroken Device Port: ' + port)
	except:
		pass
	try:
		if args.k:
			print("KMZ: TRUE")
	except:
		pass
	print("Current Working Directory: " + os.getcwd())
	print("--------------------------------------------------------------------------------------")

	if ignore_dir == None:
		ignore_dir = []
	
	mod_info = {}
	
	try:
		if output == 'csv':

			with open('apollo.csv', 'w', newline='') as csvfile:
				loccsv = csv.writer(csvfile, dialect='excel',delimiter='\t', quotechar='"')
				loccsv.writerow(['Timestamp','Activity', 'Output','Database','Module'])

				parse_module_definition(mod_info)

				print("\n===> Total number of records: " + str(records))

				if args.k:
					print("===> Total Number of Location Records: " + str(total_loc_records))

				print("\n===> Lazily outputted to CSV file: apollo.csv\n")

		elif output == 'sql' or output == 'sql_json':

			if os.path.isfile("apollo.db"):
				os.remove("apollo.db")
			connw = sqlite3.connect('apollo.db')
			cw = connw.cursor()
			cw.execute("CREATE TABLE APOLLO(Key timestamp, Activity TEXT, Output TEXT, Database TEXT, Module TEXT)")

			parse_module_definition(mod_info)

			print("\n===> Total Number of Records: " + str(records))

			connw.commit()

			if args.k:
				print("===> Total Number of Location Records: " + str(total_loc_records))
			
			print("\n===> Lazily outputted to SQLite file: apollo.db\n")

	except:
		pass

	if subparser in ['gather_macos','gather_ios', 'gather_from_zip']:
		parse_module_definition(mod_info)
		