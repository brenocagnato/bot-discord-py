import discord
from discord.ext import commands, tasks
import asyncio

class CustomHelpCommand(commands.HelpCommand):
    def __init__(self):
        super().__init__()

    async def send_bot_help(self, mapping):
        return await super().send_bot_help(mapping)

intents = discord.Intents.default()
intents.members = True
intents.messages = True
intents.message_content = True
intents.guilds = True
intents.voice_states = True

bot = commands.Bot(command_prefix='s!', intents=intents, help_command=CustomHelpCommand())

canais_temporarios = []

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    monitorar_canais_temporarios.start()

@bot.event
async def on_voice_state_update(member, before, after):
    if after.channel and after.channel.name == "++":
        dm_channel = await member.create_dm()
        await dm_channel.send("Você quer que seu canal de voz seja **privado** ou **público**? Responda com `privado` ou `público`.")

        def check(m):
            return m.content.lower() in ['privado', 'público'] and m.channel == dm_channel and m.author == member

        try:
            msg = await bot.wait_for('message', check=check, timeout=30.0)
            new_channel_name = f"Canal de {member.display_name}"
            if msg.content.lower() == 'privado':
                overwrites = {
                    after.channel.guild.default_role: discord.PermissionOverwrite(view_channel=False),
                    member: discord.PermissionOverwrite(view_channel=True)
                }
                new_channel = await after.channel.guild.create_voice_channel(name=new_channel_name, category=after.channel.category, overwrites=overwrites)
            else:
                new_channel = await after.channel.guild.create_voice_channel(name=new_channel_name, category=after.channel.category)

            await member.move_to(new_channel)
            canais_temporarios.append(new_channel.id)  # Adiciona o novo canal à lista de monitoramento

        except asyncio.TimeoutError:
            await dm_channel.send("Você não respondeu a tempo. Canal de voz não criado.")

@tasks.loop(seconds=3)  # Pode ajustar a frequência conforme necessário
async def monitorar_canais_temporarios():
    for canal_id in canais_temporarios.copy():  # Itera sobre uma cópia para evitar modificar a lista durante a iteração
        canal = bot.get_channel(canal_id)
        if canal and len(canal.members) == 0:
            await canal.delete(reason="Canal temporário vazio")
            canais_temporarios.remove(canal_id)

@bot.command(name='canais')
async def list_voice_channels(ctx):
    voice_channels_temp = [bot.get_channel(canal_id) for canal_id in canais_temporarios if bot.get_channel(canal_id)]
    if voice_channels_temp:
        channels_message = "**Canais de Voz Temporários:**\n" + "\n".join(canal.mention for canal in voice_channels_temp)
        await ctx.send(channels_message)
    else:
        await ctx.send("Não há canais de voz temporários criados pelo bot neste servidor.")

@bot.command(name='ajuda')
async def custom_help_command(ctx):
    help_message = """
    **Comandos do Bot:**
    `s!help` - Mostra esta mensagem de ajuda.
    `s!canais` - Mostra todos os canais ativos nesse servidor pelo bot.
    """
    await ctx.send(help_message)

# Roda o bot
bot.run('SEU TOKEN AQUI')
