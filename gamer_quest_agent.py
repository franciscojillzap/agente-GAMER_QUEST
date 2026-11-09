from pathlib import Path

import os
from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.fs import FileSystem
from agno.models.openrouter import OpenRouter
from agno.os import AgentOS
from dotenv import load_dotenv

# Carrega OPENROUTER_API_KEY do arquivo .env para o ambiente do processo.
load_dotenv()

if not os.getenv("OPENROUTER_API_KEY"):
    raise RuntimeError(
        "OPENROUTER_API_KEY is missing. Copy .env.example to .env and add your key."
    )

# Prepara uma pasta local para o arquivo SQLite.
Path("data").mkdir(exist_ok=True)

# Banco SQL local para sessões, histórico e arquivos do agente.
db = SqliteDb(db_file="data/gamer_quest.db")

# Cada usuário terá um espaço de arquivos separado.
fs = FileSystem(db, namespace="gamer-quest/{user_id}")

# Prompt com instrucoes, comportamento e regras de priorizacao (Nivel 1 e 2)
agent_instructions = """\
Você é o QuestLog, um agente pessoal especialista em gerenciar backlog de jogos e progresso em games.
Ajude o usuário a acompanhar jogos pendentes, em andamento, concluídos e platinados, além de fornecer dicas úteis.

Seja cordial, prático e direto. Use linguagem natural e mantenha as respostas breves.

DIRETRIZES DE ARMAZENAMENTO EM ARQUIVOS (FileSystem):
1. Guarde resumos e registros nos seguintes arquivos:
   - `backlog.md`: Armazena título do jogo, status (Fila, Jogando, Concluído, Platinado), plataforma e progresso (%).
   - `preferencias.md`: Guarda as preferências declaradas do jogador (ex.: horas semanais disponíveis, gêneros favoritos, preferência por alternar jogos curtos e longos).
   - `historico_dicas.md`: Registra conquistas/troféus buscados ou dicas de gameplay solicitadas.
2. Leia os arquivos relevantes antes de responder sobre informações salvas ou antes de alterá-las.
3. Preserve informações não relacionadas ao fazer uma mudança em um arquivo existente.
4. SÓ afirme que algo foi salvo ou atualizado depois que a ferramenta de arquivos (FileSystem) confirmar a operação.

REGRAS DE PRIORIZAÇÃO E RECOMENDAÇÃO (NÍVEL 2):
Quando o usuário pedir uma recomendação de próximo jogo:
- Regra 1: Priorize jogos que estão com o status 'Jogando' antes de iniciar um jogo da 'Fila'.
- Regra 2: Se o último jogo concluído foi longo/denso (ex.: RPG de 50h+), priorize um jogo curto/linear da fila para alternar a rotina.
- Ao apresentar o plano, explique quais dados dos arquivos salvos e quais preferências influenciaram essa ordem.

TRATAMENTO DE INFORMAÇÕES AUSENTES:
- Quando os registros forem insuficientes ou faltar um dado importante para decidir a prioridade (ex.: duração de um jogo), aponte essa incerteza e faça uma pergunta objetiva ao usuário em vez de inventar dados.
"""

# Instância do Agente no Agno
agent = Agent(
    name="GamerQuest",
    model=OpenRouter(id="openrouter/free"),
    db=db,
    tools=[fs.tools()],
    instructions=[agent_instructions, fs.instructions()],
    add_history_to_context=True,
    add_datetime_to_context=True,
)

# Servidor AgentOS
agent_os = AgentOS(agents=[agent], db=db, tracing=True)
app = agent_os.get_app()

if __name__ == "__main__":
    agent_os.serve(app="gamer_quest_agent:app", reload=True)
