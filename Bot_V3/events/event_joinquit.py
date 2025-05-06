#===============================================================================================================================================#
#========================================================EVENEMENT JOIN ET QUIT=================================================================#
#===============================================================================================================================================#
#importation des modules nécessaires
import discord
from discord.ext import commands
import datetime
import random
import json

#===============================================================================================================================================#
# Liste des embeds pour le channel de connexion
list_embed = ["Pram Heda dev", "Bot serveur leak"]

#===============================================================================================================================================#
# Définition de la classe
class JoinQuitEvents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        with open("configuration.json", "r") as f:
            self.config = json.load(f)

    #===============================================================================================================================================#
    # Événement join
    @commands.Cog.listener()
    async def on_member_join(self, member):
        welcome_channel = self.bot.get_channel(self.config.get("welcome_channel_id"))
        if welcome_channel:
            ts = int(datetime.datetime.now().timestamp())
            embed = discord.Embed(title="UN MEMBRE VIENT DE SPAWN", description=f"Bienvenue {member.mention} !!", color=discord.Color.green())
            embed.add_field(name="informations utilisateur : ", value=f"Utilisateur : {member.display_name}\n Depuis :  <t:{ts}:R>", inline=False)
            if member.avatar:
                embed.set_thumbnail(url=member.avatar.url)
            embed.set_footer(text=random.choice(list_embed))
            embed.timestamp = datetime.datetime.now()
            await welcome_channel.send(embed=embed)

    #===============================================================================================================================================#
    # Événement quit
    @commands.Cog.listener()
    async def on_member_remove(self, member):
        welcome_channel = self.bot.get_channel(self.config.get("welcome_channel_id"))
        if welcome_channel:
            ts = int(datetime.datetime.now().timestamp())
            embed = discord.Embed(title="UN ENCULE EST PARTIE", description=f"CIAO BATARD {member.mention} !!", color=discord.Color.red())
            embed.add_field(name="informations utilisateur : ", value=f"Utilisateur : {member.display_name}\n Depuis :  <t:{ts}:R>", inline=False)
            if member.avatar:
                embed.set_thumbnail(url=member.avatar.url)
            embed.set_footer(text=random.choice(list_embed))
            embed.timestamp = datetime.datetime.now()
            await welcome_channel.send(embed=embed)

#===============================================================================================================================================#
# Setup joinquit
async def setup(bot):
    await bot.add_cog(JoinQuitEvents(bot))
