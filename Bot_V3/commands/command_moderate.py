#===============================================================================================================================================#
#========================================================COMMANDE DE MODERATION=================================================================#
#===============================================================================================================================================#
#importation des modules nécessaires
import discord
from discord.ext import commands, tasks
from discord import app_commands
import datetime
import random
import calendar
import time
import asyncio
import json
import socket
import requests

#===============================================================================================================================================#
#temp passé pour le timestamp
ts = calendar.timegm(time.gmtime())

#===============================================================================================================================================#
# Liste des embeds pour le channel de connexion
list_embed = ["Pram Heda dev", "Bot serveur leak"]

#===============================================================================================================================================#
#définition de la classe
class CommandModerate(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.muted_users = {}
        self.check_mutes.start()
        self.deleted_message = None
        with open("configuration.json", "r") as f:
            self.config = json.load(f)

#===============================================================================================================================================#
#enregristrer le dernier message supprimé
    @commands.Cog.listener()
    async def on_message_delete(self, message):
        self.deleted_message = message

#===============================================================================================================================================#
# commande pour afficher le dernier message supprimé
    @commands.command(name="snipe", description="Affiche le dernier message supprimé", help="!snipe")
    async def snipe(self, ctx):
        """
        Commande pour afficher le dernier message supprimé.

        Cette commande affiche le dernier message qui a été supprimé dans le canal actuel.
        """
        if self.deleted_message is None:
            await ctx.send("Aucun message supprimé récemment.", delete_after=5)
            return

        embed = discord.Embed(
            title="Dernier message supprimé",
            description=self.deleted_message.content,
            color=discord.Color.orange()
        )
        embed.set_author(name=self.deleted_message.author.name, icon_url=self.deleted_message.author.avatar.url)
        embed.timestamp = self.deleted_message.created_at
        await ctx.send(embed=embed)

#===============================================================================================================================================#
    # Commande pour afficher l'adresse IP publique
    @commands.command(name="ip", description="Affiche ton adresse IP publique.", help="!ip")
    @commands.guild_only()
    async def ip(self, ctx, member: discord.Member = None):  
        """
        Affiche l'adresse IP publique de l'utilisateur qui a appelé la commande,
        ou l'adresse IP publique du bot.
        """

        # Utilisation d'un service externe pour obtenir l'IP publique
        try:
            ip = requests.get("https://httpbin.org/ip").json()["origin"]
        except requests.RequestException as e:
            await ctx.send(f"Erreur lors de la récupération de l'IP publique: {e}")
            return

        # Si aucun membre n'est mentionné, on affiche l'IP publique du bot
        if member is None:
            await ctx.send(f"Ton adresse IP publique est : `{ip}`")
        else:
            # Pour un membre mentionné, la même IP publique du bot est renvoyée
            await ctx.send(f"L'adresse IP publique du membre {member.mention} est : `{ip}`")

#===============================================================================================================================================#
# commande de bannissement
    @commands.command(name="ban", description="Bannir un membre du serveur", help="!ban @user [raison]")
    @commands.guild_only()
    @commands.has_permissions(ban_members=True)
    @commands.cooldown(1, 5.0, commands.BucketType.user)  # Cooldown de 5 secondes par utilisateur
    async def ban(self, ctx, member: discord.Member, *, reason: str = "Violation des règles"):
        """
        Commande de bannissement.

        Cette commande bannit un utilisateur du serveur avec une raison optionnelle. 
        """
        embed = discord.Embed(title="Utilisateur banni", description=f"{member.mention} a été banni", color=discord.Color.red())
        embed.add_field(name="Raison", value=reason, inline=False)
        embed.set_footer(icon_url=self.bot.user.avatar.url, text=random.choice(list_embed))
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url)
        embed.set_thumbnail(url=member.avatar.url)
        embed.timestamp = datetime.datetime.now()

        await ctx.send(embed=embed, delete_after=5)
        log_channel_id = self.bot.get_channel(self.config.get("log_channel_id"))
        log_channel = self.bot.get_channel(log_channel_id)
        if log_channel:
            await log_channel.send(embed=embed)

        await member.ban(reason=reason)

    # Gestion des erreurs pour la commande préfixe
    @ban.error
    async def ban_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("Vous n'avez pas la permission de bannir des membres.", ephemeral=True)
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Argument manquant. Utilisation : `!ban @membre [raison]`.", ephemeral=True)
        else:
            pass

