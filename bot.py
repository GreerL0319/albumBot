import discord
from discord.ext import commands, tasks
import asyncio
import datetime
import random
import os
import aiohttp
from dotenv import load_dotenv 
from albumaday import *
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import pytz  # Import the pytz module for handling timezones

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


load_dotenv()
DISCORD_TOKEN=os.getenv('DISCORD_TOKEN')
SPOTIFY_ID=os.getenv('SPOTIFY_ID')
SPOTIFY_SECRET=os.getenv('SPOTIFY_SECRET')

client_credentials_manager = SpotifyClientCredentials(client_id=SPOTIFY_ID, client_secret=SPOTIFY_SECRET)
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='/', intents=intents)

cst = pytz.timezone('America/Chicago')


admins_file = "admins.txt"
channels_file = "channels.txt"


admins = []
channels = []

#make file for admins if not already exists
if os.path.exists(admins_file):
        with open(admins_file, "r") as f:
            for line in f:
                admins.append(line.strip())
else:
    with open(admins_file, "w"):
        pass  # Create an empty file
    
#make file for channels if not already exist
if os.path.exists(channels_file):
    with open(channels_file, "r") as f:
        for line in f:
            channels.append(int(line.strip()))
else:
    with open(channels_file, "w"):
        pass  # Create an empty file
            
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
    for channel in channels:
        thread = bot.get_channel(channel)  # id for album of the day thread
        album = getRecommendation()
        if album:
            message=await thread.send(f"**Today's album of the day:** \n***{album[1]}- {album[2]}***.\n*Genre: {album[3]}\nReleased: {album[4]}.\nRecommended by:* ***{album[5]}\n***{album[6]}")
            
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



@bot.command(name="recommend", aliases=["recc"])  # Both /recommend and /recc will trigger this command
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
            await ctx.send(f"Thanks for the recommendation, {username}.\nI added {album_name} to the database!")
        else:
            await ctx.send("Sorry, I could not find your album")
    else:
        await ctx.send("Invalid number of arguments. Please provide album, artist.")

@bot.command()    
async def listDB(ctx):
    listDatabase()

def createPages(albums):
    pages = []
    per_page = 7
    for i in range(0, len(albums), per_page):
        embed = discord.Embed(title="Queue", color=discord.Color.blue())
        for album in albums[i:i + per_page]:
            if 'link' in album:
                title = f"[{album['title']} - {album['artist']}]({album['link']})"

            else:
                title = f"{album['title']} - {album['artist']}"
            value = f"Genre: {album['genre']}\nYear: {album['year']}\nRecommended by: {album['recommended']}"
            embed.add_field(
                name=title,
                value=value,
                inline=False
            )
        pages.append(embed)
    return pages


@bot.command()    
async def getQueue(ctx):
    albums = getDB()
    if albums:
        embed_pages = createPages(albums)
        total_pages = len(embed_pages)
        current_page = 0
        message = await ctx.send(embed=embed_pages[current_page])
        
        # Add numbered reactions
        await message.add_reaction('◀️')
        number_emotes = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣']
        for i in range(total_pages):
            await message.add_reaction(f"{number_emotes[i]}")

        await message.add_reaction('▶️')

        def check(reaction, user):
            return reaction.message.id == message.id and (str(reaction.emoji) in number_emotes or str(reaction.emoji) in ['◀️', '▶️']) and user == ctx.author
        
        while True:
            try:
                reaction, user = await bot.wait_for('reaction_add', timeout=60.0, check=check)
            except asyncio.TimeoutError:
                break
            
            # If arrow reaction is chosen, navigate between pages accordingly
            if str(reaction.emoji) == '◀️':
                current_page = (current_page - 1) % total_pages
            elif str(reaction.emoji) == '▶️':
                current_page = (current_page + 1) % total_pages
            # If numbered reaction is chosen, navigate to the corresponding page
            elif str(reaction.emoji) in number_emotes:
                page_number = number_emotes.index(str(reaction.emoji)) + 1
                current_page = page_number - 1
            
            embed = embed_pages[current_page]
            # Add page counter at the bottom
            embed.set_footer(text=f"Page {current_page + 1}/{total_pages}")
            await message.edit(embed=embed)
            
            # Remove user's reaction immediately after choosing a new page
            await message.remove_reaction(reaction.emoji, ctx.author)
    else:
        await ctx.send("The queue is empty.")

