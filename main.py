from flask import Flask
from threading import Thread
import discord
from discord.ext import commands
import asyncio
import os

# Servidor para Render não cair
app = Flask('')
@app.route('/')
def home():
    return "✅ Bot rodando!"
def run():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

# Configurações
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="/", intents=intents)

# Variáveis
mensagem_padrao = None
canal_alvo = None
inicio_minutos = 10
intervalo_minutos = 10
ligado = False
cargo_permitido = None
tarefa_loop = None

@bot.event
async def on_ready():
    print(f"✅ Bot ONLINE: {bot.user}")
    try:
        await bot.tree.sync()
        print("✅ Comandos prontos!")
    except Exception as e:
        print(f"Erro: {e}")

@bot.tree.command(name="automsg", description="Define a mensagem a enviar")
async def automsg(interaction: discord.Interaction, *, texto: str):
    global mensagem_padrao
    mensagem_padrao = texto
    await interaction.response.send_message(f"✅ Mensagem: `{texto}`", ephemeral=True)

# ✅ AQUI É A CHAVE: nomes exatos e defer rápido
@bot.tree.command(
    name="configmsg",
    description="Uso: /configmsg canal:#canal inicio:10 intervalo:5"
)
async def configmsg(
    interaction: discord.Interaction,
    canal: discord.TextChannel,
    inicio: int,
    intervalo: int
):
    global canal_alvo, inicio_minutos, intervalo_minutos, tarefa_loop

    # Responde IMEDIATO para não dar erro "não respondeu"
    await interaction.response.defer(ephemeral=True)

    # Salva valores
    canal_alvo = canal
    inicio_minutos = inicio
    intervalo_minutos = intervalo

    # Reinicia loop com novos tempos
    if tarefa_loop and not tarefa_loop.done():
        tarefa_loop.cancel()
    ligado = False
    tarefa_loop = bot.loop.create_task(loop_envio())

    # Confirmação bonita
    await interaction.followup.send(
        f"✅ TUDO OK:\n"
        f"📢 Canal: {canal.mention}\n"
        f"⏱️ 1ª mensagem: **{inicio}min**\n"
        f"🔁 Repete: **{intervalo}min**",
        ephemeral=True
    )

# Loop PERFEITO: espera início → depois intervalo
async def loop_envio():
    global ligado
    while True:
        await asyncio.sleep(1)
        if ligado and canal_alvo and mensagem_padrao:
            await asyncio.sleep(inicio_minutos * 60)
            while ligado and canal_alvo and mensagem_padrao:
                try:
                    await canal_alvo.send(mensagem_padrao)
                except Exception as e:
                    print(f"Erro envio: {e}")
                await asyncio.sleep(intervalo_minutos * 60)

@bot.tree.command(name="alternar", description="Liga/desliga o envio")
async def alternar(interaction: discord.Interaction):
    global ligado
    if cargo_permitido and not any(r.id == cargo_permitido for r in interaction.user.roles):
        return await interaction.response.send_message("❌ Sem permissão!", ephemeral=True)
    ligado = not ligado
    await interaction.response.send_message(
        f"🟢 LIGADO!\n1ª: {inicio_minutos}min | Repete: {intervalo_minutos}min"
        if ligado else "🔴 DESLIGADO",
        ephemeral=True
    )

@bot.event
async def setup_hook():
    global tarefa_loop
    tarefa_loop = bot.loop.create_task(loop_envio())

# Inicia servidor
t = Thread(target=run)
t.start()

bot.run(os.getenv("DISCORD_TOKEN"))
