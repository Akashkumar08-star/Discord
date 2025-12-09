import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import random
import asyncio
from datetime import datetime, timedelta
import aiohttp

# Bot setup with intents
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# Data files
MENTION_FILE = "mentions.json"
ECONOMY_FILE = "economy.json"
WARNINGS_FILE = "warnings.json"
LEVELS_FILE = "levels.json"

# Load/Save functions
def load_data(filename):
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            return json.load(f)
    return {}

def save_data(filename, data):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)

# Load all data
mention_data = load_data(MENTION_FILE)
economy_data = load_data(ECONOMY_FILE)
warnings_data = load_data(WARNINGS_FILE)
levels_data = load_data(LEVELS_FILE)

@bot.event
async def on_ready():
    print(f'🤖 {bot.user} is now online!')
    print(f'🔗 Connected to {len(bot.guilds)} servers')
    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"❌ Failed to sync commands: {e}")

# ==================== MENTION TRACKING ====================

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    # Mention tracking
    if message.mentions:
        guild_id = str(message.guild.id)
        if guild_id not in mention_data:
            mention_data[guild_id] = {}
        
        for mentioned_user in message.mentions:
            user_id = str(mentioned_user.id)
            if user_id not in mention_data[guild_id]:
                mention_data[guild_id][user_id] = 0
            mention_data[guild_id][user_id] += 1
        
        save_data(MENTION_FILE, mention_data)
    
    # Leveling system
    guild_id = str(message.guild.id)
    user_id = str(message.author.id)
    
    if guild_id not in levels_data:
        levels_data[guild_id] = {}
    if user_id not in levels_data[guild_id]:
        levels_data[guild_id][user_id] = {"xp": 0, "level": 1, "messages": 0}
    
    levels_data[guild_id][user_id]["messages"] += 1
    levels_data[guild_id][user_id]["xp"] += random.randint(10, 25)
    
    # Level up check
    user_data = levels_data[guild_id][user_id]
    xp_needed = user_data["level"] * 100
    
    if user_data["xp"] >= xp_needed:
        user_data["level"] += 1
        user_data["xp"] = 0
        await message.channel.send(f"🎉 {message.author.mention} leveled up to **Level {user_data['level']}**!")
    
    save_data(LEVELS_FILE, levels_data)
    
    await bot.process_commands(message)

# ==================== MENTION COMMANDS ====================

@bot.tree.command(name="mentions", description="Check how many times a user has been mentioned")
async def mentions(interaction: discord.Interaction, user: discord.Member = None):
    target_user = user if user else interaction.user
    guild_id = str(interaction.guild.id)
    user_id = str(target_user.id)
    
    count = 0
    if guild_id in mention_data and user_id in mention_data[guild_id]:
        count = mention_data[guild_id][user_id]
    
    embed = discord.Embed(title="📊 Mention Statistics", color=discord.Color.purple())
    embed.add_field(name="User", value=target_user.mention, inline=False)
    embed.add_field(name="Total Mentions", value=f"**{count}** times", inline=False)
    embed.set_thumbnail(url=target_user.display_avatar.url)
    
    await interaction.response.send_message("✅ Message sent!", ephemeral=True)

# ==================== HELP COMMAND ====================

@bot.tree.command(name="help", description="View all available commands")
async def help_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🤖 Bot Commands",
        description="Here are all available commands organized by category:",
        color=discord.Color.blue()
    )
    
    embed.add_field(
        name="📊 Mention Tracking",
        value="`/mentions` `/mentionleaderboard`",
        inline=False
    )
    
    embed.add_field(
        name="🛡️ Moderation",
        value="`/kick` `/ban` `/unban` `/timeout` `/warn` `/warnings` `/clearwarnings` `/purge`",
        inline=False
    )
    
    embed.add_field(
        name="💰 Economy",
        value="`/balance` `/daily` `/work` `/deposit` `/withdraw` `/give` `/rob` `/leaderboard`",
        inline=False
    )
    
    embed.add_field(
        name="📈 Leveling",
        value="`/rank` `/levelleaderboard`",
        inline=False
    )
    
    embed.add_field(
        name="🎮 Fun",
        value="`/8ball` `/coinflip` `/dice` `/meme` `/hug` `/slap` `/rps`",
        inline=False
    )
    
    embed.add_field(
        name="🔧 Utility",
        value="`/serverinfo` `/userinfo` `/avatar` `/poll` `/remind` `/say` `/help`",
        inline=False
    )
    
    embed.set_footer(text="Use /command_name to use any command!")
    
    await interaction.response.send_message(embed=embed)

