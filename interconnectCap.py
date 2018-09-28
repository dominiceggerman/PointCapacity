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

if __name__ == "__main__":
    # Argparse and add arguments
    parser = argparse.ArgumentParser(description="Below is a list of optional arguements with descriptions. Please refer to Readme for full documentation and examples...")
    parser.add_argument("-c", "--creds", help="Access creds from creds.txt", action="store_false")
    parser.add_argument("-s", "--save", help="Save data to csv", action="store_true")
    options = parser.parse_args()

    # Get user creds
    if os.path.exists("creds.txt") or options.creds:
        credentials = readfile.readFile("creds.txt")
        username, password = credentials[0], credentials[1]
    else:
        username = input('Enter username: ')
        password = getpass.getpass('Enter password: ')

    # Connect
    connection = access.connect(username, password)

    # Get start date and pipeline id, and point names
    date_range = pointCap.getDateRange()
    pipeline_id = int(input("Enter pipeline id: "))
    
    # Append to df_list\
    location_data = access.getInterconnectIDs(connection, pipeline_id)
        
    # Raise error if no points are returned
    if location_data == -1:
        raise(psycopg2.Error)
    
    # Get capacity data for locations
    df_list = []
    loc_ids, new_names = location_data[0], location_data[1]
    for loc, name in zip(loc_ids, new_names):
        try:
            print("Getting data for {}...".format(name))
            df = access.getCapacityData(connection, date_range, pipeline_id, loc)
            # Check if point has receipts and deliveries
            df = pointCap.checkDF(df)
            # Convert to MMcf/d
            new_col = df["scheduled_cap"] / 1030
            df = df.assign(scheduled_cap = lambda x: x["scheduled_cap"] / 1030)
            df = df.drop(columns=["operational_cap"])  # Drop opcap
            if max(df["scheduled_cap"].values) == 0 or np.average(df["scheduled_cap"].values) < 80:
                continue
            else:
                df_list.append(df)

        # Exception to handle errors
        except (IndexError, TypeError, KeyboardInterrupt, psycopg2.Error):
            print("Error encountered when querying for point, passing...")

    # Close connection
    print("Closing connection to database...\n")
    connection.close()

    # Save the data (for Excel) ?? Better way to do this
    save_data = input("Save data to csv (y/n): ")
    if save_data == "y" or save_data == "yes" or options.save:
        save_name = input("Name the file (file_name.csv): ")
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

        print("Data has been saved to saved_data/{0} in the current folder...".format(save_name))
    
    else:
        print("Data discarded...")