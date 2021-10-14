import discord
from discord import File
from discord.ext import commands
from youtube_dl import YoutubeDL
import random

class music_cog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot


        self.is_playing = False
        self.music_queue = []
        self.YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist':'True'}
        self.FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

        self.vc = ""

    def search_yt(self, item):
        with YoutubeDL(self.YDL_OPTIONS) as ydl:
            try:
                info = ydl.extract_info("ytsearch:%s" % item, download=False)['entries'][0]
            except Exception:
                return False

        return {'source': info['formats'][0]['url'], 'title': info['title']}

    def play_next(self):
        if len(self.music_queue) > 0:
            self.is_playing = True

            m_url = self.music_queue[0][0]['source']
            self.current_track = self.music_queue[0][0]['title']

            self.music_queue.pop(0)

            self.vc.play(discord.FFmpegPCMAudio(m_url, **self.FFMPEG_OPTIONS), after=lambda e: self.play_next())
        else:
            self.is_playing = False

    async def play_music(self):
        if len(self.music_queue) > 0:
            self.is_playing = True

            m_url = self.music_queue[0][0]['source']

            self.current_track = self.music_queue[0][0]['title']

            if self.vc == "" or not self.vc.is_connected() or self.vc == None:
                self.vc = await self.music_queue[0][1].connect()
            else:
                await self.vc.move_to(self.music_queue[0][1])

            print(self.music_queue)
            self.music_queue.pop(0)

            self.vc.play(discord.FFmpegPCMAudio(m_url, **self.FFMPEG_OPTIONS), after=lambda e: self.play_next())
        else:
            self.is_playing = False

    @commands.command(name="play", aliases=["p"])
    async def play(self, ctx, *args):
        query = " ".join(args)

        if not ctx.message.author.voice:
            await ctx.send('Dołącz do kanału głosowego, aby użyć tej komendy')
        else:
            voice_channel = ctx.author.voice.channel
            song = self.search_yt(query)
            if type(song) == type(True):
                await ctx.send("Nie znaleziono takiego utworu")
            else:
                self.music_queue.append([song, voice_channel])
                await ctx.send("Dodano do kolejki: " + str(self.music_queue[len(self.music_queue) - 1][0]['title']))

                if not self.is_playing:
                    await self.play_music()

    @commands.command(name="queue", aliases=["q"])
    async def queue(self, ctx):
        retval = ""
        for i in range(0, len(self.music_queue)):
            retval += str(i+1) + " | " + self.music_queue[i][0]['title'] + "\n"
        print(len(self.music_queue))
        print(retval)
        if retval != "":
            await ctx.send(retval)
        else:
            await ctx.send("Kolejka jest pusta")

    @commands.command(name='clear', aliases=['c'])
    async def clear(self, ctx):
        for n in range(0, len(self.music_queue)):
            self.music_queue.pop(0)
        await ctx.send('Wyczyszczono kolejkę')

    @commands.command(name="shuffle", aliases=["sh"])
    async def shuffle(self, ctx):
        if len(self.music_queue) != 0:
            random.shuffle(self.music_queue)
            await ctx.send('Pomieszano kolejkę')
            retval = ''
            for i in range(0, len(self.music_queue)):
                retval += str(i + 1) + " | " + self.music_queue[i][0]['title'] + "\n"
            print(len(self.music_queue))
            print(retval)
            await ctx. send(retval)
        else:
            await ctx.send("Kolejka jest pusta")

    @commands.command(name="nowplaying", aliases=["np"])
    async def nowplaying(self, ctx):
        if self.current_track != '':
            await ctx.send("Teraz leci: " + self.current_track)
        else:
            await ctx.send("Obecnie nic nie jest odtwarzane")

    @commands.command(name="skip", aliases=["s"])
    async def skip(self, ctx):
        if self.is_playing:
            if len(self.music_queue) > 0:
                await ctx.send("Skip! Teraz odtwarzam: " + self.music_queue[0][0]['title'])
            else:
                self.current_track = ''
                await ctx.send('Skip!')
            if self.vc != "" and self.vc:
                self.vc.stop()
                self.play_music()
        else:
            await ctx.send("Nic nie jest obecnie odtwarzane")

    @commands.command(name='remove', aliases=['r'])
    async def remove(self, ctx, *args):
        rem = int(' '.join(args))
        await ctx.send("Usunięto z kolejki utwór: " + str(self.music_queue[rem - 1][0]['title']))
        self.music_queue.pop(rem - 1)

    @commands.command(name="forceplay", aliases=["fp"])
    async def force_play(self, ctx, *args):
        query = " ".join(args)

        if not ctx.message.author.voice:
            await ctx.send("Dołącz do kanału głosowego, aby użyć tej komendy")
        else:
            voice_channel = ctx.author.voice.channel
            song = self.search_yt(query)
            if type(song) == type(True):
                await ctx.send("Nie znaleziono takiego utworu")
            else:
                self.music_queue.insert(0, [song, voice_channel])
                await ctx.send("Dodano na początek kolejki: " + str(self.music_queue[0][0]['title']))
                if self.is_playing == False:
                    await self.play_music()

    @commands.command(name="skipplay", aliases=["sp"])
    async def skip_play(self, ctx, *args):
        query = " ".join(args)

        if not ctx.message.author.voice:
            await ctx.send('Dołącz do kanału głosowego, aby użyć tej komendy')
        else:
            voice_channel = ctx.author.voice.channel
            song = self.search_yt(query)
            if type(song) == type(True):
                await ctx.send("Nie znaleziono takiego utworu")
            else:
                self.music_queue.insert(0, [song, voice_channel])
                self.vc.stop()
                self.play_music()
                await ctx.send("Skip! Teraz odtwarzam: " + str(self.music_queue[0][0]['title']))
                if self.is_playing == False:
                    await self.play_music()

    @commands.command(name="disconnect", aliases=["d","wypierdalaj"])
    async def disconnect(self, ctx):
        self.vc.stop()
        await ctx.voice_client.disconnect()
        await ctx.send('Bot został odłączony')

    @commands.command(name="pause", aliases=['ps'])
    async def pause(self,ctx):
      await ctx.send(":pause_button: Pause")
      await ctx.voice_client.pause()

    @commands.command(name='resume', aliases=['rs'])
    async def resume(self,ctx):
      await ctx.send(":arrow_forward: Resume")
      await ctx.voice_client.resume()

    @commands.command(name="ping")
    async def ping(self, ctx):
        bot_ping = round(self.bot.latency * 1000)
        if bot_ping in range(0,200):
            await ctx.send(f":green_square: pong! {round(self.bot.latency * 1000)}ms")
        elif bot_ping in range(201,400):
            await ctx.send(f":yellow_square: pong! {round(self.bot.latency * 1000)}ms")
        elif bot_ping > 400:
            await ctx.send(f":red_square: pong! {round(self.bot.latency * 1000)}ms")

    @commands.command(name='help', aliases=['h'])
    async def help(self, ctx):

        embed = discord.Embed(
            title='Bot Commands',
            color=discord.Color.blurple()
        )
        embed.set_thumbnail(
            url='https://cdn.discordapp.com/attachments/896336193745211392/898204632185176164/SoundSuite1.png')
        embed.add_field(name='-play', value='[-p] Dodaje wybrany utwór do kolejki', inline=True)
        embed.add_field(name='-skip', value='[-s] Pomija obecny utwór', inline=True)
        embed.add_field(name='-nowplaying', value='[-np] Wyświetla obecnie odtwarzany utwór', inline=True)
        embed.add_field(name='-forceplay', value='[-fp] Dodaje wybrany utwór do początku kolejki', inline=True)
        embed.add_field(name='-skipplay', value='[-sp] Pomija obecny utwór i odtwarza wybrany utwór', inline=True)
        embed.add_field(name='-queue', value='[-q] Wyświetla kolejkę', inline=True)
        embed.add_field(name='-remove', value='[-r] Usuwa wybrany utwór z kolejki', inline=True)
        embed.add_field(name='-shuffle', value='[-sh] Odtwarza utwory z kolejki w losowej kolejności', inline=True)
        embed.add_field(name='-clear', value='[-c] Czyści kolejkę', inline=True)
        embed.add_field(name='-disconnect', value='[-d] Rozłącza bota', inline=True)
        embed.add_field(name='-pause', value='[-ps] Wsztrymuje odtwarzanie utworów', inline=True)
        embed.add_field(name='-resume', value='[-rs] Wznawia odtwarzanie utworów bota', inline=True)
        embed.add_field(name='-ping', value='Wyświetla ping bota', inline=True)
        embed.set_footer(text='SoundSuite™')
        await ctx.send(embed=embed)

    @commands.command(name='code')
    async def code(self, ctx):
        await ctx.send(file=File('main.py'))
        await ctx.send(file=File('music_cog.py'))

    @commands.command(name='')