# Run the bot
bot.run('MTQ0Nzg1NTA5MjQwODUxNjczMg.GTuRKL.Ah2ltAOuRksMwoumhwMHnr-wKEmCZnorUcPz2M')(embed=embed)

@bot.tree.command(name="mentionleaderboard", description="Show the most mentioned users")
async def mentionleaderboard(interaction: discord.Interaction):
    guild_id = str(interaction.guild.id)
    
    if guild_id not in mention_data or not mention_data[guild_id]:
        await interaction.response.send_message("No mention data available yet!", ephemeral=True)
        return
    
    sorted_mentions = sorted(mention_data[guild_id].items(), key=lambda x: x[1], reverse=True)[:10]
    
    embed = discord.Embed(title="🏆 Most Mentioned Users", color=discord.Color.gold())
    
    for idx, (user_id, count) in enumerate(sorted_mentions, 1):
        try:
            user = await bot.fetch_user(int(user_id))
            medal = "🥇" if idx == 1 else "🥈" if idx == 2 else "🥉" if idx == 3 else f"**{idx}.**"
            embed.add_field(name=f"{medal} {user.name}", value=f"{count} mentions", inline=False)
        except:
            continue
    
    await interaction.response.send_message(embed=embed)

# ==================== MODERATION COMMANDS ====================

@bot.tree.command(name="kick", description="Kick a member from the server")
@app_commands.checks.has_permissions(kick_members=True)
async def kick(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
    await member.kick(reason=reason)
    embed = discord.Embed(title="👢 Member Kicked", color=discord.Color.orange())
    embed.add_field(name="Member", value=member.mention, inline=True)
    embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
    embed.add_field(name="Reason", value=reason, inline=False)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="ban", description="Ban a member from the server")
@app_commands.checks.has_permissions(ban_members=True)
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
    await member.ban(reason=reason)
    embed = discord.Embed(title="🔨 Member Banned", color=discord.Color.red())
    embed.add_field(name="Member", value=member.mention, inline=True)
    embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
    embed.add_field(name="Reason", value=reason, inline=False)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="unban", description="Unban a user from the server")
@app_commands.checks.has_permissions(ban_members=True)
async def unban(interaction: discord.Interaction, user_id: str):
    user = await bot.fetch_user(int(user_id))
    await interaction.guild.unban(user)
    await interaction.response.send_message(f"✅ Unbanned {user.mention}")

@bot.tree.command(name="timeout", description="Timeout a member")
@app_commands.checks.has_permissions(moderate_members=True)
async def timeout(interaction: discord.Interaction, member: discord.Member, minutes: int, reason: str = "No reason provided"):
    duration = timedelta(minutes=minutes)
    await member.timeout(duration, reason=reason)
    embed = discord.Embed(title="⏰ Member Timed Out", color=discord.Color.yellow())
    embed.add_field(name="Member", value=member.mention, inline=True)
    embed.add_field(name="Duration", value=f"{minutes} minutes", inline=True)
    embed.add_field(name="Reason", value=reason, inline=False)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="warn", description="Warn a member")
@app_commands.checks.has_permissions(moderate_members=True)
async def warn(interaction: discord.Interaction, member: discord.Member, reason: str):
    guild_id = str(interaction.guild.id)
    user_id = str(member.id)
    
    if guild_id not in warnings_data:
        warnings_data[guild_id] = {}
    if user_id not in warnings_data[guild_id]:
        warnings_data[guild_id][user_id] = []
    
    warning = {
        "reason": reason,
        "moderator": str(interaction.user.id),
        "timestamp": datetime.now().isoformat()
    }
    
    warnings_data[guild_id][user_id].append(warning)
    save_data(WARNINGS_FILE, warnings_data)
    
    total_warnings = len(warnings_data[guild_id][user_id])
    
    embed = discord.Embed(title="⚠️ Member Warned", color=discord.Color.red())
    embed.add_field(name="Member", value=member.mention, inline=True)
    embed.add_field(name="Total Warnings", value=total_warnings, inline=True)
    embed.add_field(name="Reason", value=reason, inline=False)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="warnings", description="Check warnings for a member")
