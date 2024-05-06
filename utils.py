import asyncio
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
import os
import pytz
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import sqlite3



load_dotenv()
DISCORD_TOKEN=os.getenv('DISCORD_TOKEN')

SPOTIFY_ID = os.getenv('SPOTIFY_ID')
SPOTIFY_SECRET = os.getenv('SPOTIFY_SECRET')

client_credentials_manager = SpotifyClientCredentials(client_id=SPOTIFY_ID, client_secret=SPOTIFY_SECRET)
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

cst = pytz.timezone('America/Chicago')

admins_file = "admins.txt"
channels_file = "channels.txt"

admins = []
channels = []

# Populate the arrays
def makeAdmins():
    global admins
    if os.path.exists(admins_file):
        with open(admins_file, "r") as f:
            for line in f:
                admins.append(line.strip())
    else:
        with open(admins_file, "w"):
            pass  # Create an empty file

def makeChannels():
    global channels
    if os.path.exists(channels_file):
        with open(channels_file, "r") as f:
            for line in f:
                line = line.strip()
                if line:  # Check if the line is not empty
                    channels.append(int(line))
    else:
        with open(channels_file, "w"):
            pass  # Create an empty file

# Call the functions to populate the arrays
makeAdmins()
makeChannels()
