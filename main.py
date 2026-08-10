from flask import Flask
from threading import Thread
import discord
from discord.ext import commands
import asyncio
import os
import sys
import aiohttp
import json

# ⚙️ SERVIDOR + CUTUCADA PARA NUNCA DORMIR
app = Flask('')

@app.route('/')
def home():
    return "✅ BOT LIGADO E ACORDADO!"

def run_server():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)), use_reloader=False)

# 📂 GERENCIAR CONFIGURAÇÕES (POR SERVIDOR)
def carregar_config():
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def salvar_config(config):
    with open("config.json", "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4, ensure_ascii=False)

def criar_config_se_nao_existir(guild_id):
    config = carregar_config()
    gid = str(guild_id)
    if gid not in config:
        config[gid] = {
            "canal_id": None,
            "mensagem": None,
            "inicio_minutos": 10,
            "intervalo_minutos": 10,
            "ligado": False
        }
        salvar_config(config)
    return config[gid]

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
        await asyncio.sleep(300)  # 5 minutos

# 🤖 CONFIG DO BOT
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="/", intents=intents)

# 🧵 TAREFAS DE LOOP POR SERVIDOR
tarefas = {}

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

    # 🔄 RETOMA LOOP DOS SERVIDORES QUE ESTAVAM LIGADOS
    config = carregar_config()
    for gid in config:
        if config[gid]["ligado"]:
            guild = bot.get_guild(int(gid))
            if guild:
                bot.loop.create_task(iniciar_loop_servidor(guild))

# 🆕 CRIA CONFIG AUTOMÁTICA QUANDO BOT ENTRA EM SERVIDOR NOVO
@bot.event
async def on_guild_join(guild):
    criar_config_se_nao_existir(guild.id)

# 📩 COMANDO 1: DEFINIR MENSAGEM (SÓ ESTE SERVIDOR)
@bot.tree.command(name="automsg", description="Salva o texto para enviar")
async def automsg(interaction: discord.Interaction, *, texto: str):
    gid = str(interaction.guild.id)
    criar_config_se_nao_existir(gid)
    config = carregar_config()
    config[gid]["mensagem"] = texto
    salvar_config(config)
    await interaction.response.send_message(f"✅ Mensagem salva:\n`{texto}`", ephemeral=True)

# ⚙️ COMANDO 2: CONFIGURAR CANAL E TEMPOS (SÓ ESTE SERVIDOR)
@bot.tree.command(name="configmsg", description="Uso: /configmsg canal:#canal inicio:5 intervalo:10")
async def configmsg(
    interaction: discord.Interaction,
    canal: discord.TextChannel,
    inicio: int,
    intervalo: int
):
    gid = str(interaction.guild.id)
    criar_config_se_nao_existir(gid)
    config = carregar_config()
    
    config[gid]["canal_id"] = str(canal.id)
    config[gid]["inicio_minutos"] = inicio
    config[gid]["intervalo_minutos"] = intervalo
    config[gid]["ligado"] = False
    salvar_config(config)

    # Para loop antigo se existir
    if gid in tarefas:
        tarefas[gid].cancel()
        del tarefas[gid]

    await interaction.response.send_message(
        f"✅ CONFIGURADO:\n📢 Canal: {canal.mention}\n⏱️ 1ª msg em: {inicio}min\n🔁 Repete a cada: {intervalo}min",
        ephemeral=True
    )

# 🔛 COMANDO 3: LIGAR / DESLIGAR (SÓ ESTE SERVIDOR)
@bot.tree.command(name="alternar", description="Liga ou desliga o sistema")
async def alternar(interaction: discord.Interaction):
    gid = str(interaction.guild.id)
    criar_config_se_nao_existir(gid)
    config = carregar_config()
    
    config[gid]["ligado"] = not config[gid]["ligado"]
    salvar_config(config)

    if config[gid]["ligado"]:
        bot.loop.create_task(iniciar_loop_servidor(interaction.guild))
        await interaction.response.send_message(
            f"🟢 LIGADO! 1ª msg em: {config[gid]['inicio_minutos']}min | Repete: {config[gid]['intervalo_minutos']}min",
            ephemeral=True
        )
    else:
        if gid in tarefas:
            tarefas[gid].cancel()
            del tarefas[gid]
        await interaction.response.send_message("🔴 DESLIGADO", ephemeral=True)

# 🛡️ LOOP INDIVIDUAL POR SERVIDOR (ANTITRAVAMENTO)
async def iniciar_loop_servidor(guild):
    gid = str(guild.id)
    
    # Cancela loop antigo se existir
    if gid in tarefas:
        tarefas[gid].cancel()

    async def loop_seguro():
        while True:
            config = carregar_config().get(gid, None)
            if not config or not config["ligado"]:
                break
            if not config["canal_id"] or not config["mensagem"]:
                await asyncio.sleep(5)
                continue

            canal = guild.get_channel(int(config["canal_id"]))
            if not canal:
                await asyncio.sleep(10)
                continue

            try:
                # Tempo de espera inicial
                await asyncio.sleep(config["inicio_minutos"] * 60)
                
                # Loop de repetição
                while True:
                    cfg = carregar_config().get(gid, None)
                    if not cfg or not cfg["ligado"]:
                        return
                    
                    try:
                        await canal.send(cfg["mensagem"])
                        print(f"📤 Msg enviada | Servidor: {guild.name}")
                    except Exception as e:
                        print(f"❌ Erro ao enviar [{guild.name}]: {e}")
                    
                    await asyncio.sleep(cfg["intervalo_minutos"] * 60)

            except Exception as e:
                print(f"🔁 Loop reiniciado [{guild.name}]: {e}")
                await asyncio.sleep(5)

    tarefas[gid] = bot.loop.create_task(loop_seguro())

# 🚀 INICIA TUDO
if __name__ == "__main__":
    t = Thread(target=run_server, daemon=True)
    t.start()
    try:
        bot.run(os.getenv("DISCORD_TOKEN"))
    except Exception as e:
        print(f"💥 ERRO CRÍTICO: {e}")
        sys.exit(1)
