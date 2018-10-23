# By Dominic Eggerman
# Imports
import os
import getpass
import psycopg2
import pandas as pd
import numpy as np
import datetime
import argparse
# Import pointCap modules
import pointCap
import accessDB as access
import readfile 


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Below is a list of optional arguements with descriptions. Please refer to Readme for full documentation and examples...")
    parser.add_argument("-c", "--creds", help="Access creds from creds.txt", action="store_true")
    parser.add_argument("-l", "--last", help="Use last query", action="store_true")
    parser.add_argument("-cf", "--mmcf", help="Transform to MMcf", action="store_true")
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
            point_names = input("Enter point name or location id (multiple points should be comma separated): ").split(",")

        # If spaces exist between commas of user query
        if len(point_names) > 1:
            for ind, point in enumerate(point_names):
                if point[0] == " ":
                    # Remove leading space from point name string
                    point_names[ind] = point[1:]
        
        # Final list of point names
        final_point_names = []
        # List of location ID's
        loc_id_list = []

        # First loop to get all of the point names and loc_ids. This also enables in-query addition of new points
        for ind, p in enumerate(point_names):
            # Set marker for multiple points
            another_point = True
            # Get location id and true name
            while another_point:
                # Get location id and true name
                location_data = access.getLocationIDs(connection, p, pipeline_id)
                # Raise error if returned no points
                if None in location_data:
                    print("Could not find that point in the database...")
                    continue
                elif location_data[2] is True:
                    # Add to location name and ID
                    loc_id_list.append(location_data[0])
                    final_point_names.append(location_data[1])
                    # Ask user if he/she wants to pick another point from the query
                    more_points = input("Want to add another point from this list? (y/n): ")
                    if more_points not in ["y", "yes"]:
                        another_point = False
                else:
                    loc_id_list.append(location_data[0])
                    final_point_names.append(location_data[1])
                    another_point = False
        
        # List for point data
        point_data = []

        # Second loop to get data
        for ind, (point_name, loc_id) in enumerate(zip(final_point_names, loc_id_list)):
            # Get point capacity data
            df = access.getCapacityData(connection, date_range, pipeline_id, loc_id)
            # Check if point has receipts and deliveries
            df = pointCap.checkDF(df)
            # Get flow values
            day_diff = datetime.datetime.strptime(date_range[1], "%m-%d-%Y") - datetime.datetime.strptime(date_range[0], "%m-%d-%Y")  # Calculate date difference
            flows = df["scheduled_cap"].values  # Flow data
            opcap = max(abs(df["operational_cap"].values))  # Opcap data
            point_avg = round(np.average(flows), 2)  # Calculate average of scheduled flows
            point_median = np.median(flows)  # Calculate median
            point_min, point_max = np.min(flows), np.max(flows)  # Calculate min and max
            #q25, q75 = round(np.percentile(flows, 25), 2), round(np.percentile(flows, 75), 2)  # Calculate first and third quartile
            #iqr = round(q75 - q25, 2)  # Calculate interquartile range
            # Append print statement to list
            point_data.append({"name":point_name, "day_diff":day_diff, "flow_avg":point_avg, "flow_median":point_median, "opcap":opcap, "flow_max":point_max, "flow_min":point_min})

        # Close connection
        print("Closing connection to database...")
        connection.close()

        # Print point_data
        if options.mmcf:
            print("\nCalculated Flows (MMcf/d):")
        else:
            print("\nCalculated Flows (MMbtu/d):")
        for p in point_data:
            if options.mmcf:
                print("Point name: {0} || Opcap Max: {1} | Average {2}-day Flow: {3} | Median: {4} || Min Flow: {5} | Max Flow: {6}"
                .format(p["name"], p["opcap"]/1030, p["day_diff"].days, p["flow_avg"]/1030, p["flow_median"]/1030, p["flow_min"]/1030, p["flow_max"]/1030))
            else:
                print("Point name: {0} || Opcap Max: {1} | Average {2}-day Flow: {3} | Median: {4} || Min Flow: {5} | Max Flow: {6}"
                .format(p["name"], p["opcap"], p["day_diff"].days, p["flow_avg"], p["flow_median"], p["flow_min"], p["flow_max"]))
    
    # Exception to handle errors
    except (IndexError, TypeError, KeyboardInterrupt, psycopg2.Error):
        print("Error encountered during dataase operations, closing connection...")
        connection.close()