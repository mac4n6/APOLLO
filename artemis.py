import argparse
from argparse import RawTextHelpFormatter
from six.moves.configparser import RawConfigParser
import xml.etree.ElementTree as ET  
import glob, os, sqlite3, os, sys, re, json, subprocess
from datetime import datetime, timezone

parser = argparse.ArgumentParser(description="\
	Automated Review Timeline Events Module Integrated Solution\
	\n Process selected non-SQLite data sources in Android and iOS for Apollo.py ingestion \n\n Supporting: \n -Android XML Usagestats \n -iOS Mobile Installation logs"
	
, prog='artemis.py'
, formatter_class=RawTextHelpFormatter)
parser.add_argument('-o', choices=['sql','csv'], required=True, action="store", help="Output: sql=SQLite or csv=CSV (required)")
parser.add_argument('-p', choices=['ios','yolo','android'], required=True, action="store", help="Platform: ios=iOS [supported] or android=Android [supported] (required).")
parser.add_argument('-v', choices=['8','9','10','11','12','yolo','android'], required=True, action="store",help="iOS Version or Android (required).")
parser.add_argument('modules_directory',help="Path to Module Directory")
parser.add_argument('data_dir_to_analyze',help="Path to Data Directory. It can be full file system dump or directory of extracted databases, it is recursive.")

args = parser.parse_args()

format = args.o
mod_dir = args.modules_directory
data_dir = args.data_dir_to_analyze
platform = args.p
version = args.v

print("\n--------------------------------------------------------------------------------------")
print("Artemis: Automated Review Timeline Events Module Integrated Solution")
print("Android objective: Parse Android Usagestats XML to SQLite + Android specific Apollo modules")
print("iOS objective: Parse iOS Mobile Installation logs to SQLite + iOS specific Apollo module")
print("By: Alexis Brignoni | @AlexisBrignoni | abrignoni.com")
print("Data Directory: " + data_dir)
print("Modules Directory: " + mod_dir)	
print("--------------------------------------------------------------------------------------")
print("All credit goes to Sarah Edwards for her Apollo framework which Artemis leverages")
print("Apollo Author: Sarah Edwards | @iamevltwin | mac4n6.com")

#Month to numeric with leading zero when month < 10 function
#Function call: month = month_converter(month)
def month_converter(month):
	months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
	month = months.index(month) + 1
	if (month < 10):
		month = f"{month:02d}"
	return month

#Day with leading zero if day < 10 function
#Functtion call: day = day_converter(day)
def day_converter(day):	
	day = int(day)
	if (day < 10):
		day = f"{day:02d}"
	return day

#create function for usagestats
def parse_usagestat():

	pathfound = 0

	for root, dirs, filenames in os.walk(data_dir):
			for f in dirs:
				if f == "usagestats":
					pathfound = os.path.join(root, f)
					print(pathfound)

	if pathfound == 0:
		print("No UsageStats XML directory located")
	else:
		print("--------------------------------------------------------------------------------------")
		print("Locating Usagestats XML files + processing")
		print("Please wait...") 
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


