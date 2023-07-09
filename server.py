import json
import socket
import sys
from _thread import start_new_thread
from time import sleep

from game.board import ServerBoard
from game.constants import NUM_LINHAS


def thread_registra_cliente(conexao):
    reply = ""
    username = ""
    registrado = False
    while not registrado:
        try:
            mensagem = json.loads(conexao.recv(2048).decode("utf-8"))

            if not mensagem:
                print("Falha ao receber dados do cliente. Desconectado.")
                return
            elif mensagem["tipo"] == "registrar_jogador":
                username = mensagem["dados"]["username"]
                print(f"Registrando jogador: {username}")
                if username in jogadores_conectados:
                    print(f"Jogador {username} já registrado.")
                    reply = json.dumps({"tipo": "jogador_registrado", "dados": {"registrado": False}})
                else:
                    jogadores_conectados[username] = conexao
                    reply = json.dumps({"tipo": "jogador_registrado", "dados": {"registrado": True}})
                    registrado = True
            else:
                reply = json.dumps(
                    {
                        "tipo": "erro",
                        "dados": {"mensagem": "Tipo de mensagem inesperado."},
                    }
                )
            conexao.sendall(str.encode(reply + "\0"))
        except Exception:
            print("Falha ao receber dados do cliente. Desconectado.")
            return


def process_primeira_escolha(jogador, oponente, dados, board):
    global primeira_escolha

    coord_x = dados["coluna"]
    coord_y = dados["linha"]

    if primeira_escolha is None and (escolha := board.get_card_by_pos(coord_x, coord_y)) and not escolha.virada:
        primeira_escolha = escolha
        reply = json.dumps({"tipo": "carta_valida", "dados": {"valida": True, "valor": escolha.numero}})
        reply_oponente = json.dumps(
            {
                "tipo": "primeira_escolha_oponente",
                "dados": {"coluna": coord_x, "linha": coord_y, "valor": escolha.numero},
            }
        )
        jogadores_conectados[oponente].sendall(str.encode(reply_oponente + "\0"))
    else:
        reply = json.dumps({"tipo": "carta_valida", "dados": {"valida": False}})
    jogadores_conectados[jogador].sendall(str.encode(reply + "\0"))


def process_segunda_escolha(jogador, oponente, dados, board, pontuacao) -> bool | None:
    global primeira_escolha, segunda_escolha

    coord_x = dados["coluna"]
    coord_y = dados["linha"]

    if (
        primeira_escolha is not None
        and segunda_escolha is None
        and (escolha := board.get_card_by_pos(coord_x, coord_y))
        and primeira_escolha is not escolha
        and not escolha.virada
    ):
        segunda_escolha = escolha

        reply = json.dumps({"tipo": "carta_valida", "dados": {"valida": True, "valor": escolha.numero}})
        jogadores_conectados[jogador].sendall(str.encode(reply + "\0"))
        reply_oponente = json.dumps(
            {
                "tipo": "segunda_escolha_oponente",
                "dados": {"coluna": coord_x, "linha": coord_y, "valor": escolha.numero},
            }
        )
        jogadores_conectados[oponente].sendall(str.encode(reply_oponente + "\0"))

        acertou = board.check((primeira_escolha, segunda_escolha))
        pontuacao[jogador] += int(acertou)
        reply = json.dumps(
            {
                "tipo": "resultado_jogada",
                "dados": {
                    "username": jogador,
                    "pontuacao": pontuacao[jogador],
                    "acertou": acertou,
                },
            }
        )
        jogadores_conectados[jogador].sendall(str.encode(reply + "\0"))
        jogadores_conectados[oponente].sendall(str.encode(reply + "\0"))
        return acertou

    reply = json.dumps({"tipo": "carta_valida", "dados": {"valida": False}})
    jogadores_conectados[jogador].sendall(str.encode(reply + "\0"))

    return None


primeira_escolha = None
segunda_escolha = None
jogadores_conectados = {}


def main():
    global primeira_escolha, segunda_escolha

    if len(sys.argv) != 3:
        porta = 5555
        addr = "127.0.0.1"
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    else:
        addr = sys.argv[1]
        porta = int(sys.argv[2])
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        s.bind((addr, porta))
    except socket.error:
        raise

    s.listen(2)

    for _ in range(2):
        print("Aguardando conexão...")
        conexao, endr = s.accept()
        print("Conectado a:", endr)

        start_new_thread(thread_registra_cliente, (conexao,))

    while len(jogadores_conectados) < 2:
        pass

    sleep(2)
    jogador_1, jogador_2 = list(jogadores_conectados.keys())
    msg = json.dumps({"tipo": "ordem_jogadores", "dados": {"1": jogador_1, "2": jogador_2}})
    for jogador in jogadores_conectados:
        jogadores_conectados[jogador].sendall(str.encode(msg + "\0"))

    board = ServerBoard()
    jogando = True
    jogador_vez = jogador_1
    oponente_vez = jogador_2
    pontuacao = {jogador_1: 0, jogador_2: 0}
    while jogando:
        mensagem = json.loads(jogadores_conectados[jogador_vez].recv(2048).decode("utf-8"))
        if mensagem["tipo"] == "primeira_escolha":
            process_primeira_escolha(jogador_vez, oponente_vez, mensagem["dados"], board)
        elif mensagem["tipo"] == "segunda_escolha":
            acertou = process_segunda_escolha(jogador_vez, oponente_vez, mensagem["dados"], board, pontuacao)
            if acertou is False:
                oponente_vez, jogador_vez = jogador_vez, oponente_vez
                primeira_escolha = None
                segunda_escolha = None
            elif acertou is True:
                primeira_escolha = None
                segunda_escolha = None

        if len(board.acertos) == NUM_LINHAS**2:
            fim_de_jogo = json.dumps(
                {
                    "tipo": "fim_do_jogo",
                    "dados": {
                        "pontuacao": {
                            jogador_1: pontuacao[jogador_1],
                            jogador_2: pontuacao[jogador_2],
                        }
                    },
                }
            )
            jogadores_conectados[jogador_1].sendall(str.encode(fim_de_jogo + "\0"))
            jogadores_conectados[jogador_2].sendall(str.encode(fim_de_jogo + "\0"))
            jogando = False


if __name__ == "__main__":
    main()
