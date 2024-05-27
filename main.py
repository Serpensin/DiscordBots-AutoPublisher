﻿#Import
import time
startupTime_start = time.time()
import asyncio
import datetime
import discord
import json
import jsonschema
import os
import platform
import psutil
import sentry_sdk
import signal
import sys
from aiohttp import web
from CustomModules import bot_directory
from CustomModules import log_handler
from dotenv import load_dotenv
from urllib.parse import urlparse
from zipfile import ZIP_DEFLATED, ZipFile



#Init
discord.VoiceClient.warn_nacl = False
load_dotenv()
sentry_sdk.init(
    dsn=os.getenv('SENTRY_DSN'),
    traces_sample_rate=1.0,
    profiles_sample_rate=1.0,
    environment='Production'
)
bot_version = '1.6.3'
app_folder_name = 'AutoPublisher'
bot_name = 'AutoPublisher'
if not os.path.exists(f'{app_folder_name}//Logs'):
    os.makedirs(f'{app_folder_name}//Logs')
if not os.path.exists(f'{app_folder_name}//Buffer'):
    os.makedirs(f'{app_folder_name}//Buffer')
activity_file = os.path.join(app_folder_name, 'activity.json')
    
#Load env
TOKEN = os.getenv('TOKEN')
OWNERID = os.environ.get('OWNER_ID')
support_id = os.getenv('SUPPORT_SERVER')
topgg_token = os.getenv('TOPGG_TOKEN')
LOG_LEVEL = os.getenv('LOG_LEVEL')

# Set-up Logging
log_folder = f'{app_folder_name}//Logs//'
buffer_folder = f'{app_folder_name}//Buffer//'
log_manager = log_handler.LogManager(log_folder, bot_name, LOG_LEVEL)
discord_logger = log_manager.get_logger('discord')
program_logger = log_manager.get_logger('Program')
program_logger.info('Engine powering up...')


#Create activity.json if not exists
class JSONValidator:
    schema = {
        "type" : "object",
        "properties" : {
            "activity_type" : {
                "type" : "string",
                "enum" : ["Playing", "Streaming", "Listening", "Watching", "Competing"]
            },
            "activity_title" : {"type" : "string"},
            "activity_url" : {"type" : "string"},
            "status" : {
                "type" : "string",
                "enum" : ["online", "idle", "dnd", "invisible"]
            },
        },
    }

    default_content = {
        "activity_type": "Playing",
        "activity_title": "Made by Serpensin: https://gitlab.bloodygang.com/Serpensin",
        "activity_url": "",
        "status": "online"
    }

    def __init__(self, file_path):
        self.file_path = file_path

    def validate_and_fix_json(self):
        if os.path.exists(self.file_path):
            with open(self.file_path, 'r') as file:
                try:
                    data = json.load(file)
                    jsonschema.validate(instance=data, schema=self.schema)  # validate the data
                except jsonschema.exceptions.ValidationError as ve:
                    program_logger.debug(f'ValidationError: {ve}')
                    self.write_default_content()
                except json.decoder.JSONDecodeError as jde:
                    program_logger.debug(f'JSONDecodeError: {jde}')
                    self.write_default_content()
        else:
            self.write_default_content()

    def write_default_content(self):
        with open(self.file_path, 'w') as file:
            json.dump(self.default_content, file, indent=4)
validator = JSONValidator(activity_file)
validator.validate_and_fix_json()


