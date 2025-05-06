#===============================================================================================================================================#
# Importation des modules nécessaires à l'exécution du bot Discord
import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import random
import datetime
import asyncio
import json
from dotenv import load_dotenv
from discord.ui import Button, View, Select
from flask import Flask, jsonify
import sys
from keep_alive_server import keep_alive
import keep_alive_server
print(dir(keep_alive_server))

#===============================================================================================================================================#
# Charger les variables d'environnement depuis le fichier config
load_dotenv(dotenv_path="./.env")
TOKEN = os.getenv('DISCORD_TOKEN')

#===============================================================================================================================================#
# Définition des intents pour le bot Discord
intents = discord.Intents.all()
intents.members = True
intents.message_content = True
intents.guilds = True

#===============================================================================================================================================#
# Liste des utilisateurs dans les footer d'embed
list_embed = ["Pram Heda dev", "Bot 7eme compagnie"]

#===============================================================================================================================================#
# Initialisation du bot avec un préfixe '!' et intents
bot = commands.Bot(command_prefix='!', intents=intents)

#===============================================================================================================================================#
# Définir le chemin de ffmpeg
venv_path = "d:/Mes Documents/1 - DOCUMENTS/12 - PERSO/Bot_V3/.venv/Bot_Leak"
ffmpeg_path = os.path.join(venv_path, "ffmpeg", "ffmpeg.exe")

# Passer le chemin de ffmpeg aux cogs
bot.ffmpeg_path = ffmpeg_path

#===============================================================================================================================================#
# Chemin du fichier JSON pour la configuration
CONFIG_FILE = "configuration.json"

#===============================================================================================================================================#
# Variable globale pour indiquer si une déconnexion est demandée
shutdown_requested = False

#===============================================================================================================================================#
# Fonction pour charger la configuration
def load_config():
    try:
        with open(CONFIG_FILE, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        print("Le fichier de configuration n'a pas été trouvé.")
        return {}
    except json.JSONDecodeError:
        print("Erreur lors de la lecture du fichier de configuration.")
        return {}

#===============================================================================================================================================#
# Chargement des commandes depuis le dossier commands
async def load_extensions():
    for filename in os.listdir('./commands'):
        if filename.endswith('.py'):
            await bot.load_extension(f'commands.{filename[:-3]}')
    for filename in os.listdir('./events'):
        if filename.endswith('.py'):
            await bot.load_extension(f'events.{filename[:-3]}')

#===============================================================================================================================================#
# Fonction pour envoyer ou mettre à jour l'embed d'état du bot avec emojis
async def update_bot_status_embed():
    global shutdown_requested
    channel_id = int(config.get("state_cannal_id"))
    channel = bot.get_channel(channel_id)
    
    if channel:
        embed_color = discord.Color.green() if not shutdown_requested else discord.Color.red()
        status_emoji = "🟢" if not shutdown_requested else "🟥"
        status_text = "en ligne" if not shutdown_requested else "hors ligne"

        embed = discord.Embed(
            title="État du Bot",
            description=f"{status_emoji} Le bot est maintenant **{status_text}**",
            color=embed_color
        )
        embed.add_field(name="Nom du Bot", value=bot.user.name, inline=False)
        embed.add_field(name="ID du Bot", value=bot.user.id, inline=False)
        embed.add_field(name="Date", value=f"<t:{int(datetime.datetime.now().timestamp())}:R>", inline=False)
        embed.set_footer(text=random.choice(list_embed))
        
        # Cherche un message d'état existant pour le mettre à jour
        async for message in channel.history(limit=100):
            if message.author == bot.user and message.embeds:
                await message.edit(embed=embed)
                if shutdown_requested:
                    shutdown_requested = False
                    await bot.close()
                return
        
        # Sinon, envoie un nouveau message
        await channel.send(embed=embed)
        if shutdown_requested:
            shutdown_requested = False
            await bot.close()

#===============================================================================================================================================#
# Événement déclenché lorsque le bot se connecte au serveur Discord
@bot.event
async def on_ready():
    global config
    config = load_config()

    print(f"Username: {bot.user.name}")
    print(f"User ID: {bot.user.id}")

    channel_connexion_id = int(config.get("notification_channel_id"))
    channel_connexion = bot.get_channel(channel_connexion_id)

    if channel_connexion:
        embed = discord.Embed(title="Bot en ligne !!", description="Le bot s'est connecté", color=discord.Color.green())
        ts = int(datetime.datetime.now().timestamp())
        embed.add_field(name="Informations utilisateur :", value=f"Date : <t:{ts}:R>\nRaison\nAllez faire vos achats", inline=False)
        embed.set_footer(text=random.choice(list_embed))
        embed.timestamp = datetime.datetime.now()
        await channel_connexion.send(embed=embed)

    print(f'Logged in as {bot.user.name}')
    await load_extensions()
    await bot.tree.sync(guild=discord.Object(id=1367454775108567144))

    # Mise à jour de l'état du bot
    await update_bot_status_embed()

#===============================================================================================================================================#
# Affichage des commandes par pagination
class CommandPagination(View):
    def __init__(self, ctx, embeds, timeout=60):
        super().__init__(timeout=timeout)
        self.ctx = ctx
        self.embeds = embeds
        self.current_page = 0

        self.previous_button = Button(emoji="⬅️", style=discord.ButtonStyle.primary)
        self.next_button = Button(emoji="➡️", style=discord.ButtonStyle.primary)
        self.previous_button.callback = self.previous_page
        self.next_button.callback = self.next_page

        self.update_buttons()
        self.add_item(self.previous_button)
        self.add_item(self.next_button)

    async def previous_page(self, interaction: discord.Interaction):
        self.current_page -= 1
        await self.update_embed(interaction)

    async def next_page(self, interaction: discord.Interaction):
        self.current_page += 1
        await self.update_embed(interaction)

    def update_buttons(self):
        self.previous_button.disabled = self.current_page == 0
        self.next_button.disabled = self.current_page == len(self.embeds) - 1

    async def update_embed(self, interaction: discord.Interaction):
        self.update_buttons()
        await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)

