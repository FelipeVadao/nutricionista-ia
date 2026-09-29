from agno.db.sqlite import SqliteDb

from teste_personal.agent import build_agent
from teste_personal.config import DATA_DIR, SQLITE_FILE
from teste_personal.knowledge import build_knowledge, sincronizar_base


def main() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    db = SqliteDb(db_file=SQLITE_FILE)
    knowledge = build_knowledge(db)

    print("Sincronizando a base de conhecimento (Plano_de_Dieta/)...")
    sincronizar_base(knowledge)

    agent = build_agent(db, knowledge)
    print("Nutricionista pronto. Digite 'sair' para encerrar.\n")
    while True:
        try:
            mensagem = input("Você: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if mensagem.lower() in {"sair", "exit", "quit"}:
            break
        if mensagem:
            agent.print_response(mensagem, stream=True)
            resposta = agent.get_last_run_output()
            if resposta is not None and not (resposta.content or "").strip():
                print(
                    "\n[Aviso] O agente terminou sem escrever resposta "
                    "(provável limite de tokens). Peça novamente ou de forma mais específica.\n"
                )
