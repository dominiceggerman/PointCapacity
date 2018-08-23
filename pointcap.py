# By Dominic Eggerman
# Imports
import getpass
import psycopg2
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
# Import pointcap modules
import accessDB as access

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

# Run
if __name__ == "__main__":
    # Connect to DB
    username = input('Enter username: ')
    password = getpass.getpass('Enter password: ')
    connection = access.connect(username, password)

    # Get start date, pipeline id, and point names
    start_date = input("Enter start date (MM/DD/YYYY): ")
    pipeline_id = int(input("Enter pipeline id: "))
    point_names = input("Enter point names (comma separated): ").split(",")
    # Append to df_list
    df_list = []
    for p in point_names:
        loc_id = access.getLocationIDs(connection, p, pipeline_id)
        df = access.getCapacityData(connection, start_date, pipeline_id, loc_id)
        # Check if point has receipts and deliveries
        df = checkDF(df)
        # Convert to MMcf/d
        print(df)
        new_col = df["scheduled_cap"] / 1030
        df = df.assign(scheduled_cap = lambda x: x["scheduled_cap"] / 1030)
        df = df.assign(operational_cap = lambda x: x["operational_cap"] / 1030)
        print(df)
        df_list.append(df)

    # Close connection
    print("Closing connection to database...")
    connection.close()

    # Graph
    print("Graphing points...")
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