@bot.command(name='commands')
async def commands_list(ctx, command_name=None):
    if command_name:
        command = bot.get_command(command_name)
        if command:
            description = command.description or "Pas de description"
            usage = f"Usage: !{command.name}"
            examples = command.help or "Pas d'exemple fourni"

            embed = discord.Embed(
                title=f"Aide pour la commande '{command_name}'",
                description=description,
                color=discord.Color.blue()
            )
            embed.add_field(name="Usage", value=usage[:1024], inline=False)
            embed.add_field(name="Exemple", value=examples[:1024], inline=False)
            if command.aliases:
                aliases = ", ".join(command.aliases)
                embed.add_field(name="Alias", value=aliases[:1024], inline=False)
            embed.set_footer(text=random.choice(list_embed))
            await ctx.send(embed=embed)
        else:
            await ctx.send("Commande non trouvée.")
    else:
        cogs_display_names = {
            'Event': 'Économie',
            'CommandFun': 'Commandes diverses',
            'CommandModerate': 'Administration',
            'CommandLevel': 'Gestion Niveau',
            'CommandLogistic' : 'Commande Logistique',
            'CommandNSFW' : 'Commande pour adulte'
        }

        embeds = []
        for cog_name, display_name in cogs_display_names.items():
            cog = bot.get_cog(cog_name)
            if cog:
                commands_list = [f"**{command.name}**: {command.description}" for command in cog.get_commands() if not command.hidden]
                embed = discord.Embed(title=f"Commandes de {display_name}", color=discord.Color.blue())
                commands_text = "\n".join(commands_list)
                embed.add_field(name="> Commandes", value=commands_text, inline=False)
                embed.set_footer(text=random.choice(list_embed))
                embeds.append(embed)

        if embeds:
            view = CommandPagination(ctx, embeds)
            await ctx.send(embed=embeds[0], view=view)
        else:
            await ctx.send("Aucune commande disponible.")

#===============================================================================================================================================#
# Affichage de la vue de configuration
class ConfigView(View):
    def __init__(self, bot, ctx):
        super().__init__(timeout=60)
        self.bot = bot
        self.ctx = ctx
        self.add_item(SelectConfig(bot))
        self.add_item(CancelButton(label="Annuler", style=discord.ButtonStyle.danger, custom_id="annuler_config"))

