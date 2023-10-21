import asyncio
 
import discord
import yt_dlp as youtube_dl
 
from discord.ext import commands, tasks
from discord_token import Token

import urllib
import json
import re
import bs4
from selenium import webdriver
 
# Suppress noise about console usage from errors
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

searchYoutubeHref={} # 검색결과 저장장소
playlist=[] # 노래 재생목록
global loop
loop = True
 
# youtube 음악과 로컬 음악의 재생을 구별하기 위한 클래스 작성.
class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
 
        self.data = data
 
        self.title = data.get('title')
        self.url = data.get('url')
 
    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
 
        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]
 
        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)
 




# 음악 재생 클래스. 커맨드 포함.
class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def join(self, ctx, *, channel: discord.VoiceChannel):
        """보이스 채널에 봇을 입장시킴"""
 
        if ctx.voice_client is not None:
            return await ctx.voice_client.move_to(channel)
 
        await channel.connect()
 
    @commands.command()
    async def select(self, ctx, *, query):
        """검색기능을 이용한 노래 재생"""
        try:
            number = int(query)
            select_song = searchYoutubeHref[number-1]
            playlist.insert(0, select_song)
            i = 0
            while True:
                async with ctx.typing():
                    print(playlist[0])
                    player = await YTDLSource.from_url(playlist[0], loop=self.bot.loop, stream=True)
                    print(player)
                    ctx.voice_client.play(player, after=lambda e: print(f'Player error: {e}') if e else None)
                await ctx.send(f'Now playing: {player.title}')
                while ctx.voice_client.is_playing():
                    await asyncio.sleep(0.1)
                if loop:
                    if i < len(playlist) - 1:
                        i = i + 1
                    else:
                        i = 0
                    continue
                elif i < len(playlist) - 1:
                    i = i + 1
                    continue
                break
        except Exception as e:
            print('play error')
            print(e)
            return
 
    @commands.command()
    async def play(self, ctx, *, query):
        """플레이리스트에 있는 노래 재생"""
        try:
            number = int(query)
            select_song = playlist[number-1]
            i = 0
            while True:
                async with ctx.typing():
                    player = await YTDLSource.from_url(playlist[0], loop=self.bot.loop, stream=True)
                    ctx.voice_client.play(player, after=lambda e: print(f'Player error: {e}') if e else None)
                await ctx.send(f'Now playing: {player.title}')
                while ctx.voice_client.is_playing():
                    await asyncio.sleep(0.1)
                if loop:
                    if i < len(playlist) - 1:
                        i = i + 1
                    else:
                        i = 0
                    continue
                elif i < len(playlist) - 1:
                    i = i + 1
                    continue
                break
        except:
            print('play error')
            return
 
    @commands.command()
    async def stream(self, ctx, *, url):
        """url을 이용한 노래 재생"""
        try:
            playlist.insert(0, url)
            i = 0
            global loop
            print(loop)
            while True:
                async with ctx.typing():
                    player = await YTDLSource.from_url(playlist[0], loop=self.bot.loop, stream=True)
                    ctx.voice_client.play(player, after=lambda e: print(f'Player error: {e}') if e else None)
                await ctx.send(f'Now playing: {player.title}')
                while ctx.voice_client.is_playing():
                    await asyncio.sleep(0.1)
                if loop:
                    if i < len(playlist) - 1:
                        i = i + 1
                    else:
                        i = 0
                    continue
                elif i < len(playlist) - 1:
                    i = i + 1
                    continue
                break
        except:
            print('stream error')
            return
    
    @commands.command()
    async def volume(self, ctx, volume: int):
        """볼륨 변경"""
 
        if ctx.voice_client is None:
            return await ctx.send("음성 채널에 유저가 존재하지 않습니다.")
 
        ctx.voice_client.source.volume = volume / 100
        await ctx.send(f"변경된 볼륨: {volume}%")
 
    @commands.command()
    async def stop(self, ctx):
        """노래를 멈추고 보이스채널에서 봇을 쫒아냄"""
 
        await ctx.voice_client.disconnect()

    @commands.command()
    async def loop(self, ctx):
        """노래의 루프 기능을 끄거나 킴"""
        try:
            global loop
            if loop == False:
                loop = True
            else:
                loop = False
            await ctx.send(f"현재 LOOP 상태: {loop}")
        except:
            await print("loop error")

    @commands.command()
    async def playlist(self, ctx):
        """플레이리스트에 있는 노래 목록을 보여줌"""
        try:
            message = ""
            for i in range(len(playlist)):
                message = message + f'{i}' + ': ' + playlist[i] + '\n'
            await ctx.send(f"{message}")
        except:
            await print("playlist error")

    @commands.command()
    async def remove(self, ctx, *, num):
        """플레이리스트에서 특정 노래를 제거함"""
        try:
            del playlist[num]
            await ctx.send(f"플레이리스트에서 {num}번 곡을 제거하였습니다.")
        except:
            await print("add error")
 
    @commands.command()
    async def help(self, ctx):
        """명령어 목록을 유저한테 보여줌"""
        try:
            embed = discord.Embed(title="봇을 케이크처럼 쉽게 다루는 법", description='명령어 목록은 다음과 같습니다.', color=discord.Color.green())
            embed.add_field(name='ㅡㅡㅡㅡㅡㅡㅡㅡ번역 관련 명령어ㅡㅡㅡㅡㅡㅡㅡㅡ', value='\n저희 봇은 현재 한국어, 영어, 일본어, 중국어, 스페인어의 총 5가지 언어의 번역을 제공합니다.\n각각 한 영 일 중 서로 키워드되며 번역하고 싶은 방식에 맞춰 "!XX번역"이라고 한 다음 번역하고싶은 문장을 뒤에 넣으면 봇이 해당 문장을 번역해드립니다.\n(ex: !한영번역 안녕하세요)\n', inline=False)
            embed.add_field(name='ㅡㅡㅡㅡㅡㅡㅡㅡ노래 관련 명령어ㅡㅡㅡㅡㅡㅡㅡㅡ', value='\n노래 관련 기능을 사용하려면 기본적으로 명령어를 입력하려는 사용자가 음성 채널에 존재하는 상태여야 합니다. 먼저 음성 채널에 들어간 다음 명령어를 사용해주세요.\n\n**!검색** \n 뒤에 검색하고 싶은 문구를 덧붙이면 유튜브에서 해당 문구를 검색하여 최상단에 나오는 5개의 결과를 보여줍니다.(ex: !검색 애국가)\n\n**!select** \n 뒤에 검색한 결과 중 선택하고 싶은 검색결과를 선택하면 해당 번호의 노래를 재생합니다.(ex: !select 3)\n선택한 노래는 자동으로 플레이리스트의 첫번째에 추가됩니다.\n\n**!play** \n뒤에 번호를 지정하면 플레이리스트에서 선택한 번호의 노래를 재생합니다.(ex: !play 1)\n\n**!stream** \n 뒤에 유튜브 링크를 덧붙이면 해당 링크의 노래를 재생합니다.(ex: !stream https://www.youtube.com/watch?v=XrnQgWzsRVQ)\n선택한 노래는 자동으로 플레이리스트의 첫번째에 추가됩니다.\n\n**!volume** \n 뒤에 원하는 퍼센트를 덧붙이면 노래의 볼륨을 조절합니다.(ex: !volume 50)\n기본 볼륨은 100입니다.\n\n**!stop** \n 노래 재생을 중지하고 봇을 현재 음성 채널에서 쫒아냅니다.\n\n**!loop** \n 플레이리스트의 마지막 노래까지 재생한다음 루프를 반복할지 그냥 노래 재생이 끝나게 할지를 정합니다.\n기본 상태에서는 루프를 반복합니다.\n\n**!playlist** \n 현재 플레이리스트에 존재하는 모든 곡을 보여줍니다.\n\n**!remove** \n 뒤에 번호를 지정하면 플레이리스트에서 선택한 번호의 노래를 삭제합니다.(ex: !remove 0)', inline=False)
            await ctx.send(embed=embed)
        except:
            await print("help error")

    @select.before_invoke
    @play.before_invoke
    @stream.before_invoke
    async def ensure_voice(self, ctx):
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send("음성 채널에 유저가 존재하지 않습니다. 음성 채널에 먼저 입장해주세요.")
                raise commands.CommandError("Author not connected to a voice channel.")
        elif ctx.voice_client.is_playing():
            ctx.voice_client.stop()


 