#===============================================================================================================================================#
# commande de débannissement
    @commands.command(name="unban", description="Débannir un utilisateur du serveur", help="!unban id [raison]")
    @commands.guild_only()
    @commands.has_permissions(ban_members=True)
    @commands.cooldown(1, 5.0, commands.BucketType.user)  # Cooldown de 5 secondes par utilisateur
    async def unban(self, ctx, user_id: int, *, reason: str = "Réhabilitation"):
        """
        Commande de débannissement.

        Cette commande débannit un utilisateur du serveur et envoie un message de réhabilitation avec une invitation au serveur.
        """
        user = await self.bot.fetch_user(user_id)
        await ctx.guild.unban(user, reason=reason)

        embed = discord.Embed(title="Utilisateur débanni", description=f"{user.mention} a été débanni", color=discord.Color.green())
        embed.add_field(name="Raison", value=reason, inline=False)
        embed.set_footer(icon_url=self.bot.user.avatar.url, text=random.choice(list_embed))
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url)
        embed.set_thumbnail(url=user.avatar.url)
        embed.timestamp = datetime.datetime.now()

        await ctx.send(embed=embed, delete_after=5)
        log_channel_id = self.bot.get_channel(self.config.get("log_channel_id"))
        log_channel = self.bot.get_channel(log_channel_id)
        if log_channel:
            await log_channel.send(embed=embed)

        # Créer une invitation au serveur
        invite_link = await ctx.guild.text_channels[0].create_invite()

        # Préparer le message embed pour le DM
        embed_dm = discord.Embed(
            title="Réhabilitation",
            description=f"{user.mention} Vous avez été réhabilité sur {ctx.guild.name}",
            color=discord.Color.green()
        )
        embed_dm.add_field(name="Raison", value=reason, inline=False)
        embed_dm.add_field(name="Invitation au serveur", value=f"[Cliquez ici pour rejoindre le serveur]({invite_link})", inline=False)
        embed_dm.set_footer(icon_url=self.bot.user.avatar.url, text=random.choice(list_embed))
        embed_dm.set_thumbnail(url=ctx.guild.icon.url)
        embed_dm.timestamp = datetime.datetime.now()

        # Envoyer le message en DM à l'utilisateur débanni
        try:
            await user.send(embed=embed_dm)
        except discord.Forbidden:
            print(f"Impossible d'envoyer un message privé à {user.name}#{user.discriminator}")

    # Gestion des erreurs pour la commande préfixe
    @unban.error
    async def unban_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("Vous n'avez pas la permission de débannir des membres.", ephemeral=True)
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Argument manquant. Utilisation : `!unban id [raison]`.", ephemeral=True)
        else:
            pass

#===============================================================================================================================================#
# commande de kick
    @commands.command(name="kick", description="Kick un utilisateur du serveur", help="!kick @user [raison]")
    @commands.guild_only()
    @commands.has_permissions(kick_members=True)
    @commands.cooldown(1, 5.0, commands.BucketType.user)  # Cooldown de 5 secondes par utilisateur
    async def kick(self, ctx, member: discord.Member, *, reason: str = "Violation des règles"):
        """
        Commande de kick un utilisateur du serveur.

        Cette commande exclut un utilisateur du serveur avec une raison optionnelle.
        """

        embed = discord.Embed(title="Utilisateur kick", description=f"{member.mention} a été kick", color=discord.Color.red())
        embed.add_field(name="Raison", value=reason, inline=False)
        embed.set_footer(icon_url=self.bot.user.avatar.url, text=random.choice(list_embed))
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url)
        embed.set_thumbnail(url=member.avatar.url)
        embed.timestamp = datetime.datetime.now()

        await ctx.send(embed=embed, delete_after=5)
        log_channel_id = self.bot.get_channel(self.config.get("log_channel_id"))
        log_channel = self.bot.get_channel(log_channel_id)
        if log_channel:
            await log_channel.send(embed=embed)

        await member.kick(reason=reason)

    # Gestion des erreurs pour la commande préfixe
    @kick.error
    async def kick_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("Vous n'avez pas la permission de kick des membres.", ephemeral=True)
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Argument manquant. Utilisation : `!kick @membre [raison]`.", ephemeral=True)
        else:
            pass
        

