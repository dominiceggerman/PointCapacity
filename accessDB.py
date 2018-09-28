# By Dominic Eggerman
# Imports
import getpass
import psycopg2
import pandas as pd

# Connect to database
def connect(usr, pswrd):
    # Establish connection with username and password
    conn = psycopg2.connect(dbname="insightprod", user=usr, password=pswrd, host="insightproddb")
    print("Successfully connected to database...")
    return conn

# Find location id's from names
def getLocationIDs(conn, point, pipe_id):
    # Create statement to select
    try:
        point = int(point)
        statement = """SELECT DISTINCT loc.name, loc.id
                        FROM maintenance.location AS loc
                        WHERE loc.id ILIKE {0}
                        AND loc.pipeline_id = {1}
                        ORDER BY loc.name;
                    """.format(point, pipe_id)
        print("Querying database for points matching id = {0}".format(point))
    except ValueError:
        statement = """SELECT DISTINCT loc.name, loc.id
                        FROM maintenance.location AS loc
                        WHERE loc.name ILIKE {0}
                        AND loc.pipeline_id = {1}
                        ORDER BY loc.name;
                    """.format("'%"+point+"%'", pipe_id)
        print("Querying database for points matching name ILIKE '%{0}%'...".format(point))
    # Read to dataframe
    df = pd.read_sql(statement, conn)
    points = df["name"].values
    loc_ids = df["id"].values

    # Decisions to return loc_id and name
    if len(points) == 0:
        print("No points found matching that name...")
        return -1
    elif len(points) == 1:
        return [loc_ids[0], points[0]]
    else:
        # Select from multiple points
        point_select = ["{0}: {1}".format(ind+1,p) for ind, p in enumerate(points)]
        print(point_select)
        choice = int(input("Select a point from the list by entering the corresponding number: "))
        return [loc_ids[choice-1], points[choice-1]]


# Get location ID's of interconnects to other pipes
def getInterconnectIDs(conn, pipe_id):
    # Statement to select
    statement = """SELECT DISTINCT loc.name, loc.id
                    FROM maintenance.location AS loc
                    WHERE loc.facility_id IN (11, 13, 14)
                    AND loc.pipeline_id = {0}
                    ORDER BY loc.name;
                """.format(pipe_id)
    print("Querying database for interconnects on pipe_id: {0}...".format(pipe_id))
    # Read to dataframe
    df = pd.read_sql(statement, conn)
    points = df["name"].values
    loc_ids = df["id"].values

    # Decisions to return loc_id and name
    if len(points) == 0:
        print("No interconnects with other pipes found...")
        return -1
    else:
        # Get all the points
        return [loc_ids, points]

# Query scheduled and operational caps for date range
def getCapacityData(conn, dates, pipe_id, location_id):
    # Statement to select scheduled and operational caps for date range
    statement = """SELECT eod.gas_day, eod.scheduled_cap, eod.operational_cap, lr.role_id
                    FROM analysts.location_role_eod_history_v AS eod
                    INNER JOIN maintenance.location_role AS lr ON eod.location_role_id = lr.id
                    INNER JOIN maintenance.location AS loc ON lr.location_id = loc.id
                    WHERE eod.gas_day BETWEEN {0} AND {1}
                    AND loc.pipeline_id = {2}
                    AND loc.id = {3}
                    ORDER BY eod.gas_day, lr.role_id;
                """.format("'"+dates[0]+"'", "'"+dates[1]+"'", pipe_id, location_id)

    # Read to dataframe and return
    print("Querying database for pointcap data...")
    df = pd.read_sql(statement, conn)
    return df

# Run
if __name__ == "__main__":
    # User entries
    username = input('Enter username: ')
    password = getpass.getpass('Enter password: ')
    date = input("Enter start date: ")
    pipeline_id = input("Enter pipeline id: ")
    point_name = input("Enter point name: ")

    # Connect, query, and print df
    connection = connect(username, password)
    loc_id = getLocationIDs(connection, point_name, pipeline_id)
    df = getCapacityData(connection, date, pipeline_id, loc_id)
    print(df)

    # Close connection
    print("Closing connection to database...")
    connection.close()
