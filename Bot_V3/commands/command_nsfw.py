#===============================================================================================================================================#
#=============================================================COMMANDE DE LEVEL=================================================================#
#===============================================================================================================================================#
#importation des modules nécessaires
import discord
from discord.ext import commands
import sqlite3
import json
import calendar
import time

#===============================================================================================================================================#
#temp passé pour le timestamp
ts = calendar.timegm(time.gmtime())

#===============================================================================================================================================#
# Liste des embeds pour le channel de connexion
list_embed = ["Pram Heda dev", "Bot serveur leak"]

#===============================================================================================================================================#
# Chargement de la configuration depuis le fichier JSON
with open('configuration.json') as config_file:
    config = json.load(config_file)

# Création de la base de données SQLite
conn = sqlite3.connect('link.sqlite')
c = conn.cursor()
c.execute('''
    CREATE TABLE IF NOT EXISTS porn_links (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        site_url TEXT NOT NULL,
        image_url TEXT NOT NULL,
        timestamp INTEGER NOT NULL
    )
''')

c.execute('''
    CREATE TABLE IF NOT EXISTS image_links (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        image_url TEXT NOT NULL,
        timestamp INTEGER NOT NULL
    )
''')
conn.commit()

#===============================================================================================================================================#
#définition de la classe pour le Cog
class CommandNSFW(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    #===============================================================================================================================================#
    # Commande ajout de vidéo porno
    @commands.command(
        name="likeporn",
        help="!likeporn [name] [url video] [url image]",
        description="Commande pour ajouter une vidéo porno que tu aimes"
    )
    async def likeporn(self, ctx, name: str, site_url: str, image_url: str):
        """
        Commande pour ajouter une vidéo porno que tu aimes
        """
        # Vérification que la commande est exécutée dans le bon salon
        if str(ctx.channel.id) != config["channel_nsfw"]:
            await ctx.send("Cette commande ne peut être utilisée que dans le salon NSFW configuré.")
            return

        # Insertion des données dans la base de données
        c.execute('''
            INSERT INTO porn_links (name, site_url, image_url, timestamp)
            VALUES (?, ?, ?, ?)
        ''', (name, site_url, image_url, ts))
        conn.commit()

        # Création de l'embed
        embed = discord.Embed(title="Nouveau lien ajouté", color=discord.Color.blue())
        embed.add_field(name="Nom", value=name, inline=False)
        embed.add_field(name="Site URL", value=site_url, inline=False)
        embed.add_field(name="Image URL", value=image_url, inline=False)
        embed.set_thumbnail(url=image_url)
        embed.set_footer(text=f"Ajouté par {ctx.author} à {time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(ts))}")

        # Envoi de l'embed dans le salon NSFW
        await ctx.send(embed=embed)

        # Envoi de l'embed dans le salon de logs
        log_channel = self.bot.get_channel(int(config["log_channel_id"]))
        if log_channel:
            await log_channel.send(embed=embed)

    #===============================================================================================================================================#
    # Commande ajout d'image
    @commands.command(
        name="likeimg",
        help="!likeimg [name] [url image]",
        description="Commande pour ajouter une image porno que tu aimes"
    )
    async def likeimg(self, ctx, name: str, image_url: str):
        """
        Commande pour ajouter une image porno que tu aimes
        """
        # Vérification que la commande est exécutée dans le bon salon
        if str(ctx.channel.id) != config["channel_nsfw"]:
            await ctx.send("Cette commande ne peut être utilisée que dans le salon NSFW configuré.")
            return

        # Insertion des données dans la base de données
        c.execute('''
            INSERT INTO image_links (name, image_url, timestamp)
            VALUES (?, ?, ?)
        ''', (name, image_url, ts))
        conn.commit()

        # Création de l'embed
        embed = discord.Embed(title="Nouvelle image ajoutée", color=discord.Color.green())
        embed.add_field(name="Nom", value=name, inline=False)
        embed.add_field(name="Image URL", value=image_url, inline=False)
        embed.set_thumbnail(url=image_url)
        embed.set_footer(text=f"Ajoutée par {ctx.author} à {time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(ts))}")

        # Envoi de l'embed dans le salon NSFW
        await ctx.send(embed=embed)

        # Envoi de l'embed dans le salon de logs
        log_channel = self.bot.get_channel(int(config["log_channel_id"]))
        if log_channel:
            await log_channel.send(embed=embed)

    #===============================================================================================================================================#
    # Commande pour afficher une image aléatoire
    @commands.command(
        name="boobs",
        help="!boobs",
        description="Commande pour afficher une image porno aléatoire depuis la base de données"
    )
    async def boobs(self, ctx):
        """
        Commande pour afficher une image porno aléatoire depuis la base de données
        """
        # Sélection aléatoire d'une image dans la base de données
        c.execute('SELECT name, image_url FROM image_links ORDER BY RANDOM() LIMIT 1')
        row = c.fetchone()
        
        if row:
            name, image_url = row
            # Création de l'embed
            embed = discord.Embed(title=name, color=discord.Color.purple())
            embed.set_image(url=image_url)
            embed.set_footer(text=f"Affiché par {ctx.author} à {time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(ts))}")

            # Envoi de l'embed dans le salon NSFW
            await ctx.send(embed=embed)
        else:
            await ctx.send("Aucune image trouvée dans la base de données.")

    #===============================================================================================================================================#
    # Commande pour afficher une vidéo aléatoire
    @commands.command(
        name="porn",
        help="!porn",
        description="Commande pour afficher une vidéo porno aléatoire depuis la base de données"
    )
    async def porn(self, ctx):
        """
        Commande pour afficher une vidéo porno aléatoire depuis la base de données
        """
        # Sélection aléatoire d'une vidéo dans la base de données
        c.execute('SELECT name, site_url, image_url FROM porn_links ORDER BY RANDOM() LIMIT 1')
        row = c.fetchone()
        
        if row:
            name, site_url, image_url = row
            # Création de l'embed
            embed = discord.Embed(title=name, color=discord.Color.red())
            embed.add_field(name="Site URL", value=site_url, inline=False)
            embed.set_thumbnail(url=image_url)
            embed.set_footer(text=f"Affiché par {ctx.author} à {time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(ts))}")

            # Envoi de l'embed dans le salon NSFW
            await ctx.send(embed=embed)
        else:
            await ctx.send("Aucune vidéo trouvée dans la base de données.")
#===============================================================================================================================================#
# Setup function to add the Cog to the bot
async def setup(bot):
    await bot.add_cog(CommandNSFW(bot))
