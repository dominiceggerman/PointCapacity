# By Dominic Eggerman
# Imports
import os
import getpass
import psycopg2
import pandas as pd
import numpy as np
import datetime
import argparse
# Import pointcap modules
import pointCap
import accessDB as access
import readfile

def xDayAvg():
    pass
    

# Run
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Below is a list of optional arguements with descriptions. Please refer to Readme for full documentation and examples...")
    parser.add_argument("-c", "--creds", help="Access creds from creds.txt", action="store_true")
    parser.add_argument("-l", "--last", help="Use last query", action="store_true")
    parser.add_argument("-o", "--opcap", help="Remove operational cap datapoints", action="store_true")
    options = parser.parse_args()

    # Get user creds
    if os.path.exists("creds.txt") or options.creds:
        credentials = readfile.readFile("creds.txt")
        username, password = credentials[0], credentials[1]
    else:
        username = input('Enter username: ')
        password = getpass.getpass('Enter password: ')

    # Connect
    try:
        connection = access.connect(username, password)

        # Get user query or use last query
        if options.last:
            last_query = readfile.readFile("query.txt")
            if last_query[1] == "today":
                last_query[1] = str(datetime.datetime.now().strftime("%m-%d-%Y"))
            date_range = [last_query[0], last_query[1]]
            pipeline_id = last_query[2]
            point_names = last_query[3].split(",")
        else:
            # Get start date, pipeline id, and point names
            date_range = pointCap.getDateRange()
            pipeline_id = int(input("Enter pipeline id: "))
            point_names = input("Enter point name (multiple points should be comma separated): ").split(",")

        # If spaces exist between commas of user query
        if len(point_names) > 1:
            for ind, point in enumerate(point_names):
                if point[0] == " ":
                    # Remove leading space from point name string
                    point_names[ind] = point[1:]
        
        # Get point averages
        for ind, p in enumerate(point_names):
            # Get location id and true name
            location_data = access.getLocationIDs(connection, p, pipeline_id)
            # Raise error if returned no points
            if location_data == -1:
                raise(ValueError)
            loc_id, new_name = location_data[0], location_data[1]
            point_names[ind] = new_name
            # Get point capacity data
            df = access.getCapacityData(connection, date_range, pipeline_id, loc_id)
            # Check if point has receipts and deliveries
            df = pointCap.checkDF(df)
            # Convert to MMcf/d
            new_col = df["scheduled_cap"] / 1030
            df = df.assign(scheduled_cap = lambda x: x["scheduled_cap"] / 1030)
            df = df.assign(operational_cap = lambda x: x["operational_cap"] / 1030)
            point_avg = np.average(df["scheduled_cap"].values)
            print("Point name: {0}, Average Flow: {1} MMcf/d".format(new_name, point_avg))

        # Close connection
        print("Closing connection to database...")
        connection.close()
    
    # Exception to handle errors
    except (IndexError, ValueError, TypeError, psycopg2.Error):
        print("Error encountered during dataase operations, closing connection...")
        connection.close()