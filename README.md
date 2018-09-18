# PointCapacity

## Program that uses insightprodDB to graph noms for user-specified points
*By Dominic Eggerman*\

`PointCapacity` is a program which will access Genscape's insightprod database and plot nominations for user-selected points.
The program can be launched from command line with `python pointcap.py`.

#### How To:
The program can be launched normally from the command line with `python pointCap.py`.\
Note that it is **important** to enter dates in MM-DD-YYYY (with dashes) format and not MM/DD/YYYY or other formats.\
Fast logins can be achieved by creating a `creds.txt` file in the following format:
```
username: XXXXX
password: YYYYY
```
Optional command-line arguments:

| Short Option | Alt Option | Description | Default |
|---|---|---|---|
| `-c` | `--creds` | Uses the login credentials stored in `creds.txt` | True |
| `-l` | `--last` | Uses the last query stored in `query.txt` | False |
| `-o` | `--opcap` | Does not graph the operational capacity of a point | False |
| `-s` | `--save` | Saves the data used to graph into a .csv file | False |

Note that "Default" is the value that is used if *the option is not specified*

#### Using saved queries and query.txt:
- Start date is coded as MM-DD-YYYY.
- End date can be a date, or "today", which will generate the current date.
- Pipeline ID is the id of a particular pipeline.
- Point names are the list of points / a point that you want to graph nominations for.  Multiple points can be comma separated: `point_names: wagoner east,wagoner west,ramapo AGT`

The names will be search for using an ILIKE '%XXXXX%' SQL query (or id = YYYY if you entered a location id), so entering "Wagoner", will search for locations with with strings that match that entry.  You can select one or multiple of the entries once the command has run.

#### Using the inferface:
Running `pointCap.py` from the command line will utilize user-input commands to build a query and graph nominations for certain points.  Without a `creds.txt` file, you will be prompted for login credentials.

#### Saving a query:
When creating a new query, after the graphing window has been closed, a prompt will appear to save the query (dates, pipeline, points).  This will save to `query.txt` for later use. 