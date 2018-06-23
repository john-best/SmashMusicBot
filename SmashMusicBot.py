import requests
import discord
import asyncio
import config

MUSIC_LIST_JSON = "https://www.smashbros.com/assets_v2/data/sound.json"

client = discord.Client()

subscribed_channels = {}
music_list = {}

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

@client.event
async def on_ready():
    await load_music_list()
    await client.change_presence(
        game=discord.Game(name='!subscribe for Smash music updates')
    )

client.run(config.token)
