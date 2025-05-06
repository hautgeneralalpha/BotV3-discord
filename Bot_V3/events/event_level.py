#===============================================================================================================================================#
#=========================================================EVENEMENT LEVEL USERS=================================================================#
#===============================================================================================================================================#
# Importation des modules nécessaires
import discord
from discord.ext import commands
import sqlite3
import json

#===============================================================================================================================================#
# Définition de la classe
class LevelForUser(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = 'level.sqlite'
        self._initialize_database()
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
# Méthode pour initialiser la base de données
    def _initialize_database(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                xp INTEGER DEFAULT 0,
                level INTEGER DEFAULT 0
            )
            ''')
            conn.commit()

#===============================================================================================================================================#
# Méthode pour obtenir l'XP nécessaire pour le niveau donné
    def get_xp_needed_for_level(self, level):
        return 10 * level * (level + 1) // 2  # Progression quadratique

#===============================================================================================================================================#
# Méthode pour obtenir le niveau en fonction de l'XP
    def get_level(self, xp):
        level = 0
        while self.get_xp_needed_for_level(level + 1) <= xp:
            level += 1
        return level

#===============================================================================================================================================#
# Méthode pour vérifier si un membre est boosté
    def is_boosted(self, member):
        # Vérifie si le membre a le rôle "BOOST XP"
        role_name_id = self.config.get("role_booster_ex")
        return discord.utils.get(member.roles, id=int(role_name_id)) is not None

#===============================================================================================================================================#
# Méthode pour mettre à jour l'XP de l'utilisateur
    def update_user_xp(self, user_id, xp, member):
        # Assurez-vous que xp_per_message est bien un entier
        try:
            xp_per_message = int(self.config.get("xp_per_message", 1))  # Valeur par défaut si xp_per_message n'est pas défini
        except ValueError:
            xp_per_message = 1  # Valeur par défaut si xp_per_message n'est pas valide

        # Appliquer le coefficient d'XP global
        xp *= xp_per_message

        # Appliquer un boost si le membre a le rôle BOOST XP
        try:
            boost_xp_coeff = int(self.config.get("boost_xp_coeff", 1))  # Valeur par défaut si boost_xp_coeff n'est pas défini
        except ValueError:
            boost_xp_coeff = 1  # Valeur par défaut si boost_xp_coeff n'est pas valide

        if self.is_boosted(member):
            xp *= boost_xp_coeff  # Appliquer le coefficient de boost

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT xp, level FROM users WHERE user_id = ?", (user_id,))
            result = cursor.fetchone()

            if result:
                current_xp, current_level = result
                new_xp = current_xp + int(xp)  # Assurez-vous que xp est un entier
                new_level = self.get_level(new_xp)
                cursor.execute("UPDATE users SET xp = ?, level = ? WHERE user_id = ?", (new_xp, new_level, user_id))
            else:
                new_level = self.get_level(int(xp))  # Assurez-vous que xp est un entier
                cursor.execute("INSERT INTO users (user_id, xp, level) VALUES (?, ?, ?)", (user_id, int(xp), new_level))

            conn.commit()
        
        return new_level

#===============================================================================================================================================#
# Méthode pour s'assurer que le rôle existe
    async def ensure_role_exists(self, guild, level):
        role_name = f"Level {level}"
        existing_role = discord.utils.get(guild.roles, name=role_name)
        if existing_role:
            return existing_role

        # Create the role if it does not exist
        new_role = await guild.create_role(name=role_name, reason="Role for level system")
        return new_role

#===============================================================================================================================================#
# Méthode pour mettre à jour les rôles de l'utilisateur
    async def update_roles(self, member, new_level):
        guild = member.guild
        # Ensure that the role for the new level exists
        new_role = await self.ensure_role_exists(guild, new_level)

        # Add the new role
        if new_role and new_role not in member.roles:
            await member.add_roles(new_role)

        # Remove the old roles
        current_roles = [role for role in member.roles if role.name.startswith("Level")]
        for role in current_roles:
            role_level = int(role.name.split()[1])
            if role_level < new_level:
                await member.remove_roles(role)

#===============================================================================================================================================#
# Événement on_message pour gérer l'XP des utilisateurs
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        
        user_id = message.author.id
        new_level = self.update_user_xp(user_id, 1, message.author)  # Chaque message donne 1 XP après application du coefficient

        if new_level > 0:
            await self.update_roles(message.author, new_level)

#===============================================================================================================================================#
# Setup pour le cog
async def setup(bot):
    await bot.add_cog(LevelForUser(bot))
