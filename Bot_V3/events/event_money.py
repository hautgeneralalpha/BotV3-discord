#===============================================================================================================================================#
#========================================================EVENEMENT DISCUTION MONEY==============================================================#
#===============================================================================================================================================#
#importation des modules nécessaires
import discord
from discord.ext import commands
import sqlite3
import random

#===============================================================================================================================================#
# Liste des embeds pour le channel de connexion
list_embed = ["Pram Heda dev", "Bot serveur leak"]

#===============================================================================================================================================#
# Configuration pour la génération d'argent
MIN_WORDS_FOR_MONEY = 10  # Nombre minimum de mots pour générer de l'argent
REWARD_EVERY_TEN_MESSAGES = 1  # Récompense supplémentaire tous les 10 messages
REWARD_PER_TEN_LEVELS = 100  # Récompense en coins pour chaque palier de 10 niveaux

#===============================================================================================================================================#
#définition de la classe
class AddmoneyDiscution(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.message_count = 0  # Compteur de messages reçus
        self.db_path_eco = 'eco.sqlite'  # Chemin vers la base de données SQLite pour l'argent
        self.db_path_level = 'level.sqlite'  # Chemin vers la base de données SQLite pour les niveaux

#===============================================================================================================================================#
# Fonction pour ajouter de l'argent à l'utilisateur dans la base de données
    def add_money_to_user(self, user_id, amount):
        conn = sqlite3.connect(self.db_path_eco)
        cursor = conn.cursor()
        
        # Vérifier si l'utilisateur existe déjà dans la base de données
        cursor.execute("SELECT wallet FROM eco WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        
        if result:
            # Mettre à jour le solde du portefeuille de l'utilisateur
            new_balance = result[0] + amount
            cursor.execute("UPDATE eco SET wallet = ? WHERE user_id = ?", (new_balance, user_id))
        else:
            # Ajouter l'utilisateur à la base de données avec le solde initial
            cursor.execute("INSERT INTO eco (user_id, wallet, bank, inventory) VALUES (?, ?, 0, '')", (user_id, amount))
        
        conn.commit()
        conn.close()

#===============================================================================================================================================#
# Fonction pour obtenir le niveau d'un utilisateur depuis la base de données de niveau
    def get_user_level(self, user_id):
        conn = sqlite3.connect(self.db_path_level)
        cursor = conn.cursor()
        cursor.execute("SELECT level FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        conn.close()
        if result:
            return result[0]
        else:
            return 0

#===============================================================================================================================================#
# Fonction pour ajouter des coins en fonction du niveau atteint
    def reward_for_level(self, user_id):
        level = self.get_user_level(user_id)
        if level % 10 == 0 and level != 0:
            self.add_money_to_user(user_id, REWARD_PER_TEN_LEVELS)

#===============================================================================================================================================#
# Evénement lorsque le bot reçoit un message
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return  # Ignore les messages du bot lui-même

        # Comptage des messages
        self.message_count += 1

        # Vérifier le nombre de mots dans le message
        word_count = len(message.content.split())
        money_generated = 0

        if word_count >= MIN_WORDS_FOR_MONEY:
            money_generated += 1  # Générer 1 unité d'argent pour un message de 10 mots ou plus

        # Récompense supplémentaire tous les 10 messages
        if self.message_count % 10 == 0:
            money_generated += REWARD_EVERY_TEN_MESSAGES

        # Ajouter l'argent à l'utilisateur dans la base de données
        user_id = message.author.id
        self.add_money_to_user(user_id, money_generated)

        # Récompenser l'utilisateur s'il atteint un palier de niveau
        self.reward_for_level(user_id)

#===============================================================================================================================================#
#setup joinquit
async def setup(bot):
    await bot.add_cog(AddmoneyDiscution(bot))
