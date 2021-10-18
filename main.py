from discord.ext import commands
from music_cog import music_cog

bot = commands.Bot(command_prefix='-')
bot.remove_command('help')
bot.add_cog(music_cog(bot))
bot.run("ODkxMzQzNDA3NzI3OTIzMjcx.YU8-PA.SfhIUGNuRF1GWn_dlxd3x-JLrM8")