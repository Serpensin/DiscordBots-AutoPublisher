#Import
import asyncio
import discord
import logging
import logging.handlers
import os
import platform
import sentry_sdk
import sys
from datetime import timedelta
from dotenv import load_dotenv
from zipfile import ZIP_DEFLATED, ZipFile



#Init
load_dotenv()
sentry_sdk.init(
    dsn=os.getenv('SENTRY_DSN'),
    traces_sample_rate=1.0,
    profiles_sample_rate=1.0,
    environment='Production'
)
app_folder_name = 'AutoPublisher'
if not os.path.exists(f'{app_folder_name}//Logs'):
    os.makedirs(f'{app_folder_name}//Logs')
if not os.path.exists(f'{app_folder_name}//Buffer'):
    os.makedirs(f'{app_folder_name}//Buffer')
log_folder = f'{app_folder_name}//Logs//'
buffer_folder = f'{app_folder_name}//Buffer//'
logger = logging.getLogger('discord')
manlogger = logging.getLogger('Program')
logger.setLevel(logging.INFO)
manlogger.setLevel(logging.INFO)
logging.getLogger('discord.http').setLevel(logging.INFO)
handler = logging.handlers.RotatingFileHandler(
    filename = f'{log_folder}BotLog.log',
    encoding = 'utf-8',
    maxBytes = 8 * 1024 * 1024, 
    backupCount = 5,            
    mode='w')
dt_fmt = '%Y-%m-%d %H:%M:%S'
formatter = logging.Formatter('[{asctime}] [{levelname:<8}] {name}: {message}', dt_fmt, style='{')
handler.setFormatter(formatter)
logger.addHandler(handler)
manlogger.addHandler(handler)
manlogger.info('Engine powering up...')

#Load env
TOKEN = os.getenv('TOKEN')
ownerID = os.environ.get('OWNER_ID')


class aclient(discord.AutoShardedClient):
    def __init__(self):

        intents = discord.Intents.default()
        intents.guild_messages = True

        super().__init__(owner_id = ownerID,
                              intents = intents,
                              status = discord.Status.invisible
                        )
        self.synced = False


    async def on_ready(self):
        global owner
        try:
            owner = await self.fetch_user(ownerID)
            if owner is None:
                manlogger.critical(f"Invalid ownerID: {ownerID}")
                sys.exit(f"Invalid ownerID: {ownerID}")
        except discord.HTTPException as e:
            manlogger.critical(f"Error fetching owner user: {e}")
            sys.exit(f"Error fetching owner user: {e}")
        logger.info(f'Logged in as {bot.user} (ID: {bot.user.id})')
        if not self.synced:
            manlogger.info('Syncing...')
            await tree.sync()
            manlogger.info('Synced.')
            self.synced = True
            await bot.change_presence(activity = discord.Activity(type=discord.ActivityType.watching, name='over News'), status = discord.Status.online)
        manlogger.info('All systems online...')
        print('READY')
bot = aclient()
tree = discord.app_commands.CommandTree(bot)


# Check if all required variables are set
owner_available = bool(ownerID)

#Fix error on windows on shutdown
if platform.system() == 'Windows':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
def clear():
    if platform.system() == 'Windows':
        os.system('cls')
    else:
        os.system('clear')

##Events
#Guild Remove
@bot.event
async def on_guild_remove(guild):
    manlogger.info(f'I got kicked from {guild}. (ID: {guild.id})')
#Guild Join
@bot.event
async def on_guild_join(guild):
    manlogger.info(f'I joined {guild}. (ID: {guild.id})')   
#Error
@tree.error
async def on_app_command_error(interaction: discord.Interaction, error: discord.app_commands.AppCommandError) -> None:
    if isinstance(error, discord.app_commands.CommandOnCooldown):
        await interaction.response.send_message(f'This comand is on cooldown.\nTime left: `{seconds_to_minutes(error.retry_after)}`.', ephemeral = True)
        manlogger.warning(f'{error} {interaction.user.name} | {interaction.user.id}')
    else:
        await interaction.response.send_message(error, ephemeral = True)
        manlogger.warning(f'{error} {interaction.user.name} | {interaction.user.id}')
#Message
@bot.event
async def on_message(message: discord.Message):
    if message.author == bot.user:
        return
    if message.channel.is_news():
        await auto_publish(message)


#Functions
def seconds_to_minutes(input_int):
    return(str(timedelta(seconds=input_int)))

async def auto_publish(message: discord.Message):
    channel = message.channel
    try:
        await message.add_reaction("\U0001F4E2")
        await message.publish()
        await message.remove_reaction("\U0001F4E2", bot.user)
    except discord.errors.Forbidden:
        print(f"No permission to publish in {channel}.")
        await message.add_reaction("\u26D4")
    except Exception as e:
        print(f"Error publishing message in {channel}: {e}")
        await message.add_reaction("\u26A0")

 
##Owner Commands
#Shutdown
@tree.command(name = 'shutdown', description = 'Savely shut down the bot.')
async def self(interaction: discord.Interaction):
    if interaction.user.id == int(ownerID):
        manlogger.info('Engine powering down...')
        await interaction.response.send_message('Engine powering down...', ephemeral = True)
        await bot.close()
    else:
        await interaction.response.send_message('Only the BotOwner can use this command!', ephemeral = True)


