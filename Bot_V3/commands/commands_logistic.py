#===============================================================================================================================================#
#========================================================EVENEMENT init economy=================================================================#
#===============================================================================================================================================#

#importation des modules nécessaires
import discord
from discord.ext import commands, tasks
import sqlite3
import random
import calendar
import time
import datetime
from discord.ui import Button, View, Select
import json
import asyncio  # Pour gérer l'attente du temps du giveaway

#===============================================================================================================================================#
#temp passé pour le timestamp
ts = calendar.timegm(time.gmtime())

#===============================================================================================================================================#
# Liste des embeds pour le channel de connexion
list_embed = ["Pram Heda dev", "Bot serveur leak"]

#===============================================================================================================================================#
#définition de la classe
class CommandLogisic(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_shop = 'shop.sqlite'  # Base de données du shop
        self.db_eco = 'eco.sqlite'    # Base de données de l'économie (wallet et inventaire)
        try:
            with open("configuration.json", "r") as f:
                self.config = json.load(f)
        except FileNotFoundError:
            print("Erreur : Le fichier configuration.json n'a pas été trouvé.")
            self.config = {}
        except json.JSONDecodeError:
            print("Erreur : Impossible de décoder le fichier JSON.")
            self.config = {}

    #===============================================================================================================================================#
    # Commande pour organiser un giveaway
    @commands.command(name='giveaway', description="Organise un giveaway d'un item ou de BotCoins.", help="/giveaway [nom item] [nombre] [temps]")
    @commands.has_permissions(administrator=True)  # Seuls les administrateurs peuvent organiser des giveaways
    async def giveaway(self, ctx, item: str, quantity: int, duration: int):
        """
        Organise un giveaway. Le paramètre 'item' peut être un objet du shop ou 'BotCoins'.
        La durée est en secondes.
        """

        # Vérification si l'item est 'BotCoins' ou autre
        if item.lower() == 'botcoins':
            prize_type = 'BotCoins'
        else:
            # Vérifier si l'item existe dans la base de données du shop
            conn = sqlite3.connect('shop.sqlite')
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM shop WHERE name = ?", (item,))
            result = cursor.fetchone()
            conn.close()

            if not result:
                await ctx.send(f"L'item '{item}' n'existe pas dans le shop.")
                return

            prize_type = 'Item'

        # Création de l'embed pour le giveaway
        embed = discord.Embed(
            title="🎉 GIVEAWAY 🎉",
            description=f"Réagissez à cet embed pour participer au giveaway !\n\n**Prix** : {quantity} {item}",
            color=discord.Color.blue(),
            timestamp=datetime.datetime.utcnow()
        )
        embed.add_field(name="Durée", value=f"{duration // 60} minutes et {duration % 60} secondes", inline=False)
        embed.set_footer(text="Le gagnant sera tiré au sort à la fin du temps imparti !")

        # Poster l'embed dans le salon donné
        giveaway_channel = self.bot.get_channel(1256049569494597744)
        giveaway_message = await giveaway_channel.send(embed=embed)

        # Ajouter une réaction pour que les utilisateurs puissent participer
        await giveaway_message.add_reaction("🎉")

        # Attendre la durée du giveaway
        await asyncio.sleep(duration)

        # Obtenir les utilisateurs qui ont réagi
        giveaway_message = await giveaway_channel.fetch_message(giveaway_message.id)  # On récupère le message mis à jour
        users = []
        async for user in giveaway_message.reactions[0].users():  # Itérer sur le générateur asynchrone
            if user != self.bot.user:  # Retirer le bot de la liste des participants
                users.append(user)

        # Vérifier si des participants ont été trouvés
        if len(users) == 0:
            await giveaway_channel.send("Personne n'a participé au giveaway. Aucun gagnant.")
            return

        # Tirer un gagnant aléatoire
        winner = random.choice(users)

        # Donner le prix au gagnant
        if prize_type == 'BotCoins':
            # Ajouter les BotCoins dans le wallet du gagnant
            conn = sqlite3.connect('eco.sqlite')
            cursor = conn.cursor()
            cursor.execute("SELECT wallet FROM eco WHERE user_id = ?", (winner.id,))
            wallet = cursor.fetchone()

            if wallet:
                new_balance = wallet[0] + quantity
                cursor.execute("UPDATE eco SET wallet = ? WHERE user_id = ?", (new_balance, winner.id))
            else:
                cursor.execute("INSERT INTO eco (user_id, wallet, bank, inventory) VALUES (?, ?, 0, '')", (winner.id, quantity))

            conn.commit()
            conn.close()

            prize_message = f"{quantity} BotCoins"
        
        else:
            # Ajouter l'item dans l'inventaire du gagnant
            conn = sqlite3.connect('eco.sqlite')
            cursor = conn.cursor()

            cursor.execute("SELECT inventory FROM eco WHERE user_id = ?", (winner.id,))
            recipient_inventory = cursor.fetchone()

            if recipient_inventory is None:
                # Initialiser l'inventaire du destinataire s'il n'existe pas encore
                cursor.execute("INSERT INTO eco (user_id, wallet, bank, inventory) VALUES (?, 0, 0, ?)", (winner.id, item))
            else:
                recipient_inventory = recipient_inventory[0]
                if recipient_inventory is None:
                    recipient_inventory = ""

                new_recipient_inventory = f"{recipient_inventory},{item}" if recipient_inventory else item
                cursor.execute("UPDATE eco SET inventory = ? WHERE user_id = ?", (new_recipient_inventory, winner.id))

            conn.commit()
            conn.close()

            prize_message = f"{quantity} {item}(s)"

        # Créer un embed pour annoncer le gagnant
        winner_embed = discord.Embed(
            title="🎉 GIVEAWAY TERMINÉ 🎉",
            description=f"Le gagnant du giveaway est {winner.mention} !",
            color=discord.Color.green(),
            timestamp=datetime.datetime.utcnow()
        )
        winner_embed.add_field(name="Prix", value=prize_message, inline=False)
        winner_embed.set_footer(text="Merci à tous pour votre participation !")

        # Poster l'embed du gagnant dans le même salon
        await giveaway_channel.send(embed=winner_embed)

#===============================================================================================================================================#
#setup Event
async def setup(bot):
    await bot.add_cog(CommandLogisic(bot))
