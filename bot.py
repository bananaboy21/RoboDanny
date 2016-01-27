from discord.ext import commands
import discord
from cogs.utils import checks
import datetime, re
import json, asyncio
import copy

description = """
Hello! I am a bot written by Danny to provide some nice utilities.
"""

initial_extensions = [
    'cogs.meta',
    'cogs.splatoon',
    'cogs.rng',
    'cogs.mod',
    'cogs.profile',
    'cogs.tags'
]

bot = commands.Bot(command_prefix=['?', '\u2757'], description=description, pm_help=None)

@bot.event
async def on_ready():
    print('Logged in as:')
    print('Username: ' + bot.user.name)
    print('ID: ' + bot.user.id)
    print('------')
    bot.uptime = datetime.datetime.utcnow()
    bot.commands_executed = 0

    for extension in initial_extensions:
        try:
            bot.load_extension(extension)
        except Exception as e:
            print('Failed to load extension {}\n{}: {}'.format(extension, type(e).__name__, e))

@bot.event
async def on_command(command, ctx):
    bot.commands_executed += 1
    message = ctx.message
    # <timestamp>: <author> in <destination>: <content>
    timestamp = message.timestamp.isoformat()
    author = message.author.name.encode('utf-8')
    content = message.content.encode('utf-8')
    destination = None
    if message.channel.is_private:
        destination = 'Private Message'
    else:
        channel_name = b'#' + message.channel.name.encode('utf-8')
        server_name = message.server.name.encode('utf-8')
        destination = '{} ({})'.format(channel_name, server_name)

    print('{}: {} in {}: {}'.format(timestamp, author, destination, content))

@bot.event
async def on_message(message):
    mod = bot.get_cog('Mod')

    if mod is not None:
        # check if the user is bot banned
        if message.author.id in mod.config.get('plonks', []):
            return

        # check if the channel is ignored
        # but first, resolve their permissions

        perms = message.channel.permissions_for(message.author)
        bypass_ignore = perms.manage_roles

        if not bypass_ignore:
            if not message.channel.is_private:
                bypass_ignore = discord.utils.get(message.author.roles, name='Bot Admin') is not None

        if not bypass_ignore:
            if message.channel.id in mod.config.get('ignored', []):
                return

    await bot.process_commands(message)

@bot.command()
@checks.is_owner()
async def load(*, module : str):
    """Loads a module."""
    module = module.strip()
    try:
        bot.load_extension(module)
    except Exception as e:
        await bot.say('\U0001f52b')
        await bot.say('{}: {}'.format(type(e).__name__, e))
    else:
        await bot.say('\U0001f44c')

@bot.command()
@checks.is_owner()
async def unload(*, module : str):
    """Unloads a module."""
    module = module.strip()
    try:
        bot.unload_extension(module)
    except Exception as e:
        await bot.say('\U0001f52b')
        await bot.say('{}: {}'.format(type(e).__name__, e))
    else:
        await bot.say('\U0001f44c')

@bot.command(pass_context=True, hidden=True)
@checks.is_owner()
async def debug(ctx, *, code : str):
    """Evaluates code."""
    code = code.strip('` ')
    python = '```py\n{}\n```'
    result = None

    try:
        result = eval(code)
    except Exception as e:
        await bot.say(python.format(type(e).__name__ + ': ' + str(e)))
        return

    if asyncio.iscoroutine(result):
        result = await result

    await bot.say(python.format(result))

@bot.command(pass_context=True)
async def do(ctx, times : int, *, command):
    """Repeats a command a specified number of times."""
    msg = copy.copy(ctx.message)
    msg.content = command
    for i in range(times):
        await bot.process_commands(msg)

def load_credentials():
    with open('credentials.json') as f:
        return json.load(f)

if __name__ == '__main__':
    credentials = load_credentials()
    bot.run(credentials['email'], credentials['password'])