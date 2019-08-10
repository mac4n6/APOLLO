import argparse
from argparse import RawTextHelpFormatter
from six.moves.configparser import RawConfigParser
import xml.etree.ElementTree as ET  
import glob, os, sqlite3, os, sys, re, json, subprocess

parser = argparse.ArgumentParser(description="\
	Artemis Test"
, prog='artemis.py'
, formatter_class=RawTextHelpFormatter)
parser.add_argument('-o', choices=['sql','csv'], required=True, action="store", help="Output: sql=SQLite or csv=CSV (required)")
parser.add_argument('modules_directory',help="Path to Module Directory")
parser.add_argument('data_dir_to_analyze',help="Path to Data Directory. It can be full file system dump or directory of extracted databases, it is recursive.")

args = parser.parse_args()
format = args.o
mod_dir = args.modules_directory
data_dir = args.data_dir_to_analyze

#Search for the usagestats directory

for root, dirs, filenames in os.walk(data_dir):
		for f in dirs:
			if f == "usagestats":
				pathfound = os.path.join(root, f)

#Create sqlite databases
db = sqlite3.connect(data_dir+r'\usagestats.db')
cursor = db.cursor()

#Create table usagedata.

cursor.execute('''

    CREATE TABLE data(usage_type TEXT, lastime TEXT, timeactive TEXT, package TEXT, types TEXT, classs TEXT,

					  source TEXT, fullatt TEXT)

''')

db.commit()

err=0

print("\n--------------------------------------------------------------------------------------")
print("Artemis: Android Review Timeline Events Module Integrated Solution")
print("Objective: Parse Usagestats XML to SQLite + Android specific Apollo modules")
print("By: Alexis Brignoni | @AlexisBrignoni | abrignoni.com")
print("Data Directory: " + data_dir)
print("Modules Directory: " + mod_dir)	
print("--------------------------------------------------------------------------------------")
print("All credit goes to Sarah Edwards for her Apollo framework which Artemis leverages")
print("Apollo Author: Sarah Edwards | @iamevltwin | mac4n6.com")
print("--------------------------------------------------------------------------------------")
print("Locating Usagestats XML files + processing")
print("Please wait...") 

for filename in glob.iglob(pathfound+'\**', recursive=True):
	if os.path.isfile(filename): # filter dirs
		file_name = os.path.splitext(os.path.basename(filename))[0]
		#Test if xml is well formed
		if file_name == 'version':
			continue	
		else:
			if 'daily' in filename:
				sourced = 'daily'
			elif 'weekly' in filename:
				sourced = 'weekly'
			elif 'monthly' in filename:
				sourced = 'monthly'
			elif 'yearly' in filename:
				sourced = 'yearly'
			
			try:
				file_name_int = int(file_name)
			except: 
				print('Invalid filename: ')
				print(filename)
				print('')
				err = 1
			
			try:
				ET.parse(filename)
			except ET.ParseError:
				print('Parse error - Non XML file? at: ')
				print(filename)
				print('')
				err = 1
				#print(filename)
			
			if err == 1:
				err = 0
				continue
			else:
				tree = ET.parse(filename)
				root = tree.getroot()
				print('Processing: '+filename)
				print('')
				for elem in root:
					#print(elem.tag)
					usagetype = elem.tag
					#print("Usage type: "+usagetype)
					if usagetype == 'packages':
						for subelem in elem:
							#print(subelem.attrib)
							fullatti_str = json.dumps(subelem.attrib)
							#print(subelem.attrib['lastTimeActive'])
							time1 = subelem.attrib['lastTimeActive']
							time1 = int(time1)
							if time1 < 0:
								finalt = abs(time1)
							else:
								finalt = file_name_int + time1
							#print('final time: ')
							#print(finalt)
							#print(subelem.attrib['package'])
							pkg = (subelem.attrib['package'])
							#print(subelem.attrib['timeActive'])
							tac = (subelem.attrib['timeActive'])
							#print(subelem.attrib['lastEvent'])
							#insert in database
							cursor = db.cursor()
							datainsert = (usagetype, finalt, tac, pkg, '' , '' , sourced, fullatti_str,)
							#print(datainsert)
							cursor.execute('INSERT INTO data (usage_type, lastime, timeactive, package, types, classs, source, fullatt)  VALUES(?,?,?,?,?,?,?,?)', datainsert)
							db.commit()
					
					elif usagetype == 'configurations':
						for subelem in elem:
							fullatti_str = json.dumps(subelem.attrib)
							#print(subelem.attrib['lastTimeActive'])
							time1 = subelem.attrib['lastTimeActive']
							time1 = int(time1)
							if time1 < 0:
								finalt = abs(time1)
							else:
								finalt = file_name_int + time1
							#print('final time: ')
							#print(finalt)
							#print(subelem.attrib['timeActive'])
							tac = (subelem.attrib['timeActive'])
							#print(subelem.attrib)
							#insert in database
							cursor = db.cursor()
							datainsert = (usagetype, finalt, tac, '' , '' , '' , sourced, fullatti_str,)
							cursor.execute('INSERT INTO data (usage_type, lastime, timeactive, package, types, classs, source, fullatt)  VALUES(?,?,?,?,?,?,?,?)', datainsert)
							db.commit()
			
					elif usagetype == 'event-log':
						for subelem in elem:
							#print(subelem.attrib['time'])
							time1 = subelem.attrib['time']
							time1 = int(time1)
							if time1 < 0:
								finalt = abs(time1)
							else:
								finalt = file_name_int + time1
							
							#time1 = subelem.attrib['time']
							#finalt = file_name_int + int(time1)
							#print('final time: ')
							#print(finalt)
							#print(subelem.attrib['package'])
							pkg = (subelem.attrib['package'])
							#print(subelem.attrib['type'])
							tipes = (subelem.attrib['type'])
							#print(subelem.attrib)
							fullatti_str = json.dumps(subelem.attrib)
							#add variable for type conversion from number to text explanation
							#print(subelem.attrib['fs'])
							#classy = subelem.attrib['class']
							if 'class' in subelem.attrib:
								classy = subelem.attrib['class']
								cursor = db.cursor()
								datainsert = (usagetype, finalt, '' , pkg , tipes , classy , sourced, fullatti_str,)
								cursor.execute('INSERT INTO data (usage_type, lastime, timeactive, package, types, classs, source, fullatt)  VALUES(?,?,?,?,?,?,?,?)', datainsert)
								db.commit()
							else:
							#insert in database
								cursor = db.cursor()
								datainsert = (usagetype, finalt, '' , pkg , tipes , '' , sourced, fullatti_str,)
								cursor.execute('INSERT INTO data (usage_type, lastime, timeactive, package, types, classs, source, fullatt)  VALUES(?,?,?,?,?,?,?,?)', datainsert)
								db.commit()

print("Calling Apollo for database processing...")
print("Artemis is done. Good bye")
p = subprocess.run(['python', 'apollo.py', '-o',
format, '-p', 'yolo', '-v', 'yolo',
mod_dir, data_dir])

