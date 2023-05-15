# Discord Auto Publisher

**Automatically publish messages or news in your announcement channels!**

A lightweight command-less bot that will automatically publish every new message in your [announcement/news channels](https://support.discord.com/hc/en-us/articles/360032008192-Announcement-Channels-) to other servers who follow it. An excellent solution for servers who rely on bots (such as RSS feeds) or webhooks to publish their news, allowing your moderators to get some rest from manual publishing. Unlike most other bots who can publish messages, this bot utilizes advanced URL detection algorithm that will ensure all your messages containing URLs will be published properly with no embeds missing!

![](https://media.giphy.com/media/KxgsmVFc4nMF7U50UF/giphy.gif)

**The bot features no commands because the setup is really easy!**

## How to set up?

1. [Invite](https://discord.com/api/oauth2/authorize?client_id=1105085860615045221&permissions=0&scope=bot%20applications.commands) the bot to your server.
2. Navigate to your announcement channel's settings and give the bot following permissions: `View Channel`, `Send Messages`, `Manage Messages`, `Read Message History`
3. Repeat step 2. for every channel where you want auto-publishing
4. Done!

### Keep in mind...

- The bot can only publish 10 messages per hour per channel (just as users), this is rate limited by Discord!
- If you want to temporarily stop the bot from publishing messages in any of your announcement channels, just disable its' `View Channel` permission in a desired channel and enable it back when you're ready.
