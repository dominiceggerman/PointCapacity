# By Dominic Eggerman
# Imports
import os
import getpass
import psycopg2
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import rcParams
from matplotlib import font_manager
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
def plotPoints(df_list, opcap):
    # Set font family
    rcParams["font.family"] = "Calibri"
    # Set title
    title = input("Graph title: ")
    # Set graph labels amd title
    plt.title(title, fontsize=26)
    plt.ylabel("MMcf/d", fontsize=12)
    plt.xticks(fontsize=12, rotation=90)
    plt.yticks(fontsize=12)
    if not opcap:
        types = ["Scheduled", "Operational"]
    else:
        types = ["Scheduled"]
        # Remove opcap data
        for ind, datafile in enumerate(df_list):
            datafile = datafile.drop(["operational_cap"], axis=1)
            df_list[ind] = datafile
    # Get dates
    dates = [d.strftime("%m/%d/%Y") for d in df_list[0]["gas_day"].values]  # ??

    # Loop through dataframes and plot
    ax = plt.axes()
    for datafile in df_list:
        ax.plot(dates, datafile.iloc[:,1:])  # plot data vs dates
    # Set legend and make it draggable
    legend = ax.legend([point + " " + quant for point in point_names for quant in types], ncol=len(df_list), prop={"size":12})
    legend.draggable()
    
    # Style gridlnes
    ax.yaxis.grid(linestyle=":")

    # Style spines and ticks
    ax.spines["top"].set_color("white")
    ax.spines["right"].set_color("white")

    # Show plot
    plt.tight_layout()
    plt.show()
    

# Run
if __name__ == "__main__":
    # Argparse and add arguments
    parser = argparse.ArgumentParser(description="Below is a list of optional arguements with descriptions. Please refer to Readme for full documentation and examples...")
    parser.add_argument("-c", "--creds", help="Access creds from creds.txt", action="store_true")
    parser.add_argument("-l", "--last", help="Use last query", action="store_true")
    parser.add_argument("-o", "--opcap", help="Remove operational cap datapoints", action="store_true")
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
            date_range = getDateRange()
            pipeline_id = int(input("Enter pipeline id: "))
            point_names = input("Enter point name or location id (multiple points should be comma separated): ").split(",")

        # If spaces exist between commas of user query
        if len(point_names) > 1:
            for ind, point in enumerate(point_names):
                if point[0] == " ":
                    # Remove leading space from point name string
                    point_names[ind] = point[1:]
        
        # Append to df_list
        df_list = []
        for ind, p in enumerate(point_names):
            # Set marker for multiple points
            another_point = True
            while another_point:
                # Get location id and true name
                location_data = access.getLocationIDs(connection, p, pipeline_id)
                # Ask user if he/she wants to pick another point from the query
                more_points = input("Want to add another point from this list? (y/n): ")
                if more_points not in ["y", "yes"]:
                    another_point = False
            
            # Raise error if no points are returned
            if location_data == -1:
                raise(psycopg2.Error)
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
        print("Closing connection to database...\n")
        connection.close()
    
    # Exception to handle errors
    except (IndexError, TypeError, KeyboardInterrupt, psycopg2.Error):
        print("Error encountered during dataase operations, closing connection...")
        connection.close()

    # Graph
    try:
        print("Graphing points...")
        plotPoints(df_list, options.opcap)
    # Exception to handle errors
    except:
        print("Error encountered during graphing...")

    # Save the query
    if not options.last:
        save_query = input("Save this query (y/n): ")
        if save_query == "y" or save_query == "yes":
            if os.path.exists("query.txt"):
                os.remove("query.txt")
            with open("query.txt", mode="w") as savefile:
                save_query = "start_date: {0}\nend_date: {1}\npipeline_id: {2}\npoint_names: {3}".format(date_range[0], date_range[1], pipeline_id, ",".join(point_names))
                savefile.write(save_query)
        else:
            print("Discarding query...")

    # Save the data (for Excel) ?? Better way to do this
    save_data = input("Save data to csv (y/n): ")
    if save_data == "y" or save_data == "yes" or options.save:
        save_name = input("File name.csv: ")
        if save_name[-4:] != ".csv":
            save_name = save_name + ".csv"
        # Rename columns
        for ind, (df, name) in enumerate(zip(df_list, point_names)):
            name = name.replace(" ", "_")
            df_list[ind] = df.rename(index=str, columns={"gas_day":"{0}_gas_day".format(name), "scheduled_cap":"{0}_scheduled".format(name), "operational_cap":"{}_operational".format(name)})
        
        # Concat dfs together and write to file
        pd.concat([df for df in df_list], axis=1).to_csv("saved_data/{0}".format(save_name), index=False)

        print("Data has been saved to saved_data/{0} in the current folder...".format(save_name))
    
    else:
        print("Data discarded...")