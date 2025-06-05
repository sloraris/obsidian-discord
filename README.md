# Obsidian Discord Bot

A Discord bot that saves messages to your Obsidian vault with intelligent file naming and formatting options based on the message content and the user's reactions.

## Features
- Auto-reacts to messages in the designated channel
- Intelligent file naming based on content
- Creates formatted daily notes with timestamps
- Preserves attachments as markdown links
- Confirms successful saves with reactions
- Docker support for easy deployment

## Setup

1. Create a `.env` file with the following variables:
   ```env-example
    # Discord Bot Token (from Discord Developer Portal)
    DISCORD_TOKEN=your_discord_bot_token

    # Discord Server ID (from Discord server settings)
    # This is the ID of the server where the bot will operate
    # This is a security measure to prevent the bot from operating in other servers
    ALLOWED_GUILD_IDS=your_discord_server_id

    # Path to your Obsidian vault
    # For local Python deployment: Use absolute path to your vault
    # Example: /Users/username/Documents/ObsidianVault
    # For Docker deployment: leave this as /vault and map your local vault path to /vault in the container
    # Example: /Users/username/Documents/ObsidianVault:/vault
    OBSIDIAN_VAULT_PATH=path_to_your_obsidian_vault

    # Name of the Discord channel where the bot will operate
    # This should match exactly (case-sensitive)
    BOT_CHANNEL_NAME=your_channel_name

    # Name of your custom save emoji (without the : characters)
    # Example: If your emoji is :obsidian:, just put obsidian
    SAVE_EMOJI_NAME=obsidian

    # Optional: Section in daily notes where content should be appended
    # If specified, new content will be added under this section header
    # Example: "Daily Log" will append content under "# Daily Log" or "## Daily Log"
    DAILY_NOTE_SECTION=Daily Log
   ```

2. Add a custom emoji named `:obsidian:` to your Discord server (you can change this to whatever you want in the `.env`)

3. Create a channel with the name you specified in `BOT_CHANNEL_NAME`

## Deployment

### Python
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the bot:
   ```bash
   python bot.py
   ```

### Docker

#### Using Pre-built Image
1. Pull the image:
   ```bash
   docker pull ghcr.io/sloraris/obsidian-discord:latest
   ```

2. Create a `.env` file with your configuration

3. Run the container:
   ```bash
   docker run -d \
     --name obsidian-discord \
     -v /path/to/your/vault:/vault \
     --env-file .env \
     ghcr.io/yourusername/obsidian-discord:latest
   ```

#### Building Locally
1. Build the container:
   ```bash
   docker build -t obsidian-discord-bot .
   ```

2. Run the container:
   ```bash
   docker run -d \
     --name obsidian-discord \
     -v /path/to/your/vault:/vault \
     --env-file .env \
     obsidian-discord-bot
   ```

#### Using Docker Compose
1. Download the `docker-compose.yml` file:
   ```bash
   curl -O https://raw.githubusercontent.com/sloraris/obsidian-discord/main/example.compose.yml docker-compose.yml
   ```

2. Edit the `OBSIDIAN_VAULT_PATH` in `.env` to match your local vault path

3. Run the bot:
   ```bash
   docker-compose up -d
   ```

## Usage

1. Send a message in your bot's channel
2. The bot will automatically react with available options:
   - 📝 Create a new note
   - 📅 Add to daily note (default)
   - More options coming soon...

3. Select the option you want to use by reacting with the corresponding emoji
4. When you're ready, react to the message with the `:obsidian:` emoji to save the message to Obsidian
5. The bot will process the message based on your other reactions:
   - If you selected 📝, it creates a new note
   - Otherwise, it adds to today's daily note (it will create a new daily note if one does not already exist)
6. The bot confirms success with ✅ or failure with ❌

## Note Formats

### Daily Note (`YYYY-MM-DD.md`)
The bot now respects your Obsidian Daily Notes plugin settings for:
- Note location (folder)
- Filename format
- Template file

If `DAILY_NOTE_SECTION` is set, content will be appended under that section:
```markdown
# Thursday, March 14, 2024

## Daily Log

---
## 14:30

Your message content here...

---
## 15:45

Another message content...

## Other Section
Other content...
```

If `DAILY_NOTE_SECTION` is not set, content will be appended to the end of the file:
```markdown
# Thursday, March 14, 2024

---
## 14:30

Your message content here...

---
## 15:45

Another message content...
```

### New Note
The filename is automatically generated from the message's H1 heading:

If your message starts with:
```markdown
# My Project Ideas
Some great ideas here...
```

It will be saved as `my-project-ideas.md`. If no H1 is found, it falls back to `discord_YYYYMMDDHHMMSS.md`.

If a file with the same name exists, a number is appended (e.g., `my-project-ideas-1.md`).

## Coming Soon
- Support for saving notes to different folders
- Custom templates
- More default note actions
