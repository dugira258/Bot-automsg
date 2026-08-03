from flask import Flask
from threading import Thread
import discord
from discord.ext import commands
import asyncio
import os

# Servidor para Render
app = Flask('')
@app.route('/')
def home():
    return "✅ Bot rodando!"
def run():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="/", intents=intents)

mensagem_padrao = None
canal_alvo = None
intervalo_minutos = 10
ligado = False
cargo_permitido = None

@bot.event
async def on_ready():
    print(f"✅ Bot ONLINE: {bot.user}")
    try:
        await bot.tree.sync()
        print("✅ Comandos sincronizados!")
    except Exception as e:
        print(f"Erro sync: {e}")

@bot.tree.command(name="automsg", description="Define mensagem")
async def automsg(interaction: discord.Interaction, *, texto: str):
    global mensagem_padrao
    mensagem_padrao = texto
    await interaction.response.send_message(f"✅ Mensagem: `{texto}`", ephemeral=True)

# CORREÇÃO AQUI: comando seguro, resposta rápida
@bot.tree.command(name="configmsg", description="Canal e minutos: /configmsg #canal 5")
async def configmsg(interaction: discord.Interaction, canal: discord.TextChannel, minutos: int):
    global canal_alvo, intervalo_minutos
    canal_alvo = canal
    intervalo_minutos = minutos
    await interaction.response.send_message(
        f"✅ Configurado: {canal.mention} | Tempo: {minutos}min",
        ephemeral=True
    )

async def loop_envio():
    while True:
        if ligado and canal_alvo and mensagem_padrao:
            try:
                await canal_alvo.send(mensagem_padrao)
            except Exception as e:
                print(f"Erro envio: {e}")
        await asyncio.sleep(intervalo_minutos * 60)

@bot.tree.command(name="alternar", description="Liga/desliga")
async def alternar(interaction: discord.Interaction):
    global ligado
    if cargo_permitido and not any(r.id == cargo_permitido for r in interaction.user.roles):
        return await interaction.response.send_message("❌ Sem permissão!", ephemeral=True)
    ligado = not ligado
    await interaction.response.send_message("🟢 LIGADO" if ligado else "🔴 DESLIGADO", ephemeral=True)

@bot.event
async def setup_hook():
    bot.loop.create_task(loop_envio())

t = Thread(target=run)
t.start()

bot.run(os.getenv("DISCORD_TOKEN"))