async def warnings(interaction: discord.Interaction, member: discord.Member = None):
    target = member if member else interaction.user
    guild_id = str(interaction.guild.id)
    user_id = str(target.id)
    
    warns = []
    if guild_id in warnings_data and user_id in warnings_data[guild_id]:
        warns = warnings_data[guild_id][user_id]
    
    embed = discord.Embed(title=f"⚠️ Warnings for {target.name}", color=discord.Color.orange())
    embed.add_field(name="Total Warnings", value=len(warns), inline=False)
    
    for idx, warn in enumerate(warns[-5:], 1):
        mod = await bot.fetch_user(int(warn["moderator"]))
        embed.add_field(
            name=f"Warning {idx}",
            value=f"**Reason:** {warn['reason']}\n**By:** {mod.mention}",
            inline=False
        )
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="clearwarnings", description="Clear all warnings for a member")
@app_commands.checks.has_permissions(administrator=True)
async def clearwarnings(interaction: discord.Interaction, member: discord.Member):
    guild_id = str(interaction.guild.id)
    user_id = str(member.id)
    
    if guild_id in warnings_data and user_id in warnings_data[guild_id]:
        del warnings_data[guild_id][user_id]
        save_data(WARNINGS_FILE, warnings_data)
        await interaction.response.send_message(f"✅ Cleared all warnings for {member.mention}")
    else:
        await interaction.response.send_message(f"❌ No warnings found for {member.mention}", ephemeral=True)

@bot.tree.command(name="purge", description="Delete multiple messages")
@app_commands.checks.has_permissions(manage_messages=True)
async def purge(interaction: discord.Interaction, amount: int):
    await interaction.response.defer(ephemeral=True)
    deleted = await interaction.channel.purge(limit=amount)
    await interaction.followup.send(f"✅ Deleted {len(deleted)} messages", ephemeral=True)

# ==================== ECONOMY COMMANDS ====================

def get_balance(guild_id, user_id):
    if guild_id not in economy_data:
        economy_data[guild_id] = {}
    if user_id not in economy_data[guild_id]:
        economy_data[guild_id][user_id] = {"balance": 1000, "bank": 0}
    return economy_data[guild_id][user_id]

@bot.tree.command(name="balance", description="Check your or another user's balance")
async def balance(interaction: discord.Interaction, member: discord.Member = None):
    target = member if member else interaction.user
    guild_id = str(interaction.guild.id)
    user_id = str(target.id)
    
    data = get_balance(guild_id, user_id)
    
    embed = discord.Embed(title=f"💰 {target.name}'s Balance", color=discord.Color.green())
    embed.add_field(name="Wallet", value=f"${data['balance']:,}", inline=True)
    embed.add_field(name="Bank", value=f"${data['bank']:,}", inline=True)
    embed.add_field(name="Total", value=f"${data['balance'] + data['bank']:,}", inline=False)
    embed.set_thumbnail(url=target.display_avatar.url)
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="daily", description="Claim your daily reward")
async def daily(interaction: discord.Interaction):
    guild_id = str(interaction.guild.id)
    user_id = str(interaction.user.id)
    
    data = get_balance(guild_id, user_id)
    reward = random.randint(500, 1000)
    data["balance"] += reward
    
    save_data(ECONOMY_FILE, economy_data)
    
    await interaction.response.send_message(f"💵 You claimed your daily reward of **${reward}**!")

@bot.tree.command(name="work", description="Work to earn money")
async def work(interaction: discord.Interaction):
    guild_id = str(interaction.guild.id)
    user_id = str(interaction.user.id)
    
    data = get_balance(guild_id, user_id)
    
    jobs = ["programmer", "teacher", "doctor", "chef", "artist", "musician"]
    job = random.choice(jobs)
    earnings = random.randint(100, 500)
    
    data["balance"] += earnings
    save_data(ECONOMY_FILE, economy_data)
    
    await interaction.response.send_message(f"💼 You worked as a **{job}** and earned **${earnings}**!")

