#===============================================================================================================================================#
#=====================================================EVENEMENT JOIN VOCAL CHANNEL==============================================================#
#===============================================================================================================================================#
#importation des modules nécessaires
import discord
from discord.ext import commands
import json
import asyncio
import os

#===============================================================================================================================================#
# Liste des embeds pour le channel de connexion
list_embed = ["Pram Heda dev", "Bot serveur leak"]

#===============================================================================================================================================#
# Définition de la classe
class JoinVocalChannel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.load_config()
        self.vocal_channels = {}  # Dictionnaire pour suivre les salons vocaux créés

    #===============================================================================================================================================#
    # Méthode pour charger la configuration
    def load_config(self):
        try:
            path = os.path.join(os.path.dirname(__file__), "../configuration.json")
            print(f"Chemin du fichier de configuration: {path}")
            with open(path, "r") as f:
                self.config = json.load(f)
            print("✅ Configuration chargée :", self.config)

            #Convertir l'ID du salon en entier si ce n'est pas déjà le cas
            self.config["vocal_channel_id"] = int(self.config.get("vocal_channel_id", 0))
            self.config["category_voc"] = int(self.config.get("category_voc", 0))
            print("🛠️ ID du salon vocal :", self.config["vocal_channel_id"])
            print("🛠️ ID de la catégorie :", self.config["category_voc"])
        except FileNotFoundError:
            print("❌ Le fichier de configuration n'a pas été trouvé.")
            self.config = {}
        except json.JSONDecodeError:
            print("❌ Erreur lors de la lecture du fichier de configuration.")
            self.config = {}

   #===============================================================================================================================================#
    # Evénement déclenché lorsqu'un membre rejoint un salon vocal
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if after.channel:
            print(f"{member.display_name} a rejoint le salon: {after.channel.name} (ID: {after.channel.id})")
            print(f"ID attendu depuis la config: {self.config.get('vocal_channel_id')}")

        # Vérifie si l'utilisateur a rejoint le bon salon vocal
        if after.channel and after.channel.id == int(self.config.get("vocal_channel_id")):
            print(f"Création d'un nouveau salon vocal pour {member.display_name}")

            guild = member.guild
            channel_name = f"Salon de {member.display_name}"

            # ID de la catégorie où créer les salons
            category_id = int(self.config.get("category_voc"))  # 🔁 Convertit en int
            print(f"🛠️ ID de la catégorie utilisé : {category_id}")
            category_obj = discord.utils.get(guild.categories, id=category_id)


            # Vérifie si la catégorie a bien été trouvée
            if category_obj is None:
                print(f"❌ Catégorie introuvable pour l'ID: {category_id}")
                return

            # Crée un nouveau salon vocal dans la bonne catégorie
            new_channel = await guild.create_voice_channel(channel_name, category=category_obj)

            # Donne tous les droits au créateur du salon
            await new_channel.set_permissions(member, manage_channels=True, mute_members=True, deafen_members=True, move_members=True)

            # Déplace le membre dans le nouveau salon
            await member.move_to(new_channel)
            print(f"{member.display_name} a été déplacé dans {new_channel.name}")

            # Stocke le salon et le membre associé
            self.vocal_channels[new_channel.id] = member.id

            # Enregistre l'événement de suppression automatique du salon
            self.bot.loop.create_task(self.check_empty_channel(new_channel))
        else:
            print("L'utilisateur n'a pas rejoint le bon salon ou l'ID ne correspond pas.")


    # Vérifie si le salon est vide et le supprime s'il n'y a plus personne
    async def check_empty_channel(self, channel):
        while True:
            await asyncio.sleep(10)  # Vérifie toutes les minutes
            if len(channel.members) == 0:
                del self.vocal_channels[channel.id]
                await channel.delete()
                print(f"Salon {channel.name} supprimé car vide.")
                break

    # Commande pour configurer le salon
    @commands.command(name="configcanal")
    async def config_canal(self, ctx):
        if ctx.author.voice and ctx.author.voice.channel.id in self.vocal_channels:
            creator_id = self.vocal_channels[ctx.author.voice.channel.id]
            if ctx.author.id == creator_id:
                # Créer un embed
                embed = discord.Embed(title="Configuration du Salon Vocal", color=discord.Color.blue())
                embed.add_field(name="Options disponibles", value="Choisissez une option dans la liste déroulante ou cliquez sur 'Annuler' pour quitter.")

                # Créer un menu déroulant avec discord.ui.Select
                select = discord.ui.Select(
                    placeholder="Choisissez une option...",
                    options=[
                        discord.SelectOption(label="Nombre maximum d'utilisateurs", value="max_users", description="Définir le nombre maximum d'utilisateurs"),
                    ]
                )

                # Bouton annuler
                cancel_button = discord.ui.Button(label="Annuler", style=discord.ButtonStyle.red)

                # Callback pour le sélecteur
                async def select_callback(interaction):
                    if select.values[0] == "max_users":
                        await interaction.response.send_message(f"Veuillez entrer le nombre maximum de membres pour le salon vocal `{ctx.author.voice.channel.name}` :", ephemeral=True)

                        def check_msg(m):
                            return m.author == ctx.author and m.channel == ctx.channel

                        try:
                            msg = await self.bot.wait_for("message", check=check_msg, timeout=60.0)
                            max_members = int(msg.content)
                            await ctx.author.voice.channel.edit(user_limit=max_members)
                            await interaction.followup.send(f"Le nombre maximum de membres pour le salon `{ctx.author.voice.channel.name}` a été défini à {max_members}.")
                        except ValueError:
                            await interaction.followup.send("Veuillez entrer un nombre valide.")
                        except asyncio.TimeoutError:
                            await interaction.followup.send("Temps écoulé. Veuillez réessayer.")

                # Callback pour le bouton annuler
                async def cancel_callback(interaction):
                    await interaction.message.delete()  # Supprime le message de configuration
                    await ctx.message.delete()  # Supprime le message de la commande
                    await interaction.response.send_message("Configuration annulée.", ephemeral=True)

                select.callback = select_callback
                cancel_button.callback = cancel_callback

                # Envoyer l'embed et ajouter le menu déroulant et le bouton annuler
                view = discord.ui.View()
                view.add_item(select)
                view.add_item(cancel_button)
                await ctx.send(embed=embed, view=view)
            else:
                await ctx.send("Vous n'êtes pas le créateur de ce salon.")
        else:
            await ctx.send("Vous devez être dans un salon vocal que vous avez créé pour utiliser cette commande.")

#===============================================================================================================================================#
# Setup joinquit
async def setup(bot):
    await bot.add_cog(JoinVocalChannel(bot))