intents = discord.Intents.default()
intents.message_content = True
 
bot = commands.Bot(
    command_prefix=commands.when_mentioned_or("!"),
    description='Relatively simple music bot example',
    intents=intents,
    help_command=None,
)
 
 
@bot.event
async def on_ready():
    print(f'{bot.user} 봇을 실행합니다')
    print('------')
 

@bot.event
async def on_message(message):
    
    if message.author == bot.user:
        await bot.process_commands(message)
        return

    # 번역기 기능
    p = re.compile('^!..번역')
    language = [['한','영','일','중','서'], ['ko','en','ja','zh-CN','es']]
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

    #노래검색기능
    if message.content.startswith('!검색'):
        Text = ""
        learn = message.content.split(" ")
        vrsize = len(learn)  # 배열크기
        vrsize = int(vrsize)
        for i in range(1, vrsize):  # 띄어쓰기 한 텍스트들 인식함
            Text = Text + " " + learn[i]
        encText = Text


        options = webdriver.ChromeOptions()
        options.add_argument("headless")
        driver = webdriver.Chrome(options=options)
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
    
    

    await bot.process_commands(message)

    
 
 
async def main():
    async with bot:
        await bot.add_cog(Music(bot))
        await bot.start(Token)
 
 
asyncio.run(main())