import asyncio
import discord
import requests

import config

MUSIC_LIST_JSON = "https://www.smashbros.com/assets_v2/data/sound.json"
NEWS_LIST_JSON = "https://www.smashbros.com/data/bs/en_US/json/en_US.json"
FIGHTERS_LIST_JSON = "https://www.smashbros.com/assets_v2/data/fighter.json"

client = discord.Client()

subscribed_channels = {}
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

    while not client.is_closed:
        r = requests.get(MUSIC_LIST_JSON)
        new_music_list = r.json()

        if len(new_music_list["sound"]) != len(music_list["sound"]):
            new_songs = len(new_music_list["sound"]) - len(music_list["sound"])
            print(str(new_songs) + " new songs!")

            for i in range(new_songs):
                for channel in subscribed_channels:
                    await client.send_message(client.get_channel(channel), "New Song! {} - {}: https://www.youtube.com/watch?v={}".format(new_music_list["sound"][i]["descTxt2En"], new_music_list["sound"][i]["titleEn"], new_music_list["sound"][i]["youtubeID"]))
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

    while not client.is_closed:
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

    while not client.is_closed:
        r = requests.get(NEWS_LIST_JSON)
        new_news_list = r.json()

        if len(new_news_list) != len(news_list):

            new_news = len(new_news_list) - len(news_list)

            for i in range(new_news):
                title = new_news_list[i]["title"]["rendered"]
                description = new_news_list[i]["acf"]["editor"].replace("<p>", "").replace("<br />", " - ").replace("</p>", "").replace("\n", "")

                if new_news_list[i]["acf"]["link_url"] != "":
                    description += "\n" + new_news_list[0]["acf"]["link_url"]

                if new_news_list[i]["acf"]["image2"]["url"] is not None:
                    description += "\n" + "More images: "
                    description += "\n" + new_news_list[i]["acf"]["image2"]["url"].replace('/413752', 'https://www.smashbros.com')

                if new_news_list[i]["acf"]["image3"]["url"] is not None:
                    description += "\n" + new_news_list[i]["acf"]["image3"]["url"].replace('/413752', 'https://www.smashbros.com')
                
                if new_news_list[i]["acf"]["image4"]["url"] is not None:
                    description += "\n" + new_news_list[i]["acf"]["image4"]["url"].replace('/413752', 'https://www.smashbros.com')

                embed = discord.Embed(title=title, description=description, color=0x5bc0de)

                if new_news_list[i]["acf"]["image1"]["url"] is not None:
                    image_url = new_news_list[i]["acf"]["image1"]["url"].replace('/413752', 'https://www.smashbros.com')
                    embed.set_image(url=image_url)

                embed.set_footer(text="Posted: " + new_news_list[i]["date_gmt"] + " GMT")
                for channel in subscribed_channels:
                    await client.send_message(client.get_channel(channel), embed=embed)
            news_list = new_news_list

        else:
            print("New news not found... retrying in 30 mins")
        await asyncio.sleep(1800)

@client.event
async def on_message(message):
    global music_list
    global news_list
    global fighters_list
    if message.content.startswith('!subscribe'):
        if message.channel.id not in subscribed_channels:
            subscribed_channels[message.channel.id] = True
            await client.send_message(message.channel, "Channel subscribed.")
        else:
            await client.send_message(message.channel, "Error: Channel is already subscribed.")
    
    if message.content.startswith('!unsubscribe'):
        if message.channel.id not in subscribed_channels:
            await client.send_message(message.channel, "Error: Channel is not subscribed.")
        else:
            subscribed_channels.pop(message.channel.id, None)
            await client.send_message(message.channel, "Channel unsubscribed.")

    if message.content.startswith('!mlatest'):
        await client.send_message(message.channel, "{} - {}: https://www.youtube.com/watch?v={}".format(music_list["sound"][0]["descTxt2En"], music_list["sound"][0]["titleEn"], music_list["sound"][0]["youtubeID"]))

    if message.content.startswith('!mfind'):
        if len(message.content.split()) > 1:
            song = ' '.join(message.content.split()[1:])

            for item in music_list["sound"]:
                if item["titleEn"].lower() == song.lower():
                    await client.send_message(message.channel, "{} - {}: https://www.youtube.com/watch?v={}".format(item["descTxt2En"], item["titleEn"], item["youtubeID"]))
                    return
            
            await client.send_message(message.channel, "Error: song not found")
            
        else:
            await client.send_message(message.channel, "Error: no input specified")
    
    if message.content.startswith('!maintheme'):
        await client.send_message(message.channel, "{}: https://www.youtube.com/watch?v={}".format(music_list["maintheme"][0]["titleEn"], music_list["maintheme"][0]["youtubeID"]))

    if message.content.startswith('!help'):
        description="Commands: `!un/subscribe`, `!mlatest`, `!mfind <song title>`, `!maintheme`, `!char <id>`, `!help`\n[GitHub](https://github.com/john-best/SmashMusicBot)"
        embed = discord.Embed(description=description, color=0x5bc0de)
        embed.set_author(name="Smash Ultimate News Bot", icon_url=client.user.default_avatar_url)
        await client.send_message(message.channel, embed=embed)

    if message.content.startswith('!mlist'):
        text = "```"
        text += "{}: https://www.youtube.com/watch?v={}\n".format(music_list["maintheme"][0]["titleEn"], music_list["maintheme"][0]["youtubeID"])
        for song in music_list["sound"]:
            text += "{} - {}: https://www.youtube.com/watch?v={}\n".format(song["descTxt2En"], song["titleEn"], song["youtubeID"])
        text += "```"
        await client.send_message(message.channel, text)

    if message.content.startswith('!char'):
        if len(message.content.split()) < 2:
            await client.send_message(message.channel, "Error: Need id")
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
                    await client.send_message(message.channel, embed=embed)
                    return

            await client.send_message(message.channel, "Error: unable to find fighter!")



@client.event
async def on_ready():
    await load_music_list()
    await load_news_list()
    await load_fighters_list()
    await client.change_presence(game=discord.Game(name='!help for Smash Ultimate'))

client.run(config.token)
