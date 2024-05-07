
import asyncio
import aiohttp
import datetime

from albumaday import getRecommendation
from commands import bot
from utils import *

conn=sqlite3.connect("albums.db")
cursor=conn.cursor()

cursor.execute('''CREATE TABLE IF NOT EXISTS albums (
                    id INTEGER PRIMARY KEY,
                    title TEXT,
                    artist TEXT,
                    genre TEXT,
                    year INTEGER,
                    recommended TEXT
                    link TEXT
                )''')
    
conn.commit()
conn.close()


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    await bot.wait_until_ready()  # Wait until the bot is fully ready
    ifMinute.start()


@tasks.loop(minutes=1)
async def ifMinute():
    now = datetime.datetime.now(tz=cst)  # Use CST timezone
    if now.minute == 0:
        print("correct minute")
        ifHour.start()
        ifMinute.cancel()

@tasks.loop(hours=1)
async def ifHour():
    now = datetime.datetime.now(tz=cst)  # Use CST timezone
    if now.hour == 0:
        print("correct hour")
        ifDay.start()
        ifHour.cancel()

@tasks.loop(hours=24)
async def ifDay():
    now = datetime.datetime.now(tz=cst)  # Use CST timezone
    if now.weekday() == 6:  # Sunday
        print("correct day")
        sendAlbum.start()
        ifDay.cancel()

    
@tasks.loop(hours=168)
async def sendAlbum(override=None):
    album = getRecommendation()
    if album:
        for channel in channels:
            thread = bot.get_channel(channel)  # id for album of the day thread
            message=await thread.send(f"**ALBUM OF THE WEEK:** \n***{album[1]}- {album[2]}***.\n*Genre: {album[3]}\nReleased: {album[4]}.\nRecommended by:* ***{album[5]}\n***{album[6]}")
            
            query = f"album:{album[1]} artist:{album[2]}"
            results = sp.search(q=query, type='album', limit=1)

            if results and results['albums']['items']:
                album_data = results['albums']['items'][0]
                album_title = album_data['name']
                artist_name = album_data['artists'][0]['name']

                # Update bot's status
                await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=f"{album_title} - {artist_name} (Recommended by: {album[5]})"))

                album_cover_url = album_data['images'][0]['url']

                async with aiohttp.ClientSession() as session:
                    async with session.get(album_cover_url) as resp:
                        if resp.status != 200:
                            print('Could not download album cover...')
                        image_data = await resp.read()

                await bot.user.edit(avatar=image_data)

                print("The album of the day is", album)
            else:
                await thread.send("Album not found on Spotify.")
    else:
        await thread.send("I have no items in my database :(")


bot.run(DISCORD_TOKEN)
input("Press Enter to exit...")
