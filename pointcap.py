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
    # User inputs
    # username = input('Enter username: ')
    # password = getpass.getpass('Enter password: ')
    # date = input("Enter start date: ")
    # pipeline_id = input("Enter pipeline id: ")
    # point_name = input("Enter point name: ")
    username = "deggerman"
    password = "GS8j8gvh"
    start_date = "07/01/2018"
    pipeline_id = 396
    point_names = ["Wagoner East"]
    types = ["Scheduled", "Operational"]

    # Connect to DB
    connection = access.connect(username, password)

    # Append to df_list
    df_list = []
    for p in point_names:
        loc_id = access.getLocationIDs(connection, p, pipeline_id)
        df = access.getCapacityData(connection, start_date, pipeline_id, loc_id)
        # Convert to MMcf/d
        df["scheduled_cap"] = df["scheduled_cap"].values / 1030
        df["operational_cap"] = df["operational_cap"].values / 1030
        df_list.append(df)

    # Graph

    # Set title
    title = input("Graph title: ")
    # Set graph labels
    plt.title(title, fontsize=20)
    plt.ylabel("MMcf/d")
    plt.xticks(fontsize=8, rotation=90)
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