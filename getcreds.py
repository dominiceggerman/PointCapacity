# By Dominic Eggerman
# Imports

# Read user creds from text file
def readCreds():
    creds = []
    # Open file and read lines
    with open("creds.txt", mode="r") as credfile:
        for line in credfile:
            # Strip newline, split, and get cred 
            item = line.rstrip().split(":")[1]
            # If space at front of username / pass
            if item[0] is " ":
                item = item[1:]
            # Append to cred_list
            creds.append(item)
    # Return
    return creds

# Testing
if __name__ == "__main__":
    creds = readCreds()
    print(creds)