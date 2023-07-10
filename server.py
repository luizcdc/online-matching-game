import contextlib
import json
import socket
import sys
from _thread import start_new_thread
from time import sleep

from game.board import ServerBoard
from game.constants import NUM_LINHAS
from game.game import Game


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


def process_primeira_escolha(jogador, oponente, dados, game: Game):
    coord_x = dados["coluna"]
    coord_y = dados["linha"]

    if (
        not game.escolha_1_foi_feita()
        and (escolha := game.board.get_card_by_pos(coord_x, coord_y))
        and not escolha.virada
    ):
        game.escolhas.append(escolha)
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


def process_segunda_escolha(jogador, oponente, dados, game: Game) -> bool | None:
    num_jogador = game.player_names.index(jogador)
    coord_x = dados["coluna"]
    coord_y = dados["linha"]

    if (
        game.escolha_1_foi_feita()
        and not game.escolha_2_foi_feita()
        and (escolha := game.board.get_card_by_pos(coord_x, coord_y))
        and game.escolhas[0] is not escolha
        and not escolha.virada
    ):
        game.escolhas.append(escolha)

        reply = json.dumps({"tipo": "carta_valida", "dados": {"valida": True, "valor": escolha.numero}})
        jogadores_conectados[jogador].sendall(str.encode(reply + "\0"))
        reply_oponente = json.dumps(
            {
                "tipo": "segunda_escolha_oponente",
                "dados": {"coluna": coord_x, "linha": coord_y, "valor": escolha.numero},
            }
        )
        jogadores_conectados[oponente].sendall(str.encode(reply_oponente + "\0"))

        acertou = game.board.check(game.escolhas)
        if acertou:
            game.pontuar(player=num_jogador)
        else:
            game.resetar_jogada()
        reply = json.dumps(
            {
                "tipo": "resultado_jogada",
                "dados": {
                    "username": jogador,
                    "pontuacao": game.pontuacao[num_jogador],
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


jogadores_conectados = {}


def main():
    if len(sys.argv) != 3:
        porta = 5555
        addr = "127.0.0.1"
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
        sleep(0.5)

    sleep(1)
    game = Game()
    game.player_names = list(jogadores_conectados.keys())
    msg = json.dumps({"tipo": "ordem_jogadores", "dados": {"1": game.player_names[0], "2": game.player_names[1]}})
    for jogador in jogadores_conectados:
        jogadores_conectados[jogador].sendall(str.encode(msg + "\0"))

    jogando = True
    jogador_vez = game.player_names[0]
    oponente_vez = game.player_names[1]
    try:
        while jogando:
            mensagem = json.loads(jogadores_conectados[jogador_vez].recv(2048).decode("utf-8"))
            if mensagem["tipo"] == "primeira_escolha":
                process_primeira_escolha(jogador_vez, oponente_vez, mensagem["dados"], game)
            elif mensagem["tipo"] == "segunda_escolha":
                acertou = process_segunda_escolha(jogador_vez, oponente_vez, mensagem["dados"], game)
                if acertou is False:
                    oponente_vez, jogador_vez = jogador_vez, oponente_vez

            if len(game.board.acertos) == NUM_LINHAS**2:
                sleep(3)
                fim_de_jogo = json.dumps(
                    {
                        "tipo": "fim_do_jogo",
                        "dados": {
                            "pontuacao": {
                                game.player_names[0]: game.pontuacao[0],
                                game.player_names[1]: game.pontuacao[1],
                            }
                        },
                    }
                )
                jogadores_conectados[game.player_names[0]].sendall(str.encode(fim_de_jogo + "\0"))
                jogadores_conectados[game.player_names[1]].sendall(str.encode(fim_de_jogo + "\0"))
                jogando = False
    except ConnectionResetError:
        disconnected_message = json.dumps({"tipo": "oponente_desistiu"})
        with contextlib.suppress(ConnectionResetError):
            jogadores_conectados[oponente_vez].sendall(str.encode(disconnected_message + "\0"))
        with contextlib.suppress(ConnectionResetError):
            jogadores_conectados[jogador_vez].sendall(str.encode(disconnected_message + "\0"))



if __name__ == "__main__":
    main()
