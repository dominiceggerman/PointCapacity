# By Dominic Eggerman
# Imports
import os
import getpass
import psycopg2
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import datetime
import argparse
# Import pointcap modules
import accessDB as access
import readfile

# Get user input date range
def getDateRange():
    # User inputs
    start = input("Enter starting date (MM-DD-YYYY). Enter nothing to query the last 30 days: ")
    if not start:
        start = str((datetime.datetime.now() + datetime.timedelta(-30)).strftime("%m-%d-%Y"))
        end = str(datetime.datetime.now().strftime("%m-%d-%Y"))
    else:
        end = input("Enter end date (enter nothing for today): ")
    # Troubleshoot (if end has no value)
    if not end:
        end = str(datetime.datetime.now().strftime("%m-%d-%Y"))  # date in mm/dd/yyyy
    # Check date range
    if datetime.datetime.strptime(start, "%m-%d-%Y") > datetime.datetime.strptime(end, "%m-%d-%Y"):
        print("quit")
    # Return
    return [start, end]

# Check df for receipt and delivery values
def checkDF(dataframe):
    # If adjecent dates are the same
    if dataframe.iloc[0,0] == dataframe.iloc[1,0]:
        # Make list of distinct dates
        dates = dataframe["gas_day"].values[::2]
        # Difference of scheduled cap
        sched1 = dataframe["scheduled_cap"].values[::2]
        sched2 = dataframe["scheduled_cap"].values[1::2]
        scheduled = [max(i, j) - min(i, j) for i, j in zip(sched1, sched2)]
        # Greater of either operational cap
        op1 = dataframe["operational_cap"].values[::2]
        op2 = dataframe["operational_cap"].values[1::2]
        operational = [max(i, j) for i, j in zip(op1, op2)]
        # Return filtered dataframe
        return pd.DataFrame({"gas_day":dates, "scheduled_cap":scheduled, "operational_cap":operational})
    else:
        # Else return original dataframe
        return dataframe

# Plot
def plotPoints(df_list):
    # Set title
    title = input("Graph title: ")
    # Set graph labels
    plt.title(title, fontsize=20)
    plt.ylabel("MMcf/d")
    plt.xticks(fontsize=8, rotation=90)
    types = ["Scheduled", "Operational"] # ??
    # Get dates
    dates = df_list[0]["gas_day"].values  # ??

    # Loop through dataframes and plot
    ax = plt.axes()
    for datafile in df_list:
        ax.plot(dates, datafile.iloc[:,1:])  # plot data vs dates
    # Set legend
    ax.legend([point + " " + quant for point in point_names for quant in types], bbox_to_anchor=(0.5, 0), loc=1, borderaxespad=0)
    
    # Style gridlnes
    ax.yaxis.grid(linestyle=":")

    # Show plot
    plt.tight_layout()
    plt.show()
    

# Run
if __name__ == "__main__":
    # Argparse and add arguments
    parser = argparse.ArgumentParser(description="Below is a list of optional arguements with descriptions. Please refer to Readme for full documentation and examples...")
    parser.add_argument("-c", "--creds", help="Access creds from creds.txt", action="store_true")
    parser.add_argument("-l", "--last", help="Use last query", action="store_true")
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
        date_range = getDateRange()
        pipeline_id = int(input("Enter pipeline id: "))
        point_names = input("Enter point name (multiple points should be comma separated): ").split(",")
    
    # Append to df_list
    df_list = []
    for ind, p in enumerate(point_names):
        # Get location id and true name
        location_data = access.getLocationIDs(connection, p, pipeline_id)
        loc_id, new_name = location_data[0], location_data[1]
        point_names[ind] = new_name
        # Get point capacity data
        df = access.getCapacityData(connection, date_range, pipeline_id, loc_id)
        # Check if point has receipts and deliveries
        df = checkDF(df)
        # Convert to MMcf/d
        new_col = df["scheduled_cap"] / 1030
        df = df.assign(scheduled_cap = lambda x: x["scheduled_cap"] / 1030)
        df = df.assign(operational_cap = lambda x: x["operational_cap"] / 1030)
        df_list.append(df)

    # Close connection
    print("Closing connection to database...")
    connection.close()

    # Graph
    print("Graphing points...")
    plotPoints(df_list)