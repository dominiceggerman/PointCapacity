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

### Rundown of functions

- Functions in `pointCap`
    - `getDateRange()` asks the user to input a start and end date.  Entering nothing will create a range from today to the date 30 days ago.
    - `checkDF(dataframe)` Subtracts deliveries from receipts if a location has both roles.
        - `dataframe` is an individual dataframe.
    - `plotPoints(df_list, opcap)` plots nominations data for all of the points in df_list.
        - `df_list` is the list of pandas dataframes containing nominations data, one for each location.
        - `opcap` is a boolean which will keep / drop the operational capcity column.
- Functions in `accessDB`
    - `connect(usr, pswrd)` connects to the insightprod database.  Returns that connection to be used by other functions.
        - `usr` is a username.
        - `pswrd` is a password.
    - `getLocationIDs(conn, point, pipe_id)` obtains the location IDs of points by matching them on a name.  Returns the database name and the location ID.  The additonal index in the returned list handles multiple points matching the same name string.
        - `conn` is the connection to the database.
        - `point` is the name (string) of a location.
        - `pipe_id` is the ID of the pipeline.
    - `getInterconnectIDs(conn, pipe_id)` obtains and returns the all of the location IDs that match interconnects (intra / inter) on a particular pipeline.
        - `conn` is the connection to the database.
        - `pipe_id` is the ID of the pipeline.
    - `getCapacityData(conn, dates, pipe_id, location_id)` obtains nominations data for a particular point and returns a dataframe with the columns [date, scheduled, operational, role_id].
        - `conn` is the connection to the database.
        - `dates` is the range of dates to get nominations data for.
        - `pipe_id` is the ID of the pipeline.
        - `location_id` is the numeric ID of the location.