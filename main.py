import discord
from discord.ext import commands
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="/", intents=intents)

mensagem_padrao = None
canal_alvo = None
intervalo_minutos = 10
ligado = False
cargo_permitido = None

@bot.event
async def on_ready():
    print(f"✅ Bot ligado como: {bot.user}")
    await bot.tree.sync()

@bot.tree.command(name="automsg", description="Define a mensagem automática")
async def automsg(interaction: discord.Interaction, *, texto: str):
    global mensagem_padrao
    mensagem_padrao = texto
    await interaction.response.send_message(f"✅ Mensagem salva: `{texto}`", ephemeral=True)

@bot.tree.command(name="configmsg", description="Configura canal e tempo")
async def configmsg(interaction: discord.Interaction, canal: discord.TextChannel, minutos: int):
    global canal_alvo, intervalo_minutos
    canal_alvo = canal
    intervalo_minutos = minutos
    await interaction.response.send_message(f"✅ Canal: {canal.mention} | Tempo: {minutos}min", ephemeral=True)

async def loop_envio():
    while True:
        if ligado and canal_alvo and mensagem_padrao:
            try:
                await canal_alvo.send(mensagem_padrao)
            except Exception as e:
                print(f"Erro: {e}")
        await asyncio.sleep(intervalo_minutos * 60)

@bot.tree.command(name="alternar", description="Liga/desliga o sistema")
async def alternar(interaction: discord.Interaction):
    global ligado
    if cargo_permitido and not any(r.id == cargo_permitido for r in interaction.user.roles):
        return await interaction.response.send_message("❌ Sem permissão!", ephemeral=True)
    ligado = not ligado
    await interaction.response.send_message(f"🟢 LIGADO" if ligado else "🔴 DESLIGADO")

@bot.event
async def setup_hook():
    bot.loop.create_task(loop_envio())

bot.run(os.getenv("DISCORD_TOKEN"))
