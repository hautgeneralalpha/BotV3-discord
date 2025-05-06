#===============================================================================================================================================#
#=============================================================COMMANDE DE FUN===================================================================#
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
from discord.ui import Button, View, Modal, Select, TextInput
import youtube_dl
from discord import FFmpegPCMAudio
import yt_dlp as youtube_dl
import aiohttp
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from discord.utils import get
import json
import os

#===============================================================================================================================================#
#temp passé pour le timestamp
ts = calendar.timegm(time.gmtime())

#===============================================================================================================================================#
# Liste des embeds pour le channel de connexion
list_embed = ["Pram Heda dev", "Bot serveur leak"]

#===============================================================================================================================================#
# Configuration Spotify
SPOTIPY_CLIENT_ID = '95d6ea59715142afa421593fe283be6a'
SPOTIPY_CLIENT_SECRET = '2e8b495dfe064f10a8754245f4f3c051'
# Authentification Spotify
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=SPOTIPY_CLIENT_ID,
                                                           client_secret=SPOTIPY_CLIENT_SECRET))


#===============================================================================================================================================#
#définition de la classe pour le Cog
class CommandFun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.music_queue = {}
        self.polls = {}   
        self.voters = {}  # Dictionnaire pour stocker les utilisateurs qui ont voté
        self.cooldowns = {}
        
        # Le chemin vers le fichier configuration.json (dans le dossier parent)
        self.configuration_file = os.path.join(os.path.dirname(__file__), "..", "configuration.json")
        self.message_id = None  # ID du message

        # Charger la configuration à partir du fichier JSON
        self.load_config()

        # Charger l'ID du message à partir du fichier de configuration
        self.load_message_id()

    def load_message_id(self):
        try:
            # Vérifier si la configuration a été correctement chargée
            if hasattr(self, 'config') and self.config:
                print("🛠️ ID du message :", self.config.get("message_id"))
                self.message_id = self.config.get("message_id")  # Récupérer l'ID du message
            else:
                print("Configuration non chargée ou vide.")
        except FileNotFoundError:
            pass  # Si le fichier n'existe pas, on continue sans erreur

    def load_config(self):
        try:
            with open(self.configuration_file, "r") as f:
                self.config = json.load(f)  # Charger la configuration
        except FileNotFoundError:
            self.config = {}  # Si le fichier n'existe pas, on initialise la configuration vide

    def save_message_id(self, message_id):
        try:
            # Charger les données actuelles du fichier
            with open(self.configuration_file, "r") as f:
                data = json.load(f)
        except FileNotFoundError:
            data = {}  # Si le fichier n'existe pas, créer un dictionnaire vide

        # Ajouter ou mettre à jour l'ID du message dans les données
        data["message_id"] = message_id

        # Sauvegarder les données dans le fichier
        with open(self.configuration_file, "w") as f:
            json.dump(data, f, indent=4)

#===============================================================================================================================================#
#commande avatar
    @app_commands.command(name="avatar", description="Récupérer l'avatar d'un membre (optionnel)")
    @app_commands.guilds(discord.Object(id=1367454775108567144))
    async def avatar(self, interaction: discord.Interaction, member: discord.Member = None):
        """
        Slash command pour récupérer l'avatar d'un membre.
        """
        if member is None:
            member = interaction.user

        embed = discord.Embed(
            title=f"Avatar de {member.name}",
            description=f"[Lien vers l'avatar]({member.display_avatar.url})",
            color=discord.Color.blue()
        )
        embed.set_image(url=member.display_avatar.url)

        # Vérifie que le bot a bien un avatar, sinon évite l'erreur
        if self.bot.user.avatar:
            embed.set_footer(icon_url=self.bot.user.avatar.url, text=random.choice(list_embed))

        if interaction.user.avatar:
            embed.set_author(name=interaction.user.name, icon_url=interaction.user.avatar.url)

        if interaction.guild and interaction.guild.icon:
            embed.set_thumbnail(url=interaction.guild.icon.url)

        embed.timestamp = datetime.datetime.now()

        await interaction.response.send_message(embed=embed)


