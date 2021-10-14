from discord.ext import commands
from music_cog import music_cog

bot = commands.Bot(command_prefix='.')

bot.remove_command('help')

bot.add_cog(music_cog(bot))

bot.run("ODk1MDE3OTUyNzc1MTEwNzk2.YVycbA.9MxdbQuZM_Wx8_4ANpYPzXmzsqs")
