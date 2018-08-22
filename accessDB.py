# By Dominic Eggerman

# Connect to database
def connect(usr, pswrd):
    # Establish connection with username and password
    conn = psycopg2.connect(dbname="insightprod", user=usr, password=pswrd, host="insightproddb")
    print("Successfully connected to database...")
    return conn

# Find location id's from names
def getLocationIDs(conn, point, pipe_id):
    # Create statement to select 
    statement = """SELECT DISTINCT loc.name, loc.id
                    FROM maintenance.location AS loc
                    WHERE loc.name ILIKE {0}
                    AND loc.pipeline_id = {1}
                    ORDER BY loc.name;
    """.format("'%"+point+"%'", pipe_id)
    # Read to dataframe
    print("Querying database for points matching name ILIKE '%{0}%'...".format(point))
    df = pd.read_sql(statement, conn)
    points = df["name"].values
    loc_ids = df["id"].values

    # Decisions
    if len(points) == 0:
        print("No points found matching that name.")
        return -1
    elif len(points) == 1:
        return loc_ids[0]
    else:
        point_select = ["{0}: {1}".format(ind+1,p) for ind, p in enumerate(points)]
        print(point_select)
        choice = int(input("Select a point from the list by entering the corresponding number: "))
        return loc_ids[choice-1]

# Query scheduled and operational caps for date range
def getCapacityData(conn, start_date, pipe_id, location_id):
    # Statement to select scheduled and operational caps for date range
    statement = """SELECT eod.gas_day, eod.scheduled_cap, eod.operational_cap  
                    FROM analysts.location_role_eod_history_v AS eod
                    INNER JOIN maintenance.location_role AS lr ON eod.location_role_id = lr.id
                    INNER JOIN maintenance.location AS loc ON lr.location_id = loc.id
                    WHERE eod.gas_day >= {0}
                    AND loc.pipeline_id = {1}
                    AND loc.id ILIKE {2}
                    ORDER BY eod.gas_day;
    """.format(start_date, pipe_id, location_id)

    # Read to dataframe and return
    print("Querying database for opcap data...")
    df = pd.read_sql(statement, conn)
    return df

# Run
if __name__ == "__main__":
    # Imports
    import getpass
    import psycopg2
    import pandas as pd

    # User entries
    # username = input('Enter username: ')
    # password = getpass.getpass('Enter password: ')
    # date = input("Enter start date: ")
    # pipeline_id = input("Enter pipeline id: ")
    # point_name = input("Enter point name: ")
    username = "deggerman"
    password = "GS8j8gvh"
    date = "'08/01/2018'"
    pipeline_id = 396
    point_name = "Wagoner East"

    # Connect, query, and print df
    connection = connect(username, password)
    loc_id = getLocationIDs(connection, point_name, pipeline_id)
    df = getCapacityData(connection, date, pipeline_id, loc_id)
    print(df)

    # Save loc_id and date range