#===============================================================================================================================================#
# Commande pour jouer de la musique
    @app_commands.command(name="play", description="Joue une chanson à partir d'une URL ou d'un nom.")
    @app_commands.guilds(discord.Object(id=1367454775108567144))
    @app_commands.guild_only()
    async def play(self, interaction: discord.Interaction, query: str):
        """ Slash command pour jouer de la musique """
        await interaction.response.defer()

        # Vérifie si l'utilisateur est dans un canal vocal
        voice_state = interaction.user.voice
        if voice_state is None or voice_state.channel is None:
            return await interaction.followup.send("❌ Vous devez être dans un salon vocal pour utiliser cette commande.")

        voice_channel = voice_state.channel

        # Initialise la queue si nécessaire
        guild_id = interaction.guild.id
        if guild_id not in self.music_queue:
            self.music_queue[guild_id] = {
                "channel": voice_channel,
                "queue": [],
                "is_playing": False
            }

        self.music_queue[guild_id]["queue"].append(query)

        if not self.music_queue[guild_id]["is_playing"]:
            await self.connect_to_channel(voice_channel)
            await self.play_music(interaction, interaction.guild)

        await interaction.followup.send(embed=discord.Embed(
            title="🎶 En attente",
            description=f"Ajout de **{query}** à la file d'attente.",
            color=discord.Color.blue()
        ))

    async def connect_to_channel(self, voice_channel):
        if not discord.utils.get(self.bot.voice_clients, guild=voice_channel.guild):
            await voice_channel.connect()

    async def play_music(self, interaction, guild):
        queue_info = self.music_queue[guild.id]
        voice_client = discord.utils.get(self.bot.voice_clients, guild=guild)

        if queue_info["queue"] and not queue_info["is_playing"]:
            queue_info["is_playing"] = True
            query = queue_info["queue"].pop(0)

            with youtube_dl.YoutubeDL({'format': 'bestaudio', 'noplaylist': True}) as ydl:
                info = ydl.extract_info(f"ytsearch:{query}", download=False)
                url = info['entries'][0]['url']

            voice_client.stop()
            voice_client.play(
                FFmpegPCMAudio(url, executable=self.bot.ffmpeg_path),
                after=lambda e: self.bot.loop.create_task(self.after_play(interaction, guild))
            )

            await interaction.followup.send(embed=discord.Embed(
                title="▶️ Lecture",
                description=f"Lecture de **{query}**.",
                color=discord.Color.green()
            ))

    async def after_play(self, interaction, guild):
        queue_info = self.music_queue[guild.id]

        if not queue_info["queue"]:
            voice_client = discord.utils.get(self.bot.voice_clients, guild=guild)
            if voice_client and voice_client.is_connected():
                await voice_client.disconnect()
                del self.music_queue[guild.id]
                await interaction.channel.send(embed=discord.Embed(
                    title="🔇 Déconnexion",
                    description="Plus de musique à jouer. Je me déconnecte.",
                    color=discord.Color.red()
                ))
        else:
            await self.play_music(interaction, guild)


#===============================================================================================================================================#
# Commande pour passer à la musique suivante
    @app_commands.command(name="skip", description="Passer à la musique suivante")
    @app_commands.guilds(discord.Object(id=1367454775108567144))  # ID du serveur
    @app_commands.guild_only()
    async def skip(self, interaction: discord.Interaction):
        """ Slash command pour passer à la musique suivante """

        await interaction.response.defer()

        guild_id = interaction.guild.id
        if guild_id not in self.music_queue or not self.music_queue[guild_id]["queue"]:
            return await interaction.followup.send("❌ Il n'y a pas de musique en cours de lecture.")

        voice_client = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
        if voice_client and voice_client.is_playing():
            voice_client.stop()
            await interaction.followup.send(embed=discord.Embed(
                title="⏭️ Passage",
                description="La musique en cours a été sautée.",
                color=discord.Color.orange()
            ))
            await self.play_music(interaction, interaction.guild)
        else:
            await interaction.followup.send(embed=discord.Embed(
                title="❌ Erreur",
                description="Il n'y a pas de musique dans la queue.",
                color=discord.Color.orange()
            ))


