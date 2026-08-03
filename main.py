from flask import Flask
from threading import Thread
import discord
from discord.ext import commands
import asyncio
import os
import sys
import aiohttp

# ⚙️ SERVIDOR + CUTUCADA PARA NUNCA DORMIR
app = Flask('')

@app.route('/')
def home():
    return "✅ BOT LIGADO E ACORDADO!"

def run_server():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)), use_reloader=False)

# 🔁 TAREFA QUE CUTUCA O PRÓPRIO SITE A CADA 5 MINUTOS
async def manter_acordado(url):
    await asyncio.sleep(10)
    while True:
        try:
            async with aiohttp.ClientSession() as sessao:
                async with sessao.get(url) as resp:
                    print(f"🔄 Cutucada: Status {resp.status}")
        except Exception as e:
            print(f"⚠️ Erro na cutucada: {e}")
        await asyncio.sleep(300)  # 5 minutos = 300 segundos

# 🤖 CONFIG DO BOT
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="/", intents=intents)

# 📝 VARIÁVEIS GLOBAIS
mensagem_padrao = None
canal_alvo = None
inicio_minutos = 10
intervalo_minutos = 10
ligado = False
cargo_permitido = None
tarefa_loop = None

# ✅ EVENTO QUANDO LIGA
@bot.event
async def on_ready():
    print(f"✅ BOT ONLINE: {bot.user}")
    try:
        await bot.tree.sync()
        print("✅ COMANDOS PRONTOS!")
    except Exception as e:
        print(f"Erro sincronia: {e}")
    
    # 🚀 INICIA A CUTUCADA AUTOMÁTICA
    url_do_seu_site = f"https://{os.getenv('RENDER_SERVICE_NAME', 'bot-automsg')}.onrender.com"
    bot.loop.create_task(manter_acordado(url_do_seu_site))
    print(f"🔁 Manutenção ativada: {url_do_seu_site}")

# 📩 COMANDO 1: DEFINIR MENSAGEM
@bot.tree.command(name="automsg", description="Salva o texto para enviar")
async def automsg(interaction: discord.Interaction, *, texto: str):
    global mensagem_padrao
    mensagem_padrao = texto
    await interaction.response.send_message(f"✅ Mensagem: `{texto}`", ephemeral=True)

# ⚙️ COMANDO 2: CONFIGURAR CANAL E TEMPOS
@bot.tree.command(name="configmsg", description="Uso: /configmsg canal:#canal inicio:5 intervalo:10")
async def configmsg(
    interaction: discord.Interaction,
    canal: discord.TextChannel,
    inicio: int,
    intervalo: int
):
    global canal_alvo, inicio_minutos, intervalo_minutos, tarefa_loop
    await interaction.response.defer(ephemeral=True)

    canal_alvo = canal
    inicio_minutos = inicio
    intervalo_minutos = intervalo

    if tarefa_loop and not tarefa_loop.done():
        tarefa_loop.cancel()
    ligado = False
    tarefa_loop = bot.loop.create_task(loop_seguro())

    await interaction.followup.send(
        f"✅ CONFIGURADO:\n📢 Canal: {canal.mention}\n⏱️ 1ª: {inicio}min\n🔁 Repete: {intervalo}min",
        ephemeral=True
    )

# 🛡️ LOOP ANTITRAVAMENTO (SE DER ERRO, REINICIA SOZINHO)
async def loop_seguro():
    global ligado
    while True:
        await asyncio.sleep(2)
        if not ligado or not canal_alvo or not mensagem_padrao:
            continue
        try:
            await asyncio.sleep(inicio_minutos * 60)
            while ligado and canal_alvo and mensagem_padrao:
                try:
                    await canal_alvo.send(mensagem_padrao)
                except Exception as e:
                    print(f"❌ Erro ao enviar: {e}")
                await asyncio.sleep(intervalo_minutos * 60)
        except Exception as e:
            print(f"🔁 Loop reiniciado: {e}")
            await asyncio.sleep(5)

# 🔛 COMANDO 3: LIGAR / DESLIGAR
@bot.tree.command(name="alternar", description="Liga ou desliga o sistema")
async def alternar(interaction: discord.Interaction):
    global ligado
    await interaction.response.defer(ephemeral=True)

    if cargo_permitido and not any(r.id == cargo_permitido for r in interaction.user.roles):
        return await interaction.followup.send("❌ Sem permissão!", ephemeral=True)

    ligado = not ligado
    await interaction.followup.send(
        f"🟢 LIGADO! 1ª: {inicio_minutos}min | Repete: {intervalo_minutos}min"
        if ligado else "🔴 DESLIGADO",
        ephemeral=True
    )

# 🚀 INICIALIZA TAREFAS
@bot.event
async def setup_hook():
    global tarefa_loop
    tarefa_loop = bot.loop.create_task(loop_seguro())

# 🧠 INICIA TUDO COM SEGURANÇA
if __name__ == "__main__":
    t = Thread(target=run_server, daemon=True)
    t.start()
    try:
        bot.run(os.getenv("DISCORD_TOKEN"))
    except Exception as e:
        print(f"💥 ERRO CRÍTICO: {e}")
        sys.exit(1)