@bot.tree.command(name="deposit", description="Deposit money to your bank")
async def deposit(interaction: discord.Interaction, amount: int):
    guild_id = str(interaction.guild.id)
    user_id = str(interaction.user.id)
    
    data = get_balance(guild_id, user_id)
    
    if amount > data["balance"]:
        await interaction.response.send_message("❌ You don't have enough money in your wallet!", ephemeral=True)
        return
    
    data["balance"] -= amount
    data["bank"] += amount
    save_data(ECONOMY_FILE, economy_data)
    
    await interaction.response.send_message(f"✅ Deposited **${amount:,}** to your bank!")

@bot.tree.command(name="withdraw", description="Withdraw money from your bank")
async def withdraw(interaction: discord.Interaction, amount: int):
    guild_id = str(interaction.guild.id)
    user_id = str(interaction.user.id)
    
    data = get_balance(guild_id, user_id)
    
    if amount > data["bank"]:
        await interaction.response.send_message("❌ You don't have enough money in your bank!", ephemeral=True)
        return
    
    data["bank"] -= amount
    data["balance"] += amount
    save_data(ECONOMY_FILE, economy_data)
    
    await interaction.response.send_message(f"✅ Withdrew **${amount:,}** from your bank!")

@bot.tree.command(name="give", description="Give money to another user")
async def give(interaction: discord.Interaction, member: discord.Member, amount: int):
    guild_id = str(interaction.guild.id)
    sender_id = str(interaction.user.id)
    receiver_id = str(member.id)
    
    sender_data = get_balance(guild_id, sender_id)
    receiver_data = get_balance(guild_id, receiver_id)
    
    if amount > sender_data["balance"]:
        await interaction.response.send_message("❌ You don't have enough money!", ephemeral=True)
        return
    
    sender_data["balance"] -= amount
    receiver_data["balance"] += amount
    save_data(ECONOMY_FILE, economy_data)
    
    await interaction.response.send_message(f"✅ You gave **${amount:,}** to {member.mention}!")

@bot.tree.command(name="rob", description="Try to rob another user")
async def rob(interaction: discord.Interaction, member: discord.Member):
    guild_id = str(interaction.guild.id)
    robber_id = str(interaction.user.id)
    victim_id = str(member.id)
    
    robber_data = get_balance(guild_id, robber_id)
    victim_data = get_balance(guild_id, victim_id)
    
    if victim_data["balance"] < 100:
        await interaction.response.send_message(f"❌ {member.mention} doesn't have enough money to rob!", ephemeral=True)
        return
    
    success = random.choice([True, False])
    
    if success:
        stolen = random.randint(50, min(500, victim_data["balance"]))
        robber_data["balance"] += stolen
        victim_data["balance"] -= stolen
        await interaction.response.send_message(f"💰 You successfully robbed **${stolen}** from {member.mention}!")
    else:
        fine = random.randint(100, 300)
        robber_data["balance"] = max(0, robber_data["balance"] - fine)
        await interaction.response.send_message(f"❌ You got caught! You paid a fine of **${fine}**!")
    
    save_data(ECONOMY_FILE, economy_data)

@bot.tree.command(name="leaderboard", description="View the richest users")
async def leaderboard(interaction: discord.Interaction):
    guild_id = str(interaction.guild.id)
    
    if guild_id not in economy_data:
        await interaction.response.send_message("No economy data available!", ephemeral=True)
        return
    
    sorted_users = sorted(
        economy_data[guild_id].items(),
        key=lambda x: x[1]["balance"] + x[1]["bank"],
        reverse=True
    )[:10]
    
    embed = discord.Embed(title="💎 Richest Users", color=discord.Color.gold())
    
    for idx, (user_id, data) in enumerate(sorted_users, 1):
        try:
            user = await bot.fetch_user(int(user_id))
            total = data["balance"] + data["bank"]
            medal = "🥇" if idx == 1 else "🥈" if idx == 2 else "🥉" if idx == 3 else f"**{idx}.**"
            embed.add_field(name=f"{medal} {user.name}", value=f"${total:,}", inline=False)
        except:
            continue
    
    await interaction.response.send_message(embed=embed)

# ==================== LEVELING COMMANDS ====================