#===============================================================================================================================================#
# Commande pour supprimer toute la queue de musique
    @app_commands.command(name="clear_queue", description="Supprimer toute la file d'attente de musique")
    @app_commands.guilds(discord.Object(id=1367454775108567144))  # ID du serveur
    @app_commands.guild_only()
    async def clear_queue(self, interaction: discord.Interaction):
        """ Slash command pour supprimer la queue de musique """

        await interaction.response.defer()

        guild_id = interaction.guild.id
        if guild_id in self.music_queue:
            self.music_queue[guild_id]["queue"].clear()
            await interaction.followup.send(embed=discord.Embed(
                title="🗑️ Queue Effacée",
                description="La file d'attente de musique a été vidée.",
                color=discord.Color.red()
            ))
        else:
            await interaction.followup.send("❌ Il n'y a pas de file d'attente de musique à effacer.")


#===============================================================================================================================================#
# Commande pour mettre en pause la musique
    # Commande pour mettre en pause la musique
    @app_commands.command(name="pause", description="Mettre en pause la musique")
    @app_commands.guilds(discord.Object(id=1367454775108567144))  # ID du serveur
    @app_commands.guild_only()
    async def pause(self, interaction: discord.Interaction):
        """ Slash command pour mettre en pause la musique """

        await interaction.response.defer()

        voice_client = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
        if voice_client and voice_client.is_playing():
            voice_client.pause()
            await interaction.followup.send(embed=discord.Embed(
                title="⏸️ Pause",
                description="La musique a été mise en pause.",
                color=discord.Color.yellow()
            ))
        else:
            await interaction.followup.send("❌ Aucune musique n'est en cours de lecture pour être mise en pause.")


#===============================================================================================================================================#
# Commande pour reprendre la musique
    @app_commands.command(name="resume", description="Reprendre la musique")
    @app_commands.guilds(discord.Object(id=1367454775108567144))  # ID du serveur
    @app_commands.guild_only()
    async def resume(self, interaction: discord.Interaction):
        """ Slash command pour reprendre la musique """

        await interaction.response.defer()

        voice_client = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
        if voice_client and voice_client.is_paused():
            voice_client.resume()
            await interaction.followup.send(embed=discord.Embed(
                title="▶️ Reprise",
                description="La musique a été reprise.",
                color=discord.Color.green()
            ))
        else:
            await interaction.followup.send("❌ Aucune musique n'est en pause pour être reprise.")


