# By Dominic Eggerman
# Imports
import os
import getpass
import psycopg2
import pandas as pd
import numpy as np
import datetime
import argparse
# Import PointCap modules
import pointCap
import accessDB as access
import readfile

if __name__ == "__main__":
    # Argparse and add arguments
    parser = argparse.ArgumentParser(description="Below is a list of optional arguements with descriptions. Please refer to Readme for full documentation and examples...")
    parser.add_argument("-c", "--creds", help="Access creds from creds.txt", action="store_false")
    parser.add_argument("-btu", "--mmbtu", help="Display data in units of MMbtu rather than MMcf" action="store_false")
    options = parser.parse_args()

    # Get user creds
    if os.path.exists("creds.txt") or options.creds:
        credentials = readfile.readFile("creds.txt")
        username, password = credentials[0], credentials[1]
    else:
        username = input('Enter username: ')
        password = getpass.getpass('Enter password: ')

    # Connect to the database
    connection = access.connect(username, password)

    # Get date range and pipeline id
    date_range = pointCap.getDateRange()
    pipeline_id = int(input("Enter pipeline id: "))
    
    # Get the names and location IDs for all interconnects
    location_data = access.getInterconnectIDs(connection, pipeline_id)
        
    # Raise error if no points are returned
    if location_data == -1:
        raise(psycopg2.Error)
    
    # Get capacity data for locations
    df_list = []
    # Separate loc_ids and names from location data
    loc_ids, new_names = location_data[0], location_data[1]
    for loc, name in zip(loc_ids, new_names):
        try:
            # Get cap data
            print("Getting data for {}...".format(name))
            df = access.getCapacityData(connection, date_range, pipeline_id, loc)
            # Check if point has receipts and deliveries
            df = pointCap.checkDF(df)
            # Convert to MMcf unless option is true
            if options.mmbtu is False:
                df = df.assign(scheduled_cap = lambda x: x["scheduled_cap"] / 1030)
            # Drop operational capacity column
            df = df.drop(columns=["operational_cap"])
            # Filter out zero noms and averages < threshold
            if max(df["scheduled_cap"].values) == 0:
                continue
            elif (np.average(df["scheduled_cap"].values) <= 80 or np.average(df["scheduled_cap"].values) >= -80) and abs(max(df["scheduled_cap"].values)) < 100:
                continue
            else:
                # Else append to df_list
                df_list.append(df)

        # Exception to handle errors
        except (IndexError, TypeError, KeyboardInterrupt, psycopg2.Error):
            print("<<Error encountered when querying for point, passing>>")

    # Close connection
    print("Closing connection to database...\n")
    connection.close()

    # Save the data (for Excel) ?? Better way to do this
    save_name = input("Name the file to save to (Example: file_name.csv): ")
    if save_name[-4:] != ".csv":
        save_name = save_name + ".csv"
    # Get all data to master df
    for ind, (df, name) in enumerate(zip(df_list, new_names)):
        if ind == 0:
            df_list[ind] = df.rename(index=str, columns={"gas_day":"Gas Day", "scheduled_cap":"{0} Scheduled".format(name)})
        else:
            df_list[ind] = df.drop(columns=["gas_day"])
            df_list[ind] = df_list[ind].rename(index=str, columns={"scheduled_cap":"{0} Scheduled".format(name)})
    
    # Concat dfs together and write to file
    pd.concat([df for df in df_list], axis=1).to_csv("saved_data/{0}".format(save_name), index=False)

    # Final print
    print("Data has been saved to saved_data/{0} in the current folder...".format(save_name))