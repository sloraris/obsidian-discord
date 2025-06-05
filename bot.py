import os
import discord
from discord.ext import commands
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure bot
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.guilds = True
intents.members = False
intents.presences = False

bot = commands.Bot(command_prefix='!', intents=intents)

# Constants
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
ALLOWED_GUILD_IDS = os.getenv('ALLOWED_GUILD_IDS')
OBSIDIAN_VAULT_PATH = os.getenv('OBSIDIAN_VAULT_PATH')
BOT_CHANNEL_NAME = os.getenv('BOT_CHANNEL_NAME')
SAVE_EMOJI_NAME = os.getenv('SAVE_EMOJI_NAME')

# Action emojis and their meanings
ACTION_EMOJIS = {
    '📅': 'daily',     # Add to daily note
    '📝': 'note',      # Create a new note
    # '': 'wip-note',
    # '': 'projects-note',
    # '': 'personal-note',
}

def get_formatted_date():
    """Get today's date in a readable format for H1."""
    return datetime.now().strftime('%A, %B %d, %Y')

def get_daily_note_path():
    """Get the path to today's daily note."""
    today = datetime.now().strftime('%Y-%m-%d')
    return Path(OBSIDIAN_VAULT_PATH) / f'{today}.md'

def ensure_daily_note_exists(file_path):
    """Create the daily note if it doesn't exist."""
    if not file_path.exists():
        template = f"""# {get_formatted_date()}"""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(template)

def append_to_daily_note(file_path, content):
    """Append content to the daily note with timestamp."""
    current_time = datetime.now().strftime('%H:%M')

    with open(file_path, 'a', encoding='utf-8') as f:
        f.write(f"\n---\n## {current_time}\n\n{content}\n")

def slugify(text):
    """Convert text to a URL and filename friendly format."""
    # Remove special characters and convert spaces to hyphens
    import re
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text).strip('-')
    return text

def extract_title(content):
    """Extract the H1 title from markdown content."""
    import re
    # Look for # Title at the start of the content
    match = re.match(r'^#\s+(.+)$', content.split('\n')[0].strip())
    if match:
        return match.group(1)
    return None

def create_note(message):
    """Create a new note, using H1 as filename if present."""
    title = extract_title(message.content)

    if title:
        # Use the H1 title as filename
        filename = f"{slugify(title)}.md"
    else:
        # Fallback to timestamp if no H1 found
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        filename = f"discord_{timestamp}.md"

    file_path = Path(OBSIDIAN_VAULT_PATH) / filename

    # If file exists, append a number
    base_path = file_path.parent
    base_name = file_path.stem
    extension = file_path.suffix
    counter = 1

    while file_path.exists():
        file_path = base_path / f"{base_name}-{counter}{extension}"
        counter += 1

    content = f"""{message.content}"""

    if message.attachments:
        content += "\n\n## Attachments\n"
        for attachment in message.attachments:
            content += f"- [{attachment.filename}]({attachment.url})\n"

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

@bot.event
async def on_guild_join(guild):
    if guild.id not in ALLOWED_GUILD_IDS:
        await guild.leave()
        print(f"Left unauthorized guild: {guild.name} ({guild.id})")

@bot.event
async def on_ready():
    for guild in bot.guilds:
        print(f'{bot.user} has connected to {guild.name}')
    print(f'{bot.user} is connected to {len(bot.guilds)} guild(s)')

@bot.event
async def on_message(message):
    # Only process messages in the bot's assigned channel
    if message.channel.name == BOT_CHANNEL_NAME and not message.author.bot:
        # Add all action emojis as reactions
        for emoji in ACTION_EMOJIS.keys():
            await message.add_reaction(emoji)

        # Find the obsidian emoji in the server and wait for it to be reacted on the message
        obsidian_emoji = discord.utils.get(message.guild.emojis, name=SAVE_EMOJI_NAME)
        if obsidian_emoji:
            print(f"{obsidian_emoji} found, waiting for message reaction...")
            await message.add_reaction(obsidian_emoji)
        else:
            print(f"{SAVE_EMOJI_NAME} not found.")

@bot.event
async def on_raw_reaction_add(payload):
    # Ignore bot's own reactions
    if payload.user_id == bot.user.id:
        return

    # Get the channel and message
    channel = await bot.fetch_channel(payload.channel_id)
    if channel.name != BOT_CHANNEL_NAME:
        return

    message = await channel.fetch_message(payload.message_id)

    # Only process if the obsidian emoji was added
    if not payload.emoji.is_custom_emoji() or payload.emoji.name != SAVE_EMOJI_NAME:
        return

    try:
        # Get all the user's reactions to this message
        user_reactions = []
        for reaction in message.reactions:
            if str(reaction.emoji) in ACTION_EMOJIS:
                async for user in reaction.users():
                    if user.id == payload.user_id:
                        user_reactions.append(str(reaction.emoji))
                        break

        # Format the base content
        base_content = message.content
        if message.attachments:
            attachment_links = [f"[{a.filename}]({a.url})" for a in message.attachments]
            base_content += f"\n\nAttachments:\n" + "\n".join(f"- {link}" for link in attachment_links)

        # Process based on reactions
        if '📝' in user_reactions:
            # Create a new note
            create_note(message)
        else:
            # Default to daily note
            daily_note_path = get_daily_note_path()
            ensure_daily_note_exists(daily_note_path)
            append_to_daily_note(daily_note_path, base_content)

        # Add complete emoji reaction
        await message.add_reaction('✅')

    except Exception as e:
        print(f"Error processing message: {e}")
        await message.add_reaction('❌')

# Run the bot
if __name__ == "__main__":
    if not DISCORD_TOKEN:
        raise ValueError("Discord token not found in .env file")
    if not OBSIDIAN_VAULT_PATH:
        raise ValueError("Obsidian vault path not found in .env file")

    print("Bot is starting...")
    print(f"{SAVE_EMOJI_NAME}")
    bot.run(DISCORD_TOKEN)
