import asyncio
import discord
import json
import os.path
import requests
import time

import config

MUSIC_LIST_JSON = "https://www.smashbros.com/assets_v2/data/sound.json"
NEWS_LIST_JSON = "https://www.smashbros.com/data/bs/en_US/json/en_US.json"
FIGHTERS_LIST_JSON = "https://www.smashbros.com/assets_v2/data/fighter.json"
CHANNELS_FILE = "channels.json"

client = discord.Client()

if not os.path.isfile(CHANNELS_FILE):
    subscribed_channels = {}
else:
    with open(CHANNELS_FILE) as f:
        subscribed_channels = json.load(f)


print(subscribed_channels)
music_list = {}
news_list = {}
fighters_list = {}

async def load_music_list():
    global music_list
    r = requests.get(MUSIC_LIST_JSON)
    music_list = r.json()

    print('Loaded current music list.')
    client.loop.create_task(update_music_list())

async def update_music_list():
    global music_list
    await client.wait_until_ready()

    while not client.is_closed():
        r = requests.get(MUSIC_LIST_JSON)
        new_music_list = r.json()

        if len(new_music_list["sound"]) != len(music_list["sound"]):
            new_songs = len(new_music_list["sound"]) - len(music_list["sound"])
            print(str(new_songs) + " new songs!")

            for i in range(new_songs):
                for channel in subscribed_channels:
                    await client.get_channel(channel).send("New Song! {} - {}: https://www.youtube.com/watch?v={}".format(new_music_list["sound"][i]["descTxt2En"], new_music_list["sound"][i]["titleEn"], new_music_list["sound"][i]["youtubeID"]))
            music_list = new_music_list
        
        else:
            print("New music not found... retrying in 30 mins")
        await asyncio.sleep(1800)

async def load_news_list():
    global news_list
    r = requests.get(NEWS_LIST_JSON)
    news_list = r.json()
    print('Loaded current news list.')
    client.loop.create_task(update_news_list())


async def update_fighters_list():
    global fighters_list
    await client.wait_until_ready()

    while not client.is_closed():
        r = requests.get(FIGHTERS_LIST_JSON)

        # we don't need to send an update because a blog post will (obviously) be made for new characters
        fighters_list = r.json()
        print("Updated fighters list.")
        await asyncio.sleep(1800)

async def load_fighters_list():
    global fighters_list
    r = requests.get(FIGHTERS_LIST_JSON)
    fighters_list = r.json()
    print('Loaded current fighters list.')
    client.loop.create_task(update_fighters_list())


async def update_news_list():
    global news_list
    await client.wait_until_ready()

    while not client.is_closed():
        r = requests.get(NEWS_LIST_JSON)
        new_news_list = r.json()

        if len(new_news_list) != len(news_list):

            new_news = len(new_news_list) - len(news_list)
            news_list = new_news_list

            for i in range(new_news):
                for channel in subscribed_channels:
                    await client.get_channel(channel).send(embed=generate_news_embed(i))

        else:
            print("New news not found... retrying in 30 mins")
        await asyncio.sleep(1800)