#Get Logs
if owner_available:
    @tree.command(name = 'get_logs', description = 'Get the current, or all logfiles.')
    @discord.app_commands.describe(choice = 'Choose which log files you want to receive.')
    @discord.app_commands.choices(choice = [
        discord.app_commands.Choice(name="Last X lines", value="xlines"),
        discord.app_commands.Choice(name="Current Log", value="current"),
        discord.app_commands.Choice(name="Whole Folder", value="whole")
    ])
    async def self(interaction: discord.Interaction, choice: str):
        if interaction.user.id != int(ownerID):
            await interaction.response.send_message('Only the BotOwner can use this command!', ephemeral = True)
            return
        else:
            if choice == 'xlines':
                class LastXLines(discord.ui.Modal, title = 'Line Input'):
                    def __init__(self, interaction):
                        super().__init__()
                        self.timeout = 15
                        self.answer = discord.ui.TextInput(label = 'How many lines?', style = discord.TextStyle.short, required = True, min_length = 1, max_length = 4)
                        self.add_item(self.answer)

                    async def on_submit(self, interaction: discord.Interaction):
                        try:
                            int(self.answer.value)
                        except:
                            await interaction.response.send_message(content = 'You can only use numbers!', ephemeral = True)
                            return
                        if int(self.answer.value) == 0:
                            await interaction.response.send_message(content = 'You can not use 0 as a number!', ephemeral = True)
                            return
                        with open(log_folder+'BotLog.log', 'r', encoding='utf8') as f:
                            with open(buffer_folder+'log-lines.txt', 'w', encoding='utf8') as f2:
                                count = 0
                                for line in (f.readlines()[-int(self.answer.value):]):
                                    f2.write(line)
                                    count += 1
                        await interaction.response.send_message(content = f'Here are the last {count} lines of the current logfile:', file = discord.File(r''+buffer_folder+'log-lines.txt') , ephemeral = True)
                        if os.path.exists(buffer_folder+'log-lines.txt'):
                            os.remove(buffer_folder+'log-lines.txt')
                await interaction.response.send_modal(LastXLines(interaction))
            elif choice == 'current':
                await interaction.response.defer(ephemeral = True)
                try:
                    await interaction.followup.send(file=discord.File(r''+log_folder+'BotLog.log'), ephemeral=True)
                except discord.HTTPException as err:
                    if err.status == 413:
                        with ZipFile(buffer_folder+'Logs.zip', mode='w', compression=ZIP_DEFLATED, compresslevel=9, allowZip64=True) as f:
                            f.write(log_folder+'BotLog.log')
                        try:
                            await interaction.response.send_message(file=discord.File(r''+buffer_folder+'Logs.zip'))
                        except discord.HTTPException as err:
                            if err.status == 413:
                                await interaction.followup.send("The log is too big to be send directly.\nYou have to look at the log in your server(VPS).")
                        os.remove(buffer_folder+'Logs.zip')
            elif choice == 'whole':
                if os.path.exists(buffer_folder+'Logs.zip'):
                    os.remove(buffer_folder+'Logs.zip')
                with ZipFile(buffer_folder+'Logs.zip', mode='w', compression=ZIP_DEFLATED, compresslevel=9, allowZip64=True) as f:
                    for file in os.listdir(log_folder):
                        if file.endswith(".zip"):
                            continue
                        f.write(log_folder+file)
                try:
                    await interaction.response.send_message(file=discord.File(r''+buffer_folder+'Logs.zip'), ephemeral=True)
                except discord.HTTPException as err:
                    if err.status == 413:
                        await interaction.followup.send("The folder is too big to be send directly.\nPlease get the current file, or the last X lines.")
                os.remove(buffer_folder+'Logs.zip')


#tell user what permissions are required
@tree.command(
    name='permissions',
    description='Tell what permissions are required or check if the bot has necessary permissions in a channel.'
)
@discord.app_commands.describe(choice='Choose an option.')
@discord.app_commands.choices(choice=[
    discord.app_commands.Choice(name="Explain permissions", value="explain"),
    discord.app_commands.Choice(name="Check bot permissions", value="check")
])
async def permissions(interaction: discord.Interaction, choice: str, channel: discord.abc.GuildChannel = None):
    if interaction.user.guild_permissions.manage_roles or interaction.user.guild_permissions.manage_channels:
        if choice == 'explain':
            await interaction.response.send_message('In order for this bot to be able to publish messages, he needs the following permissions for each channel he publishes messages for:\n`View Channel`, `Send Messages`, `Manage Messages` and `Read Message History`.', ephemeral=True)
        elif choice == 'check':
            if channel is None:
                await interaction.response.send_message('Please specify a channel.', ephemeral=True)
                return

            if isinstance(channel, discord.TextChannel):
                if not channel.is_news():
                    await interaction.response.send_message('The specified channel is not an announcement channel.', ephemeral=True)
                    return

                perms = channel.permissions_for(interaction.guild.me)
                needed_permissions = ['view_channel', 'send_messages', 'manage_messages', 'read_message_history', 'add_reactions']
                missing_permissions = [perm for perm in needed_permissions if not getattr(perms, perm)]
                
                if not missing_permissions:
                    await interaction.response.send_message('The bot has all the necessary permissions in this channel.', ephemeral=True)
                else:
                    await interaction.response.send_message(f'The bot is missing the following permissions in this channel: {", ".join(missing_permissions)}.', ephemeral=True)
            else:
                await interaction.response.send_message('Please specify a text channel.', ephemeral=True)
    else:
        await interaction.response.send_message('You need the `manage_roles` or `manage_channels` permission to use this command.', ephemeral=True)










bot.run(TOKEN, log_handler=None)

