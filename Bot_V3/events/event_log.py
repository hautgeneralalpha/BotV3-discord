#===============================================================================================================================================#
#========================================================EVENEMENT LOG DU SERVEUR===============================================================#
#===============================================================================================================================================#
#importation des modules nécessaires
import discord
from discord.ext import commands
import random

#===============================================================================================================================================#
# Liste des embeds pour le channel de connexion
list_embed = ["Pram Heda dev", "Bot serveur leak"]

# ID du salon de journalisation
LOG_CHANNEL_ID = 1367458777657507880

#===============================================================================================================================================#
#définition de la classe
class EventLog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

#===============================================================================================================================================#
    # Fonction pour envoyer des messages de log au salon de journalisation
    async def send_log_message(self, title, description, color=discord.Color.blue()):
        log_channel = self.bot.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            embed = discord.Embed(title=title, description=description, color=color)
            embed.set_footer(text=random.choice(list_embed))
            await log_channel.send(embed=embed)
        else:
            print(f"Salon de log avec l'ID {LOG_CHANNEL_ID} non trouvé.")

#===============================================================================================================================================#
    # Événement déclenché lors de la création d'un salon
    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        await self.send_log_message(
            "Nouveau Salon Créé",
            f"Le salon '{channel.name}' a été créé.",
            color=discord.Color.green()
        )

#===============================================================================================================================================#
    # Événement déclenché lors de la suppression d'un salon
    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        await self.send_log_message(
            "Salon Supprimé",
            f"Le salon '{channel.name}' a été supprimé.",
            color=discord.Color.red()
        )

#===============================================================================================================================================#
    # Événement déclenché lors de la mise à jour d'un salon
    @commands.Cog.listener()
    async def on_guild_channel_update(self, before, after):
        await self.send_log_message(
            "Salon Mis à Jour",
            f"Le salon '{before.name}' a été mis à jour en '{after.name}'.",
            color=discord.Color.orange()
        )

#===============================================================================================================================================#
    # Événement déclenché lorsqu'un membre est banni
    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        await self.send_log_message(
            "Membre Banni",
            f"Le membre '{user.name}' a été banni du serveur.",
            color=discord.Color.dark_red()
        )

#===============================================================================================================================================#
    # Événement déclenché lorsqu'un membre est débanni
    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):
        await self.send_log_message(
            "Membre Débanni",
            f"Le membre '{user.name}' a été débanni du serveur.",
            color=discord.Color.green()
        )

#===============================================================================================================================================#
    # Événement déclenché lorsqu'un membre rejoint le serveur
    @commands.Cog.listener()
    async def on_member_join(self, member):
        await self.send_log_message(
            "Membre Rejoint",
            f"Le membre '{member.name}' a rejoint le serveur.",
            color=discord.Color.green()
        )

#===============================================================================================================================================#
    # Événement déclenché lorsqu'un membre quitte le serveur
    @commands.Cog.listener()
    async def on_member_remove(self, member):
        await self.send_log_message(
            "Membre Parti",
            f"Le membre '{member.name}' a quitté le serveur.",
            color=discord.Color.red()
        )

#===============================================================================================================================================#
    # Événement déclenché lorsqu'un membre est mis à jour (ex : changement de pseudo)
    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if before.nick != after.nick:
            await self.send_log_message(
                "Pseudo Mis à Jour",
                f"Le membre '{before.name}' a changé son pseudo de '{before.nick}' à '{after.nick}'.",
                color=discord.Color.orange()
            )
        if before.roles != after.roles:
            before_roles = set(before.roles)
            after_roles = set(after.roles)
            added_roles = after_roles - before_roles
            removed_roles = before_roles - after_roles
            for role in added_roles:
                await self.send_log_message(
                    "Rôle Ajouté",
                    f"Le rôle '{role.name}' a été ajouté à '{before.name}'.",
                    color=discord.Color.blue()
                )
            for role in removed_roles:
                await self.send_log_message(
                    "Rôle Retiré",
                    f"Le rôle '{role.name}' a été retiré de '{before.name}'.",
                    color=discord.Color.blue()
                )

#===============================================================================================================================================#
    # Événement déclenché lorsqu'un message est supprimé
    @commands.Cog.listener()
    async def on_message_delete(self, message):
        await self.send_log_message(
            "Message Supprimé",
            f"Un message de '{message.author.name}' a été supprimé dans le salon '{message.channel.name}':\n{message.content}",
            color=discord.Color.red()
        )

#===============================================================================================================================================#
    # Événement déclenché lorsqu'un message est modifié
    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.content != after.content:
            await self.send_log_message(
                "Message Édité",
                f"Un message de '{before.author.name}' a été modifié dans le salon '{before.channel.name}':\nAvant: {before.content}\nAprès: {after.content}",
                color=discord.Color.orange()
            )

#===============================================================================================================================================#
#setup joinquit
async def setup(bot):
    await bot.add_cog(EventLog(bot))