#===============================================================================================================================================#
# Sélecteur de configuration avec bouton Annuler
class SelectConfig(Select):
    def __init__(self, bot):
        options = [
            discord.SelectOption(label="Canal de logs", value="log_channel_id"),
            discord.SelectOption(label="Canal de bienvenue", value="welcome_channel_id"),
            discord.SelectOption(label="Argent par message", value="money_per_message"),
            discord.SelectOption(label="XP par message", value="xp_per_message"),
            discord.SelectOption(label="Canal de notifications", value="notification_channel_id"),
            discord.SelectOption(label="Canal vocal automatique", value="vocal_channel_id"),
            discord.SelectOption(label="Canal d'état du bot", value="state_cannal_id"),
            discord.SelectOption(label="Role boosté pour xp", value="role_booster_ex"),
            discord.SelectOption(label="Coefficient de boost XP", value="boost_xp_coeff"),
            discord.SelectOption(label="Canal NSFW", value="channel_nsfw")
        ]
        super().__init__(placeholder="Choisissez une option à configurer...", min_values=1, max_values=1, options=options)
        self.bot = bot

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        config_type = self.values[0]
        
        if config_type == "role_booster_ex":
            role_name = "BOOST XP"
            guild = interaction.guild
            existing_role = discord.utils.get(guild.roles, name=role_name)
            
            if not existing_role:
                # Créer le rôle s'il n'existe pas
                role = await guild.create_role(name=role_name)
                role_id = role.id
                # Mettre à jour le fichier JSON avec le nouvel ID de rôle
                await self.update_config("role_booster_ex", str(role_id))
                embed = discord.Embed(
                    title="Rôle créé",
                    description=f"Le rôle `{role_name}` a été créé avec l'ID {role_id}.",
                    color=discord.Color.green()
                )
            else:
                role_id = existing_role.id
                embed = discord.Embed(
                    title="Rôle existant",
                    description=f"Le rôle `{role_name}` existe déjà avec l'ID {role_id}.",
                    color=discord.Color.yellow()
                )

            await interaction.channel.send(embed=embed)

            # Demander le coefficient de boost à l'utilisateur
            await interaction.channel.send("Veuillez entrer le coefficient de boost XP dans le chat.")

            def check(m):
                return m.author == interaction.user and m.channel == interaction.channel

            try:
                user_message = await self.bot.wait_for('message', timeout=60.0, check=check)
                new_value = user_message.content
                await self.update_config("boost_xp_coeff", new_value)
                
                update_embed = discord.Embed(
                    title="Configuration mise à jour",
                    description=f"Le coefficient de boost XP est maintenant {new_value}.",
                    color=discord.Color.green()
                )
                update_embed.set_footer(text=random.choice(list_embed))
                await interaction.followup.send(embed=update_embed)

                # Afficher la vue de confirmation
                confirm_view_message = await interaction.channel.send(embed=discord.Embed(title="Confirmation", description="La configuration est-elle terminée ?", color=discord.Color.blue()))
                confirm_view = ConfirmView(interaction.channel, interaction.user, message=confirm_view_message)
                await confirm_view_message.edit(view=confirm_view)

                # Mettre à jour l'embed de l'état du bot si la configuration du canal d'état a changé
                if config_type == "state_cannal_id":
                    await update_bot_status_embed()

            except asyncio.TimeoutError:
                timeout_embed = discord.Embed(
                    title="Temps écoulé",
                    description="Vous avez mis trop de temps pour répondre. La configuration a été annulée.",
                    color=discord.Color.red()
                )
                timeout_embed.set_footer(text=random.choice(list_embed))
                await interaction.followup.send(embed=timeout_embed)

            finally:
                await user_message.delete()

        else:
            embed = discord.Embed(
                title="Configuration",
                description=f"Veuillez entrer la nouvelle valeur pour `{config_type}` dans le chat.",
                color=discord.Color.blue()
            )
            embed.add_field(name="Option", value=config_type, inline=False)
            embed.set_footer(text=random.choice(list_embed))
            
            message = await interaction.channel.send(embed=embed)
            
            def check(m):
                return m.author == interaction.user and m.channel == interaction.channel

            try:
                user_message = await self.bot.wait_for('message', timeout=60.0, check=check)
                new_value = user_message.content
                await self.update_config(config_type, new_value)
                
                update_embed = discord.Embed(
                    title="Configuration mise à jour",
                    description=f"`{config_type}` = {new_value}",
                    color=discord.Color.green()
                )
                update_embed.set_footer(text=random.choice(list_embed))
                await interaction.followup.send(embed=update_embed)

                # Afficher la vue de confirmation
                confirm_view_message = await interaction.channel.send(embed=discord.Embed(title="Confirmation", description="La configuration est-elle terminée ?", color=discord.Color.blue()))
                confirm_view = ConfirmView(interaction.channel, interaction.user, message=confirm_view_message)
                await confirm_view_message.edit(view=confirm_view)

                # Mettre à jour l'embed de l'état du bot si la configuration du canal d'état a changé
                if config_type == "state_cannal_id":
                    await update_bot_status_embed()

            except asyncio.TimeoutError:
                timeout_embed = discord.Embed(
                    title="Temps écoulé",
                    description="Vous avez mis trop de temps pour répondre. La configuration a été annulée.",
                    color=discord.Color.red()
                )
                timeout_embed.set_footer(text=random.choice(list_embed))
                await interaction.followup.send(embed=timeout_embed)

            finally:
                await message.delete()

    async def update_config(self, key, value):
        with open(CONFIG_FILE, 'r') as file:
            config = json.load(file)
        config[key] = value
        with open(CONFIG_FILE, 'w') as file:
            json.dump(config, file, indent=4)

