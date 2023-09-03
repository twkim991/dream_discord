import discord, asyncio
import yt_dlp as youtube_dl
from discord.ext import commands
from dico_token import Token
import urllib
import json
import re

asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
 
app = commands.Bot(command_prefix='!',intents=discord.Intents.all())
 
youtube_dl.utils.bug_reports_message = lambda: ''

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',  # bind to ipv4 since ipv6 addresses cause issues sometimes
}
 
ffmpeg_options = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn',
}
 
ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

@app.event
async def on_ready():
    print('Done')
    print(f'{app.user} 봇을 실행합니다')

@app.event
async def on_message(message):
    p = re.compile('^!..번역')
    language = [['한','영','일','중','서'], ['ko','en','ja','zh-CN','es']]
    if message.author == app.user:
        await app.process_commands(message)
        return

    if message.content.startswith('아~ 야스하고싶다~'):
        await message.channel.send('큰소리로 말하지 마 병신아')

    
    if (p.match(message.content)) != None:
        learn = message.content.split(" ")
        Text = ""

        client_id = "lFpJfkVMP9boqIkFN6vU"
        client_secret = "Gi1tS0JN1L"

        url = "https://openapi.naver.com/v1/papago/n2mt"
        sourceindex = language[0].index((learn[0])[1])
        source = language[1][sourceindex]
        targetindex = language[0].index((learn[0])[2])
        target = language[1][targetindex]
        
        vrsize = len(learn)  # 배열크기
        vrsize = int(vrsize)
        for i in range(1, vrsize): #띄어쓰기 한 텍스트들 인식함
            Text = Text+" "+learn[i]
        encText = urllib.parse.quote(Text)
        data = f"source={source}&target={target}&text=" + encText

        request = urllib.request.Request(url)
        request.add_header("X-Naver-Client-Id", client_id)
        request.add_header("X-Naver-Client-Secret", client_secret)

        response = urllib.request.urlopen(request, data=data.encode("utf-8"))

        rescode = response.getcode()
        if (rescode == 200):
            response_body = response.read()
            data = response_body.decode('utf-8')
            data = json.loads(data)
            tranText = data['message']['result']['translatedText']
        else:
            print("Error Code:" + rescode)

        print('번역된 내용 :', tranText)
        await message.channel.send(tranText)

    await app.process_commands(message)

    


@app.command()
async def hello(message):
    await message.channel.send('Hi!')

@app.command()
async def join(ctx):
    print(ctx.author.voice)
    if ctx.author.voice and ctx.author.voice.channel:
        channel = ctx.author.voice.channel
        await ctx.send("봇이 {0.author.voice.channel} 채널에 입장합니다.".format(ctx))
        await channel.connect()
        print("음성 채널 정보: {0.author.voice}".format(ctx))
        print("음성 채널 이름: {0.author.voice.channel}".format(ctx))
    else:
        await ctx.send("음성 채널에 유저가 존재하지 않습니다. 1명 이상 입장해 주세요.")

@app.command()
async def out(ctx):
    try:
        await ctx.voice_client.disconnect()
        await ctx.send("봇을 {0.author.voice.channel} 에서 내보냈습니다.".format(ctx))
    except IndexError as error_message:
        print(f"에러 발생: {error_message}")
        await ctx.send("{0.author.voice.channel}에 유저가 존재하지 않거나 봇이 존재하지 않습니다.\\n다시 입장후 퇴장시켜주세요.".format(ctx))
    except AttributeError as not_found_channel:
        print(f"에러 발생: {not_found_channel}")
        await ctx.send("봇이 존재하는 채널을 찾는 데 실패했습니다.")

app.run('MTE0NTMyOTE4Mjg2ODUyNTA5Ng.GP6ZCg.OJcx8DYpd7D4Pqbcd0YMzMYrGiRhZK4z2OeaCE')
