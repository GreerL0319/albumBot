import os

admins_file = "admins.txt"
channels_file = "channels.txt"


admins = []
channels = []#make file for admins if not already exists

def makeAdmins():
    if os.path.exists(admins_file):
            with open(admins_file, "r") as f:
                for line in f:
                    admins.append(line.strip())
    else:
        with open(admins_file, "w"):
            pass  # Create an empty file
    
def makeChannels():
    #make file for channels if not already exist
    if os.path.exists(channels_file):
        with open(channels_file, "r") as f:
            for line in f:
                line = line.strip()
                if line:  # Check if the line is not empty
                    channels.append(int(line))
    else:
        with open(channels_file, "w"):
            pass  # Create an empty file
        
makeAdmins()
makeChannels()