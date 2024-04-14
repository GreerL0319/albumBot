import discord
from discord.ext import commands, tasks
import asyncio
import datetime
import os
from dotenv import load_dotenv 
from albumaday import *
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

load_dotenv()
DISCORD_TOKEN=os.getenv('DISCORD_TOKEN')
SPOTIFY_ID=os.getenv('SPOTIFY_ID')
SPOTIFY_SECRET=os.getenv('SPOTIFY_SECRET')

client_credentials_manager = SpotifyClientCredentials(client_id=SPOTIFY_ID, client_secret=SPOTIFY_SECRET)
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='/', intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    await bot.wait_until_ready()  # Wait until the bot is fully ready

@tasks.loop(hours=24)
async def sendAlbum():
    thread=bot.get_channel(1128454083917922366)#id for album of the day thread
    if thread:
        album=getRecommendation()
        if album:
            await thread.send(f"```Today's album of the day: \n{album[1]}- {album[2]}.\nGenre: {album[3]}\nReleased: {album[4]}.\n Recommended by: {album[5]}\n {album[6]}```")
            print("the album of the day is",album)
        else:
            await thread.send("I have no items in my database.")
 
@sendAlbum.before_loop
async def setTime():
    #Calculate the delay until the next 10 AM CST
    now = datetime.datetime.now(tz=datetime.timezone.utc)
    target_time = datetime.datetime(now.year, now.month, now.day, 10, 0, 0, tzinfo=datetime.timezone.utc)
    if now.hour >= 10:  # If it's already past 10 AM, schedule it for the next day
        target_time += datetime.timedelta(days=1)
    delta = target_time - now
    await asyncio.sleep(delta.total_seconds())
  
@bot.command()
async def recommend(ctx, *, args):
    # Split the arguments by commas
    args_list = args.split(',')
    # Remove leading and trailing whitespaces from each argument
    args_list = [arg.strip() for arg in args_list]
    
    # Extract individual parameters from the args_list
    if len(args_list) == 2:
        album, artist = args_list
        results = sp.search(q=f"album:{album} artist:{artist}", type='album',limit=1)#to save memory im just going to limit to 1 return
        if results['albums']['items']:
            top_album = results['albums']['items'][0]  # Get the top album
            album_name = top_album['name']
            link = top_album['external_urls']['spotify']
            genres = set()
            i = 0
            for artist_info in top_album['artists']:
                artist_id = artist_info['id']
                spartist = sp.artist(artist_id)
                genres.update(spartist['genres'])#spotify artist spartists :)
                i += 1
                if i > 2:
                    break

            # Convert genres set to a comma-separated string
            genres_str = ', '.join(genres)

            release_date = top_album['release_date']
            username = ctx.author.name
            addAlbum(album, artist, genres_str, release_date, username, link)
            await ctx.send("Album added. Thanks!")
        else:
            await ctx.send("Sorry, I could not find your album")
    else:
        await ctx.send("Invalid number of arguments. Please provide album, artist, genre, and year separated by commas.")

@bot.command()    
async def listDB(ctx):
    listDatabase()
    
@bot.command()    
async def getQueue(ctx):
    f = open('queue.txt', 'a')
    f.tell()  # Show the position of the cursor
    # As you can see, the position is at the end
    f.seek(0, 0) # Put the position at the beginning
    f.truncate() # Truncate the file
    albums = getDB()
    for album in albums:
        f.write(album + "\n")
    f.close()  # Close the file

    if albums:
        # Create a discord.File object from the file
        file_discord = discord.File('queue.txt', filename='queue.txt')
        # Send the file as an attachment
        await ctx.send(file=file_discord)
    else:
        await ctx.send("Nobody has recommended any albums.")
        
@bot.command()
async def removeItem(ctx,title: str):
    username = ctx.author.name
    if username=="thisgreer":
        result=removeRecommendation(title)
        await ctx.send(result)
    else:
        await ctx.send("You do not have permissions to remove items.")

bot.run(DISCORD_TOKEN)
input("Press Enter to exit...")
