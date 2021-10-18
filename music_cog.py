import discord
from discord import File
from discord.ext import commands
from youtube_dl import YoutubeDL
import random
import os
import os.path
from math import floor

class music_cog(commands.Cog):

    current_track = ''

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
        return {'source': info['formats'][0]['url'], 'title': info['title'], 'duration': info['duration'],
                'view_count': info['view_count']}

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

    # Dodaje wybrany utwór do kolejki
    @commands.command(name="play", aliases=["p"])
    async def play(self, ctx, *args):
        embed = discord.Embed(color=discord.Color.blurple())
        query = " ".join(args)
        if not ctx.message.author.voice:
            embed.add_field(name='Invalid use of command',
                            value='In order to use this command you need to be connected to a voice channel')
            await ctx.send(embed=embed)
        else:
            voice_channel = ctx.author.voice.channel
            song = self.search_yt(query)
            if type(song) == type(True):
                embed.add_field(name='Could not find given song',
                                value="Unfortunately the song you wanted to play isn't in our library.")
                await ctx.send(embed=embed)
            else:
                self.music_queue.append([song, voice_channel])
                embed.add_field(name=str(self.music_queue[len(self.music_queue) - 1][0]['title']),
                                value='was added to the queue', inline=False)
                await ctx.send(embed=embed)
                if not self.is_playing:
                    await self.play_music()

    # Dodaje wybrany utwór do początku kolejki
    @commands.command(name="force_play", aliases=["fp"])
    async def force_play(self, ctx, *args):
        embed = discord.Embed(color=discord.Color.blurple())
        query = " ".join(args)
        if not ctx.message.author.voice:
            embed.add_field(name='Invalid use of command',
                            value='In order to use this command you need to be connected to a voice channel')
        else:
            voice_channel = ctx.author.voice.channel
            song = self.search_yt(query)
            if type(song) == type(True):
                embed.add_field(name='Could not find given song',
                                value="Unfortunately the song you wanted to play isn't in our library.")
            else:
                self.music_queue.insert(0, [song, voice_channel])
                embed.add_field(name=str(self.music_queue[0][0]['title']),
                                value='was added to the top of the queue')
                if self.is_playing == False:
                    await self.play_music()
        await ctx.send(embed=embed)

    # Pomija obecny utwór i odtwarza wybrany utwór
    @commands.command(name="skip_play", aliases=["sp"])
    async def skip_play(self, ctx, *args):
        embed = discord.Embed(color=discord.Color.blurple())
        query = " ".join(args)
        if not ctx.message.author.voice:
            embed.add_field(name='Invalid use of command',
                            value='In order to use this command you need to be connected to a voice channel')
        else:
            voice_channel = ctx.author.voice.channel
            song = self.search_yt(query)
            if type(song) == type(True):
                embed.add_field(name='Could not find given song',
                                value="Unfortunately the song you wanted to play isn't in our library.")
            else:
                self.music_queue.insert(0, [song, voice_channel])
                self.vc.stop()
                self.play_music()
                embed.add_field(name=str(self.music_queue[0][0]['title']),
                                value='was added to the top of the queue')
                if self.is_playing == False:
                    await self.play_music()
        await ctx.send(embed=embed)

    # Wyświetla kolejkę
    @commands.command(name="queue", aliases=["q"])
    async def queue(self, ctx):
        embed = discord.Embed(title='Queue', color=discord.Color.blurple())
        queue = ""
        queue_duration1 = 0
        for i in range(0, len(self.music_queue)):
            queue += str(i+1) + " | " + self.music_queue[i][0]['title'] + "\n"
            queue_duration1 += int(self.music_queue[i][0]['duration'])
        queue_duration2 = ''
        if queue_duration1 > 3599:
            queue_duration2 += str(floor(queue_duration1 / 3600)) + 'h ' + str(floor(queue_duration1 / 60 % 60)) + 'm '
        elif queue_duration1 > 59:
            queue_duration2 += str(floor(queue_duration1 / 60 % 60)) + 'm '
        queue_duration2 += str(queue_duration1 % 60) + 's'
        print(len(self.music_queue))
        print(queue)
        if queue != "":
            for n in range(0, len(self.music_queue)):
                duration = int(self.music_queue[n][0]['duration'])
                duration = str(int(duration / 60)) + 'm ' + str(duration % 60) + 's'
                embed.add_field(name=str(n+1)+' | '+self.music_queue[n][0]['title'],
                                value=duration, inline=False)
            embed.set_footer(text='Total queue duration: '+queue_duration2)
        else:
            embed.add_field(name='The queue is currently empty',
                            value='Use [-play] or [-p] to add songs to the queue', inline=False)
        await ctx.send(embed=embed)

    # Pomija obecnie odtwarzany utwór
    @commands.command(name="skip", aliases=["s"])
    async def skip(self, ctx):
        embed = discord.Embed(color=discord.Color.blurple())
        if self.is_playing:
            if len(self.music_queue) > 0:
                embed.add_field(name='Skip!',
                                value='Now playing: '+self.music_queue[0][0]['title'], inline=False)
            else:
                self.current_track = ''
                embed.add_field(name='Skip!',
                                value='The queue is currently empty\n'
                                      'Use [-play] or [-p] to add songs to the queue', inline=False)
            if self.vc != "" and self.vc:
                self.vc.stop()
                self.play_music()
        else:
            embed.add_field(name='Nothing is currently being played',
                            value='Use [-play] or [-p] to add songs to the queue', inline=False)
        await ctx.send(embed=embed)

    # Czyści kolejkę
    @commands.command(name='clear', aliases=['c'])
    async def clear(self, ctx):
        embed = discord.Embed(color=discord.Color.blurple())
        if len(self.music_queue) > 0:
            for n in range(0, len(self.music_queue)):
                self.music_queue.pop(0)
            embed.add_field(name='The queue has been cleared', value='Use [-play] or [-p] to add songs to the queue', inline=False)
        else:
            embed.add_field(name='The queue is already empty', value='Use [-play] or [-p] to add songs to the queue',
                            inline=False)
        await ctx.send(embed=embed)

    # Odtwarza utwory z kolejki w losowej kolejności
    @commands.command(name="shuffle", aliases=["sh"])
    async def shuffle(self, ctx):
        embed = discord.Embed(color=discord.Color.blurple())
        if len(self.music_queue) != 0:
            random.shuffle(self.music_queue)
            embed.add_field(name='Shuffle!', value='The queue has been shuffled successfully')
        else:
            embed.add_field(name='The queue is empty', value='Use [-play] or [-p] to add songs to the queue')
        await ctx.send(embed=embed)

    # Usuwa wybrany utwór z kolejki
    @commands.command(name='remove', aliases=['r'])
    async def remove(self, ctx, *args):
        embed = discord.Embed(color=discord.Color.blurple())
        rem = int(' '.join(args))
        if 1 <= rem <= len(self.music_queue):
            embed.add_field(name=str(self.music_queue[rem - 1][0]['title']),
                            value='has been removed from the queue')
            self.music_queue.pop(rem - 1)
        else:
            embed.add_field(name='Wrong song number given',
                            value="Make sure the position you want to remove is located in the queue")
        await ctx.send(embed=embed)

    # Wyświetla obecnie odtwarzany utwór
    @commands.command(name="now_playing", aliases=["np"])
    async def now_playing(self, ctx):

        embed = discord.Embed(
            #title='Now Playing',
            color=discord.Color.blurple()
        )
        if self.current_track != '':
            embed.add_field(name=self.current_track, value='is currently being played', inline=False)
        else:
            embed.add_field(name='Nothing is currently being played',
                            value='Use [-play] or [-p] to add songs to the queue', inline=False)
        await ctx.send(embed=embed)

    # Wyświetla następny utwór w kolejce
    @commands.command(name="next_song", aliases=["ns","nxt"])
    async def next_song(self, ctx):
        embed = discord.Embed(color=discord.Color.blurple())
        if len(self.music_queue) > 0:
            embed.add_field(name=self.music_queue[0][0]['title'], value='is up next in the queue', inline=False)
        else:
            embed.add_field(name='The queue is currently empty',
                            value='Use [-play] or [-p] to add songs to the queue', inline=False)
        await ctx.send(embed=embed)

    # Odłącza bota z kanału głosowego i zapisuje obecną kolejkę
    @commands.command(name="disconnect", aliases=["dsc"])
    async def disconnect(self, ctx):
        os.remove("playlist.txt")
        file = open("playlist.txt", "a+")
        file.write((self.current_track.lower() + '\n').replace('ą', 'a').replace('ć', 'c').replace('ę', 'e')
                   .replace('ł', 'l').replace('ń', 'n').replace('ó', 'o').replace('ś', 's').replace('ż' or 'ź',
                                                                                                    'z'))
        for n in range(0, len(self.music_queue)):
            file.write((self.music_queue[n][0]['title'].lower() + '\n').replace('ą', 'a').replace('ć', 'c')
                       .replace('ę', 'e').replace('ł', 'l').replace('ń', 'n').replace('ó', 'o').replace('ś', 's')
                       .replace('ż' or 'ź', 'z'))
        file.close()
        if self.current_track == '' and len(self.music_queue) == 0:
            await ctx.voice_client.disconnect()
        else:
            for n in range(0, len(self.music_queue)):
                self.music_queue.pop(0)
            await ctx.voice_client.disconnect()
            await ctx.send('Zapisano obecną kolejkę')
            await ctx.send('Bot został odłączony')

    # Przyłącza bota do kanału głosowego i uruchamia ostatnio graną kolejkę
    @commands.command(name='connect', aliases=["con"])
    async def connect(self, ctx):
        if not ctx.message.author.voice:
            await ctx.send('Dołącz do kanału głosowego, aby użyć tej komendy')
        else:
            def is_file_empty(x):
                return os.path.exists(x) and os.stat(x).st_size == 0

            file_path = "playlist.txt"
            is_empty = is_file_empty(file_path)
            if is_empty:
                await ctx.send("Playlista jest pusta")
            else:
                voice_channel = ctx.author.voice.channel
                with open('playlist.txt', 'r+') as file:
                    for line in file:
                        song = self.search_yt(line)
                        self.music_queue.append([song, voice_channel])
                        if not self.is_playing:
                            await self.play_music()
                            await ctx.send("Przywrócono ostatnią kolejkę")

    # Tworzy playlistę z utworych w kolejcę
    @commands.command(name='create_playlist', aliases=['create', 'cp'])
    async def create_playlist(self, ctx, *args):
        embed = discord.Embed(color=discord.Color.blurple())

        save_path = "playlists/"
        name = " ".join(args)
        file_name = name+'.txt'
        full_path = os.path.join(save_path,file_name)
        file = open(full_path, 'a+')
        file.truncate(0)

        if self.current_track == '' and len(self.music_queue) == 0:
            await ctx.send('Nie ma playlisty do zapisania')
            embed.add_field(name='There is no queue to be saved as a playlist',
                            value='Use [-play] or [-p] to add songs to the queue')
        else:
            embed.add_field(name='Please wait', value='while your playlist is being processed')
            await ctx.send(embed=embed)
            embed.remove_field(0)
            file.write((self.current_track.lower() + '\n').replace('ą', 'a').replace('ć', 'c').replace('ę', 'e')
                       .replace('ł', 'l').replace('ń', 'n').replace('ó', 'o').replace('ś', 's').replace('ż' or 'ź',
                                                                                                        'z'))
            for n in range(0, len(self.music_queue)):
                file.write((self.music_queue[n][0]['title'].lower() + '\n').replace('ą', 'a').replace('ć', 'c')
                           .replace('ę', 'e').replace('ł', 'l').replace('ń', 'n').replace('ó', 'o').replace('ś', 's')
                           .replace('ż' or 'ź', 'z'))
            file.close()
            embed.add_field(name='Playlist "'+name+'"', value='has been created successfully')
        await ctx.send(embed=embed)

    # Dodaje piosenki z kolejki do playlisty
    @commands.command(name='append_playlist', aliases=['ap'])
    async def append_playlist(self, ctx, *args):
        embed = discord.Embed(color=discord.Color.blurple())

        file_path = "playlists/"
        name = " ".join(args)
        file_name = name + '.txt'
        full_path = os.path.join(file_path, file_name)
        file = open(full_path, 'a+')

        if self.current_track == '' and len(self.music_queue) == 0:
            await ctx.send('Nie ma playlisty do zapisania')
            embed.add_field(name='There is no queue to be saved as a playlist',
                            value='Use [-play] or [-p] to add songs to the queue')
        else:
            embed.add_field(name='Please wait', value='while your playlist is being processed')
            await ctx.send(embed=embed)
            embed.remove_field(0)
            file.write((self.current_track.lower() + '\n').replace('ą', 'a').replace('ć', 'c').replace('ę', 'e')
                       .replace('ł', 'l').replace('ń', 'n').replace('ó', 'o').replace('ś', 's').replace('ż' or 'ź',
                                                                                                        'z'))
            for n in range(0, len(self.music_queue)):
                file.write((self.music_queue[n][0]['title'].lower() + '\n').replace('ą', 'a').replace('ć', 'c')
                           .replace('ę', 'e').replace('ł', 'l').replace('ń', 'n').replace('ó', 'o').replace('ś', 's')
                           .replace('ż' or 'ź', 'z'))
            embed.add_field(name='Playlist "' + name + '"', value='has been created successfully')
        await ctx.send(embed=embed)

    # Wyświetla wszystkie zapisane playlisty
    @commands.command(name='show_playlists', aliases=['shp'])
    async def show_playlists(self, ctx):
        embed = discord.Embed(color=discord.Color.blurple())
        my_list = os.listdir('playlists/')
        print(my_list)
        for element in my_list:
            file = open('playlists/'+element, "r")
            line_count = 0
            for line in file:
                if not line == '\n':
                    line_count += 1
            file.close()
            line_count -= 1
            playlist_name = element.replace('.txt', ' ')
            embed.add_field(name=playlist_name, value=str(line_count)+' tracks in this playlist', inline=False)
        await ctx.send(embed=embed)

    # Pokazuje utwory w playliscie

    # Usuwa wybrane utwory z playlisty

    # Czyści kolejkę i odtwarza utwory z playlisty
    @commands.command(name='open_playlist', aliases=['op'])
    async def open_playlist(self, ctx, *args):
        embed = discord.Embed(color=discord.Color.blurple())

        if not ctx.message.author.voice:
            embed.add_field(name='Invalid use of command',
                            value='In order to use this command you need to be connected to a voice channel')
        else:
            def is_file_empty(x):
                return os.path.exists(x) and os.stat(x).st_size == 0

            save_path = "playlists/"
            file_name = " ".join(args)
            full_path = os.path.join(save_path, file_name + '.txt')

            if is_file_empty(full_path):
                embed.add_field(name='This playlist is empty',
                                value='In order to add tracks to a playlist use the [-create_playlist] command')
            else:
                voice_channel = ctx.author.voice.channel
                for n in range(0, len(self.music_queue)):
                    self.music_queue.pop(0)
                with open(full_path, 'r+') as file:
                    count = 0
                    for line in file:
                        song = self.search_yt(line)
                        self.music_queue.append([song, voice_channel])
                        if not self.is_playing:
                            await self.play_music()
                        else:
                            if count == 0:
                                self.vc.stop()
                                self.play_music()
                                embed.add_field(name=self.current_track, value='is currently being played')
                                await ctx.send(embed=embed)
                                embed.remove_field(0)
                        count += 1
                embed.add_field(name='Playlist loaded',
                                value='The queue has been replaced with the chosen playlist')
        await ctx.send(embed=embed)

    # Dodaje utwory z playlisty do kolejki
    @commands.command(name='play_playlist', aliases=['pp'])
    async def play_playlist(self, ctx, *args):
        embed = discord.Embed(color=discord.Color.blurple())

        if not ctx.message.author.voice:
            embed.add_field(name='Invalid use of command',
                            value='In order to use this command you need to be connected to a voice channel')
        else:
            def is_file_empty(x):
                return os.path.exists(x) and os.stat(x).st_size == 0

            save_path = "playlists/"
            file_name = " ".join(args)
            full_path = os.path.join(save_path, file_name + '.txt')

            if is_file_empty(full_path):
                embed.add_field(name='This playlist is empty',
                                value='In order to add tracks to a playlist use the [-create_playlist] command')
            else:
                voice_channel = ctx.author.voice.channel
                with open(full_path, 'r+') as file:
                    for line in file:
                        song = self.search_yt(line)
                        self.music_queue.append([song, voice_channel])
                        if not self.is_playing:
                            await self.play_music()
                embed.add_field(name='Playlist loaded',
                                value='Songs from the playlist have been added to the current queue')
        await ctx.send(embed=embed)

    # Wsztrymuje odtwarzanie utworów
    @commands.command(name="pause", aliases=['ps'])
    async def pause(self, ctx):
        await ctx.send(":pause_button: Pause")
        await ctx.voice_client.pause()

    # Wznawia odtwarzanie utworów
    @commands.command(name='resume', aliases=['rs'])
    async def resume(self, ctx):
        await ctx.send(":arrow_forward: Resume")
        await ctx.voice_client.resume()

    # Wyświetla ping bota
    @commands.command(name="ping")
    async def ping(self, ctx):
        bot_ping = round(self.bot.latency * 1000)
        if bot_ping in range(0, 200):
            await ctx.send(f":green_square: ping = {round(self.bot.latency * 1000)}ms")
        elif bot_ping in range(201, 400):
            await ctx.send(f":yellow_square: ping = {round(self.bot.latency * 1000)}ms")
        elif bot_ping > 400:
            await ctx.send(f":red_square: pong! {round(self.bot.latency * 1000)}ms")

    # Wysyła pliki bota
    @commands.command(name='code')
    async def code(self, ctx):
        await ctx.send(file=File('main.py'))
        await ctx.send(file=File('music_cog.py'))

    # Wyświetla listę komend bota
    @commands.command(name='help', aliases=['h'])
    async def help(self, ctx):

        embed = discord.Embed(
            title='Bot Commands',
            color=discord.Color.blurple()
        )
        kobi = 'http://marcinek.poznan.pl/source/strony/Pracownicy/2051827782.jpg'
        ss = 'https://cdn.discordapp.com/attachments/896336193745211392/898204632185176164/SoundSuite1.png'
        embed.set_thumbnail(
            url=kobi)
        embed.add_field(name='-play', value='[-p] Dodaje wybrany utwór do kolejki', inline=True)
        embed.add_field(name='-force_play', value='[-fp] Dodaje wybrany utwór do początku kolejki', inline=True)
        embed.add_field(name='-skip_play', value='[-sp] Pomija obecny utwór i odtwarza wybrany utwór', inline=True)

        embed.add_field(name='-queue', value='[-q] Wyświetla kolejkę', inline=True)
        embed.add_field(name='-skip', value='[-s] Pomija obecnie odtwarzany utwór', inline=True)
        embed.add_field(name='-remove', value='[-r] Usuwa wybrany utwór z kolejki', inline=True)
        embed.add_field(name='-shuffle', value='[-sh] Odtwarza utwory z kolejki w losowej kolejności', inline=True)
        embed.add_field(name='-clear', value='[-c] Czyści kolejkę', inline=True)
        embed.add_field(name='-now_playing', value='[-np] Wyświetla obecnie odtwarzany utwór', inline=True)

        embed.add_field(name='-disconnect', value='[-dsc] Rozłącza bota z kanału głosowego', inline=True)
        embed.add_field(name='-connect', value='[-con] Podłącza bota do kanału głosowego', inline=True)

        embed.add_field(name='-create_playlist', value='[-cp] Tworzy playlistę z utworych w kolejcę', inline=True)
        embed.add_field(name='-append_playlist', value='[-ap] Tworzy playlistę z utworych w kolejcę', inline=True)
        embed.add_field(name='-show_playlists', value='[-shp] Tworzy playlistę z utworych w kolejcę', inline=True)
        embed.add_field(name='-open_playlist', value='[-op] Zastępuje obecną kolejkę utworami z playlisty', inline=True)
        embed.add_field(name='-play_playlist', value='[-pp] Dodaje utwory z playlisty do kolejki', inline=True)

        embed.add_field(name='-pause', value='[-ps] Wsztrymuje odtwarzanie utworów', inline=True)
        embed.add_field(name='-resume', value='[-rs] Wznawia odtwarzanie utworów', inline=True)

        embed.add_field(name='-ping', value='Wyświetla ping bota', inline=True)
        embed.add_field(name='-code', value='Wysyła pliki bota', inline=True)

        embed.set_footer(text='SoundSuite')
        await ctx.send(embed=embed)