class aclient(discord.AutoShardedClient):
    def __init__(self):

        intents = discord.Intents.default()

        super().__init__(owner_id = OWNERID,
                              intents = intents,
                              status = discord.Status.invisible,
                              auto_reconnect = True
                        )
        self.synced = False
        self.initialized = False


    class Presence():
        @staticmethod
        def get_activity() -> discord.Activity:
            with open(activity_file) as f:
                data = json.load(f)
                activity_type = data['activity_type']
                activity_title = data['activity_title']
                activity_url = data['activity_url']
            if activity_type == 'Playing':
                return discord.Game(name=activity_title)
            elif activity_type == 'Streaming':
                return discord.Streaming(name=activity_title, url=activity_url)
            elif activity_type == 'Listening':
                return discord.Activity(type=discord.ActivityType.listening, name=activity_title)
            elif activity_type == 'Watching':
                return discord.Activity(type=discord.ActivityType.watching, name=activity_title)
            elif activity_type == 'Competing':
                return discord.Activity(type=discord.ActivityType.competing, name=activity_title)

        @staticmethod
        def get_status() -> discord.Status:
            with open(activity_file) as f:
                data = json.load(f)
                status = data['status']
            if status == 'online':
                return discord.Status.online
            elif status == 'idle':
                return discord.Status.idle
            elif status == 'dnd':
                return discord.Status.dnd
            elif status == 'invisible':
                return discord.Status.invisible


    async def on_guild_remove(self, guild):
        program_logger.info(f'I got kicked from {guild}. (ID: {guild.id})')


    async def on_guild_join(self, guild):
        program_logger.info(f'I joined {guild}. (ID: {guild.id})')


    async def on_app_command_error(self, interaction: discord.Interaction, error: discord.app_commands.AppCommandError) -> None:
        options = interaction.data.get("options")
        option_values = ""
        if options:
            for option in options:
                option_values += f"{option['name']}: {option['value']}"
        if isinstance(error, discord.app_commands.CommandOnCooldown):
            await interaction.response.send_message(f'This command is on cooldown.\nTime left: `{str(datetime.timedelta(seconds=int(error.retry_after)))}`', ephemeral=True)
            return
        if isinstance(error, discord.app_commands.MissingPermissions):
            await interaction.response.send_message(f'You are missing the following permissions: `{", ".join(error.missing_permissions)}`', ephemeral=True)
            return
        else:
            try:
                try:
                    await interaction.response.send_message(f"Error! Try again.", ephemeral=True)
                except:
                    try:
                        await interaction.followup.send(f"Error! Try again.", ephemeral=True)
                    except:
                        pass
            except discord.Forbidden:
                try:
                    await interaction.followup.send(f"{error}\n\n{option_values}", ephemeral=True)
                except discord.NotFound:
                    try:
                        await interaction.response.send_message(f"{error}\n\n{option_values}", ephemeral=True)
                    except discord.NotFound:
                        pass
                except Exception as e:
                    program_logger.warning(f"Unexpected error while sending message: {e}")
            finally:
                try:
                    program_logger.warning(f"{error} -> {option_values} | Invoked by {interaction.user.name} ({interaction.user.id}) @ {interaction.guild.name} ({interaction.guild.id}) with Language {interaction.locale[1]}")
                except AttributeError:
                    program_logger.warning(f"{error} -> {option_values} | Invoked by {interaction.user.name} ({interaction.user.id}) with Language {interaction.locale[1]}")
                sentry_sdk.capture_exception(error)


    async def on_message(self, message: discord.Message):
        async def __wrong_selection():
            await message.channel.send('```'
                                       'Commands:\n'
                                       'help - Shows this message\n'
                                       'log - Get the log\n'
                                       'activity - Set the activity of the bot\n'
                                       'status - Set the status of the bot\n'
                                       'shutdown - Shutdown the bot\n'
                                       '```')

        if message.author == bot.user:
            return
        if message.channel.type == discord.ChannelType.news:
            message_types = [6, 19, 20]
            if message.type.value in message_types:
                return
            await Functions.auto_publish(message)
        if message.guild is None and message.author.id == int(OWNERID):
            args = message.content.split(' ')
            program_logger.debug(args)
            command, *args = args
            if command == 'help':
                await __wrong_selection()
                return

            elif command == 'log':
                await Owner.log(message, args)
                return

            elif command == 'activity':
                await Owner.activity(message, args)
                return

            elif command == 'status':
                await Owner.status(message, args)
                return

            elif command == 'shutdown':
                await Owner.shutdown(message)
                return

            else:
                await __wrong_selection()


    async def on_ready(self):
        if self.initialized:
            await bot.change_presence(activity = self.Presence.get_activity(), status = self.Presence.get_status())
            return
        global owner, start_time, shutdown
        shutdown = False
        try:
            owner = await self.fetch_user(OWNERID)
            if owner is None:
                program_logger.critical(f"Invalid ownerID: {OWNERID}")
                sys.exit(f"Invalid ownerID: {OWNERID}")
        except discord.HTTPException as e:
            program_logger.critical(f"Error fetching owner user: {e}")
            sys.exit(f"Error fetching owner user: {e}")
        discord_logger.info(f'Logged in as {bot.user} (ID: {bot.user.id})')
        if not self.synced:
            program_logger.info('Syncing...')
            await tree.sync()
            program_logger.info('Synced.')
            self.synced = True
            await bot.change_presence(activity = self.Presence.get_activity(), status = self.Presence.get_status())

        #Start background tasks
        stats = bot_directory.Stats(bot=bot,
                                    logger=program_logger,
                                    TOPGG_TOKEN=topgg_token)
        bot.loop.create_task(Functions.health_server())
        bot.loop.create_task(stats.task())

        program_logger.info('All systems online...')
        start_time = datetime.datetime.now()
        clear()
        self.initialized = True
        message = f"Initialization completed in {time.time() - startupTime_start} seconds."
        program_logger.info(message)
