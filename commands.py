

from tkinter import CURRENT
from albumaday import *
from utils import *

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='/', intents=intents)

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
    per_page = 5
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


def create_embed(title, description, color=discord.Color.blue()):
    embed = discord.Embed(title=title, description=description, color=color)
    return embed

async def paginate_embed(ctx, embed_pages):
    total_pages = len(embed_pages)
    current_page = 0
    message = await ctx.send(embed=embed_pages[current_page])
    
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
            embed=embed_pages[current_page]
            embed.set_footer(text=f'Page {current_page + 1}/{total_pages} TIMED OUT')
            await message.edit(embed=embed)
            break
            
        if str(reaction.emoji) == '◀️':
            current_page = (current_page - 1) % total_pages
        elif str(reaction.emoji) == '▶️':
            current_page = (current_page + 1) % total_pages
            
        elif str(reaction.emoji) in number_emotes:
            page_number = number_emotes.index(str(reaction.emoji)) + 1
            current_page = page_number - 1
            
        embed = embed_pages[current_page]
        embed.set_footer(text=f"Page {current_page + 1}/{total_pages}")
        await message.edit(embed=embed)
        await message.remove_reaction(reaction.emoji, ctx.author)
        

@bot.command()    
async def getQueue(ctx):
    albums = getDB()
    if albums:
        embed_pages = createPages(albums)
        await paginate_embed(ctx, embed_pages)
    else:
        await ctx.send("The queue is empty.")

@bot.command()
async def albumHelp(ctx):
    commands = [
        ("/albumHelp", "Display this help message."),
        ("/recommend <album>, <artist>", "Recommend an album."),
        ("/getQueue", "Display the album queue with pagination."),
        ("/removeAlbum <title>", "Remove your own album or admin override."),
        ("/reroll", "Vote to reroll or admin override"),
        ("/promote <username>", "Promote a user to admin. (GREER ONLY)"),
        ("/demote <username>", "Demote an admin.(GREER ONLY)"),
        ("/setChannel", "Set the current channel as the album of the week channel. (ADMIN ONLY)"),
        ("/removeChannel", "Remove the current channel as the album of the week channel.(ADMIN ONLY)")
    ]

    pages = []
    per_page = 5
    for i in range(0, len(commands), per_page):
        embed = create_embed("Album Bot Help", "", discord.Color.blue())
        for command in commands[i:i + per_page]:
            embed.add_field(name=command[0], value=command[1], inline=False)
        pages.append(embed)
    
    await paginate_embed(ctx, pages)


@bot.command()
async def removeAlbum(ctx, *, title):
    username = ctx.author.name
    recommended = getRecommended("title", title)
    for admin in admins:
        if username == admin or username == recommended:
            result = removeRecommendation(title)
            if result:
                await ctx.send(result)
            else:
                await ctx.send("Album not found.")
            return  # Exit the loop early if permission check passes
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
    for admin in admins:
        if admin==ctx.author.name:
            # Check if the channel is already added
            with open(channels_file, "r") as f:
                if ctx.channel.id in channels:
                    await ctx.send("This channel is already the album of the week channel.")
                    return

            with open(channels_file, "a") as f:
                f.write(str(ctx.channel.id) + "\n")
            await ctx.send(f"{ctx.channel.name} has been set as the album of the week channel.")
 
@bot.command()
async def removeChannel(ctx):
    for admin in admins:
        if admin==ctx.author.name:
            # Check if the channel is in the list of channels
            with open(channels_file, "r") as f:
                if ctx.channel.id not in channels:
                    await ctx.send("This channel is not the album of the week channel.")
                    return

            # Remove the channel from the list and update the file
            channels.remove(ctx.channel.id)
            with open(channels_file, "w") as f:
                f.writelines(str(channel for channel in channels))
            await ctx.send(f"{ctx.channel.name} has been removed as the album of the week channel.")
        