@bot.command()
async def remove(ctx,title: str):
    username = ctx.author.name
    recommended=getRecommended("title",title)
    for admin in admins:
        if username==admin or username==recommended:
            result=removeRecommendation(title)
            await ctx.send(result)
        else:
            await ctx.send("You do not have permissions to remove this item.")

@bot.command()
async def reroll(ctx):
    username = ctx.author.name
    for admin in admins:
        if username == admin:
            await sendAlbum(1)  # send the 1 as an override to the loop
            return

    # If the user is not an admin, create a poll
    embed = discord.Embed(title="Reroll Album?", color=discord.Color.blue())
    value = "Vote with reactions. Poll ends in an hour"
    embed.add_field(
        name="Poll",
        value=value,
        inline=False
    )
    embed.set_footer(text="Need at least 3 votes...")
    message = await ctx.send(embed=embed)
    await message.add_reaction('✅')
    await message.add_reaction('❌')
    await asyncio.sleep(3600)#sleep for an hour
    message = await ctx.channel.fetch_message(message.id)

    yes_count = 0
    no_count = 0
    for reaction in message.reactions:
        if str(reaction.emoji) == '✅':
            yes_count = reaction.count - 1  # Subtract 1 to exclude bot's reaction
        elif str(reaction.emoji) == '❌':
            no_count = reaction.count - 1   # Subtract 1 to exclude bot's reaction

    # Check if the poll was successful (at least 3 yes votes)
    conclusion=""        
    if yes_count >= 3 and yes_count>no_count:
        conclusion="The people have spoken! The reroll is a success!"
        await sendAlbum(1)
    if yes_count<3:
        conclusion="The people have not spoken... Poll discarded."
    if no_count>yes_count:
        conclusion="The people have spoken! The reroll is a failure!"
    embed.set_footer(text=conclusion)
    await message.edit(embed=embed)
    
@bot.command()
async def promote(ctx, user_name: str):
    if ctx.author.name == admins[0]:
        # Check if the user is already an admin
        if user_name in admins:
            await ctx.send(f"{user_name} is already an admin.")
        else:
            # Add the user to the admins list and write to file
            admins.append(user_name)
            with open(admins_file, "a") as f:
                f.write(user_name + "\n")
            await ctx.send(f"{user_name} has been promoted as an admin.")
    else:
        await ctx.send("Only the bot owner can add admins.")

@bot.command()
async def demote(ctx, user_name: str):
    if ctx.author.name == admins[0]:
        # Check if the user is an admin
        if user_name in admins:
            # Remove the user from the admins list and update file
            admins.remove(user_name)
            with open(admins_file, "w") as f:
                f.writelines(admin + "\n" for admin in admins)
            await ctx.send(f"{user_name} no longer has admin.")
        else:
            await ctx.send(f"{user_name} is not an admin.")
    else:
        await ctx.send("Only the bot owner can demote admins.")

# Command to add the album of the week channel
@bot.command()
async def setChannel(ctx):
    # Check if the channel is already added
    with open(channels_file, "r") as f:
        channels = f.readlines()
        if str(ctx.channel.id) in channels:
            await ctx.send("This channel is already the album of the week channel.")
            return

    with open(channels_file, "a") as f:
        f.write(str(ctx.channel.id) + "\n")
    await ctx.send(f"{ctx.channel.name} has been set as the album of the week channel.")
        
        
        
        

bot.run(DISCORD_TOKEN)
input("Press Enter to exit...")