bot = aclient()
tree = discord.app_commands.CommandTree(bot)
tree.on_error = bot.on_app_command_error



class SignalHandler:
    def __init__(self):
        signal.signal(signal.SIGINT, self._shutdown)
        signal.signal(signal.SIGTERM, self._shutdown)

    def _shutdown(self, signum, frame):
        program_logger.info('Received signal to shutdown...')
        bot.loop.create_task(Owner.shutdown(owner))



# Check if all required variables are set
support_available = bool(support_id)

#Fix error on windows on shutdown
if platform.system() == 'Windows':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
def clear():
    if platform.system() == 'Windows':
        os.system('cls')
    else:
        os.system('clear')



#Functions
class Functions():
    async def health_server():
        async def __health_check(request):
            return web.Response(text="Healthy")

        app = web.Application()
        app.router.add_get('/health', __health_check)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', 5000)
        try:
            await site.start()
        except OSError as e:
            program_logger.warning(f'Error while starting health server: {e}')

    def seconds_to_minutes(input_int):
        return(str(datetime.timedelta(seconds=input_int)))

    async def auto_publish(message: discord.Message):
        channel = message.channel
        permissions = channel.permissions_for(channel.guild.me)
        if permissions.add_reactions:
            await message.add_reaction("\U0001F4E2")
        if permissions.send_messages and permissions.manage_messages:
            try:
                await message.publish()
            except Exception as e:
                if not message.flags.crossposted:
                    discord_logger.error(f"Error publishing message in {channel}: {e}")
                    if permissions.add_reactions:
                        await message.add_reaction("\u26A0")
            finally:
                await message.remove_reaction("\U0001F4E2", bot.user)
        else:
            discord_logger.warning(f"No permission to publish in {channel}.")
            await message.remove_reaction("\U0001F4E2", bot.user)
            if permissions.add_reactions:
                await message.add_reaction("\u26D4")

    async def create_support_invite(interaction):
        try:
            guild = bot.get_guild(int(support_id))
        except ValueError:
            return "Could not find support guild."
        if guild is None:
            return "Could not find support guild."
        if not guild.text_channels:
            return "Support guild has no text channels."
        try:
            member = await guild.fetch_member(interaction.user.id)
        except discord.NotFound:
            member = None
        if member is not None:
            return "You are already in the support guild."
        channels: discord.TextChannel = guild.text_channels
        for channel in channels:
            try:
                invite: discord.Invite = await channel.create_invite(
                    reason=f"Created invite for {interaction.user.name} from server {interaction.guild.name} ({interaction.guild_id})",
                    max_age=60,
                    max_uses=1,
                    unique=True
                )
                return invite.url
            except discord.Forbidden:
                continue
            except discord.HTTPException:
                continue
        return "Could not create invite. There is either no text-channel, or I don't have the rights to create an invite."