#===============================================================================================================================================#
# commande clear
    @commands.command(name="clear", description="Supprimer un nombre spécifique de messages du canal actuel", help="!clear [nombre] [canal]")
    @commands.guild_only()
    @commands.cooldown(1, 5.0, commands.BucketType.user)  # Cooldown de 5 secondes par utilisateur
    async def clear(self, ctx: commands.Context, amount: int, channel: discord.TextChannel = None) -> discord.Message:
        """
        Commande pour supprimer un nombre spécifique de messages.

        Cette commande supprime un nombre donné de messages du canal actuel ou d'un canal spécifié.
        """
        
        is_limit_reached = amount < 1

        if is_limit_reached:
            return await ctx.send("Vous ne pouvez supprimer que 1 ou plus de messages.", delete_after=5)

        channel = ctx.message.channel 
        if channel is None:
            channel = ctx.channel
        
        await ctx.channel.purge(limit=amount)

        embed = discord.Embed(title="Messages supprimés", description=f"{amount} messages ont été supprimés", color=discord.Color.green())
        embed.set_footer(icon_url=self.bot.user.avatar.url, text=random.choice(list_embed))
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url)
        embed.set_thumbnail(url=ctx.guild.icon.url)
        embed.timestamp = datetime.datetime.now()

        await ctx.send(embed=embed, delete_after=5)
        log_channel_id = self.bot.get_channel(self.config.get("log_channel_id"))
        log_channel = self.bot.get_channel(log_channel_id)
        if log_channel:
            await log_channel.send(embed=embed)

    # Gestion des erreurs pour la commande préfixe
    @clear.error
    async def clear_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("Vous n'avez pas la permission de gérer les messages.", delete_after=5, ephemeral=True)
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Argument manquant. Utilisation : !clear [nombre].", delete_after=5, ephemeral=True)
        else:
            await ctx.send("Une erreur s'est produite lors de l'exécution de cette commande.", delete_after=5, ephemeral=True)

#===============================================================================================================================================#
# commande mute
    @commands.command(name="mute", description="Mute un utilisateur", help="!mute @user <temps> [raison]")
    @commands.has_permissions(manage_messages=True)
    @commands.guild_only()
    @commands.cooldown(1, 5.0, commands.BucketType.user)
    async def mute(self, ctx, member: discord.Member, time: str, *, reason: str = "Aucune raison fournie"):
        """
        Commande pour mute un membre.

        Cette commande applique un mute à un membre pour une durée spécifiée et envoie un message de confirmation.
        """
        bot_role = discord.utils.get(ctx.guild.roles, name="Serveur Leak")
        member_role = member.top_role
        log_channel_id = self.bot.get_channel(self.config.get("log_channel_id"))
        log_channel = self.bot.get_channel(log_channel_id)

        await log_channel.send(f"ID du membre: {member.id}\nRoles du membre: {[role.name for role in member.roles]}")

        if member.id == ctx.guild.owner_id:
            await ctx.send("ESPECE D'ENCULE, TU ESSAYE DE MUTE LE GRAND CHEF !", delete_after=5)
            return

        if member_role >= bot_role:
            await ctx.send("Je ne peux pas mute un membre avec un rôle plus élevé ou égal au mien.", delete_after=5)
            return
        
        guild = ctx.guild

        mutedRole = discord.utils.get(guild.roles, name="muted")
        
        if not mutedRole:
            mutedRole = await guild.create_role(name="muted")

        for channel in guild.channels:
            await channel.set_permissions(mutedRole, speak=False, send_messages=False, read_message_history=True, read_messages=False)

        self.muted_users[member.id] = {
        "roles": [role for role in member.roles if role != guild.default_role],
        "end_time": datetime.datetime.now() + self.parse_time(time)
        }

        await member.remove_roles(*self.muted_users[member.id]["roles"], reason=reason)
        await member.add_roles(mutedRole, reason=reason)

        time_convert = {"s": 1, "m": 60, "h": 3600, "j": 86400, "w": 604800, "mo": 2592000, "a": 31536000}
        try:
            tempmute = int(time[:-1]) * time_convert[time[-1]]
        except (ValueError, KeyError):
            await ctx.send("Format de temps invalide. Utilisation correcte : `<nombre><s|m|h|j|w|mo|a>`", delete_after=5, ephemeral=True)
            return

        embed = discord.Embed(title="Mute d'un membre", description=f"{member.mention} a été mute pour {time}", colour=discord.Colour.light_gray())
        embed.add_field(name="Raison:", value=reason, inline=True)
        embed.set_footer(icon_url=self.bot.user.avatar.url, text=random.choice(["Random message 1", "Random message 2"]))
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url)
        embed.set_thumbnail(url=member.avatar.url)
        embed.timestamp = datetime.datetime.now()

        await ctx.send(embed=embed, delete_after=5)

        if log_channel:
            await log_channel.send(embed=embed)
            await log_channel.send(f"ID du membre: {member.id}\nRoles du membre: {[role.name for role in member.roles]}")

        await asyncio.sleep(tempmute)

        await member.remove_roles(mutedRole, reason="Mute terminé")
        del self.muted_users[member.id]

        await member.send(f"Vous avez été unmute de {guild.name}")

    @mute.error
    async def mute_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("Vous n'avez pas la permission de mute ce membre.", delete_after=5)
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Argument manquant. Utilisation : !mute @membre <temps> [raison].", delete_after=5)
        else:
            pass