@bot.tree.command(name="rank", description="Check your or another user's rank")
async def rank(interaction: discord.Interaction, member: discord.Member = None):
    target = member if member else interaction.user
    guild_id = str(interaction.guild.id)
    user_id = str(target.id)
    
    if guild_id not in levels_data or user_id not in levels_data[guild_id]:
        await interaction.response.send_message("No rank data available!", ephemeral=True)
        return
    
    data = levels_data[guild_id][user_id]
    xp_needed = data["level"] * 100
    
    embed = discord.Embed(title=f"📊 {target.name}'s Rank", color=discord.Color.blue())
    embed.add_field(name="Level", value=data["level"], inline=True)
    embed.add_field(name="XP", value=f"{data['xp']}/{xp_needed}", inline=True)
    embed.add_field(name="Messages", value=data["messages"], inline=True)
    embed.set_thumbnail(url=target.display_avatar.url)
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="levelleaderboard", description="View top ranked users")
async def levelleaderboard(interaction: discord.Interaction):
    guild_id = str(interaction.guild.id)
    
    if guild_id not in levels_data:
        await interaction.response.send_message("No level data available!", ephemeral=True)
        return
    
    sorted_users = sorted(
        levels_data[guild_id].items(),
        key=lambda x: (x[1]["level"], x[1]["xp"]),
        reverse=True
    )[:10]
    
    embed = discord.Embed(title="🏅 Top Ranked Users", color=discord.Color.purple())
    
    for idx, (user_id, data) in enumerate(sorted_users, 1):
        try:
            user = await bot.fetch_user(int(user_id))
            medal = "🥇" if idx == 1 else "🥈" if idx == 2 else "🥉" if idx == 3 else f"**{idx}.**"
            embed.add_field(
                name=f"{medal} {user.name}",
                value=f"Level {data['level']} | {data['messages']} messages",
                inline=False
            )
        except:
            continue
    
    await interaction.response.send_message(embed=embed)

# ==================== FUN COMMANDS ====================

@bot.tree.command(name="8ball", description="Ask the magic 8ball a question")
async def eightball(interaction: discord.Interaction, question: str):
    responses = [
        "Yes, definitely!", "It is certain.", "Without a doubt.",
        "You may rely on it.", "As I see it, yes.", "Most likely.",
        "Outlook good.", "Yes.", "Signs point to yes.",
        "Reply hazy, try again.", "Ask again later.", "Better not tell you now.",
        "Cannot predict now.", "Concentrate and ask again.",
        "Don't count on it.", "My reply is no.", "My sources say no.",
        "Outlook not so good.", "Very doubtful."
    ]
    
    embed = discord.Embed(title="🎱 Magic 8Ball", color=discord.Color.purple())
    embed.add_field(name="Question", value=question, inline=False)
    embed.add_field(name="Answer", value=random.choice(responses), inline=False)
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="coinflip", description="Flip a coin")
async def coinflip(interaction: discord.Interaction):
    result = random.choice(["Heads", "Tails"])
    await interaction.response.send_message(f"🪙 The coin landed on: **{result}**!")

@bot.tree.command(name="dice", description="Roll a dice")
async def dice(interaction: discord.Interaction, sides: int = 6):
    result = random.randint(1, sides)
    await interaction.response.send_message(f"🎲 You rolled a **{result}** (out of {sides})!")

@bot.tree.command(name="meme", description="Get a random meme")
async def meme(interaction: discord.Interaction):
    await interaction.response.defer()
    
    async with aiohttp.ClientSession() as session:
        async with session.get("https://meme-api.com/gimme") as response:
            if response.status == 200:
                data = await response.json()
                
                embed = discord.Embed(title=data["title"], color=discord.Color.random())
                embed.set_image(url=data["url"])
                embed.set_footer(text=f"👍 {data['ups']} | r/{data['subreddit']}")
                
                await interaction.followup.send(embed=embed)
            else:
                await interaction.followup.send("Failed to fetch meme!", ephemeral=True)

@bot.tree.command(name="hug", description="Hug someone")
async def hug(interaction: discord.Interaction, member: discord.Member):
    await interaction.response.send_message(f"🤗 {interaction.user.mention} hugged {member.mention}!")

@bot.tree.command(name="slap", description="Slap someone")
async def slap(interaction: discord.Interaction, member: discord.Member):
    await interaction.response.send_message(f"👋 {interaction.user.mention} slapped {member.mention}!")

