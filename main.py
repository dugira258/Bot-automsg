from flask import Flask
from threading import Thread
import discord
from discord.ext import commands
import asyncio
import os

# Mantém o Render feliz
app = Flask('')
@app.route('/')
def home():
    return "✅ Bot funcionando!"
def run():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

# Configurações
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="/", intents=intents)

# Variáveis globais
mensagem_padrao = None
canal_alvo = None
inicio_minutos = 10   # Tempo até a PRIMEIRA mensagem
intervalo_minutos = 10 # Intervalo entre as próximas
ligado = False
cargo_permitido = None
tarefa_loop = None

# Evento ligado
@bot.event
async def on_ready():
    print(f"✅ Bot ONLINE: {bot.user}")
    try:
        await bot.tree.sync()
        print("✅ Comandos prontos!")
    except Exception as e:
        print(f"Erro: {e}")

# Comando 1: Definir mensagem
@bot.tree.command(name="automsg", description="Escolha o texto a enviar")
async def automsg(interaction: discord.Interaction, *, texto: str):
    global mensagem_padrao
    mensagem_padrao = texto
    await interaction.response.send_message(f"✅ Mensagem salva: `{texto}`", ephemeral=True)

# Comando 2: CONFIGURAR TEMPOS (arrumado como pediu!)
@bot.tree.command(
    name="configmsg",
    description="Configura: canal | minutos para começar | intervalo depois"
)
async def configmsg(
    interaction: discord.Interaction,
    canal: discord.TextChannel,
    inicio: int,
    intervalo: int
):
    global canal_alvo, inicio_minutos, intervalo_minutos, tarefa_loop, ligado

    # Salva configurações
    canal_alvo = canal
    inicio_minutos = inicio
    intervalo_minutos = intervalo

    # Reinicia o loop com os novos valores
    if tarefa_loop and not tarefa_loop.done():
        tarefa_loop.cancel()

    ligado = False
    tarefa_loop = bot.loop.create_task(loop_envio())

    await interaction.response.send_message(
        f"✅ TUDO CONFIGURADO:\n"
        f"📢 Canal: {canal.mention}\n"
        f"⏱️ Primeira mensagem: **{inicio}min**\n"
        f"🔁 Repete a cada: **{intervalo}min**",
        ephemeral=True
    )

# Loop principal com início + intervalo corretos
async def loop_envio():
    global ligado
    while True:
        await asyncio.sleep(1)
        if ligado and canal_alvo and mensagem_padrao:
            # Primeira espera
            await asyncio.sleep(inicio_minutos * 60)
            while ligado and canal_alvo and mensagem_padrao:
                try:
                    await canal_alvo.send(mensagem_padrao)
                except Exception as e:
                    print(f"Erro: {e}")
                # Espera o intervalo normal
                await asyncio.sleep(intervalo_minutos * 60)
        else:
            await asyncio.sleep(1)

# Comando 3: Ligar/Desligar
@bot.tree.command(name="alternar", description="Liga ou desliga o sistema")
async def alternar(interaction: discord.Interaction):
    global ligado
    if cargo_permitido and not any(r.id == cargo_permitido for r in interaction.user.roles):
        return await interaction.response.send_message("❌ Sem permissão!", ephemeral=True)
    ligado = not ligado
    if ligado:
        await interaction.response.send_message(
            f"🟢 LIGADO!\n"
            f"1ª mensagem: **{inicio_minutos}min** | Intervalo: **{intervalo_minutos}min**",
            ephemeral=True
        )
    else:
        await interaction.response.send_message("🔴 DESLIGADO", ephemeral=True)

# Inicializa tudo
@bot.event
async def setup_hook():
    global tarefa_loop
    tarefa_loop = bot.loop.create_task(loop_envio())

# Inicia servidor e bot
t = Thread(target=run)
t.start()

bot.run(os.getenv("DISCORD_TOKEN"))