#===============================================================================================================================================#
# Commande pour afficher la liste des musiques dans la queue
    @app_commands.command(name="queue", description="Afficher la liste des musiques dans la file d'attente")
    @app_commands.guilds(discord.Object(id=1367454775108567144))  # ID du serveur
    @app_commands.guild_only()
    async def queue(self, interaction: discord.Interaction):
        """ Slash command pour afficher la liste des musiques dans la file """

        await interaction.response.defer()

        guild_id = interaction.guild.id
        if guild_id in self.music_queue and self.music_queue[guild_id]["queue"]:
            queue_list = self.music_queue[guild_id]["queue"]
            embeds = []
            embed = discord.Embed(
                title="Liste de la file d'attente",
                color=discord.Color.blue()
            )
            
            for index, track in enumerate(queue_list):
                if len(embed.fields) >= 25 or len(embed) + len(track) > 6000:
                    embeds.append(embed)
                    embed = discord.Embed(
                        title="Liste de la file d'attente (suite)",
                        color=discord.Color.blue()
                    )
                embed.add_field(name=f"Musique {index + 1}", value=track, inline=False)

            embeds.append(embed)  # Ajouter le dernier embed

            for embed in embeds:
                await interaction.followup.send(embed=embed)
        else:
            embed = discord.Embed(
                title="File d'attente vide",
                description="Il n'y a pas de musique dans la file d'attente.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed)


#===============================================================================================================================================#
# Commande pour afficher et interagir avec la liste des musiques dans la queue
    @app_commands.command(name="choice_queue", description="Choisir une musique dans la file d'attente")
    @app_commands.guilds(discord.Object(id=1367454775108567144))  # ID du serveur
    @app_commands.guild_only()
    async def choice_queue(self, interaction: discord.Interaction):
        """ Slash command pour afficher la file d'attente et choisir une musique """

        await interaction.response.defer()

        guild_id = interaction.guild.id
        if guild_id in self.music_queue and self.music_queue[guild_id]["queue"]:
            queue_list = self.music_queue[guild_id]["queue"]
            options = [discord.SelectOption(label=track, value=str(index)) for index, track in enumerate(queue_list)]
            
            select_menu = Select(
                placeholder="Choisissez une musique...",
                options=options,
                custom_id="select_music"
            )
            
            # Création des boutons
            previous_button = Button(label="Previous", style=discord.ButtonStyle.primary, emoji="◀️", custom_id="prev_music")
            next_button = Button(label="Next", style=discord.ButtonStyle.primary, emoji="▶️", custom_id="next_music")
            
            view = View()
            view.add_item(select_menu)
            view.add_item(previous_button)
            view.add_item(next_button)
            
            embed = discord.Embed(
                title="Sélection de musique",
                description="Choisissez une musique à partir de la liste ci-dessous ou utilisez les boutons pour naviguer.",
                color=discord.Color.blue()
            )
            
            await interaction.followup.send(embed=embed, view=view)
        else:
            embed = discord.Embed(
                title="File d'attente vide",
                description="Il n'y a pas de musique dans la file d'attente.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed)

    # Gestion des interactions
    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if interaction.type == discord.InteractionType.component:
            custom_id = interaction.data["custom_id"]
            print(f"Interaction type: {interaction.type}, custom_id: {custom_id}")  # Débogage

            if custom_id == "select_music":
                try:
                    index = int(interaction.data["values"][0])
                    guild_id = interaction.guild.id

                    if guild_id in self.music_queue and self.music_queue[guild_id]["queue"]:
                        track = self.music_queue[guild_id]["queue"][index]

                        # Stopper la musique en cours
                        voice_client = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
                        if voice_client and voice_client.is_playing():
                            voice_client.stop()

                        # Mettre à jour la file d'attente pour jouer la musique choisie immédiatement
                        self.music_queue[guild_id]["queue"].pop(index)  # Retirer la musique choisie de la queue
                        self.music_queue[guild_id]["queue"].insert(0, track)  # Placer la musique choisie au début de la queue

                        # Jouer la musique choisie
                        await self.play_music(interaction, interaction.guild)

                        embed = discord.Embed(
                            title="Musique Choisie",
                            description=f"Vous avez choisi **{track}** et elle est maintenant en cours de lecture.",
                            color=discord.Color.green()
                        )
                        await interaction.response.send_message(embed=embed, ephemeral=True)
                    else:
                        embed = discord.Embed(
                            title="Erreur",
                            description="La musique choisie n'est plus disponible.",
                            color=discord.Color.red()
                        )
                        await interaction.response.send_message(embed=embed, ephemeral=True)
                except Exception as e:
                    print(f"Erreur lors du traitement de l'interaction: {str(e)}")  # Afficher l'erreur dans la console
                    embed = discord.Embed(
                        title="Erreur",
                        description="Une erreur est survenue lors du choix de la musique.",
                        color=discord.Color.red()
                    )
                    await interaction.response.send_message(embed=embed, ephemeral=True)

            elif custom_id == "next_music":
                # Gestion de la musique suivante (logique similaire à `select_music`)
                pass

            elif custom_id == "prev_music":
                guild_id = interaction.guild.id
                
                if guild_id in self.music_queue and self.music_queue[guild_id]["queue"]:
                    current_track_index = self.music_queue[guild_id]["queue"].index(self.music_queue[guild_id]["queue"][0])
                    prev_track_index = (current_track_index - 1) % len(self.music_queue[guild_id]["queue"])
                    prev_track = self.music_queue[guild_id]["queue"][prev_track_index]
                    
                    # Stopper la musique en cours
                    voice_client = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
                    if voice_client and voice_client.is_playing():
                        voice_client.stop()
                    
                    # Mettre à jour la file d'attente pour jouer la musique précédente
                    self.music_queue[guild_id]["queue"].pop(0)  # Retirer la musique en cours de la queue
                    self.music_queue[guild_id]["queue"].insert(0, prev_track)  # Ajouter la musique précédente au début de la queue
                    
                    # Jouer la musique précédente
                    await self.play_music(interaction, interaction.guild)
                    
                    embed = discord.Embed(
                        title="Musique Précédente",
                        description=f"Je passe à la musique précédente : **{prev_track}**.",
                        color=discord.Color.green()
                    )
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                else:
                    embed = discord.Embed(
                        title="Erreur",
                        description="Il n'y a pas de musique précédente dans la file d'attente.",
                        color=discord.Color.red()
                    )
                    await interaction.response.send_message(embed=embed, ephemeral=True)

#===============================================================================================================================================#
# Commande pour déconnecter le bot et réinitialiser la queue de musique
    @app_commands.command(name="disconnect", description="Déconnecter le bot et réinitialiser la file d'attente de musique")
    @app_commands.guilds(discord.Object(id=1367454775108567144))  # ID du serveur
    @app_commands.guild_only()
    async def disconnect(self, interaction: discord.Interaction):
        """
        Commande slash pour déconnecter le bot et réinitialiser la file d'attente.
        """
        guild_id = interaction.guild.id
        if guild_id in self.music_queue:
            # Déconnecter le bot du salon vocal
            voice_client = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
            if voice_client:
                await voice_client.disconnect()
                del self.music_queue[guild_id]  # Réinitialiser la queue de musique pour ce serveur

                await interaction.response.send_message(embed=discord.Embed(
                    title="Déconnexion",
                    description="Le bot a été déconnecté et la file d'attente de musique a été réinitialisée.",
                    color=discord.Color.green()
                ))
            else:
                await interaction.response.send_message(embed=discord.Embed(
                    title="Erreur",
                    description="Le bot n'est pas connecté à un salon vocal.",
                    color=discord.Color.red()
                ))
        else:
            await interaction.response.send_message(embed=discord.Embed(
                title="Erreur",
                description="La file d'attente est déjà vide ou le bot n'est pas connecté.",
                color=discord.Color.red()
            ))

#===============================================================================================================================================#
# Commande pour créer des emojis
    @app_commands.command(name="create", description="Créer un emoji sur le serveur")
    @app_commands.guilds(discord.Object(id=1367454775108567144))  # ID du serveur
    @app_commands.guild_only()
    async def create(self, interaction: discord.Interaction, emoji_name: str = None, emoji_url: str = None):
        """
        Commande pour créer un emoji sur le serveur.
        """
        if not emoji_name or not emoji_url:
            await interaction.response.send_message("Veuillez fournir un nom d'emoji et une URL d'image. Utilisation : `/create <nom_emoji> <URL_image>`.")
            return

        # Vérifier les permissions du bot
        if not interaction.guild.me.guild_permissions.manage_emojis:
            await interaction.response.send_message("Je n'ai pas les permissions nécessaires pour créer des emojis sur ce serveur.")
            return

        # Vérifier que l'URL est bien une image
        if not emoji_url.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
            await interaction.response.send_message("L'URL fournie ne correspond pas à une image valide. Veuillez utiliser une URL d'image PNG, JPG, JPEG ou GIF.")
            return

        # Tenter de créer l'emoji
        try:
            async with interaction.channel.typing():
                image_bytes = await self.get_image_bytes(emoji_url)
                emoji = await interaction.guild.create_custom_emoji(name=emoji_name, image=image_bytes)
                await interaction.response.send_message(f"L'emoji {emoji} a été créé avec succès !")
        except Exception as e:
            await interaction.response.send_message(f"Une erreur est survenue lors de la création de l'emoji: {e}")

    async def get_image_bytes(self, url: str):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    raise Exception("Erreur lors de la récupération de l'image.")
                return await response.read()

#===============================================================================================================================================#
# Commande pour copier un emoji d'un autre serveur
    @app_commands.command(name="copy_emoji", description="Copier un emoji d'un autre serveur avec son ID")
    @app_commands.guilds(discord.Object(id=1367454775108567144))  # ID du serveur
    @app_commands.guild_only()
    async def copy_emoji(self, interaction: discord.Interaction, emoji_id: str, new_name: str):
        """
        Slash command pour copier un emoji avec son ID et lui donner un nouveau nom.
        """
        await interaction.response.defer()

        # Valider le nom du nouvel emoji
        if not new_name.isalnum() or len(new_name) > 32:
            await interaction.followup.send("❌ Le nom de l'emoji doit être alphanumérique et ne pas dépasser 32 caractères.")
            return

        # Valider l'ID (doit être un nombre)
        try:
            emoji_id_int = int(emoji_id)
        except ValueError:
            await interaction.followup.send("❌ L'ID de l'emoji doit être un nombre.")
            return

        # Tenter de récupérer l'URL valide
        image_url = await self.get_emoji_url(emoji_id_int)
        if not image_url:
            await interaction.followup.send("❌ L'emoji avec cet ID est introuvable ou n'est pas accessible.")
            return

        # Télécharger et créer l'emoji
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url) as resp:
                    if resp.status != 200:
                        raise Exception("Erreur de récupération de l'image")
                    image_data = await resp.read()

            await interaction.guild.create_custom_emoji(name=new_name, image=image_data)
            await interaction.followup.send(f"✅ L'emoji `{new_name}` a été copié avec succès !")

        except discord.Forbidden:
            await interaction.followup.send("❌ Je n'ai pas la permission de créer des emojis sur ce serveur.")
        except Exception as e:
            await interaction.followup.send(f"❌ Une erreur est survenue : {e}")

    async def get_emoji_url(self, emoji_id: int) -> str:
        """
        Vérifie si un emoji est un GIF ou une image PNG.
        """
        base_url = f"https://cdn.discordapp.com/emojis/{emoji_id}"
        async with aiohttp.ClientSession() as session:
            for ext in ["gif", "png"]:
                url = f"{base_url}.{ext}"
                async with session.get(url) as response:
                    if response.status == 200:
                        return url
        return None
    
#===============================================================================================================================================#
# Commande pour ajouter une playlist entière
    @app_commands.command(name="playlistyt", description="Ajouter une playlist entière à la file d'attente (YouTube)")
    @app_commands.guilds(discord.Object(id=1367454775108567144))  # ID du serveur
    async def playlistyt(self, interaction: discord.Interaction, url: str):
        """Ajoute une playlist YouTube entière à la file d'attente musicale."""

        if not interaction.user.voice or not interaction.user.voice.channel:
            await interaction.response.send_message("Vous devez être dans un salon vocal pour utiliser cette commande.", ephemeral=True)
            return

        await interaction.response.defer()

        voice_channel = interaction.user.voice.channel
        guild_id = interaction.guild.id

        if guild_id not in self.music_queue:
            self.music_queue[guild_id] = {
                "channel": voice_channel,
                "queue": [],
                "is_playing": False
            }

        ydl_opts = {
            'quiet': True,
            'extract_flat': 'in_playlist',
            'skip_download': True,
        }

        try:
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if 'entries' in info:
                    for entry in info['entries']:
                        if entry and 'id' in entry:
                            video_url = f"https://www.youtube.com/watch?v={entry['id']}"
                            self.music_queue[guild_id]["queue"].append(video_url)
        except Exception as e:
            await interaction.followup.send(f"Erreur lors du chargement de la playlist : {e}")
            return

        # Connexion et lecture
        if not self.music_queue[guild_id]["is_playing"]:
            if not interaction.guild.voice_client:
                await voice_channel.connect()
            await self.play_music(interaction, interaction.guild)

        await interaction.followup.send(embed=discord.Embed(
            title="Playlist ajoutée",
            description="Les musiques de la playlist ont été ajoutées à la file d'attente.",
            color=discord.Color.blue()
        ))

#===============================================================================================================================================#
# Commande pour ajouter une playlist entière depuis Spotify
    @app_commands.command(
    name="playlistspy",
    description="Ajouter une playlist entière de Spotify à la file d'attente"
    )
    @app_commands.guilds(discord.Object(id=1367454775108567144))  # Remplace par l’ID de ton serveur
    async def playlistspy(self, interaction: discord.Interaction, url: str):
        """
        Slash command pour ajouter une playlist Spotify entière à la file d'attente musicale.
        """

        if not interaction.user.voice or not interaction.user.voice.channel:
            await interaction.response.send_message(
                "Vous devez être dans un salon vocal pour utiliser cette commande.",
                ephemeral=True
            )
            return

        await interaction.response.defer()

        voice_channel = interaction.user.voice.channel
        guild_id = interaction.guild.id

        if guild_id not in self.music_queue:
            self.music_queue[guild_id] = {
                "channel": voice_channel,
                "queue": [],
                "is_playing": False
            }

        playlist_id = url.split('/')[-1].split('?')[0]  # Extraire l'ID de la playlist Spotify

        try:
            # Récupérer les morceaux de la playlist
            results = sp.playlist_tracks(playlist_id)
            tracks = results['items']

            while results['next']:
                results = sp.next(results)
                tracks.extend(results['items'])

            # Ajouter les titres à la queue
            for item in tracks:
                track = item['track']
                if track:  # Vérifie que la piste existe
                    track_name = f"{track['name']} - {track['artists'][0]['name']}"
                    self.music_queue[guild_id]["queue"].append(track_name)

            if not self.music_queue[guild_id]["is_playing"]:
                if not interaction.guild.voice_client:
                    await voice_channel.connect()
                await self.play_music(interaction, interaction.guild)

            await interaction.followup.send(embed=discord.Embed(
                title="Playlist ajoutée",
                description="Les musiques de la playlist Spotify ont été ajoutées à la file d'attente.",
                color=discord.Color.green()
            ))

        except Exception as e:
            await interaction.followup.send(
                f"Une erreur est survenue lors de l'ajout de la playlist : {e}"
            )


#===============================================================================================================================================#
#commande sondage
    @commands.command(name="sondage", description="Créer un sondage avec des boutons d'interaction", help="!sondage [nom] ""arg1"" ""arg2"" ""arg3"" ""arg4""")
    async def sondage(self, ctx: commands.Context, title: str, *args):
        """
        Commande sondage avec des boutons d'interaction.

        """
        if len(args) < 2 or len(args) > 4:
            return await ctx.send("Vous devez fournir entre 2 et 4 options pour le sondage.")

        options = list(args)
        poll_id = len(self.polls) + 1
        self.polls[poll_id] = {option: 0 for option in options}
        self.voters[poll_id] = []

        embed = discord.Embed(title=f"Sondage: {title}", description="Choisissez une option:", color=discord.Color.blue())
        for option in options:
            embed.add_field(name=option, value=self.create_progress_bar(0, 0), inline=False)
        embed.set_footer(text=f"Sondage #{poll_id}")
        embed.timestamp = datetime.datetime.now()

        view = View()

        for option in options:
            button = Button(label=option, custom_id=f"{poll_id}:{option}")

            async def button_callback(interaction: discord.Interaction, option=option):
                if interaction.user.id in self.voters[poll_id]:
                    return await interaction.response.send_message("Vous avez déjà voté!", ephemeral=True)
                self.polls[poll_id][option] += 1
                self.voters[poll_id].append(interaction.user.id)
                self.update_embed(embed, poll_id)
                await interaction.response.edit_message(embed=embed, view=view)

            button.callback = button_callback
            view.add_item(button)

        await ctx.send(embed=embed, view=view)

    def create_progress_bar(self, count, total):
        bar_length = 20  # Longueur de la barre
        filled_length = int(round(bar_length * count / float(total))) if total > 0 else 0
        bar = '█' * filled_length + '-' * (bar_length - filled_length)
        percentage = round(100.0 * count / float(total), 1) if total > 0 else 0
        return f"|{bar}| {percentage}% ({count} votes)"

    def update_embed(self, embed, poll_id):
        total_votes = sum(self.polls[poll_id].values())
        for i in range(len(embed.fields)):
            option = embed.fields[i].name
            votes = self.polls[poll_id][option]
            embed.set_field_at(i, name=option, value=self.create_progress_bar(votes, total_votes), inline=False)

#===============================================================================================================================================#
#commande reset_polls
    @commands.command(name="reset_polls", description="Réinitialiser les sondages et les votes", help="!rest_polls")
    @commands.has_permissions(administrator=True)
    async def reset_polls(self, ctx: commands.Context):
        """
        Commande pour réinitialiser tous les sondages et les votes.

        """
        self.polls.clear()
        self.voters.clear()
        await ctx.send("Tous les sondages et votes ont été réinitialisés.")

#===============================================================================================================================================#
#commande configure_ticket
    @commands.command(name="configure_ticket", description="Configurer le système de tickets", help="!configure_ticket")
    @commands.has_permissions(administrator=True)
    async def configure_ticket(self, ctx: commands.Context):
        """
        Commande pour configurer le salon de ticket.
        """
        embed = discord.Embed(title="Système de Tickets", description="Réagissez avec 📬 pour créer un ticket.", color=discord.Color.blue())
        message = await ctx.send(embed=embed)
        await message.add_reaction("📬")

        # Sauvegarder l'ID du message dans le fichier de configuration
        self.save_message_id(message.id)

        def check(reaction, user):
            return str(reaction.emoji) == "📬" and reaction.message.id == message.id and not user.bot

        while True:
            try:
                reaction, user = await self.bot.wait_for("reaction_add", timeout=None, check=check)
                if user.id in self.cooldowns and self.cooldowns[user.id] > datetime.datetime.now():
                    await ctx.send(f"{user.mention}, vous devez attendre avant de créer un nouveau ticket.", delete_after=10, ephemeral=True)
                    await reaction.remove(user)
                    continue

                self.cooldowns[user.id] = datetime.datetime.now() + datetime.timedelta(hours=1)
                await reaction.remove(user)
                await self.create_ticket(ctx, user)
            except Exception as e:
                print(f"Error in ticket creation: {e}")

    async def create_ticket(self, ctx, user):
        guild = ctx.guild

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True)
        }

        try:
            channel = await guild.create_text_channel(f"ticket-{user.name}", overwrites=overwrites)
            
            # Embed de confirmation dans le nouveau salon
            embed = discord.Embed(
                title="Ticket",
                description="Merci de nous avoir contactés. Un modérateur va bientôt s'occuper de votre demande.",
                color=discord.Color.blue()
            )
            await channel.send(embed=embed, view=self.create_ticket_view())
            
            # Envoyer une notification dans le salon spécifique
            notification_channel_id = 1367458820493672478
            notification_channel = self.bot.get_channel(notification_channel_id)
            if notification_channel:
                notification_embed = discord.Embed(
                    title="Nouveau Ticket Créé",
                    description=f"Un nouveau ticket a été créé par {user.mention}. Cliquez [ici]({channel.jump_url}) pour le consulter.",
                    color=discord.Color.green()
                )
                await notification_channel.send(embed=notification_embed)
            else:
                print(f"Salon de notification avec l'ID {notification_channel_id} non trouvé.")
        except Exception as e:
            print(f"Error creating channel: {e}")
            await ctx.send(f"Une erreur est survenue lors de la création du salon: {e}")

    def create_ticket_view(self):
        view = View()
        close_button = Button(label="Fermer le ticket", emoji="🔒", style=discord.ButtonStyle.danger)
        claim_button = Button(label="Réclamer", emoji="✋", style=discord.ButtonStyle.primary)

        async def close_callback(interaction: discord.Interaction):
            if interaction.user.guild_permissions.administrator:
                modal = CloseReasonModal()
                await interaction.response.send_modal(modal)
                await modal.wait()
                reason = modal.reason.value
                await interaction.channel.send(f"Ticket fermé par {interaction.user.mention} pour la raison suivante : {reason}")
                await interaction.channel.delete()
            else:
                await interaction.response.send_message("Vous n'avez pas la permission de fermer ce ticket.", ephemeral=True)

        async def claim_callback(interaction: discord.Interaction):
            if interaction.user.guild_permissions.administrator:
                await interaction.channel.send(f"@everyone {interaction.user.mention} a réclamé ce ticket.")
                await interaction.response.defer()
            else:
                await interaction.response.send_message("Vous n'avez pas la permission de réclamer ce ticket.", ephemeral=True)

        close_button.callback = close_callback
        claim_button.callback = claim_callback
        view.add_item(close_button)
        view.add_item(claim_button)
        return view
    
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        # Vérifie si c’est le bon message
        if payload.message_id != self.message_id:
            return

        if str(payload.emoji) != "📬":
            return

        # Empêche les bots de déclencher la création
        guild = self.bot.get_guild(payload.guild_id)
        user = guild.get_member(payload.user_id)
        if user.bot:
            return

        # Anti-spam / cooldown
        now = datetime.datetime.now()
        if user.id in self.cooldowns and self.cooldowns[user.id] > now:
            channel = self.bot.get_channel(payload.channel_id)
            await channel.send(f"{user.mention}, vous devez attendre avant de créer un nouveau ticket.", delete_after=10)
            return

        # Appliquer le cooldown
        self.cooldowns[user.id] = now + datetime.timedelta(hours=1)

        # Supprimer la réaction
        channel = self.bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        await message.remove_reaction(payload.emoji, user)

        # Créer le ticket
        ctx = await self.bot.get_context(message)
        await self.create_ticket(ctx, user)


class CloseReasonModal(Modal, title="Raison de la fermeture"):
    reason = TextInput(label="Raison", style=discord.TextStyle.paragraph, required=True)

    def __init__(self):
        super().__init__()

    async def on_submit(self, interaction: discord.Interaction):
        self.stop()

#===============================================================================================================================================#
#setup fun
async def setup(bot):
    await bot.add_cog(CommandFun(bot))