@bot.tree.command(name="rps", description="Play Rock Paper Scissors")
async def rps(interaction: discord.Interaction, choice: str):
    choices = ["rock", "paper", "scissors"]
    choice = choice.lower()
    
    if choice not in choices:
        await interaction.response.send_message("❌ Invalid choice! Choose rock, paper, or scissors.", ephemeral=True)
        return
    
    bot_choice = random.choice(choices)
    
    if choice == bot_choice:
        result = "It's a tie!"
    elif (choice == "rock" and bot_choice == "scissors") or \
         (choice == "paper" and bot_choice == "rock") or \
         (choice == "scissors" and bot_choice == "paper"):
        result = "You win! 🎉"
    else:
        result = "You lose! 😢"
    
    embed = discord.Embed(title="✊✋✌️ Rock Paper Scissors", color=discord.Color.blue())
    embed.add_field(name="Your Choice", value=choice.capitalize(), inline=True)
    embed.add_field(name="Bot's Choice", value=bot_choice.capitalize(), inline=True)
    embed.add_field(name="Result", value=result, inline=False)
    
    await interaction.response.send_message(embed=embed)

# ==================== UTILITY COMMANDS ====================

@bot.tree.command(name="serverinfo", description="Get server information")
async def serverinfo(interaction: discord.Interaction):
    guild = interaction.guild
    
    embed = discord.Embed(title=f"ℹ️ {guild.name}", color=discord.Color.blue())
    embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
    embed.add_field(name="Owner", value=guild.owner.mention, inline=True)
    embed.add_field(name="Members", value=guild.member_count, inline=True)
    embed.add_field(name="Channels", value=len(guild.channels), inline=True)
    embed.add_field(name="Roles", value=len(guild.roles), inline=True)
    embed.add_field(name="Created", value=guild.created_at.strftime("%B %d, %Y"), inline=True)
    embed.add_field(name="Server ID", value=guild.id, inline=True)
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="userinfo", description="Get user information")
async def userinfo(interaction: discord.Interaction, member: discord.Member = None):
    target = member if member else interaction.user
    
    embed = discord.Embed(title=f"👤 {target.name}", color=target.color)
    embed.set_thumbnail(url=target.display_avatar.url)
    embed.add_field(name="ID", value=target.id, inline=True)
    embed.add_field(name="Nickname", value=target.nick if target.nick else "None", inline=True)
    embed.add_field(name="Status", value=str(target.status).capitalize(), inline=True)
    embed.add_field(name="Joined Server", value=target.joined_at.strftime("%B %d, %Y"), inline=True)
    embed.add_field(name="Account Created", value=target.created_at.strftime("%B %d, %Y"), inline=True)
    embed.add_field(name="Roles", value=len(target.roles) - 1, inline=True)
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="avatar", description="Get a user's avatar")
async def avatar(interaction: discord.Interaction, member: discord.Member = None):
    target = member if member else interaction.user
    
    embed = discord.Embed(title=f"🖼️ {target.name}'s Avatar", color=discord.Color.blue())
    embed.set_image(url=target.display_avatar.url)
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="poll", description="Create a poll")
async def poll(interaction: discord.Interaction, question: str, option1: str, option2: str, option3: str = None, option4: str = None):
    embed = discord.Embed(title="📊 Poll", description=question, color=discord.Color.blue())
    
    options = [option1, option2]
    if option3:
        options.append(option3)
    if option4:
        options.append(option4)
    
    reactions = ["1️⃣", "2️⃣", "3️⃣", "4️⃣"]
    
    for idx, option in enumerate(options):
        embed.add_field(name=f"{reactions[idx]} Option {idx + 1}", value=option, inline=False)
    
    await interaction.response.send_message(embed=embed)
    message = await interaction.original_response()
    
    for i in range(len(options)):
        await message.add_reaction(reactions[i])

@bot.tree.command(name="remind", description="Set a reminder")
async def remind(interaction: discord.Interaction, time_minutes: int, message: str):
    await interaction.response.send_message(f"⏰ I'll remind you in {time_minutes} minute(s)!")
    
    await asyncio.sleep(time_minutes * 60)
    
    await interaction.user.send(f"⏰ **Reminder:** {message}")

@bot.tree.command(name="say", description="Make the bot say something")
@app_commands.checks.has_permissions(manage_messages=True)
async def say(interaction: discord.Interaction, message: str, channel: discord.TextChannel = None):
    target_channel = channel if channel else interaction.channel
    await target_channel.send(message)
    await interaction.response.send_message
