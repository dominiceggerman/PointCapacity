# By Dominic Eggerman
# Imports
import getpass
import psycopg2
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
# Import pointcap modules
import accessDB as access

# Run
if __name__ == "__main__":
    # Connect to DB
    username = input('Enter username: ')
    password = getpass.getpass('Enter password: ')
    connection = access.connect(username, password)

    # Get start date, pipeline id, and point names
    # start_date = input("Enter start date (MM/DD/YYYY): ")
    start_date = "08/01/2018"
    # pipeline_id = int(input("Enter pipeline id: "))
    pipeline_id = 396
    # point_names = input("Enter point names (comma separated): ").split(",")
    point_names = ["ramapo AGT", "wagoner east"] # change ramapo
    print(point_names)
    # Append to df_list
    df_list = []
    for p in point_names:
        loc_id = access.getLocationIDs(connection, p, pipeline_id)
        print(loc_id)
        df = access.getCapacityData(connection, start_date, pipeline_id, loc_id)
        # Convert to MMcf/d
        df["scheduled_cap"] = df["scheduled_cap"].values / 1030
        df["operational_cap"] = df["operational_cap"].values / 1030
        df_list.append(df)
        print(df)

    # Graph

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
    for (ind, datafile) in enumerate(df_list):
        ax.plot(dates, datafile.iloc[:,1:])  # plot data vs dates
    # Set legend
    ax.legend([point + " " + quant for point in point_names for quant in types])
    
    # Style gridlnes and xticks
    ax.yaxis.grid(linestyle=":")
    # for label in ax.xaxis.get_ticklabels()[1::2]:
        # label.set_visible(False)
    # ??

    # Show plot
    plt.tight_layout()
    plt.show()