#create function for mobile installation logs
def parse_mobile_installation_logs():

	#initialize counters
	counter = 0
	filescounter = 0
	goto = 0

	#Create sqlite databases
	db = sqlite3.connect(data_dir+r'\mib.db')

	cursor = db.cursor()

	#Create table fileds for destroyed, installed, moved and made identifiers.

	cursor.execute('''

		CREATE TABLE dimm(time_stamp text, action TEXT, bundle_id TEXT, 

						  path TEXT)

	''')

	db.commit()
	print("--------------------------------------------------------------------------------------")
	print("Locating Mobile Installation Logs + processing")
	print("Please wait...") 

	for root, dirs, filenames in os.walk(data_dir):
		for f in filenames: 
			if f.endswith("mobile_installation.log.0"):
				goto = 1
				log = (os.path.join(root, f))
			if f.endswith("mobile_installation.log.1"):
				goto = 1
				log = (os.path.join(root, f))
			
			if goto == 1:
				goto = 0
				file = open(log, 'r', encoding='utf8' )
				filescounter = filescounter + 1
				for line in file:
					counter = counter+1
					matchObj = re.search( r"(Install Successful for)", line) #Regex for installed applications
					if matchObj:
						actiondesc = "Install successful"
						#print(actiondesc)
						matchObj = re.search( r"(?<=for \()(.*)(?=\))", line) #Regex for bundle id
						if matchObj:
							bundleid = matchObj.group(1)
							#print ("Bundle ID: ", bundleid )
					
						matchObj = re.search( r"(?<=^)(.*)(?= \[)", line) #Regex for timestamp
						if matchObj:
							timestamp = matchObj.group(1)
							weekday, month, day, time, year = (str.split(timestamp))
							day = day_converter(day)
							month = month_converter(month)
							inserttime = str(year)+ '-'+ str(month) + '-' + str(day) + ' ' + str(time)
							#print(inserttime)
							#print(month)
							#print(day)
							#print(year)
							#print(time)
							#print ("Timestamp: ", timestamp)
						
						#print(inserttime, actiondesc, bundleid)
						
						#insert to database
						cursor = db.cursor()
						datainsert = (inserttime, actiondesc, bundleid, '' ,)
						cursor.execute('INSERT INTO dimm (time_stamp, action, bundle_id, path)  VALUES(?,?,?,?)', datainsert)
						db.commit()
						
						#print()
							
					
					matchObj = re.search( r"(Destroying container with identifier)", line) #Regex for destroyed containers
					if matchObj:
						actiondesc = "Destroying container"
						#print(actiondesc)
						#print("Destroyed containers:")
						matchObj = re.search( r"(?<=identifier )(.*)(?= at )", line) #Regex for bundle id
						if matchObj:
							bundleid = matchObj.group(1)
							#print ("Bundle ID: ", bundleid )
					
						matchObj = re.search( r"(?<=^)(.*)(?= \[)", line) #Regex for timestamp
						if matchObj:
							timestamp = matchObj.group(1)
							weekday, month, day, time, year = (str.split(timestamp))
							day = day_converter(day)
							month = month_converter(month)
							inserttime = str(year)+ '-'+ str(month) + '-' + str(day) + ' ' + str(time)
							#print(inserttime)
							#print(month)
							#print(day)
							#print(year)
							#print(time)
							#print ("Timestamp: ", timestamp)
						
						matchObj = re.search( r"(?<= at )(.*)(?=$)", line) #Regex for path
						if matchObj:
							path = matchObj.group(1)
							#print ("Path: ", matchObj.group(1))
						
					
						#print(inserttime, actiondesc, bundleid, path)			
						
						#insert to database
						cursor = db.cursor()
						datainsert = (inserttime, actiondesc, bundleid, path ,)
						cursor.execute('INSERT INTO dimm (time_stamp, action, bundle_id, path)  VALUES(?,?,?,?)', datainsert)
						db.commit()
						
						#print()
						

					matchObj = re.search( r"(Data container for)", line) #Regex Moved data containers
					if matchObj:
						actiondesc = "Data container moved"
						#print(actiondesc)
						#print("Data container moved:")
						matchObj = re.search( r"(?<=for )(.*)(?= is now )", line) #Regex for bundle id
						if matchObj:
							bundleid = matchObj.group(1)
							#print ("Bundle ID: ", bundleid )
					
						matchObj = re.search( r"(?<=^)(.*)(?= \[)", line) #Regex for timestamp
						if matchObj:
							timestamp = matchObj.group(1)
							weekday, month, day, time, year = (str.split(timestamp))
							day = day_converter(day)
							month = month_converter(month)
							inserttime = str(year)+ '-'+ str(month) + '-' + str(day) + ' ' + str(time)
							#print(inserttime)
							#print(month)
							#print(day)
							#print(year)
							#print(time)
							#print ("Timestamp: ", timestamp)
						
						matchObj = re.search( r"(?<= at )(.*)(?=$)", line) #Regex for path
						if matchObj:
							path = matchObj.group(1)
							#print ("Path: ", matchObj.group(1))
							
						#print(inserttime, actiondesc, bundleid, path)			
						
						#insert to database
						cursor = db.cursor()
						datainsert = (inserttime, actiondesc, bundleid, path ,)
						cursor.execute('INSERT INTO dimm (time_stamp, action, bundle_id, path)  VALUES(?,?,?,?)', datainsert)
						db.commit()
						
						#print()
						
					matchObj = re.search( r"(Made container live for)", line) #Regex for made container
					if matchObj:
						actiondesc = "Made container live"
						#print(actiondesc)
						#print("Made container:")
						matchObj = re.search( r"(?<=for )(.*)(?= at)", line) #Regex for bundle id
						if matchObj:
							bundleid = matchObj.group(1)
							#print ("Bundle ID: ", bundleid )
					
						matchObj = re.search( r"(?<=^)(.*)(?= \[)", line) #Regex for timestamp
						if matchObj:
							timestamp = matchObj.group(1)
							weekday, month, day, time, year = (str.split(timestamp))
							day = day_converter(day)
							month = month_converter(month)
							inserttime = str(year)+ '-'+ str(month) + '-' + str(day) + ' ' + str(time)
							#print(inserttime)
							#print(month)
							#print(day)
							#print(year)
							#print(time)
							#print ("Timestamp: ", timestamp)
						
						matchObj = re.search( r"(?<= at )(.*)(?=$)", line) #Regex for path
						if matchObj:
							path = matchObj.group(1)
							#print ("Path: ", matchObj.group(1))
						#print(inserttime, actiondesc, bundleid, path)			
						
						#insert to database
						cursor = db.cursor()
						datainsert = (inserttime, actiondesc, bundleid, path ,)
						cursor.execute('INSERT INTO dimm (time_stamp, action, bundle_id, path)  VALUES(?,?,?,?)', datainsert)
						db.commit()
						
					matchObj = re.search( r"(Uninstalling identifier )", line) #Regex for made container
					if matchObj:
						actiondesc = "Uninstalling identifier"
						#print(actiondesc)
						#print("Uninstalling identifier")
						matchObj = re.search( r"(?<=Uninstalling identifier )(.*)", line) #Regex for bundle id
						if matchObj:
							bundleid = matchObj.group(1)
							#print ("Bundle ID: ", bundleid )
					
						matchObj = re.search( r"(?<=^)(.*)(?= \[)", line) #Regex for timestamp
						if matchObj:
							timestamp = matchObj.group(1)
							weekday, month, day, time, year = (str.split(timestamp))
							day = day_converter(day)
							month = month_converter(month)
							inserttime = str(year)+ '-'+ str(month) + '-' + str(day) + ' ' + str(time)
							#print(inserttime)
							#print(month)
							#print(day)
							#print(year)
							#print(time)
							#print ("Timestamp: ", timestamp)
						
						#insert to database
						cursor = db.cursor()
						datainsert = (inserttime, actiondesc, bundleid, '' ,)
						cursor.execute('INSERT INTO dimm (time_stamp, action, bundle_id, path)  VALUES(?,?,?,?)', datainsert)
						db.commit()

					matchObj = re.search( r"(main: Reboot detected)", line) #Regex for reboots
					if matchObj:
						actiondesc = "Reboot detected"
						#print(actiondesc)		
						matchObj = re.search( r"(?<=^)(.*)(?= \[)", line) #Regex for timestamp
						if matchObj:
							timestamp = matchObj.group(1)
							weekday, month, day, time, year = (str.split(timestamp))
							day = day_converter(day)
							month = month_converter(month)
							inserttime = str(year)+ '-'+ str(month) + '-' + str(day) + ' ' + str(time)
							#print(inserttime)
							#print(month)
							#print(day)
							#print(year)
							#print(time)
							#print ("Timestamp: ", timestamp)
						
						#insert to database
						cursor = db.cursor()
						datainsert = (inserttime, actiondesc, '', '' ,)
						cursor.execute('INSERT INTO dimm (time_stamp, action, bundle_id, path)  VALUES(?,?,?,?)', datainsert)
						db.commit()			
						
					matchObj = re.search( r"(Attempting Delta patch update of )", line) #Regex for Delta patch
					if matchObj:
						actiondesc = "Attempting Delta patch"
						#print(actiondesc)
						#print("Made container:")
						matchObj = re.search( r"(?<=Attempting Delta patch update of )(.*)(?= from)", line) #Regex for bundle id
						if matchObj:
							bundleid = matchObj.group(1)
							#print ("Bundle ID: ", bundleid )
					
						matchObj = re.search( r"(?<=^)(.*)(?= \[)", line) #Regex for timestamp
						if matchObj:
							timestamp = matchObj.group(1)
							weekday, month, day, time, year = (str.split(timestamp))
							day = day_converter(day)
							month = month_converter(month)
							inserttime = str(year)+ '-'+ str(month) + '-' + str(day) + ' ' + str(time)
							#print(inserttime)
							#print(month)
							#print(day)
							#print(year)
							#print(time)
							#print ("Timestamp: ", timestamp)
						
						matchObj = re.search( r"(?<= from )(.*)", line) #Regex for path
						if matchObj:
							path = matchObj.group(1)
							#print ("Path: ", matchObj.group(1))
						#print(inserttime, actiondesc, bundleid, path)			
						
						#insert to database
						cursor = db.cursor()
						datainsert = (inserttime, actiondesc, bundleid, path ,)
						cursor.execute('INSERT INTO dimm (time_stamp, action, bundle_id, path)  VALUES(?,?,?,?)', datainsert)
						db.commit()

	print ('Logs processed: ', filescounter)
	print ('Lines processed: ', counter)

#create function to pass processing to apollo



if platform == "android":
	parse_usagestat()
	
if platform == "ios":
	parse_mobile_installation_logs()
	
if platform == "yolo":
	parse_usagestat()
	parse_mobile_installation_logs()
	
print("--------------------------------------------------------------------------------------")
print("Calling Apollo for database processing...")
print("Artemis is done. Good bye")
#Poner un try si apollo no esta para que de un error
p = subprocess.run(['python', 'apollo.py', '-o', format, '-p', platform, '-v', version, mod_dir, data_dir])