#===============================================================================================================================================#
# commande unmute
    @commands.command(name="unmute", description="Unmute un utilisateur", help="!unmute @user")
    @commands.has_permissions(manage_messages=True)
    @commands.guild_only()
    @commands.cooldown(1, 5.0, commands.BucketType.user)
    async def unmute(self, ctx, member: discord.Member):
        """
        Commande pour démute un membre.

        Cette commande enlève le mute d'un membre et restaure ses rôles précédents.
        """
        if member.id not in self.muted_users:
            await ctx.send("Ce membre n'est pas mute.", delete_after=5)
            return

        await self.unmute_member(ctx, member, "Unmute manuel par un modérateur")

    async def unmute_member(self, ctx, member, reason):
        mutedRole = discord.utils.get(ctx.guild.roles, name="muted")

        if mutedRole in member.roles:
            await member.remove_roles(mutedRole, reason=reason)
            await member.add_roles(*self.muted_users[member.id], reason=reason)
            del self.muted_users[member.id]

            await member.send(f"Vous avez été unmute de {ctx.guild.name}")

            embed = discord.Embed(title="Unmute d'un membre", description=f"{member.mention} a été unmute", colour=discord.Colour.green())
            embed.add_field(name="Raison:", value=reason, inline=True)
            embed.set_footer(icon_url=self.bot.user.avatar.url, text=random.choice(["Random message 1", "Random message 2"]))
            embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url)
            embed.set_thumbnail(url=member.avatar.url)
            embed.timestamp = datetime.datetime.now()

            await ctx.send(embed=embed, delete_after=5)
            log_channel_id = self.bot.get_channel(self.config.get("log_channel_id"))
            log_channel = self.bot.get_channel(log_channel_id)
            if log_channel:
                await log_channel.send(embed=embed)
                await log_channel.send(f"ID du membre: {member.id}\nRoles du membre: {[role.name for role in member.roles]}")
        else:
            await ctx.send("Ce membre n'est pas actuellement mute.", delete_after=5)

    @unmute.error
    async def unmute_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("Vous n'avez pas la permission de unmute ce membre.", delete_after=5)
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Argument manquant. Utilisation : !unmute @membre.", delete_after=5)
        else:
            pass

#===============================================================================================================================================#
#commande mute timeout
    #déclaration de la commande textuelle
    @commands.command(name="mute_time", description="Affiche le temps restant du mute d'un utilisateur", help="!mute_time @user")
    @commands.has_permissions(manage_messages=True)
    @commands.guild_only()
    #définition de la commande avec ses paramètres
    async def mute_time(self, ctx, member: discord.Member):
        """
        Commande pour afficher le temps restant du mute d'un membre.

        """
        #si le membre n'est pas mute
        if member.id not in self.muted_users:
            #envoyer un message et return
            await ctx.send("Ce membre n'est pas mute.", delete_after=5)
            return


        end_time = self.muted_users[member.id]["end_time"]
        remaining_time = end_time - datetime.datetime.now()
        if remaining_time.total_seconds() <= 0:
            await ctx.send("Le mute de ce membre est terminé.", delete_after=5)
            return

        await ctx.send(f"Temps restant du mute de {member.mention}: {str(remaining_time).split('.')[0]}", delete_after=10)

    def parse_time(self, time_str):
        time_convert = {"s": 1, "m": 60, "h": 3600, "j": 86400, "w": 604800, "mo": 2592000, "a": 31536000}
        try:
            return datetime.timedelta(seconds=int(time_str[:-1]) * time_convert[time_str[-1]])
        except (ValueError, KeyError):
            raise commands.BadArgument("Format de temps invalide. Utilisation correcte : `<nombre><s|m|h|j|w|mo|a>`")

    @tasks.loop(seconds=60)
    async def check_mutes(self):
        current_time = datetime.datetime.now()
        to_unmute = [member_id for member_id, data in self.muted_users.items() if data["end_time"] <= current_time]

        for member_id in to_unmute:
            guild = self.bot.get_guild(self.muted_users[member_id]["guild_id"])
            member = guild.get_member(member_id)
            if member:
                await self.unmute_member(None, member, "Mute terminé")

    @mute_time.error
    async def mute_time_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("Vous n'avez pas la permission de voir le temps restant du mute de ce membre.", delete_after=5)
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Argument manquant. Utilisation : !mute_time @membre.", delete_after=5)
        else:
            pass

