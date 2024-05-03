import discord
from discord.ext import commands, tasks
import asyncio
import datetime
import os
import aiohttp
from dotenv import load_dotenv 
from albumaday import *
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials


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

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    await bot.wait_until_ready()  # Wait until the bot is fully ready
    sendAlbum.start()

@tasks.loop(hours=1)
async def sendAlbum(override=None):
    now = datetime.datetime.now(tz=datetime.timezone.utc)
    if now.hour==15 or override:#10am cst
        thread=bot.get_channel(1228434151464505465)#id for album of the day thread
        if thread:
            album=getRecommendation()
            if album:
                await thread.send(f"**Today's album of the day:** \n***{album[1]}- {album[2]}***.\n*Genre: {album[3]}\nReleased: {album[4]}.\nRecommended by:* ***{album[5]}\n***{album[6]}")
                print("the album of the day is",album)
                query = f"album:{album[1]} artist:{album[2]}"
                results = sp.search(q=query, type='album', limit=1)
                try:
                    if results['albums']['items']:
                        album_data = results['albums']['items'][0]
                        albumCover=album_data['images'][0]['url']
                        async with aiohttp.ClientSession() as session:
                            async with session.get(albumCover) as resp:
                                if resp.status != 200:
                                    return await thread.send('Could not download album cover...')
                                image_data = await resp.read()

                        await bot.user.edit(avatar=image_data)
                except:
                    print("album cover not found")

            else:
                await thread.send("I have no items in my database :(")

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
            await ctx.send(f"Thanks for the recommendation, {username}.\nI added {album_name} to the database!")
        else:
            await ctx.send("Sorry, I could not find your album")
    else:
        await ctx.send("Invalid number of arguments. Please provide album, artist, genre, and year separated by commas.")

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
async def removeItem(ctx,title: str):
    username = ctx.author.name
    if username=="thisgreer":
        result=removeRecommendation(title)
        await ctx.send(result)
    else:
        await ctx.send("You do not have permissions to remove items.")

@bot.command()
async def reroll(ctx):
    username=ctx.author.name
    if username=="thisgreer":
        await sendAlbum(1)#send the 1 as an override to the loop
    else:
        await ctx.send("You do not have permissions to reroll the album.")
        
bot.run(DISCORD_TOKEN)
input("Press Enter to exit...")
