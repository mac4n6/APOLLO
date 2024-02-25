# Apple Pattern of Life Lazy Output'er (APOLLO)

# v1.4
* Gather database files on macOS and jailbroken iOS devices, gather_macos and gather_ios (IP/Port required)
* Ability to ignore certain directories with --ignore
* Improved CSV Output
* JSON Output within SQLite Output

# v1.3
* License Updated

## Dependencies
* [SimpleKML](https://simplekml.readthedocs.io) - Copy the `simplekml` directory to the directory where apollo.py is being run from. [Download here](https://pypi.org/project/simplekml/#files)

### To install `simplekml` dependencies on macOS:
* `sudo easy_install pip`
* `pip3 install simplekml`

## Usage
`python3 apollo.py {gather_macos, gather_ios} <modules directory> <data directory> --ignore <dir>`

`python3 apollo.py extract -o {csv, sql, sql_json} -p {apple, android, windows, yolo} -v {8,9,10,11,12,13,14,10.13,10.14,10.15,10.16,and9,and10,and11,win10_1803,win10_1809,win10_1903,win10_1909,yolo} -k <modules directory> <data directory>`

## Output Options (-o)
* `csv` - CSV (Tab Delimited)
* `sql` - SQLite Database (Output in square brackets)
* `sql_json` - SQLite Database (Output in JSON)

## KMZ Output(-k)
* Outputs location coordinates to separate files based on module.
* [iOS Location Mapping with APOLLO - I Know Where You Were Today, Yesterday, Last Month, and Years Ago!](https://www.mac4n6.com/blog/2019/8/21/i-know-where-you-were-today-yesterday-last-month-and-many-years-ago)
* [iOS Location Mapping with APOLLO – Part 2: Cellular and Wi-Fi Data (locationd)](https://www.mac4n6.com/blog/2019/8/25/ios-location-mapping-with-apollo-part-2-cellular-and-wi-fi-data-locationd)

## Platform Options (-p)
* `apple`
* `android`
* `windows`
* `yolo` - Just parse whatever. Will use all available queries. Be careful with this option as you may get redundant data. 

## Version Options (-v)
* iOS `8`, `9`, `10`, `11`, `12`,`13`,`14`
* macOS `10.13`, `10.14`, `10.15`,`10.16` (macOS 11)
* Android `and8`, `and9`, `and10`
* Windows 10 `win10_1803`, `win10_1809`, `win10_1903`, `win10_1909`
* `yolo` - Just parse whatever. Will use all available queries. Be careful with this option as you may get redundant data.

## Getting Errors? Try This (Windows users, use equivalent commands)

* Pro Tip: The 'gather' functions chmod/chown the files to ensure they are accessible.

You may see that APOLLO reports back "0 databases" found when executed, most likely from CurrentPowerlog.PLSQL and locationd modules. Two common directories with databases that cause problems due to permissions (depends on how files were extracted from device):
* `/private/var/root/Library/Caches/locationd/`
* `/private/var/containers/Shared/SystemGroup/[GUID]/Library/BatteryLife`
### Fix Permissions:
* `chmod -R 755 /private/var/containers/Shared/SystemGroup/[GUID_for BatteryLife Data]/`
* `chmod -R 755 /private/var/root`

### Still not working?
* Check database permissions - Use `chmod` to give some databases with "all blank" permissions some sort of permission. (Happens with many types of physical-logical extractions.)
* Check database ownership - Use `chown` to take ownership of the files.

## To Do List
* Powerlog Gzip Files
* Database Coalescing
* Visualizations
* Accept Zip file input
* Output Formats (JSON?)
* Modules:
  * Additional Health modules 
  * Additional Native App Specific Modules 

## Thank You!
* Thanks to Sam Alptekin of @sjc_CyberCrimes, script is much, much faster than original.
* Thanks to @AlexisBrignoni for Python 3 support.

## References
* Search APOLLO on mac4n6.com
