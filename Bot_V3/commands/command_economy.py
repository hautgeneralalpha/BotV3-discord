#===============================================================================================================================================#
#========================================================EVENEMENT init economy=================================================================#
#===============================================================================================================================================#
#importation des modules nécessaires
import discord
from discord.ext import commands
import sqlite3
import random
import calendar
import time
import datetime
from discord.ui import Button, View, Select
import json

#===============================================================================================================================================#
#temp passé pour le timestamp
ts = calendar.timegm(time.gmtime())

#===============================================================================================================================================#
# Liste des embeds pour le channel de connexion
list_embed = ["Pram Heda dev", "Bot serveur leak"]

#===============================================================================================================================================#
#définition de la classe
class Event(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.init_db()
        with open("configuration.json", "r") as f:
            self.config = json.load(f)

#===============================================================================================================================================#
#initialisation
    @commands.Cog.listener()
    async def on_ready(self):
        db = sqlite3.connect("eco.sqlite")
        cursor = db.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS eco (
                user_id INTEGER PRIMARY KEY,
                wallet INTEGER,
                bank INTEGER,
                inventory TEXT
            )
        """)
        db.commit()
        cursor.close()
        db.close()
        print("Bot is ready")

#===============================================================================================================================================#
#initialisation quand premier message
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        author = message.author
        db = sqlite3.connect("eco.sqlite")
        cursor = db.cursor()

        cursor.execute("SELECT user_id FROM eco WHERE user_id = ?", (author.id,))
        result = cursor.fetchone()
        if result is None:
            cursor.execute(
                "INSERT INTO eco(user_id, wallet, bank, inventory) VALUES (?, ?, ?, ?)",
                (author.id, 100, 0, "")  # Ajout d'un inventaire vide
            )

        db.commit()
        cursor.close()
        db.close()

    @discord.ui.button(label="salut", style=discord.ButtonStyle.blurple)
    async def callback_salut(self, button, interaction : discord.Interaction):
        await interaction.response.send_message("salut je suis un message invicible.", ephemeral=True)

#===============================================================================================================================================#
#commande voir portefeuille
    @commands.command(name="balance", description="Affiche le portefeuille d'un utilisateur", help="!balance @user")
    @commands.guild_only()
    @commands.cooldown(1, 5.0, commands.BucketType.user)
    async def balance(self, ctx, member: discord.Member = None):
        """
        Affiche le portefeuille d'un utilisateur.

        """
        if member is None:
            member = ctx.author

        db = sqlite3.connect("eco.sqlite")
        cursor = db.cursor()

        cursor.execute("SELECT wallet, bank FROM eco WHERE user_id = ?", (member.id,))
        bal = cursor.fetchone()
        if bal is None:
            wallet, bank = 0, 0
        else:
            wallet, bank = bal

        embed = discord.Embed(
            title="Porte feuille",
            description=f"{member.mention} a {wallet} BotCoins dans son portefeuille et {bank} BotCoins dans sa banque",
            color=discord.Color.red()
        )
        embed.set_footer(icon_url=self.bot.user.avatar.url, text=random.choice(list_embed))
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url)
        embed.set_thumbnail(url=member.avatar.url)
        embed.timestamp = datetime.datetime.now()

        await ctx.send(embed=embed)
        cursor.close()
        db.close()

#===============================================================================================================================================#
#commande voir l'inventaire
    @commands.command(name="inventory", description="Affiche l'inventaire d'un utilisateur", help="!inventory @user")
    @commands.guild_only()
    @commands.cooldown(1, 5.0, commands.BucketType.user)
    async def inventory(self, ctx, member: discord.Member = None):
        """
        Affiche l'inventaire d'un utilisateur

        """
        if member is None:
            member = ctx.author

        db = sqlite3.connect("eco.sqlite")
        cursor = db.cursor()

        cursor.execute("SELECT inventory FROM eco WHERE user_id = ?", (member.id,))
        inv = cursor.fetchone()
        if inv is None or inv[0] is None or inv[0] == "":
            inventory = "rien"
        else:
            inventory = inv[0]

        embed = discord.Embed(
            title="Inventaire",
            description=f"{member.mention} a {inventory} dans son inventaire",
            color=discord.Color.red()
        )
        embed.set_footer(icon_url=self.bot.user.avatar.url, text=random.choice(list_embed))
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url)
        embed.set_thumbnail(url=member.avatar.url)
        embed.timestamp = datetime.datetime.now()

        await ctx.send(embed=embed)
        cursor.close()
        db.close()
        
#===============================================================================================================================================#
#commande gagner aléatoirement de l'argent
    @commands.command(name="earn", description="Gagne aléatoirement de l'argent entre 0 et 5", help="!earn")
    @commands.guild_only()
    @commands.cooldown(1, 5000.0, commands.BucketType.user)
    async def earn(self, ctx):
        """
        Commande pour gagner aléatoirement de l'argent entre 0 et 5

        """
        member = ctx.author
        earnings = random.randint(0, 5)

        db = sqlite3.connect("eco.sqlite")
        cursor = db.cursor()

        cursor.execute("SELECT wallet FROM eco WHERE user_id = ?", (member.id,))
        result = cursor.fetchone()

        if result is None:
            wallet = 0
        else:
            wallet = result[0]  # Extraire la valeur entière de la tuple

        new_wallet_balance = wallet + earnings
        cursor.execute("UPDATE eco SET wallet = ? WHERE user_id = ?", (new_wallet_balance, member.id))

        db.commit()  # Assurez-vous que les modifications sont enregistrées

        embed = discord.Embed(
            title="Jeux du hasard",
            description=f"Tu as gagné {earnings} BotCoins",
            color=discord.Color.green()
        )
        embed.set_footer(icon_url=self.bot.user.avatar.url, text=random.choice(list_embed))
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url)
        embed.set_thumbnail(url=member.avatar.url)
        embed.timestamp = datetime.datetime.now()

        await ctx.send(embed=embed)
        log_channel_id = self.bot.get_channel(self.config.get("log_channel_id"))
        log_channel = self.bot.get_channel(log_channel_id)
        if log_channel:
            await log_channel.send(embed=embed)

        cursor.close()
        db.close()

#===============================================================================================================================================#
#initialisation du shop
    def init_db(self):
        # Initialisation de la base de données du shop
        conn = sqlite3.connect('shop.sqlite')
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS shop (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        description TEXT,
                        price INTEGER NOT NULL,
                        category TEXT,
                        type_item TEXT,
                        actions,
                        icon TEXT)''')  
        conn.commit()
        conn.close()

#===============================================================================================================================================#
#commande pour ajouter des items dans le shop
    @commands.command(name="add_item", description="Permet d'ajouter un item dans le shop", help='!add_item "name" "description" [prix] [categorie] [type (url ou role)] [action (lien ou nom du role)] [url de l\'icon]')
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def add_item(self, ctx, name: str, description: str, price: int, category: str, type_item: str, actions: str, icon: str):
        """
        Permet d'ajouter un item dans le shop.

        """
        try:
            # Utilisation de `with` pour garantir que la connexion est fermée correctement
            with sqlite3.connect('shop.sqlite') as conn:
                cursor = conn.cursor()
                cursor.execute('INSERT INTO shop (name, description, price, category, type_item, actions, icon) VALUES (?, ?, ?, ?, ?, ?, ?)', 
                            (name, description, price, category, type_item, actions, icon))
                conn.commit()

            embed = discord.Embed(title="Ajout d'item", description=f"L'item {name} de type {type_item} a été ajouté dans le shop.", color=discord.Color.green())
            embed.set_footer(icon_url=self.bot.user.avatar.url, text=random.choice(list_embed))
            embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url)
            embed.set_thumbnail(url=f"{icon}")
            embed.timestamp = datetime.datetime.now()

            await ctx.send(embed=embed)
            log_channel_id = self.bot.get_channel(self.config.get("log_channel_id"))
            log_channel = self.bot.get_channel(log_channel_id)
            if log_channel:
                await log_channel.send(embed=embed)

        except sqlite3.OperationalError as e:
            await ctx.send(f"Une erreur est survenue lors de l'ajout de l'item: {e}")
        except Exception as e:
            await ctx.send(f'Une erreur exceptionnelle est arrivée: {e}')

#===============================================================================================================================================#
# commande pour mettre à jour le category d'un item
    @commands.command(name="updatecategory", description="Met à jour le category d'un article dans la base de données", help="!updatecategory [ID de l'item ou nom] [nouveau nom]")
    @commands.guild_only()
    @commands.has_permissions(administrator=True)  # Assurez-vous que seuls les administrateurs peuvent utiliser cette commande
    async def update_category(self, ctx, item_id: int, new_category: str):
        """
        Met à jour le category d'un article dans la base de données.

        :param item_id: L'identifiant de l'article dont le category doit être mis à jour.
        :param new_category: Le nouveau category à définir pour l'article.
        """
        try:
            # Connexion à la base de données
            conn = sqlite3.connect('shop.sqlite')
            cursor = conn.cursor()

            # Vérifier si le nouveau category existe déjà
            cursor.execute('SELECT id FROM shop WHERE category = ?', (new_category,))

            # Requête SQL pour mettre à jour le category
            cursor.execute('''
                UPDATE shop
                SET category = ?
                WHERE id = ?
            ''', (new_category, item_id))

            # Validation de la transaction
            conn.commit()

            # Vérifier si la mise à jour a eu un effet
            if cursor.rowcount > 0:
                await ctx.send(f"Le category de l'article avec ID {item_id} a été mis à jour avec succès.")
            else:
                await ctx.send("Aucun article trouvé avec cet ID.")

        except sqlite3.Error as e:
            await ctx.send(f"Erreur lors de la mise à jour du category : {e}")

        finally:
            # Fermeture de la connexion
            conn.close()

#===============================================================================================================================================#
#commande pour acheter des items du shop
    @commands.command(name='buy', description="Permet à un utilisateur d'acheter un article du shop", help="!buy [nom de l'item]")
    @commands.guild_only()
    async def buy(self, ctx, item_name: str):
        """
        Commande qui permet à un utilisateur d'acheter un article du shop.

        """
        user_id = ctx.author.id
        user_name = ctx.author.name

        with sqlite3.connect('shop.sqlite') as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT price, type_item FROM shop WHERE name = ?', (item_name,))
            item = cursor.fetchone()
            if item is None:
                await ctx.send('Item non trouvé.')
                return

            item_price, item_type = item

        with sqlite3.connect('eco.sqlite') as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT wallet, inventory FROM eco WHERE user_id = ?', (user_id,))
            user = cursor.fetchone()
            if user is None:
                cursor.execute('INSERT INTO eco (user_id, wallet, bank, inventory) VALUES (?, 0, 0, "")', (user_id,))
                conn.commit()
                user_wallet = 0
                user_inventory = ""
            else:
                user_wallet, user_inventory = user

            if user_wallet < item_price:
                embed_pa = discord.Embed(
                    title="Manque d'argent",
                    description=f"{ctx.author.mention}, tu n'as pas assez d'argent.",
                    color=discord.Color.blue()
                )
                embed_pa.set_footer(icon_url=self.bot.user.avatar.url, text=random.choice(list_embed))
                embed_pa.set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url)
                embed_pa.set_thumbnail(url=ctx.author.avatar.url)
                embed_pa.timestamp = datetime.datetime.now()

                await ctx.send(embed=embed_pa, delete_after=10)
                return

            new_wallet = user_wallet - item_price
            new_inventory = f"{user_inventory},{item_name}" if user_inventory else item_name
            cursor.execute('UPDATE eco SET wallet = ?, inventory = ? WHERE user_id = ?', (new_wallet, new_inventory, user_id))
            conn.commit()

        embed = discord.Embed(
            title="Achat d'item",
            description=f"{user_name} a acheté {item_name} de type {item_type}.",
            color=discord.Color.green()
        )
        embed.set_footer(icon_url=self.bot.user.avatar.url, text=random.choice(list_embed))
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url)
        embed.set_thumbnail(url=ctx.author.avatar.url)
        embed.timestamp = datetime.datetime.now()

        await ctx.send(embed=embed)
        log_channel_id = self.bot.get_channel(self.config.get("log_channel_id"))
        log_channel = self.bot.get_channel(log_channel_id)
        if log_channel:
            await log_channel.send(embed=embed)

#===============================================================================================================================================#
#commande pour voir tous les items du shop
    @commands.command(name="shop", description="Affiche les articles du shop, soit tous les articles, soit ceux d'une catégorie spécifique", help="!shop [categorie (facultatif)]")
    @commands.guild_only()
    async def shop(self, ctx, category: str = None):
        """
        Affiche les articles du shop, soit tous les articles, soit ceux d'une catégorie spécifique.

        :param category: La catégorie des articles à afficher. Si None, affiche tous les articles.
        """
        try:
            # Connexion à la base de données du shop
            conn = sqlite3.connect('shop.sqlite')
            cursor = conn.cursor()

            # Requête SQL pour sélectionner les articles
            if category:
                # Filtrer par catégorie
                cursor.execute('SELECT name, description, price, category, type_item, icon FROM shop WHERE category = ?', (category,))
            else:
                # Afficher tous les articles
                cursor.execute('SELECT name, description, price, category, type_item, icon FROM shop')

            items = cursor.fetchall()
            conn.close()

            if not items:
                if category:
                    embed = discord.Embed(
                        title="SHOP",
                        description=f"Aucun article trouvé dans la catégorie '{category}'.",
                        color=discord.Color.red()  # Vous pouvez personnaliser la couleur de l'embed
                    )
                else:
                    embed = discord.Embed(
                        title="SHOP",
                        description="Le magasin est vide.",
                        color=discord.Color.red()  # Vous pouvez personnaliser la couleur de l'embed
                    )
                await ctx.send(embed=embed)
                return

            # Création des embeds pour chaque item
            for item in items:
                name, description, price, item_category, type_item, icon_url = item

                embed = discord.Embed(
                    title=name,
                    description=description,
                    color=discord.Color.blue()  # Vous pouvez personnaliser la couleur de l'embed
                )
                embed.add_field(name="Prix", value=f"{price} BotCoins")
                embed.add_field(name="Catégorie", value=item_category)
                embed.add_field(name="Type d'article", value=type_item)
                if icon_url:
                    embed.set_thumbnail(url=icon_url)  # Ajout de l'image de l'item
                
                await ctx.send(embed=embed)

        except sqlite3.Error as e:
            await ctx.send(f"Erreur lors de la récupération des articles : {e}")

#===============================================================================================================================================#
#commande pour supprimer des items du shop
    @commands.command(name="del_item", description="Permet de supprimer un item du shop", help="!del_item [nom de l'item]")
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def del_item(self, ctx, *, item_name: str):
        """
        Commande qui permet de supprimer un item du shop.

        """
        conn = sqlite3.connect('shop.sqlite')
        cursor = conn.cursor()

        cursor.execute('DELETE FROM shop WHERE name = ?', (item_name,))
        conn.commit()
        rows_deleted = cursor.rowcount
        conn.close()

        embed = discord.Embed(title="Suppression d'item", color=discord.Color.red())

        if rows_deleted == 0:
            embed.add_field(name="Échec", value=f"L'item '{item_name}' n'a pas été trouvé dans le shop.")
        else:
            embed.add_field(name="Succès", value=f"L'item '{item_name}' a été supprimé du shop.")

        await ctx.send(embed=embed)

#===============================================================================================================================================#
# Commande pour supprimer des items d'un inventaire
    @commands.command(name="del_inventory", help="del_inventory @user [nom de l'item]", description="Supprime un item de l'inventaire d'un utilisateur")
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def del_inventory(self, ctx, member: discord.Member, item_name: str):
        """
        Supprime un item de l'inventaire d'un utilisateur spécifié.

        :param member: L'utilisateur dont l'item doit être supprimé.
        :param item_name: Le nom de l'item à supprimer.
        """
        conn = sqlite3.connect('eco.sqlite')
        cursor = conn.cursor()
        cursor.execute('SELECT inventory FROM eco WHERE user_id = ?', (member.id,))
        user_inventory = cursor.fetchone()

        if user_inventory is None:
            await ctx.send(f"{member.mention} n'a pas d'inventaire.")
            conn.close()
            return

        inventory_items = user_inventory[0].split(',') if user_inventory[0] else []
        if item_name in inventory_items:
            inventory_items.remove(item_name)
            new_inventory = ','.join(inventory_items)
            cursor.execute('UPDATE eco SET inventory = ? WHERE user_id = ?', (new_inventory, member.id))
            conn.commit()
            await ctx.send(f'L\'item "{item_name}" a été supprimé de l\'inventaire de {member.mention}.')
        else:
            await ctx.send(f'{member.mention} n\'a pas "{item_name}" dans son inventaire.')

        conn.close()

#===============================================================================================================================================#
# Commande pour donner un item à un autre utilisateur
    @commands.command(name="don", help="!don @user [nom de l'item]", description="Permet de donner un item à un autre utilisateur")
    @commands.guild_only()
    @commands.cooldown(1, 10.0, commands.BucketType.user)
    async def don(self, ctx, recipient: discord.Member, *, item_name: str):
        """
        Permet de donner un item à un autre utilisateur sans compter les ressources.

        :param recipient: L'utilisateur qui recevra l'item.
        :param item_name: Le nom de l'item à donner.
        """
        donor_id = ctx.author.id
        recipient_id = recipient.id

        db = sqlite3.connect("eco.sqlite")
        cursor = db.cursor()

        # Vérifier l'inventaire du donneur
        cursor.execute("SELECT inventory FROM eco WHERE user_id = ?", (donor_id,))
        donor_inventory = cursor.fetchone()
        if donor_inventory is None:
            await ctx.send(f"{ctx.author.mention}, ton inventaire est introuvable.")
            cursor.close()
            db.close()
            return

        donor_inventory = donor_inventory[0]
        if donor_inventory is None:
            donor_inventory = ""

        # Vérifier si l'item est dans l'inventaire du donneur
        inventory_items = donor_inventory.split(',') if donor_inventory else []
        if item_name not in inventory_items:
            await ctx.send(f"{ctx.author.mention}, tu n'as pas l'item '{item_name}' dans ton inventaire.")
            cursor.close()
            db.close()
            return

        # Retirer l'item de l'inventaire du donneur
        inventory_items.remove(item_name)
        new_donor_inventory = ','.join(inventory_items)
        cursor.execute("UPDATE eco SET inventory = ? WHERE user_id = ?", (new_donor_inventory, donor_id))

        # Ajouter l'item à l'inventaire du destinataire
        cursor.execute("SELECT inventory FROM eco WHERE user_id = ?", (recipient_id,))
        recipient_inventory = cursor.fetchone()
        if recipient_inventory is None:
            # Initialiser l'inventaire du destinataire s'il n'existe pas encore
            cursor.execute("INSERT INTO eco (user_id, wallet, bank, inventory) VALUES (?, 0, 0, ?)", (recipient_id, item_name))
        else:
            recipient_inventory = recipient_inventory[0]
            if recipient_inventory is None:
                recipient_inventory = ""

            new_recipient_inventory = f"{recipient_inventory},{item_name}" if recipient_inventory else item_name
            cursor.execute("UPDATE eco SET inventory = ? WHERE user_id = ?", (new_recipient_inventory, recipient_id))

        db.commit()
        cursor.close()
        db.close()

        embed = discord.Embed(
            title="Item donné",
            description=f"{ctx.author.mention} a donné l'item '{item_name}' à {recipient.mention}.",
            color=discord.Color.green()
        )
        embed.set_footer(icon_url=self.bot.user.avatar.url, text=random.choice(list_embed))
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url)
        embed.set_thumbnail(url=ctx.author.avatar.url)
        embed.timestamp = datetime.datetime.now()

        await ctx.send(embed=embed)

        # Envoyer une confirmation au destinataire
        try:
            recipient_embed = discord.Embed(
                title="Item reçu",
                description=f"Tu as reçu l'item '{item_name}' de {ctx.author.mention}.",
                color=discord.Color.blue()
            )
            recipient_embed.set_footer(icon_url=self.bot.user.avatar.url, text=random.choice(list_embed))
            recipient_embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url)
            recipient_embed.set_thumbnail(url=ctx.author.avatar.url)
            recipient_embed.timestamp = datetime.datetime.now()

            await recipient.send(embed=recipient_embed)
        except discord.Forbidden:
            await ctx.send(f"{recipient.mention} a ses DMs fermés, donc je ne peux pas lui envoyer de confirmation.")

#===============================================================================================================================================#
# Commande pour donner un item à un autre utilisateur (admin uniquement, sans avoir l'item dans l'inventaire)
    @commands.command(name="give", help="!give @user [nom de l'item]", description="Permet aux administrateurs de donner un item à un utilisateur sans avoir l'item dans l'inventaire.")
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def give(self, ctx, recipient: discord.Member, *, item_name: str):
        """
        Permet aux administrateurs de donner un item à un utilisateur, sans avoir besoin de l'item dans l'inventaire du donneur.

        :param recipient: L'utilisateur qui recevra l'item.
        :param item_name: Le nom de l'item à donner.
        """
        recipient_id = recipient.id

        db = sqlite3.connect("eco.sqlite")
        cursor = db.cursor()

        # Vérifier l'inventaire du destinataire
        cursor.execute("SELECT inventory FROM eco WHERE user_id = ?", (recipient_id,))
        recipient_inventory = cursor.fetchone()
        if recipient_inventory is None:
            # Initialiser l'inventaire du destinataire s'il n'existe pas encore
            cursor.execute("INSERT INTO eco (user_id, wallet, bank, inventory) VALUES (?, 0, 0, ?)", (recipient_id, item_name))
        else:
            recipient_inventory = recipient_inventory[0]
            if recipient_inventory is None:
                recipient_inventory = ""

            new_recipient_inventory = f"{recipient_inventory},{item_name}" if recipient_inventory else item_name
            cursor.execute("UPDATE eco SET inventory = ? WHERE user_id = ?", (new_recipient_inventory, recipient_id))

        db.commit()
        cursor.close()
        db.close()

        # Envoi de la confirmation à l'administrateur
        embed_admin = discord.Embed(
            title="Item donné",
            description=f"> {ctx.author.mention}, tu as donné l'item '{item_name}' à {recipient.mention}.",
            color=discord.Color.green()
        )
        embed_admin.set_footer(icon_url=self.bot.user.avatar.url, text=random.choice(list_embed))
        embed_admin.set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url)
        embed_admin.set_thumbnail(url=ctx.author.avatar.url)
        embed_admin.timestamp = datetime.datetime.now()

        await ctx.send(embed=embed_admin)

        # Envoi de la confirmation au destinataire
        try:
            embed_recipient = discord.Embed(
                title="Item reçu",
                description=f"> {recipient.mention}, tu as reçu l'item '{item_name}' de {ctx.author.mention}.",
                color=discord.Color.blue()
            )
            embed_recipient.set_footer(icon_url=self.bot.user.avatar.url, text=random.choice(list_embed))
            embed_recipient.set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url)
            embed_recipient.set_thumbnail(url=ctx.author.avatar.url)
            embed_recipient.timestamp = datetime.datetime.now()

            await recipient.send(embed=embed_recipient)
        except discord.Forbidden:
            embed_error = discord.Embed(
                title="Erreur",
                description=f"{recipient.mention} a ses DMs fermés, donc je ne peux pas lui envoyer de confirmation.",
                color=discord.Color.red()
            )
            embed_error.set_footer(icon_url=self.bot.user.avatar.url, text=random.choice(list_embed))
            embed_error.set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url)
            embed_error.set_thumbnail(url=ctx.author.avatar.url)
            embed_error.timestamp = datetime.datetime.now()

            await ctx.send(embed=embed_error)

#===============================================================================================================================================#
# Commande choice
    @commands.command(name="choice", help="!choice", description="Affiche les articles du shop et permet de choisir un article à acheter.")
    @commands.guild_only()
    async def choice(self, ctx):
        """
        Affiche les articles du shop et permet à l'utilisateur de choisir un article à acheter.

        """
        # Connexion à la base de données du shop
        conn = sqlite3.connect('shop.sqlite')
        cursor = conn.cursor()

        cursor.execute('SELECT name, description, price FROM shop')
        items = cursor.fetchall()
        conn.close()

        if not items:
            embed = discord.Embed(
                title="Shop vide",
                description="Le shop est actuellement vide.",
                color=discord.Color.red()
            )
            embed.set_footer(icon_url=self.bot.user.avatar.url, text=random.choice(list_embed))
            embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url)
            embed.timestamp = datetime.datetime.now()
            await ctx.send(embed=embed)
            return

        options = [
            discord.SelectOption(label=item[0], description=f"{item[1]} - {item[2]} BotCoins")
            for item in items
        ]

        select = Select(
            placeholder="Choisissez un article à acheter...",
            options=options
        )

        # Stocke les messages envoyés pour suppression ultérieure
        self.messages_to_delete = []

        async def select_callback(interaction: discord.Interaction):
            selected_item = select.values[0]

            # Déférer la réponse pour pouvoir la modifier plus tard
            await interaction.response.defer()

            embed = discord.Embed(
                title="Confirmation d'achat",
                description=f"Voulez-vous acheter **{selected_item}** ?",
                color=discord.Color.orange()
            )
            embed.set_footer(icon_url=self.bot.user.avatar.url, text=random.choice(list_embed))
            embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url)
            embed.timestamp = datetime.datetime.now()

            confirmation_view = View()

            confirm_button = Button(label="Oui", style=discord.ButtonStyle.green)
            cancel_button = Button(label="Non", style=discord.ButtonStyle.red)

            async def confirm_callback(interaction: discord.Interaction):
                await self.buy_item(ctx, selected_item)

                embed_success = discord.Embed(
                    title="Achat réussi",
                    description=f"Vous avez acheté **{selected_item}**.",
                    color=discord.Color.green()
                )
                embed_success.set_footer(icon_url=self.bot.user.avatar.url, text=random.choice(list_embed))
                embed_success.set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url)
                embed_success.timestamp = datetime.datetime.now()

                await interaction.response.edit_message(embed=embed_success, view=None)

                # Supprimer les messages d'interaction après confirmation
                for msg in self.messages_to_delete:
                    try:
                        await msg.delete()
                    except discord.NotFound:
                        pass

            async def cancel_callback(interaction: discord.Interaction):
                embed_cancel = discord.Embed(
                    title="Achat annulé",
                    description="L'achat a été annulé.",
                    color=discord.Color.red()
                )
                embed_cancel.set_footer(icon_url=self.bot.user.avatar.url, text=random.choice(list_embed))
                embed_cancel.set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url)
                embed_cancel.timestamp = datetime.datetime.now()
                await interaction.response.edit_message(embed=embed_cancel, view=None)

                # Supprimer les messages d'interaction après annulation
                for msg in self.messages_to_delete:
                    try:
                        await msg.delete()
                    except discord.NotFound:
                        pass

            confirm_button.callback = confirm_callback
            cancel_button.callback = cancel_callback

            confirmation_view.add_item(confirm_button)
            confirmation_view.add_item(cancel_button)

            # Envoyer le message de confirmation avec les boutons
            message = await interaction.followup.send(embed=embed, view=confirmation_view)
            self.messages_to_delete.append(message)

        select.callback = select_callback

        view = View()
        view.add_item(select)

        embed = discord.Embed(
            title="Shop",
            description="Choisissez un article à acheter dans le shop.",
            color=discord.Color.blue()
        )
        embed.set_footer(icon_url=self.bot.user.avatar.url, text=random.choice(list_embed))
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url)
        embed.timestamp = datetime.datetime.now()

        message = await ctx.send(embed=embed, view=view)
        self.messages_to_delete.append(message)

    async def buy_item(self, ctx, item_name):
        user_id = ctx.author.id
        user_name = ctx.author.name

        with sqlite3.connect('shop.sqlite') as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT price, type_item FROM shop WHERE name = ?', (item_name,))
            item = cursor.fetchone()
            if item is None:
                embed = discord.Embed(
                    title="Item non trouvé",
                    description="L'item que vous avez choisi n'existe pas.",
                    color=discord.Color.red()
                )
                embed.set_footer(icon_url=self.bot.user.avatar.url, text=random.choice(list_embed))
                embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url)
                embed.timestamp = datetime.datetime.now()
                await ctx.send(embed=embed, delete_after=10)
                return

            item_price, item_type = item

        with sqlite3.connect('eco.sqlite') as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT wallet, inventory FROM eco WHERE user_id = ?', (user_id,))
            user = cursor.fetchone()
            if user is None:
                cursor.execute('INSERT INTO eco (user_id, wallet, bank, inventory) VALUES (?, 0, 0, "")', (user_id,))
                conn.commit()
                user_wallet = 0
                user_inventory = ""
            else:
                user_wallet, user_inventory = user

            if user_wallet < item_price:
                embed = discord.Embed(
                    title="Manque d'argent",
                    description=f"{ctx.author.mention}, tu n'as pas assez d'argent.",
                    color=discord.Color.red()
                )
                embed.set_footer(icon_url=self.bot.user.avatar.url, text=random.choice(list_embed))
                embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url)
                embed.timestamp = datetime.datetime.now()

                await ctx.send(embed=embed, delete_after=10)
                return

            new_wallet = user_wallet - item_price
            new_inventory = f"{user_inventory},{item_name}" if user_inventory else item_name
            cursor.execute('UPDATE eco SET wallet = ?, inventory = ? WHERE user_id = ?', (new_wallet, new_inventory, user_id))
            conn.commit()

        embed = discord.Embed(
            title="Achat réussi",
            description=f"{user_name} a acheté **{item_name}** de type **{item_type}**.",
            color=discord.Color.green()
        )
        embed.set_footer(icon_url=self.bot.user.avatar.url, text=random.choice(list_embed))
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url)
        embed.timestamp = datetime.datetime.now()

        await ctx.send(embed=embed, delete_after=10)
        log_channel_id = self.bot.get_channel(self.config.get("log_channel_id"))
        log_channel = self.bot.get_channel(log_channel_id)
        if log_channel:
            await log_channel.send(embed=embed)

#===============================================================================================================================================#
#commande utiliser des items du shop
    @commands.command(name="use", description="Permet d'utiliser un objet", help="!use [item]")
    @commands.guild_only()
    @commands.cooldown(1, 5.0, commands.BucketType.user)
    async def use(self, ctx, *, item_name: str):
        """
        Permet d'utiliser un objet de ton inventaire
        """
        user = ctx.author
        guild = ctx.guild

        # Connexion à shop.sqlite pour vérifier le type d'item
        with sqlite3.connect('shop.sqlite') as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT type_item, actions, icon FROM shop WHERE name = ?', (item_name,))
            item = cursor.fetchone()

        if item is None:
            embed = discord.Embed(
                title="Objet non trouvé",
                description=f"L'objet **{item_name}** n'a pas été trouvé dans le shop.",
                color=discord.Color.red()
            )
            embed.set_footer(icon_url=self.bot.user.avatar.url, text=random.choice(list_embed))
            embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url)
            embed.set_thumbnail(url=ctx.author.avatar.url)
            embed.timestamp = datetime.datetime.now()
            await ctx.send(embed=embed)
            return

        item_type, item_actions, item_icon = item

        # Connexion à eco.sqlite pour mettre à jour l'inventaire
        with sqlite3.connect('eco.sqlite') as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT inventory FROM eco WHERE user_id = ?', (user.id,))
            user_inventory = cursor.fetchone()

            if user_inventory is None:
                cursor.execute('INSERT INTO eco (user_id, wallet, bank, inventory) VALUES (?, 0, 0, "")', (user.id,))
                user_inventory = ('',)
            else:
                user_inventory = user_inventory[0]

            # Supprimer l'item de l'inventaire
            inventory_items = user_inventory.split(',') if user_inventory else []
            if item_name in inventory_items:
                inventory_items.remove(item_name)
                new_inventory = ','.join(inventory_items)
                cursor.execute('UPDATE eco SET inventory = ? WHERE user_id = ?', (new_inventory, user.id))
            else:
                embed = discord.Embed(
                    title="Objet non trouvé",
                    description=f'Vous n\'avez pas **{item_name}** dans votre inventaire.',
                    color=discord.Color.red()
                )
                embed.set_footer(icon_url=self.bot.user.avatar.url, text=random.choice(list_embed))
                embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url)
                embed.set_thumbnail(url=ctx.author.avatar.url)
                embed.timestamp = datetime.datetime.now()
                await ctx.send(embed=embed)
                return

            conn.commit()

        if item_type == 'url':
            # Envoi de l'URL par message privé
            try:
                # Création de l'embed pour le message privé
                embed = discord.Embed(
                    title=f"URL pour **{item_name}**",
                    description=f"Voici l'URL pour **{item_name}** : {item_actions}",
                    color=discord.Color.blurple()
                )
                embed.set_footer(icon_url=self.bot.user.avatar.url, text=random.choice(list_embed))
                embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url)
                embed.set_thumbnail(url=item_icon)
                embed.timestamp = datetime.datetime.now()

                await user.send(embed=embed)
                
                embed = discord.Embed(
                    title="URL envoyée",
                    description=f"L'URL pour **{item_name}** a été envoyée par message privé.",
                    color=discord.Color.green()
                )
                embed.set_footer(icon_url=self.bot.user.avatar.url, text=random.choice(list_embed))
                embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url)
                embed.set_thumbnail(url=item_icon)
                embed.timestamp = datetime.datetime.now()
                await ctx.send(embed=embed)
            except discord.Forbidden:
                embed = discord.Embed(
                    title="Erreur d'envoi",
                    description='Je ne peux pas vous envoyer un message privé. Veuillez activer les MP depuis ce serveur.',
                    color=discord.Color.red()
                )
                embed.set_footer(icon_url=self.bot.user.avatar.url, text=random.choice(list_embed))
                embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url)
                embed.set_thumbnail(url=ctx.author.avatar.url)
                embed.timestamp = datetime.datetime.now()
                await ctx.send(embed=embed)
        elif item_type == 'role':
            # Attribution du rôle
            role = discord.utils.get(guild.roles, name=item_name)
            if role is None:
                embed = discord.Embed(
                    title="Rôle non trouvé",
                    description=f'Le rôle **{item_name}** n\'a pas été trouvé sur ce serveur.',
                    color=discord.Color.red()
                )
                embed.set_footer(icon_url=self.bot.user.avatar.url, text=random.choice(list_embed))
                embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url)
                embed.set_thumbnail(url=item_icon)
                embed.timestamp = datetime.datetime.now()
                await ctx.send(embed=embed)
                return

            try:
                await user.add_roles(role)
                embed = discord.Embed(
                    title="Rôle attribué",
                    description=f'Vous avez reçu le rôle **{item_name}**.',
                    color=discord.Color.green()
                )
                embed.set_footer(icon_url=self.bot.user.avatar.url, text=random.choice(list_embed))
                embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url)
                embed.set_thumbnail(url=item_icon)
                embed.timestamp = datetime.datetime.now()
                await ctx.send(embed=embed)
            except discord.Forbidden:
                embed = discord.Embed(
                    title="Erreur d'attribution",
                    description='Je n\'ai pas les permissions nécessaires pour attribuer ce rôle. Veuillez vérifier mes permissions.',
                    color=discord.Color.red()
                )
                embed.set_footer(icon_url=self.bot.user.avatar.url, text=random.choice(list_embed))
                embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url)
                embed.set_thumbnail(url=item_icon)
                embed.timestamp = datetime.datetime.now()
                await ctx.send(embed=embed)
            except discord.HTTPException as e:
                embed = discord.Embed(
                    title="Erreur",
                    description=f'Une erreur est survenue lors de l\'attribution du rôle : {e}',
                    color=discord.Color.red()
                )
                embed.set_footer(icon_url=self.bot.user.avatar.url, text=random.choice(list_embed))
                embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url)
                embed.set_thumbnail(url=item_icon)
                embed.timestamp = datetime.datetime.now()
                await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                title="Type d'objet non supporté",
                description='Ce type d\'objet n\'est pas pris en charge par cette commande.',
                color=discord.Color.orange()
            )
            embed.set_footer(icon_url=self.bot.user.avatar.url, text=random.choice(list_embed))
            embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url)
            embed.set_thumbnail(url=item_icon)
            embed.timestamp = datetime.datetime.now()
            await ctx.send(embed=embed)

#===============================================================================================================================================#
# Commande pour ajouter de l'argent à un membre (administrateur uniquement)
    @commands.command(name="add_money", help="!add_money @user [montant]", description="Ajoute de l'argent au portefeuille d'un membre.")
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def add_money(self, ctx, member: discord.Member, amount: int):
        """
        Ajoute de l'argent au portefeuille d'un membre. Cette commande est réservée aux administrateurs.
        """
        if amount <= 0:
            embed = discord.Embed(
                title="Montant invalide",
                description="Le montant doit être supérieur à 0.",
                color=discord.Color.red()
            )
            embed.set_footer(text=random.choice(list_embed))
            embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url)
            embed.timestamp = datetime.datetime.now()
            await ctx.send(embed=embed)
            return

        # Connexion à la base de données
        with sqlite3.connect("eco.sqlite") as db:
            cursor = db.cursor()

            # Vérifie si l'utilisateur existe dans la base de données
            cursor.execute("SELECT wallet FROM eco WHERE user_id = ?", (member.id,))
            result = cursor.fetchone()

            if result is None:
                # Création d'un nouvel enregistrement si l'utilisateur n'existe pas
                cursor.execute(
                    "INSERT INTO eco (user_id, wallet, bank, inventory) VALUES (?, ?, ?, ?)",
                    (member.id, amount, 0, "")
                )
            else:
                # Mise à jour du portefeuille de l'utilisateur
                current_wallet = result[0]
                new_wallet_balance = current_wallet + amount
                cursor.execute("UPDATE eco SET wallet = ? WHERE user_id = ?", (new_wallet_balance, member.id))

            db.commit()

        # Création de l'embed pour la réponse
        embed = discord.Embed(
            title="Argent ajouté",
            description=f"{ctx.author.mention} a ajouté **{amount} BotCoins** à {member.mention}.",
            color=discord.Color.green()
        )
        embed.set_footer(icon_url=self.bot.user.avatar.url, text=random.choice(list_embed))
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url)
        embed.set_thumbnail(url=ctx.author.avatar.url)
        embed.timestamp = datetime.datetime.now()

        await ctx.send(embed=embed)

        # Envoi d'un message dans le canal de log, si défini
        log_channel_id = self.config.get("log_channel_id")
        if log_channel_id:
            log_channel = self.bot.get_channel(log_channel_id)
            if log_channel:
                await log_channel.send(embed=embed)

#===============================================================================================================================================#
# Commande pour retirer de l'argent à un membre (administrateur uniquement)
    @commands.command(name="remove_money", help="!remove_money @user [montant]", description="Retire de l'argent du portefeuille d'un membre.")
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def remove_money(self, ctx, member: discord.Member, amount: int = None):
        """
        Retire de l'argent du portefeuille d'un membre. Cette commande est réservée aux administrateurs.
        """
        # Connexion à la base de données
        with sqlite3.connect("eco.sqlite") as db:
            cursor = db.cursor()

            # Vérifie si l'utilisateur existe dans la base de données
            cursor.execute("SELECT wallet FROM eco WHERE user_id = ?", (member.id,))
            result = cursor.fetchone()

            if result is None:
                embed = discord.Embed(
                    title="Portefeuille vide",
                    description=f"{member.mention} n'a pas d'argent dans son portefeuille.",
                    color=discord.Color.red()
                )
                embed.set_footer(text=random.choice(list_embed))
                embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url)
                embed.timestamp = datetime.datetime.now()
                await ctx.send(embed=embed)
                return

            current_wallet = result[0]

            if amount is None:
                # Retirer tout l'argent si aucun montant n'est spécifié
                new_wallet_balance = 0
            elif amount <= 0:
                embed = discord.Embed(
                    title="Montant invalide",
                    description="Le montant doit être supérieur à 0.",
                    color=discord.Color.red()
                )
                embed.set_footer(text=random.choice(list_embed))
                embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url)
                embed.timestamp = datetime.datetime.now()
                await ctx.send(embed=embed)
                return
            else:
                # Retirer le montant spécifié
                new_wallet_balance = max(current_wallet - amount, 0)  # Empêcher un solde négatif

            cursor.execute("UPDATE eco SET wallet = ? WHERE user_id = ?", (new_wallet_balance, member.id))
            db.commit()

        # Création de l'embed pour la réponse
        embed = discord.Embed(
            title="Argent retiré",
            description=f"{ctx.author.mention} a retiré **{amount if amount else 'tout l\'argent'}** de {member.mention}.",
            color=discord.Color.red()
        )
        embed.set_footer(icon_url=self.bot.user.avatar.url, text=random.choice(list_embed))
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url)
        embed.set_thumbnail(url=ctx.author.avatar.url)
        embed.timestamp = datetime.datetime.now()

        await ctx.send(embed=embed)

        # Envoi d'un message dans le canal de log, si défini
        log_channel_id = self.config.get("log_channel_id")
        if log_channel_id:
            log_channel = self.bot.get_channel(log_channel_id)
            if log_channel:
                await log_channel.send(embed=embed)

#===============================================================================================================================================#
#setup Event
async def setup(bot):
    await bot.add_cog(Event(bot))
