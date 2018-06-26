import asyncio
import discord
import requests

import config

MUSIC_LIST_JSON = "https://www.smashbros.com/assets_v2/data/sound.json"
NEWS_LIST_JSON = "https://www.smashbros.com/data/bs/en_US/json/en_US.json"

client = discord.Client()

subscribed_channels = {}
music_list = {}
news_list = {}

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
            print("New music not found... retrying in 1 hour")

        await asyncio.sleep(3600)

async def load_news_list():
    global news_list
    r = requests.get(NEWS_LIST_JSON)
    news_list = r.json()
    news_list = {}
    print('Loaded current news list.')
    client.loop.create_task(update_news_list())


async def update_news_list():
    global news_list
    await client.wait_until_ready()

    while not client.is_closed:
        r = requests.get(NEWS_LIST_JSON)
        new_news_list = r.json()

        # only one news post per day... music might be the same thing but i have no confirmation on that vs news posts
        if len(new_news_list) != len(news_list):
            title = new_news_list[0]["title"]["rendered"]
            description = new_news_list[0]["acf"]["editor"].replace("<p>", "").replace("<br />", " - ").replace("</p>", "").replace("\n", "")

            if new_news_list[0]["acf"]["link_url"] != "":
                description += "\n" + new_news_list[0]["acf"]["link_url"]

            embed = discord.Embed(title=title, description=description, color=0x5bc0de)

            if new_news_list[0]["acf"]["image1"]["url"] is not None:
                image_url = new_news_list[0]["acf"]["image1"]["url"].replace('/413752', 'https://www.smashbros.com')
                embed.set_image(url=image_url)

            for channel in subscribed_channels:
                await client.send_message(client.get_channel(channel), embed=embed)
            news_list = new_news_list

        else:
            print("New news not found... retrying in 1 hour")
        await asyncio.sleep(3600)

@client.event
async def on_message(message):
    global music_list
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

    if message.content.startswith('!latest'):
        await client.send_message(message.channel, "{} - {}: https://www.youtube.com/watch?v={}".format(music_list["sound"][0]["descTxt2En"], music_list["sound"][0]["titleEn"], music_list["sound"][0]["youtubeID"]))

    if message.content.startswith('!find'):
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
        description="Commands: `!un/subscribe`, `!latest`, `!find <song title>`, `!maintheme`, `!help`\n[GitHub](https://github.com/john-best/SmashMusicBot)"
        embed = discord.Embed(description=description, color=0x5bc0de)
        embed.set_author(name="Smash Ultimate Music Bot", icon_url=client.user.default_avatar_url)
        await client.send_message(message.channel, embed=embed)

    if message.content.startswith('!list'):
        text = "```"
        text += "{}: https://www.youtube.com/watch?v={}\n".format(music_list["maintheme"][0]["titleEn"], music_list["maintheme"][0]["youtubeID"])
        for song in music_list["sound"]:
            text += "{} - {}: https://www.youtube.com/watch?v={}\n".format(song["descTxt2En"], song["titleEn"], song["youtubeID"])
        text += "```"
        await client.send_message(message.channel, text)


@client.event
async def on_ready():
    await load_music_list()
    await load_news_list()
    await client.change_presence(game=discord.Game(name='!help for Smash Ultimate'))

client.run(config.token)
