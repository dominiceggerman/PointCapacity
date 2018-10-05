# PointCapacity

## Program that uses insightprodDB to obtain nominations data for user-specified points

*By Dominic Eggerman*

`PointCapacity` is a program which will access Genscape's insightprod database and obtain nominations for user-selected points.
The program can be launched from the command line.

### How To - `pointCap`

`pointCap` will obtain and plot nominations data for a point or group of points on a specified pipeline.  The program can be launched normally from the command line with `python pointCap.py`, and the user prompts will guide you through a query.  Note that it is **important** to enter dates in MM-DD-YYYY (with dashes) format and not MM/DD/YYYY or other formats.  Database credentials can be entered automatically by creating a `creds.txt` file in the following format:

```

username: XXXXX
password: YYYYY

```

`pointCap` will also allow users to save their new query (to `query.txt`) and/or to save the data to a csv.  `pointCap` also has additional optional command-line arguments.

| Short Option | Alt Option | Description | Default |
|---|---|---|---|
| `-c` | `--creds` | Uses the login credentials stored in `creds.txt` | True |
| `-l` | `--last` | Uses the last query stored in `query.txt` | False |
| `-o` | `--opcap` | Does not graph the operational capacity of a point | False |

Note that "Default" is the value that is used if *the option is not specified*

Example use: `python pointCap.py -l -o`.  This will use the query stored in `query.txt` and not graph the operational capacity for the desired points.

### How To - `pointFlowAverage`

`pointFlowAverage` utilizes similar logic to `pointCap` to obtain statistical information (average, median, etc.) of location nominations data.  The program is launched from the command line with `python pointFlowAverage.py`, and has similar user prompts to `pointCap`.

| Short Option | Alt Option | Description | Default |
|---|---|---|---|
| `-c` | `--creds` | Uses the login credentials stored in `creds.txt` | True |
| `-l` | `--last` | Uses the last query stored in `query.txt` | False |
| `-cf` | `--mmcf` | Displays data in units of MMcf rather than MMbtu | False |

### How To - `interconnectCap`

`interconnectCap` uses a range of dates and a pipeline id to obtain all of the nominations for intrastate and interstate interconnects on a pipeline.  It will then save the data to a csv for viewing.  The filters for average/max flow over period can be changed as well.

| Short Option | Alt Option | Description | Default |
|---|---|---|---|
| `-c` | `--creds` | Uses the login credentials stored in `creds.txt` | True |
| `-btu` | `--mmbtu` | Display data in units of MMbtu rather than MMcf | False |

### Using saved queries and query.txt

- Start date is coded as MM-DD-YYYY.
- End date can be a date or "today", which will generate the current date.
- Pipeline ID is the id of a particular pipeline.
- Point names are the list of points / a point that you want to graph nominations for.  Multiple points can be comma separated: `point_names: wagoner east,wagoner west,ramapo AGT`.  You can also use location ID's.

String names will be searched for using an ILIKE '%XXXXX%' SQL query (or id = XXXXX if you entered a location id), so entering "Wagoner", will search for locations with with strings that match that entry.  You can select one or multiple of the entries once the command has run.