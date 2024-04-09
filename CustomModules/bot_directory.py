import aiohttp
import asyncio



class Stats():
    def __init__(self, bot, logger = None, TOPGG_TOKEN: str = '', DISCORDBOTS_TOKEN: str = '', DISCORDBOTLISTCOM_TOKEN: str = '', DISCORDLIST_TOKEN: str = ''):
        """Initialize the Stats class.

        Args:
            bot: The Discord bot instance.
            logger: The logger instance for logging messages.
            shutdown: A boolean flag indicating whether the bot is shutting down.
            TOPGG_TOKEN: Token for top.gg API.
            DISCORDBOTS_TOKEN: Token for discord.bots.gg API.
            DISCORDBOTLISTCOM_TOKEN: Token for discordbotlist.com API.
            DISCORDLIST_TOKEN: Token for discordlist.gg API.
            DISCORDS_TOKEN: Token for discords.com API.
        """
        self.bot = bot
        self.logger = logger
        self.TOPGG_TOKEN = TOPGG_TOKEN
        self.DISCORDBOTS_TOKEN = DISCORDBOTS_TOKEN
        self.DISCORDBOTLISTCOM_TOKEN = DISCORDBOTLISTCOM_TOKEN
        self.DISCORDLIST_TOKEN = DISCORDLIST_TOKEN

    async def _topgg(self):
        if not self.TOPGG_TOKEN:
            return
        headers = {
            'Authorization': self.TOPGG_TOKEN,
            'Content-Type': 'application/json'
        }
        while True:
            async with aiohttp.ClientSession() as session:
                async with session.post(f'https://top.gg/api/bots/{self.bot.user.id}/stats', headers=headers, json={'server_count': len(self.bot.guilds), 'shard_count': len(self.bot.shards)}) as resp:
                    if resp.status != 200 and self.logger is not None:
                        self.logger.error(f'Failed to update top.gg: {resp.status} {resp.reason}')
            try:
                await asyncio.sleep(60*30)
            except asyncio.CancelledError:
                break

    async def _discordbots(self):
        if not self.DISCORDBOTS_TOKEN:
            return
        headers = {
            'Authorization': self.DISCORDBOTS_TOKEN,
            'Content-Type': 'application/json'
        }
        while True:
            async with aiohttp.ClientSession() as session:
                async with session.post(f'https://discord.bots.gg/api/v1/bots/{self.bot.user.id}/stats', headers=headers, json={'guildCount': len(self.bot.guilds), 'shardCount': len(self.bot.shards)}) as resp:
                    if resp.status != 200 and self.logger is not None:
                        self.logger.error(f'Failed to update discord.bots.gg: {resp.status} {resp.reason}')
            try:
                await asyncio.sleep(60*30)
            except asyncio.CancelledError:
                break

    async def _discordbotlist_com(self):
        if not self.DISCORDBOTLISTCOM_TOKEN:
            return
        headers = {
            'Authorization': self.DISCORDBOTLISTCOM_TOKEN,
            'Content-Type': 'application/json'
        }
        while True:
            async with aiohttp.ClientSession() as session:
                async with session.post(f'https://discordbotlist.com/api/v1/bots/{self.bot.user.id}/stats', headers=headers, json={'guilds': len(self.bot.guilds), 'users': sum(guild.member_count for guild in self.bot.guilds)}) as resp:
                    if resp.status != 200 and self.logger is not None:
                        self.logger.error(f'Failed to update discordbotlist.com: {resp.status} {resp.reason}')
            try:
                await asyncio.sleep(60*30)
            except asyncio.CancelledError:
                break

    async def _discordlist(self):
        if not self.DISCORDLIST_TOKEN:
            return
        headers = {
            'Authorization': f'Bearer {self.DISCORDLIST_TOKEN}',
            'Content-Type': 'application/json; charset=utf-8'
        }
        while True:
            async with aiohttp.ClientSession() as session:
                async with session.post(f'https://api.discordlist.gg/v0/bots/{self.bot.user.id}/guilds', headers=headers, json={"count": len(self.bot.guilds)}) as resp:
                    if resp.status != 200 and self.logger is not None:
                        self.logger.error(f'Failed to update discordlist.gg: {resp.status} {resp.reason}')
            try:
                await asyncio.sleep(60*30)
            except asyncio.CancelledError:
                break

    async def start_stats_update(self):
        """Start updating statistics on various bot listing sites."""
        updates = [self._topgg(),
                   self._discordbots(),
                   self._discordbotlist_com(),
                   self._discordlist()
                   ]

        tasks = [asyncio.create_task(update) for update in updates]

        for task in tasks:
            await task

    async def task(self):
        """Start the task for periodic statistics updates."""
        while True:
            await self.start_stats_update()
            try:
                await asyncio.sleep(60*30)
            except asyncio.CancelledError:
                break