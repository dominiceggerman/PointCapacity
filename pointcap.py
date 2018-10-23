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

    # If start is blank, query for last 30 days, else input an end date
    if not start:
        start = str((datetime.datetime.now() + datetime.timedelta(-30)).strftime("%m-%d-%Y"))
        end = str(datetime.datetime.now().strftime("%m-%d-%Y"))
    else:
        end = input("Enter end date (enter nothing for today): ")
    # If end has no value, make it today
    if not end:
        end = str(datetime.datetime.now().strftime("%m-%d-%Y"))  # date in mm/dd/yyyy
    # Check date range
    if datetime.datetime.strptime(start, "%m-%d-%Y") > datetime.datetime.strptime(end, "%m-%d-%Y"):
        raise ValueError("Start date is after the end date.")

    # Check date range
    if end < start:
        raise ValueError("Start date is after end date.")
    # Return dates
    else:
        return [start, end]


# Check df for receipt and delivery values
def checkDF(dataframe):
    # If adjecent dates are the same
    if dataframe.iloc[0,0] == dataframe.iloc[1,0]:
        # Make list of distinct dates
        dates = dataframe["gas_day"].values[::2]
        # Difference of scheduled cap (receipts - deliveries)
        sched1 = dataframe["scheduled_cap"].values[::2]
        sched2 = dataframe["scheduled_cap"].values[1::2]
        scheduled = [i - abs(j) for i, j in zip(sched1, sched2)]
        # Create operational cap
        op1 = dataframe["operational_cap"].values[::2]
        op2 = dataframe["operational_cap"].values[1::2]
        operational = []
        # For loop to check if opcap is negative in value
        for ind, (i, j) in enumerate(zip(op1, op2)):
            if i == 0 and j == 0:
                # In case of opcap actually equalling zero
                operational.append(0)
            if scheduled[ind] > 0:
                operational.append(i)
            elif scheduled[ind] < 0:
                operational.append(j * -1)
            else:
                # Else use last opcap value
                operational.append(operational[ind-1])
        # Return reduced dataframe
        return pd.DataFrame({"gas_day":dates, "scheduled_cap":scheduled, "operational_cap":operational})
    else:
        # Else return dataframe with no role id
        return dataframe.drop(columns="role_id")


# Plot
def plotPoints(df_list, loc_names, opcap):
    # Set font family to Calibri
    rcParams["font.family"] = "Calibri"
    # Input title
    title = input("Graph title: ")
    # Set graph labels (colors, font, rotation) amd title
    plt.title(title, fontsize=24, color="#595959")
    plt.ylabel("MMcf/d", fontsize=12, color="#595959")
    plt.xticks(fontsize=12, rotation=90, color="#595959")
    plt.yticks(fontsize=12, color="#595959")

    # Check to display operational capacity
    if not opcap:
        types = ["Scheduled", "Operational"]
    else:
        types = ["Scheduled"]
        # Remove opcap data
        for ind, datafile in enumerate(df_list):
            datafile = datafile.drop(["operational_cap"], axis=1)
            df_list[ind] = datafile

    # Get dates
    dates = [d.strftime("%m/%d/%Y") for d in df_list[0]["gas_day"].values]

    # Loop through dataframes and plot
    ax = plt.axes()
    for datafile in df_list:
        ax.plot(dates, datafile.iloc[:,1:])  # plot data vs dates
        
    # Set legend, make it draggable, set color
    legend = plt.legend([point + " " + quant for point in loc_names for quant in types], ncol=2, prop={"size":12}, frameon=False)
    legend.draggable()
    plt.setp([text for text in legend.get_texts()], color="#595959")
    
    # Style gridlnes
    ax.yaxis.grid(linestyle=":")

    # Style spines and ticks
    ax.spines["top"].set_color("white")
    ax.spines["right"].set_color("white")
    ax.spines["bottom"].set_color("#595959")
    ax.spines["left"].set_color("#595959")

    # Show plot
    plt.tight_layout()
    plt.show()
    

if __name__ == "__main__":
    # Argparse and add arguments
    parser = argparse.ArgumentParser(description="Below is a list of optional arguements with descriptions. Please refer to README.md for full documentation and examples...")
    parser.add_argument("-c", "--creds", help="Access creds from creds.txt", action="store_false")
    parser.add_argument("-l", "--last", help="Use last query", action="store_true")
    parser.add_argument("-o", "--opcap", help="Remove operational cap datapoints", action="store_true")
    parser.add_argument("-g", "--graph", help="Do not display graph.", action="store_false")
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
                    another_point = False
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

        # Master df_list
        df_list = []

        # Second loop to get data
        for loc_id in loc_id_list:
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
        print("Error encountered during database operations, closing connection...")
        connection.close()

    # Graph
    if options.graph:
        try:
            print("Graphing points...")
            plotPoints(df_list, final_point_names, options.opcap)
        # Exception to handle errors
        except:
            print("Error encountered during graphing...")
    else:
        print("Skipping graphing...")

    # Save the query
    if not options.last:
        save_query = input("Save this query (y/n): ")
        if save_query == "y" or save_query == "yes":
            if os.path.exists("query.txt"):
                os.remove("query.txt")
            with open("query.txt", mode="w") as savefile:
                save_query = "start_date: {0}\nend_date: {1}\npipeline_id: {2}\npoint_names: {3}".format(date_range[0], date_range[1], pipeline_id, ",".join(final_point_names))
                savefile.write(save_query)
        else:
            print("Discarding query...")

    # Save the data (for Excel) ?? Better way to do this
    save_data = input("Save data to csv (y/n): ")
    if save_data == "y" or save_data == "yes":
        save_name = input("Name the file (file_name.csv): ")
        if save_name[-4:] != ".csv":
            save_name = save_name + ".csv"
        # Get all data to master df
        for ind, (df, name) in enumerate(zip(df_list, final_point_names)):
            if ind == 0:
                df_list[ind] = df.rename(index=str, columns={"gas_day":"Gas Day", "scheduled_cap":"{0} Scheduled".format(name)})
            else:
                df_list[ind] = df.drop(columns=["gas_day"])
                df_list[ind] = df_list[ind].rename(index=str, columns={"scheduled_cap":"{0} Scheduled".format(name)})
        
        # Concat dfs together and write to file
        pd.concat([df for df in df_list], axis=1).to_csv("saved_data/{0}".format(save_name), index=False)

        print("Data has been saved to saved_data/{0} in the current folder...".format(save_name))

        # Get abs path and open the file
        abs_path = os.path.abspath("saved_data/{0}".format(save_name))
        os.startfile(abs_path)
    
    else:
        print("Data discarded...")