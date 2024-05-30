# Discord Auto Publisher [![Discord Bot Invite](https://img.shields.io/badge/Invite-blue)](https://discord.com/oauth2/authorize?client_id=1105085860615045221&permissions=0&scope=bot%20applications.commands)[![Discord Bots](https://top.gg/api/widget/servers/1105085860615045221.svg)](https://top.gg/bot/1105085860615045221)

**Automatically publish messages or news in your announcement channels!**

A bot that will automatically publish every new message in your [announcement/news channels](https://support.discord.com/hc/en-us/articles/360032008192-Announcement-Channels-) to other servers who follow it. An excellent solution for servers who rely on bots (such as RSS feeds) or webhooks to publish their news, allowing your moderators to get some rest from manual publishing.

![](https://media.giphy.com/media/KxgsmVFc4nMF7U50UF/giphy.gif)

**The bot features no commands because the setup is really easy!**

## Setup

### Classic Method

1. Ensure Python 3.9 is installed. This bot was developed using Python 3.9.7. Download it [here](https://www.python.org/downloads/).
2. Clone this repository or download the zip file.
3. Open a terminal in the "DBDStats" folder where you cloned the repository or extracted the zip file.
4. Run `pip install -r requirements.txt` to install the dependencies.
5. Open the file ".env.template" and complete all variables:
   - `TOKEN`: The token of your bot. Obtain it from the [Discord Developer Portal](https://discord.com/developers/applications).
   - `OWNER_ID`: Your Discord ID.
6. Rename the file ".env.template" to ".env".
7. Run `python main.py` or `python3 main.py` to start the bot.

### Docker Method

#### Docker Compose Method

If you have cloned the repository, you will find a docker-compose.yml file in the folder.

1. Make sure Docker and Docker Compose are installed. Download Docker [here](https://docs.docker.com/get-docker/) and Docker Compose [here](https://docs.docker.com/compose/install/).

2. Navigate to the folder where you cloned the repository or extracted the zip file.

3. Open the `docker-compose.yml` file and update the environment variables as needed (such as `TOKEN` and `OWNER_ID`).

4. In the terminal, run the following command from the folder to start the bot:
`docker-compose up -d`

#### Docker Run

1. Ensure Docker is installed. Download it from the [Docker website](https://docs.docker.com/get-docker/).
2. Open a terminal.
3. Run the bot with the command below:
   - Modify the variables according to your requirements.
   - Set the `TOKEN`, and `OWNER_ID`.

#### Run the bot
```bash
docker run -d \
-e TOKEN=BOT_TOKEN \
-e OWNER_ID=DISCORD_ID_OF_OWNER \
--name AutoPublisher \
--restart any \
-v autopublisher_log:/app/AutoPublisher/Logs \
serpensin/autopublisher
```

### Keep in mind...

- The bot can only publish 10 messages per hour per channel (just as users), this is rate limited by Discord!
- If you want to temporarily stop the bot from publishing messages in any of your announcement channels, just disable its' `View Channel` permission in a desired channel and enable it back when you're ready.
- You should run the /permissions command to see the permissions the bot needs to work properly. (`View Channel`, `Send Messages`, `Manage Messages` and `Read Message History`)