#===============================================================================================================================================#
#commande slowmode
    @commands.command(name="slowmode", description="Active le slowmode dans un salon", help="!slowmode [temps en secondes] [#salon]")
    @commands.has_permissions(manage_channels=True)
    @commands.guild_only()
    async def slowmode(self, ctx: commands.Context, seconds: int, channel: discord.TextChannel = None) -> discord.Message:
        """
        Commande pour modifier le slowmode d'un salon.

        """
        if channel is None:
            channel = ctx.channel

        if not ctx.author.guild_permissions.manage_channels:
            return await ctx.send("Vous n'avez pas la permission de modifier le slowmode", delete_after=5)
        
        if ctx.guild is None:
            return await ctx.send("Commande non utilisable dans un message privé", delete_after=5)
        
        if seconds < 0 or seconds > 21600:
            return await ctx.send("Le temps doit être compris entre 0 et 21600 secondes", delete_after=5)
        
        if seconds == 0:
            await channel.edit(slowmode_delay=0)
            return await ctx.send("Le slowmode est maintenant désactivé", delete_after=5)
        
        await channel.edit(slowmode_delay=seconds)

        embed = discord.Embed(title="Salon en slowmode", description=f"Le slowmode a été modifié pour {channel.mention} pour {seconds} secondes", colour=discord.Colour.green())
        embed.set_footer(icon_url=self.bot.user.avatar.url, text=random.choice(["Random message 1", "Random message 2"]))
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url)
        embed.set_thumbnail(url=ctx.guild.icon.url)
        embed.timestamp = datetime.datetime.now()

        log_channel_id = self.bot.get_channel(self.config.get("log_channel_id"))
        log_channel = self.bot.get_channel(log_channel_id)
        if log_channel:
            await log_channel.send(embed=embed)

        await ctx.send(embed=embed, delete_after= 5)

    @slowmode.error
    async def slowmode_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("Vous n'avez pas la permission de faire cette commande.", delete_after=5)
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Argument manquant. Utilisation : !slowmode [temps] [#salon].", delete_after=5)
        else:
            pass

#===============================================================================================================================================#
#commande nick
    @commands.command(name="nick", description="Change le pseudo d'un membre", help="!nick @membre [nouveau pseudo]")
    @commands.has_permissions(manage_nicknames=True)
    @commands.guild_only()
    async def nick(self, ctx: commands.Context, member: discord.Member, *, nickname: str = ""):
        """
        Commande pour changer le pseudo d'un membre.

        """
        log_channel_id = self.bot.get_channel(self.config.get("log_channel_id"))
        log_channel = self.bot.get_channel(log_channel_id)

        if nickname == "":
            await member.edit(nick=None)

            embed_log = discord.Embed(title="Suppression de pseudo", description=f"Le pseudo de {member.mention} a été supprimé", colour=discord.Colour.green())
            embed_log.set_footer(icon_url=self.bot.user.avatar.url, text=random.choice(["Random message 1", "Random message 2"]))
            embed_log.set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url)
            embed_log.set_thumbnail(url=member.avatar.url)
            embed_log.timestamp = datetime.datetime.now()

            await ctx.send(embed=embed_log, delete_after= 5)

            return await log_channel.send(embed=embed_log)

        await member.edit(nick=nickname)

        embed = discord.Embed(title="Changement de pseudo", description=f"Le pseudo de {member.mention} a été changé en {nickname}", colour=discord.Colour.green())
        embed.set_footer(icon_url=self.bot.user.avatar.url, text=random.choice(["Random message 1", "Random message 2"]))
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url)
        embed.set_thumbnail(url=member.avatar.url)
        embed.timestamp = datetime.datetime.now()

        await ctx.send(embed=embed, delete_after= 5)

        if log_channel:
            await log_channel.send(embed=embed)

    @nick.error
    async def nick_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("Vous n'avez pas la permission de faire cette commande.", delete_after=5)
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Argument manquant. Utilisation : !nick [membre] [nouveau pseudo].", delete_after=5)
        else:
            pass

