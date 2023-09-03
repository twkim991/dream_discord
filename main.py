import discord, asyncio
import yt_dlp as youtube_dl
from discord.ext import commands
import urllib
import json
import re
import bs4
from selenium import webdriver
from discord_token import TOKEN

asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
 
app = commands.Bot(command_prefix='!',intents=discord.Intents.all())
 

@app.event
async def on_ready():
    print('Done')
    print(f'{app.user} 봇을 실행합니다')

@app.event
async def on_message(message):
    searchYoutubeHref={} # 유튜브 하이퍼링크 모음
    p = re.compile('^!..번역')
    language = [['한','영','일','중','서'], ['ko','en','ja','zh-CN','es']]
    if message.author == app.user:
        await app.process_commands(message)
        return

    if message.content.startswith('!검색'):
        Text = ""
        learn = message.content.split(" ")
        vrsize = len(learn)  # 배열크기
        vrsize = int(vrsize)
        for i in range(1, vrsize):  # 띄어쓰기 한 텍스트들 인식함
            Text = Text + " " + learn[i]
        encText = Text


        driver = webdriver.Chrome()
        driver.get('https://www.youtube.com/results?search_query='+encText) #유튜브 검색링크
        source = driver.page_source
        bs = bs4.BeautifulSoup(source, 'lxml')
        entire = bs.find_all('a', {'id': 'video-title'}) # a태그에서 video title 이라는 id를 찾음

        embed = discord.Embed(
            title="영상들!",
            description="검색한 영상 결과",
            colour=discord.Color.blue())

        for i in range(0, 5):
            entireNum = entire[i]
            entireText = entireNum.text.strip()  # 영상제목
            print(entireText)
            test1 = entireNum.get('href')  # 하이퍼링크
            print(test1)
            rink = 'https://www.youtube.com'+test1
            embed.add_field(name=str(i + 1) + '번째 영상', value='\n' + '[%s](<%s>)' % (entireText, rink),
                            inline=False)  # [텍스트](<링크>) 형식으로 적으면 텍스트 하이퍼링크 만들어집니다
            searchYoutubeHref[i] = rink
        await message.channel.send(embed=embed)
    
    if message.content.startswith('!재생 '):
        print('숫자로 말하면 검색한 결과 5개중에 하나 선택, 링크를 주면 해당 링크 재생목록에 넣고 재생')

    if message.content.startswith('!재생목록'):
        print('재생목록에 뭐가 들어있는지 확인시켜줌')

    if message.content.startswith('!재생목록 제거'):
        print('숫자로 말하면 재생목록에서 해당 번호의 노래를 제거함')

    if message.content.startswith('!재생방식 선택'):
        print('숫자로 말하면 노래를 한바퀴돌면 끝낼지/끝에서처음으로돌아가는지/랜덤으로돌아가는지 정함')

    if message.content.startswith('!주간인기곡'):
    print('웹크롤링으로 주간인기곡 가져와서 재생시켜줌')


    
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

app.run(TOKEN)