##Owner Commands
class Owner():
    async def log(message, args):
        async def __wrong_selection():
            await message.channel.send('```'
                                       'log [current/folder/lines] (Replace lines with a positive number, if you only want lines.) - Get the log\n'
                                       '```')

        if args == []:
            await __wrong_selection()
            return
        if args[0] == 'current':
            try:
                await message.channel.send(file=discord.File(r''+log_folder+bot_name+'.log'))
            except discord.HTTPException as err:
                if err.status == 413:
                    with ZipFile(buffer_folder+'Logs.zip', mode='w', compression=ZIP_DEFLATED, compresslevel=9, allowZip64=True) as f:
                        f.write(log_folder+bot_name+'.log')
                    try:
                        await message.channel.send(file=discord.File(r''+buffer_folder+'Logs.zip'))
                    except discord.HTTPException as err:
                        if err.status == 413:
                            await message.channel.send("The log is too big to be send directly.\nYou have to look at the log in your server (VPS).")
                    os.remove(buffer_folder+'Logs.zip')
                    return
        elif args[0] == 'folder':
            if os.path.exists(buffer_folder+'Logs.zip'):
                os.remove(buffer_folder+'Logs.zip')
            with ZipFile(buffer_folder+'Logs.zip', mode='w', compression=ZIP_DEFLATED, compresslevel=9, allowZip64=True) as f:
                for file in os.listdir(log_folder):
                    if file.endswith(".zip"):
                        continue
                    f.write(log_folder+file)
            try:
                await message.channel.send(file=discord.File(r''+buffer_folder+'Logs.zip'))
            except discord.HTTPException as err:
                if err.status == 413:
                    await message.channel.send("The folder is too big to be send directly.\nPlease get the current file, or the last X lines.")
            os.remove(buffer_folder+'Logs.zip')
            return
        else:
            try:
                if int(args[0]) < 1:
                    await __wrong_selection()
                    return
                else:
                    lines = int(args[0])
            except ValueError:
                await __wrong_selection()
                return
            with open(log_folder+bot_name+'.log', 'r', encoding='utf8') as f:
                with open(buffer_folder+'log-lines.txt', 'w', encoding='utf8') as f2:
                    count = 0
                    for line in (f.readlines()[-lines:]):
                        f2.write(line)
                        count += 1
            await message.channel.send(content = f'Here are the last {count} lines of the current logfile:', file = discord.File(r''+buffer_folder+'log-lines.txt'))
            if os.path.exists(buffer_folder+'log-lines.txt'):
                os.remove(buffer_folder+'log-lines.txt')
            return

    async def activity(message, args):
        async def __wrong_selection():
            await message.channel.send('```'
                                       'activity [playing/streaming/listening/watching/competing] [title] (url) - Set the activity of the bot\n'
                                       '```')
        def isURL(zeichenkette):
            try:
                ergebnis = urlparse(zeichenkette)
                return all([ergebnis.scheme, ergebnis.netloc])
            except:
                return False

        def remove_and_save(liste):
            if liste and isURL(liste[-1]):
                return liste.pop()
            else:
                return None

        if args == []:
            await __wrong_selection()
            return
        action = args[0].lower()
        url = remove_and_save(args[1:])
        title = ' '.join(args[1:])
        program_logger.debug(title)
        program_logger.debug(url)
        with open(activity_file, 'r', encoding='utf8') as f:
            data = json.load(f)
        if action == 'playing':
            data['activity_type'] = 'Playing'
            data['activity_title'] = title
            data['activity_url'] = ''
        elif action == 'streaming':
            data['activity_type'] = 'Streaming'
            data['activity_title'] = title
            data['activity_url'] = url
        elif action == 'listening':
            data['activity_type'] = 'Listening'
            data['activity_title'] = title
            data['activity_url'] = ''
        elif action == 'watching':
            data['activity_type'] = 'Watching'
            data['activity_title'] = title
            data['activity_url'] = ''
        elif action == 'competing':
            data['activity_type'] = 'Competing'
            data['activity_title'] = title
            data['activity_url'] = ''
        else:
            await __wrong_selection()
            return
        with open(activity_file, 'w', encoding='utf8') as f:
            json.dump(data, f, indent=2)
        await bot.change_presence(activity = bot.Presence.get_activity(), status = bot.Presence.get_status())
        await message.channel.send(f'Activity set to {action} {title}{" " + url if url else ""}.')

    async def status(message, args):
        async def __wrong_selection():
            await message.channel.send('```'
                                       'status [online/idle/dnd/invisible] - Set the status of the bot\n'
                                       '```')

        if args == []:
            await __wrong_selection()
            return
        action = args[0].lower()
        with open(activity_file, 'r', encoding='utf8') as f:
            data = json.load(f)
        if action == 'online':
            data['status'] = 'online'
        elif action == 'idle':
            data['status'] = 'idle'
        elif action == 'dnd':
            data['status'] = 'dnd'
        elif action == 'invisible':
            data['status'] = 'invisible'
        else:
            await __wrong_selection()
            return
        with open(activity_file, 'w', encoding='utf8') as f:
            json.dump(data, f, indent=2)
        await bot.change_presence(activity = bot.Presence.get_activity(), status = bot.Presence.get_status())
        await message.channel.send(f'Status set to {action}.')

    async def shutdown(message):
        global shutdown
        program_logger.info('Engine powering down...')
        try:
            await message.channel.send('Engine powering down...')
        except:
            await owner.send('Engine powering down...')
        await bot.change_presence(status=discord.Status.invisible)
        shutdown = True

        tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
        [task.cancel() for task in tasks]
        await asyncio.gather(*tasks, return_exceptions=True)

        await bot.close()


#Support Invite
if support_available:
    @tree.command(name = 'support', description = 'Get invite to our support server.')
    @discord.app_commands.checks.cooldown(1, 60, key=lambda i: (i.user.id))
    async def self(interaction: discord.Interaction):
        if str(interaction.guild.id) != support_id:
            await interaction.response.defer(ephemeral = True)
            await interaction.followup.send(await Functions.create_support_invite(interaction), ephemeral = True)
        else:
            await interaction.response.send_message('You are already in our support server!', ephemeral = True)


