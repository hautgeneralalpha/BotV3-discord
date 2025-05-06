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
#définition de la classe pour le Cog
class CommandLevel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = 'level.sqlite'
        self.load_config()

#===============================================================================================================================================#
# Méthode pour charger la configuration
    def load_config(self):
        try:
            with open("configuration.json", "r") as f:
                self.config = json.load(f)
        except FileNotFoundError:
            print("Le fichier de configuration n'a pas été trouvé.")
            self.config = {}
        except json.JSONDecodeError:
            print("Erreur lors de la lecture du fichier de configuration.")
            self.config = {}

#===============================================================================================================================================#
# Méthode pour obtenir les données utilisateur
    def get_user_data(self, user_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT xp, level FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        conn.close()
        if result:
            return result
        else:
            return (0, 0)

#===============================================================================================================================================#
# Méthode pour mettre à jour les données utilisateur
    def update_user_data(self, user_id, xp, level):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("REPLACE INTO users (user_id, xp, level) VALUES (?, ?, ?)", (user_id, xp, level))
        conn.commit()
        conn.close()

#===============================================================================================================================================#
# Méthode pour obtenir l'XP nécessaire pour le niveau donné
    def get_xp_needed_for_level(self, level):
        return 10 * level * (level + 1) // 2

#===============================================================================================================================================#
# Méthode pour générer la barre de niveau
    def generate_level_bar(self, xp, level):
        xp_needed = self.get_xp_needed_for_level(level + 1)
        xp_current_level = self.get_xp_needed_for_level(level)
        progress = (xp - xp_current_level) / (xp_needed - xp_current_level)
        bar_length = 20
        bar = '█' * int(bar_length * progress) + '-' * (bar_length - int(bar_length * progress))
        return bar, progress * 100

#===============================================================================================================================================#
# Commande pour afficher le niveau et la barre de progression
    @commands.command(name='level', description="Affiche le niveau et la barre de progression d'un utilisateur", help="!level")
    async def level(self, ctx):
        """
        Commande pour afficher le niveau et la barre de progression d'un utilisateur.
        """
        user_id = ctx.author.id
        xp, level = self.get_user_data(user_id)
        
        if not xp and not level:
            embed = discord.Embed(
                title="Données non trouvées",
                description="Aucune donnée trouvée pour cet utilisateur.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        # Generate level bar and percentage
        bar, progress = self.generate_level_bar(xp, level)
        
        # Create embed with level information
        embed = discord.Embed(title=f"Niveau de {ctx.author.name}", color=discord.Color.blue())
        embed.add_field(name="Niveau", value=f"Level {level}", inline=False)
        embed.add_field(name="XP Total", value=f"{xp} XP", inline=False)
        embed.add_field(name="Progrès", value=f"{bar} ({progress:.2f}%)", inline=False)

        # Send embed
        await ctx.send(embed=embed)

#===============================================================================================================================================#
# Commande pour donner des niveaux à un utilisateur
    @commands.command(name='givelevel', description="Donne des niveaux à un utilisateur", help="!givelevel [@user] [nombre]")
    @commands.has_permissions(administrator=True)  # Assurez-vous que la commande peut être exécutée par un administrateur
    async def givelevel(self, ctx, member: discord.Member = None, levels: int = None):
        """
        Commande pour donner des niveaux à un utilisateur ou à l'auteur si aucun utilisateur n'est précisé.
        
        Exemple: !givelevel @user 5 ou !givelevel 5
        """
        if levels is None:
            embed = discord.Embed(
                title="Erreur",
                description="Veuillez spécifier le nombre de niveaux à ajouter.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        if levels < 1:
            embed = discord.Embed(
                title="Erreur",
                description="Le nombre de niveaux doit être supérieur à 0.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        # Déterminer le membre cible
        if member is None:
            member = ctx.author

        # Obtenir les données de l'utilisateur cible
        xp, level = self.get_user_data(member.id)
        
        if xp == 0 and level == 0:
            # Si l'utilisateur n'a pas encore de données, initialisez-les
            xp = 0
            level = 0
        
        # Calculer le niveau final
        new_level = level + levels
        new_xp = self.get_xp_needed_for_level(new_level) - 1  # Mettre le XP à un point juste avant le niveau suivant
        
        # Mettre à jour les données de l'utilisateur
        self.update_user_data(member.id, new_xp, new_level)
        
        # Créer un embed de confirmation
        embed = discord.Embed(
            title="Niveaux attribués",
            description=f"{member.mention} a maintenant le niveau {new_level} avec {new_xp} XP.",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

#===============================================================================================================================================#
# Commande pour attribuer le rôle BOOST XP à un utilisateur
    @commands.command(name='boostxp', description="Attribue le rôle BOOST XP à un utilisateur", help="!boostxp @user")
    @commands.has_permissions(administrator=True)  # Assurez-vous que la commande peut être exécutée par un administrateur
    async def boostxp(self, ctx, member: discord.Member = None):
        """
        Commande pour attribuer le rôle BOOST XP à un utilisateur.
        """
        role_name_id = self.config.get("role_booster_ex")

        if not role_name_id:
            embed = discord.Embed(
                title="Erreur de configuration",
                description="L'ID du rôle BOOST XP n'est pas défini dans la configuration.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        try:
            role_id = int(role_name_id)
        except ValueError:
            embed = discord.Embed(
                title="Erreur de configuration",
                description="L'ID du rôle BOOST XP dans la configuration n'est pas valide.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        # Cherchez le rôle BOOST XP
        role = discord.utils.get(ctx.guild.roles, id=role_id)

        if role is None:
            embed = discord.Embed(
                title="Rôle non trouvé",
                description=f"Le rôle BOOST XP avec ID `{role_id}` n'existe pas sur ce serveur.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        if member is None:
            embed = discord.Embed(
                title="Erreur",
                description="Veuillez spécifier un utilisateur pour attribuer le rôle BOOST XP.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        # Assignez le rôle à l'utilisateur cible
        try:
            await member.add_roles(role)
            # Créez un embed de confirmation
            embed = discord.Embed(
                title="Rôle BOOST XP attribué",
                description=f"Le rôle BOOST XP a été attribué à {member.mention}.",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
        except discord.Forbidden:
            embed = discord.Embed(
                title="Permission refusée",
                description="Je n'ai pas la permission d'attribuer des rôles.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(
                title="Erreur",
                description=f"Une erreur s'est produite : {e}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

#===============================================================================================================================================#
# Commande pour retirer le rôle BOOST XP à un utilisateur
    @commands.command(name='unboostxp', description="Retire le rôle BOOST XP à un utilisateur", help="!unboostxp @user")
    @commands.has_permissions(administrator=True)  # Assurez-vous que la commande peut être exécutée par un administrateur
    async def unboostxp(self, ctx, member: discord.Member = None):
        """
        Commande pour retirer le rôle BOOST XP à un utilisateur.
        """
        role_name_id = self.config.get("role_booster_ex")

        if not role_name_id:
            embed = discord.Embed(
                title="Erreur de configuration",
                description="L'ID du rôle BOOST XP n'est pas défini dans la configuration.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        try:
            role_id = int(role_name_id)
        except ValueError:
            embed = discord.Embed(
                title="Erreur de configuration",
                description="L'ID du rôle BOOST XP dans la configuration n'est pas valide.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        # Cherchez le rôle BOOST XP
        role = discord.utils.get(ctx.guild.roles, id=role_id)

        if role is None:
            embed = discord.Embed(
                title="Rôle non trouvé",
                description=f"Le rôle BOOST XP avec ID `{role_id}` n'existe pas sur ce serveur.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        if member is None:
            embed = discord.Embed(
                title="Erreur",
                description="Veuillez spécifier un utilisateur pour retirer le rôle BOOST XP.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        # Retirer le rôle de l'utilisateur cible
        try:
            await member.remove_roles(role)
            # Créez un embed de confirmation
            embed = discord.Embed(
                title="Rôle BOOST XP retiré",
                description=f"Le rôle BOOST XP a été retiré de {member.mention}.",
                color=discord.Color.dark_red()
            )
            await ctx.send(embed=embed)
        except discord.Forbidden:
            embed = discord.Embed(
                title="Permission refusée",
                description="Je n'ai pas la permission de retirer des rôles.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(
                title="Erreur",
                description=f"Une erreur s'est produite : {e}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

#===============================================================================================================================================#
# Setup function to add the Cog to the bot
async def setup(bot):
    await bot.add_cog(CommandLevel(bot))