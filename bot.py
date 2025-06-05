import os
import json
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
DAILY_NOTE_SECTION = os.getenv('DAILY_NOTE_SECTION')

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

def get_daily_notes_settings():
    """Read Obsidian Daily Notes plugin settings."""
    vault_path = Path(OBSIDIAN_VAULT_PATH)
    settings_path = vault_path / '.obsidian' / 'daily-notes.json'

    # Default settings if plugin not installed or configured
    default_settings = {
        'folder': '',  # Root of vault
        'format': 'YYYY-MM-DD',
        'template': ''
    }

    try:
        if settings_path.exists():
            print("Found daily notes settings file")
            with open(settings_path, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                return {
                    'folder': settings.get('folder', default_settings['folder']),
                    'format': settings.get('format', default_settings['format']),
                    'template': settings.get('template', default_settings['template'])
                }
    except Exception as e:
        print(f"Error reading Daily Notes settings: {e}")

    return default_settings

def format_date_for_filename(date_format):
    """Convert Obsidian's moment.js date format to Python's strftime format."""
    # Basic conversion of common formats
    format_map = {
        'YYYY': '%Y',
        'YY': '%y',
        'MM': '%m',
        'DD': '%d',
        'HH': '%H',
        'mm': '%M',
        'ss': '%S'
    }

    # Replace each format token with its Python equivalent
    python_format = date_format
    for moment_fmt, py_fmt in format_map.items():
        python_format = python_format.replace(moment_fmt, py_fmt)

    return python_format

def get_daily_note_path():
    """Get the path to today's daily note using Obsidian's settings."""
    settings = get_daily_notes_settings()

    # Convert moment.js format to Python's strftime format
    python_date_format = format_date_for_filename(settings['format'])
    filename = f"{datetime.now().strftime(python_date_format)}.md"

    # Construct the full path
    vault_path = Path(OBSIDIAN_VAULT_PATH)
    if settings['folder']:
        # Create the folder if it doesn't exist
        print(f"Daily note location specified, ensuring {vault_path}/{settings['folder']}/{filename} exists...")
        folder_path = vault_path / settings['folder']
        folder_path.mkdir(parents=True, exist_ok=True)
        return folder_path / filename
    else:
        print(f"No daily note directory specified. Defaulting to {vault_path}/{filename}...")
        return vault_path / filename

def ensure_daily_note_exists(file_path):
    """Create the daily note if it doesn't exist, using template if available and enabled."""
    if not file_path.exists():
        settings = get_daily_notes_settings()
        template_content = ""

        # Try to load template if specified
        if settings['template']:
            template_path = Path(OBSIDIAN_VAULT_PATH) / settings['template']
            try:
                if template_path.exists():
                    with open(template_path, 'r', encoding='utf-8') as f:
                        template_content = f.read()
            except Exception as e:
                print(f"Error reading template: {e}")

        # If no template or template not found, use default
        if not template_content:
            template_content = f"# {get_formatted_date()}"

        # Create the note
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(template_content)

def append_to_daily_note(file_path, content):
    """Append content to the daily note with timestamp, optionally under a specific section."""
    current_time = datetime.now().strftime('%H:%M')
    formatted_content = f"\n---\n## {current_time}\n\n{content}\n"

    if not DAILY_NOTE_SECTION:
        # If no section specified, append to end of file
        with open(file_path, 'a', encoding='utf-8') as f:
            f.write(formatted_content)
        return

    # Read the entire file
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Find the specified section
        section_found = False
        insert_index = len(lines)  # Default to end of file
        next_section_level = None

        for i, line in enumerate(lines):
            # Check for the target section header
            if line.strip().startswith('#'):
                current_header = line.strip()
                current_level = len(current_header.split()[0])  # Count the #'s

                if current_header.lstrip('#').strip() == DAILY_NOTE_SECTION.strip():
                    section_found = True
                    next_section_level = current_level
                    continue

                if section_found and current_level <= next_section_level:
                    insert_index = i
                    break

        # If section wasn't found, create it
        if not section_found:
            # Determine the appropriate header level (default to h2)
            header_level = '##'
            formatted_content = f"\n{header_level} {DAILY_NOTE_SECTION}\n{formatted_content}"

        # Insert the content at the appropriate location
        lines.insert(insert_index, formatted_content)

        # Write the modified content back to the file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)

    except Exception as e:
        print(f"Error modifying daily note: {e}")
        # Fallback to simple append if anything goes wrong
        with open(file_path, 'a', encoding='utf-8') as f:
            f.write(formatted_content)

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

async def update_bot_status(status_type="default"):
    """Update bot status based on current action."""
    if status_type == "saving":
        await bot.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.playing,
                name="with today's notes 💾"
            ),
            status=discord.Status.online
        )
    elif status_type == "creating":
        await bot.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.playing,
                name="with new files ✨"
            ),
            status=discord.Status.online
        )
    else:
        # Default status
        await bot.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="files grow 🌱"
            ),
            status=discord.Status.online
        )

@bot.event
async def on_ready():
    # Set the default bot status
    await update_bot_status()

    # Find and add the custom Obsidian emoji to bot's emoji array
    for guild in bot.guilds:
        obsidian_emoji = discord.utils.get(guild.emojis, name=SAVE_EMOJI_NAME)
        if obsidian_emoji:
            ACTION_EMOJIS[str(obsidian_emoji)] = 'save'
            print(f'Found and added {SAVE_EMOJI_NAME} emoji to actions')
            break

    # List all guilds bot has successfully joined
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
            await update_bot_status("creating")
            print(f"Creating new note with {message.id} content from ID")
            create_note(message)
        else:
            # Default to daily note
            await update_bot_status("saving")
            print(f"Adding message {message.id} content to daily note")
            daily_note_path = get_daily_note_path()
            ensure_daily_note_exists(daily_note_path)
            append_to_daily_note(daily_note_path, base_content)

        # Add complete emoji reaction and reset status
        await message.add_reaction('✅')
        await update_bot_status()

        # Remove reactions added by bot
        for emoji in ACTION_EMOJIS.keys():
            await message.remove_reaction(emoji, bot.user)

    except Exception as e:
        print(f"Error processing message: {e}")
        await message.add_reaction('❌')
        await update_bot_status()  # Reset status in case of error

        # Remove reactions added by bot
        for emoji in ACTION_EMOJIS.keys():
            await message.remove_reaction(emoji, bot.user)

# Run the bot
if __name__ == "__main__":
    if not DISCORD_TOKEN:
        raise ValueError("Discord token not found in .env file")
    if not OBSIDIAN_VAULT_PATH:
        raise ValueError("Obsidian vault path not found in .env file")

    print("Bot is starting...")
    bot.run(DISCORD_TOKEN)