@client.event
async def on_message(message):
    if message.content.startswith('!subscribe'):
        if message.channel.id not in subscribed_channels:
            subscribed_channels[message.channel.id] = True

            js = json.dumps(subscribed_channels)
            f = open(CHANNELS_FILE, "w")
            f.write(js)
            f.close()

            await message.channel.send("Channel subscribed.")
        else:
            await message.channel.send("Error: Channel is already subscribed.")
    
    if message.content.startswith('!unsubscribe'):
        if message.channel.id not in subscribed_channels:
            await message.channel.send("Error: Channel is not subscribed.")
        else:
            subscribed_channels.pop(message.channel.id, None)

            js = json.dumps(subscribed_channels)
            f = open("channels.json","w")
            f.write(js)
            f.close()

            await message.channel.send("Channel unsubscribed.")

    if message.content.startswith('!mlatest'):
        await message.channel.send("{} - {}: https://www.youtube.com/watch?v={}".format(music_list["sound"][0]["descTxt2En"], music_list["sound"][0]["titleEn"], music_list["sound"][0]["youtubeID"]))

    if message.content.startswith('!mfind'):
        if len(message.content.split()) > 1:
            song = ' '.join(message.content.split()[1:])

            for item in music_list["sound"]:
                if item["titleEn"].lower() == song.lower():
                    await message.channel.send("{} - {}: https://www.youtube.com/watch?v={}".format(item["descTxt2En"], item["titleEn"], item["youtubeID"]))
                    return  
            await message.channel.send("Error: song not found")
            
        else:
            await message.channel.send("Error: no input specified")
    
    if message.content.startswith('!maintheme'):
        await message.channel.send("{}: https://www.youtube.com/watch?v={}".format(music_list["maintheme"][0]["titleEn"], music_list["maintheme"][0]["youtubeID"]))

    if message.content.startswith('!help'):
        description="Commands: `!un/subscribe`, `!mlatest`, `!mfind <song title>`, `!maintheme`, `!char <id>`, `!latest`, `!help`\n[GitHub](https://github.com/john-best/SmashMusicBot)"
        embed = discord.Embed(description=description, color=0x5bc0de)
        embed.set_author(name="Smash Ultimate News Bot", icon_url=client.user.default_avatar_url)

        await message.channel.send(embed=embed)

    if message.content.startswith('!mlist'):
        text = "```"
        text += "{}: https://www.youtube.com/watch?v={}\n".format(music_list["maintheme"][0]["titleEn"], music_list["maintheme"][0]["youtubeID"])
        for song in music_list["sound"]:
            text += "{} - {}: https://www.youtube.com/watch?v={}\n".format(song["descTxt2En"], song["titleEn"], song["youtubeID"])
        text += "```"
        await message.channel.send(text)

    if message.content.startswith('!char'):
        if len(message.content.split()) < 2:
            await message.channel.send("Error: Need id")
        else:
            contents = message.content.split()
            search_id = contents[1]
            link_id = contents[1]
            if contents[1].endswith('e') or contents[1].endswith('\'') or contents[1].endswith('ᵋ'):
                search_id = contents[1][:-1] + '\''
                link_id = contents[1][:-1] + 'e'
                
            if len(search_id) == 1:
                search_id = '0' + search_id
                link_id = '0' + link_id

            # these are grouped
            # pokemon trainer
            if search_id == "33" or search_id == "34" or search_id == "35":
                search_id = "33-35"
                link_id = "33-35"

            # mii fighters
            if search_id == "51" or search_id == "52" or search_id == "53":
                search_id = "51-53"
                link_id = "51-53"
                
            for fighter in fighters_list["fighters"]:
                if fighter["displayNum"] == search_id:

                    title = fighter["displayName"]["en_US"].replace("<br>", "") + "/" + fighter["displayName"]["ja_JP"].replace("<br>", "")
                    embed = discord.Embed(title=fighter["displayName"]["en_US"].replace("<br>", ""), description="https://www.smashbros.com/en_US/fighter/{}.html".format(link_id), color=int(fighter["color"][1:], 16))
                    embed.set_image(url="https://www.smashbros.com/assets_v2/img/fighter/thumb_h/{}.png".format(fighter["file"]))
                    await message.channel.send(embed=embed)
                    return
            await message.channel.send("Error: unable to find fighter!")

    if message.content.startswith('!latest'):
        await message.channel.send(embed=generate_news_embed(0))
        
        

@client.event
async def on_ready():

    if music_list == {}:
        await load_music_list()

    if news_list == {}:
        await load_news_list()
    
    if fighters_list == {}:
        await load_fighters_list()
        
    await client.change_presence(activity=discord.Game(name='!help for Smash Ultimate'))


def generate_news_embed(i):
    title = news_list[i]["title"]["rendered"]
    description = news_list[i]["acf"]["editor"].replace("<p>", "").replace("<br />", " - ").replace("</p>", "").replace("\n", "")

    if news_list[i]["acf"]["link_url"] != "":
        description += "\n" + news_list[0]["acf"]["link_url"]

    if news_list[i]["acf"]["image2"]["url"] is not None:
        description += "\n" + "More images: "
        description += "\n" + news_list[i]["acf"]["image2"]["url"].replace('/413752', 'https://www.smashbros.com')

    if news_list[i]["acf"]["image3"]["url"] is not None:
        description += "\n" + news_list[i]["acf"]["image3"]["url"].replace('/413752', 'https://www.smashbros.com')
    
    if news_list[i]["acf"]["image4"]["url"] is not None:
        description += "\n" + news_list[i]["acf"]["image4"]["url"].replace('/413752', 'https://www.smashbros.com')

    embed = discord.Embed(title=title, description=description, color=0x5bc0de)

    if news_list[i]["acf"]["image1"]["url"] is not None:
        image_url = news_list[i]["acf"]["image1"]["url"].replace('/413752', 'https://www.smashbros.com')
        embed.set_image(url=image_url)

    embed.set_footer(text="Posted: " + news_list[i]["date_gmt"] + " GMT")
    return embed

client.run(config.token, reconnect=True)