#===============================================================================================================================================#
# Vue pour confirmer la fin de configuration
class ConfirmView(View):
    def __init__(self, channel, user, message=None):
        super().__init__(timeout=60)
        self.channel = channel
        self.user = user
        self.message = message
        self.add_item(ConfirmButton(label="Oui", style=discord.ButtonStyle.success, custom_id="oui"))
        self.add_item(ConfirmButton(label="Non", style=discord.ButtonStyle.danger, custom_id="non"))

    async def on_timeout(self):
        if self.message:
            try:
                await self.message.delete()
            except discord.NotFound:
                pass

#===============================================================================================================================================#
# Bouton de confirmation
class ConfirmButton(Button):
    def __init__(self, label, style, custom_id):
        super().__init__(label=label, style=style, custom_id=custom_id)

    async def callback(self, interaction: discord.Interaction):
        confirm_view = self.view  # Get the parent view
        if self.custom_id == 'oui':
            await interaction.message.delete()
            await self.cleanup_messages(interaction.channel, interaction.user)
        elif self.custom_id == 'non':
            await interaction.message.delete()
            # Additional handling if needed when "Non" is clicked

    async def cleanup_messages(self, channel, user):
        def is_user_message(message):
            return message.author == user or message.author == bot.user

        async for message in channel.history(limit=None):
            if message.content.startswith('!configbot') and message.author == user:
                await message.delete()
                break

            if is_user_message(message):
                await message.delete()

#===============================================================================================================================================#
# Commande de configuration du bot
@bot.command(name='configbot')
async def configbot(ctx):
    embed = discord.Embed(
        title="Configuration du Bot",
        description="Choisissez ce que vous souhaitez configurer :",
        color=discord.Color.green()
    )
    embed.set_footer(text=random.choice(list_embed))
    
    view = ConfigView(bot, ctx)

    message = await ctx.send(embed=embed, view=view)
    
    ctx.bot.configbot_message_id = message.id

#===============================================================================================================================================#
# Bouton d'annulation
class CancelButton(Button):
    def __init__(self, label, style, custom_id):
        super().__init__(label=label, style=style, custom_id=custom_id)

    async def callback(self, interaction: discord.Interaction):
        if self.custom_id == 'annuler_config':
            await interaction.message.delete()
            await self.cleanup_messages(interaction.channel, interaction.user)

    async def cleanup_messages(self, channel, user):
        async for message in channel.history(limit=None):
            if message.content.startswith('!configbot') and message.author == user:
                await message.delete()
                break

            if message.author == user or message.author == bot.user:
                await message.delete()


#===============================================================================================================================================#
# Commande de déconnexion du bot
@bot.command(name='shutdown')
@commands.is_owner()
async def shutdown(ctx):
    global shutdown_requested
    shutdown_requested = True

    # Créez un embed pour indiquer que le bot va se déconnecter
    embed = discord.Embed(
        title="Bot hors ligne !!",
        description="Le bot va se déconnecter",
        color=discord.Color.red()
    )
    ts = int(datetime.datetime.now().timestamp())
    embed.add_field(
        name="Informations utilisateur :", 
        value=f"Date : <t:{ts}:R>\nRaison : Le bot est arrêté", 
        inline=False
    )
    embed.set_footer(text=random.choice(list_embed))
    embed.timestamp = datetime.datetime.now()

    # Envoyer le message d'état de déconnexion dans le canal de notification
    channel_connexion_id = int(config.get("notification_channel_id"))
    channel_connexion = bot.get_channel(channel_connexion_id)
    if channel_connexion:
        await channel_connexion.send(embed=embed)

    # Mettre à jour l'embed de l'état du bot pour refléter qu'il est hors ligne
    await update_bot_status_embed()

#===============================================================================================================================================#
# Commande de redémarrage du bot
@bot.command(name='restart')
@commands.is_owner()
async def restart(ctx):
    await ctx.send("Le bot va redémarrer...", ephemeral=True)
    await bot.close()
    os.execv(sys.executable, ['python'] + sys.argv)

#===============================================================================================================================================#
# Connexion du bot
keep_alive()
bot.run(TOKEN)