#Tell user what permissions are required
@tree.command(
    name='permissions',
    description='Tell what permissions are required or check if the bot has necessary permissions in a channel.'
)
@discord.app_commands.describe(choice='Choose an option.', channel='Select channel.')
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

                if interaction.guild.me.guild_permissions.administrator:
                    await interaction.response.send_message('The bot has Administrator, so he has all the necessary permissions in this channel.', ephemeral=True)
                elif not missing_permissions:
                    await interaction.response.send_message('The bot has all the necessary permissions in this channel.', ephemeral=True)
                else:
                    await interaction.response.send_message(f'The bot is missing the following permissions in this channel: {", ".join(missing_permissions)}.\nYou can also give him Administrator.', ephemeral=True)
            else:
                await interaction.response.send_message('Please specify a text channel.', ephemeral=True)
    else:
        await interaction.response.send_message('You need the `manage_roles` or `manage_channels` permission to use this command.', ephemeral=True)


#Bot Information
@tree.command(name = 'botinfo', description = 'Get information about the bot.')
@discord.app_commands.checks.cooldown(1, 60, key=lambda i: (i.user.id))
async def self(interaction: discord.Interaction):
        member_count = sum(guild.member_count for guild in bot.guilds)

        embed = discord.Embed(
            title=f"Informationen about {bot.user.name}",
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url=bot.user.avatar.url if bot.user.avatar else '')

        embed.add_field(name="Created at", value=bot.user.created_at.strftime("%d.%m.%Y, %H:%M:%S"), inline=True)
        embed.add_field(name="Version", value=bot_version, inline=True)
        embed.add_field(name="Uptime", value=str(datetime.timedelta(seconds=int((datetime.datetime.now() - start_time).total_seconds()))), inline=True)

        embed.add_field(name="Owner", value=f"<@!{OWNERID}>", inline=True)
        embed.add_field(name="\u200b", value="\u200b", inline=True)
        embed.add_field(name="\u200b", value="\u200b", inline=True)

        embed.add_field(name="Server", value=f"{len(bot.guilds)}", inline=True)
        embed.add_field(name="Member count", value=str(member_count), inline=True)
        embed.add_field(name="\u200b", value="\u200b", inline=True)

        embed.add_field(name="Shards", value=f"{bot.shard_count}", inline=True)
        embed.add_field(name="Shard ID", value=f"{interaction.guild.shard_id if interaction.guild else 'N/A'}", inline=True)
        embed.add_field(name="\u200b", value="\u200b", inline=True)

        embed.add_field(name="Python", value=f"{platform.python_version()}", inline=True)
        embed.add_field(name="discord.py", value=f"{discord.__version__}", inline=True)
        embed.add_field(name="Sentry", value=f"{sentry_sdk.consts.VERSION}", inline=True)

        embed.add_field(name="Repo", value=f"[GitLab](https://gitlab.bloodygang.com/Serpensin/autopublisher)", inline=True)
        embed.add_field(name="Invite", value=f"[Invite me](https://discord.com/oauth2/authorize?client_id={bot.user.id}&permissions=67423232&scope=bot)", inline=True)
        embed.add_field(name="\u200b", value="\u200b", inline=True)

        if interaction.user.id == int(OWNERID):
            # Add CPU and RAM usage
            process = psutil.Process(os.getpid())
            cpu_usage = process.cpu_percent()
            ram_usage = round(process.memory_percent(), 2)
            ram_real = round(process.memory_info().rss / (1024 ** 2), 2)

            embed.add_field(name="CPU", value=f"{cpu_usage}%", inline=True)
            embed.add_field(name="RAM", value=f"{ram_usage}%", inline=True)
            embed.add_field(name="RAM", value=f"{ram_real} MB", inline=True)

        await interaction.response.send_message(embed=embed)








if __name__ == '__main__':
    if not TOKEN:
        error_message = 'Missing token. Please check your .env file.'
        program_logger.critical(error_message)
        sys.exit(error_message)
    else:
        try:
            SignalHandler()
            bot.run(TOKEN, log_handler=None)
        except discord.errors.LoginFailure:
            error_message = 'Invalid token. Please check your .env file.'
            program_logger.critical(error_message)
            sys.exit(error_message)
        except asyncio.CancelledError:
            if shutdown:
                pass