#===============================================================================================================================================#
#commande pour exclure
    @commands.command(name="ext", description="Expulser un membre pour un temps donné", help="!ext @membre [temps] [raison (facultatif)]")
    @commands.has_permissions(kick_members=True)
    @commands.guild_only()
    async def ext(self, ctx, member: discord.Member, time: str, *, reason: str = "Aucune raison fournie"):
        """
        Commande pour exclure un membre pour une durée donnée.

        """
        bot_role = discord.utils.get(ctx.guild.roles, name="Serveur Leak")
        member_role = member.top_role
        log_channel_id = self.bot.get_channel(self.config.get("log_channel_id"))
        log_channel = self.bot.get_channel(log_channel_id)

        if member.id == ctx.guild.owner_id:
            await ctx.send("ESPECE D'ENCULE, TU ESSAYE DE MUTE LE GRAND CHEF !", delete_after=5)
            return

        if member_role >= bot_role:
            await ctx.send("Je ne peux pas exclure un membre avec un rôle plus élevé ou égal au mien.", delete_after=5)
            return

        time_convert = {"s": 1, "m": 60, "h": 3600, "j": 86400, "w": 604800, "mo": 2592000, "a": 31536000}

        try:
            tempmute = int(time[:-1]) * time_convert[time[-1]]
        except (ValueError, KeyError):
            await ctx.send("Format de temps invalide. Utilisation correcte : `<nombre><s|m|h|j|w|mo|a>`", delete_after=5)
            return

        embed = discord.Embed(title="Exclusion d'un membre", description=f"{member.mention} a été exclu pour {time}", colour=discord.Colour.light_gray())
        embed.add_field(name="Raison:", value=f">{reason}", inline=True)
        embed.set_footer(icon_url=self.bot.user.avatar.url, text=random.choice(["Random message 1", "Random message 2"]))
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url)
        embed.set_thumbnail(url=member.avatar.url)
        embed.timestamp = datetime.datetime.now()

        await ctx.send(embed=embed, delete_after=5)

        if log_channel:
            await log_channel.send(embed=embed)

        await member.timeout(datetime.timedelta(seconds=tempmute), reason=f"{ctx.author.name} a exclu {member.name} pendant {time}.")

    @ext.error
    async def ext_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("Vous n'avez pas la permission d'exclure ce membre.", delete_after=5)
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Argument manquant. Utilisation : !ext @membre <temps> [raison].", delete_after=5)
        else:
            pass

#===============================================================================================================================================#
#commande pour désexclure
    @commands.command(name="unext", description="Annuler l'exclusion d'un membre", help="!unext @membre [raison (facultatif)]")
    @commands.has_permissions(kick_members=True)
    @commands.guild_only()
    async def unext(self, ctx, member: discord.Member, *, reason: str = "Aucune raison fournie"):
        """
        Commande pour annuler l'exclusion d'un membre.

        """
        log_channel_id = self.bot.get_channel(self.config.get("log_channel_id"))
        log_channel = self.bot.get_channel(log_channel_id)

        embed = discord.Embed(title="Annulation de l'exclusion d'un membre", description=f"{member.mention} a été unmute", colour=discord.Colour.light_gray())
        embed.add_field(name="Raison:", value=f">{reason}", inline=True)
        embed.set_footer(icon_url=self.bot.user.avatar.url, text=random.choice(["Random message 1", "Random message 2"]))
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url)
        embed.set_thumbnail(url=member.avatar.url)
        embed.timestamp = datetime.datetime.now()

        await ctx.send(embed=embed, delete_after=5)

        if log_channel:
            await log_channel.send(embed=embed)

        await member.timeout(None, reason=f"{ctx.author.name} a annulé l'exclusion de {member.name}.")

    @unext.error
    async def unext_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("Vous n'avez pas la permission de annuler l'exclusion de ce membre.", delete_after=5)
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Argument manquant. Utilisation : !unext @membre [raison].", delete_after=5)
        else:
            pass
        
#===============================================================================================================================================#
#setup moderation
async def setup(bot):
    await bot.add_cog(CommandModerate(bot))
