# A pygame program for an online matching game
import queue

import pygame
from _thread import start_new_thread
from game.constants import (
    SCREEN_W,
    SCREEN_H,
    BOARD_POS,
    NUM_LINHAS,
    BRANCO,
    PRETO,
    CINZA,
    AZUL,
)
from game.board import Board, Card
from client import Client
from game.game import Game, GameState

SERVER_IP = "127.0.0.1"
SERVER_PORT = 5555


def desenha_letreiro_superior(janela, message: str = ""):
    fill_superior = pygame.draw.rect(
        janela, AZUL, (10, 10, SCREEN_W - 20, 50), border_radius=10
    )
    borda_superior = pygame.draw.rect(
        janela, PRETO, (10, 10, SCREEN_W - 20, 50), 3, border_radius=10
    )
    if message:
        fonte = pygame.font.SysFont("comicsans", 30)
        texto = fonte.render(message, True, PRETO)
        janela.blit(
            texto,
            (
                fill_superior.centerx - texto.get_width() // 2,
                fill_superior.centery - texto.get_height() // 2,
            ),
        )


def desenha_menu_inferior(janela, scores):
    fill_inferior = pygame.draw.rect(janela, AZUL, (0, SCREEN_H - 100, SCREEN_W, 100))
    borda_inferior = pygame.draw.rect(
        janela, PRETO, (0, SCREEN_H - 100, SCREEN_W, 100), 3
    )
    fonte = pygame.font.SysFont("comicsans", 30)
    # print score on left side
    score_me = fonte.render(f"Você: {str(scores[0])}", 1, PRETO)
    janela.blit(score_me, (10, fill_inferior.centery - score_me.get_height() // 2))
    score_them = fonte.render(f"Oponente: {str(scores[1])}", 1, PRETO)
    janela.blit(
        score_them,
        (
            SCREEN_W - score_them.get_width() - 10,
            fill_inferior.centery - score_them.get_height() // 2,
        ),
    )


def desenha_tabuleiro(janela, game):
    area_tabuleiro = pygame.draw.rect(janela, CINZA, BOARD_POS, border_radius=10)
    game.board.draw(janela, game.escolhas_atuais)


def desenhar_janela(janela, message: str, game: Game):
    janela.fill(BRANCO)
    desenha_letreiro_superior(janela, message)
    desenha_tabuleiro(janela, game)
    desenha_menu_inferior(janela, tuple(game.pontuacao))
    pygame.display.update()


frame_clock = pygame.time.Clock()


def main():
    rodando = True
    client = Client(SERVER_IP, SERVER_PORT)
    game = Game(client=True)
    start_new_thread(client.thread_cliente, ())
    while username := input(
        "Digite seu nome de usuário para conectar-se ao servidor: "
    ):
        print(f"Tentando registrar com username {username}")
        if client.registrar_username(username):
            print(f"Conectado ao servidor como {username}.")
            game.add_player(username)
            break
        print("O nome de usuário já está sendo utilizado, tente outro.")
        print()

    # inicializar pygame e a janela de jogo
    pygame.init()
    janela = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption(
        f"Jogo da Memória Multiplayer: conectado como {username}."
    )

    print("Bom jogo!")

    while True:
        reply_jogador_inicial = client.receber_jogador_inicial()
        if reply_jogador_inicial is not None:
            break

    minha_vez, nome_oponente = reply_jogador_inicial
    game.add_player(nome_oponente)
    game.start_game(eu_comeco=minha_vez)

    message = f"O jogo irá começar! Quem joga primeiro é {username if minha_vez else nome_oponente}"
    desenhar_janela(janela, message, game)
    pygame.time.delay(2000)

    message = "Sua vez!" if game.minha_vez else "Vez do oponente!"

    escolha_temp = None
    while rodando:
        frame_clock.tick(60)
        if client.fim_de_jogo:
            try:
                fim_de_jogo = client.fila_recebidos.get_nowait()
                if fim_de_jogo["tipo"] != "fim_do_jogo":
                    continue
                fim_de_jogo = fim_de_jogo["dados"]["pontuacao"]
                game.pontuacao = [
                    fim_de_jogo[username],
                    fim_de_jogo[nome_oponente],
                ]
                if game.pontuacao[0] > game.pontuacao[1]:
                    message = "Você venceu"
                elif game.pontuacao[0] < game.pontuacao[1]:
                    message = "Você perdeu"
                else:
                    message = "Empate"
                message += " por desistência!" if game.pontuacao[1] < 0 else "!"

                game.pontuacao[1] = max(0, game.pontuacao[1])
                desenhar_janela(
                    janela,
                    message,
                    game,
                )
                pygame.display.update()
                pygame.time.delay(5000)
                rodando = False
                break
            except queue.Empty:
                continue

        desenhar_janela(janela, message, game)
        if game.minha_vez:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    rodando = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    escolha_temp = processar_click_mouse(
                        client, janela, game, escolha_temp, event
                    )
            if game.game_state == GameState.VERIFICANDO_1:
                escolha_temp, message = verifica_primeira_escolha_valida(
                    client, game, escolha_temp, message
                )
            elif game.game_state == GameState.VERIFICANDO_2:
                escolha_temp, message = verifica_segunda_escolha_valida(
                    client, game, escolha_temp, message
                )
            elif game.game_state == GameState.AGUARDANDO_MEU_RESULTADO:
                message = processar_resultado_rodada(client, game, message)

        else:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    rodando = False
            if game.game_state == GameState.OPONENTE_ESCOLHENDO_1:
                jogada_oponente = client.receber_primeira_escolha_oponente()
                if jogada_oponente is not None:
                    game.escolhas_atuais.append(
                        game.board.cards[jogada_oponente["coluna"]][
                            jogada_oponente["linha"]
                        ]
                    )
                    game.escolhas_atuais[0].numero = jogada_oponente["valor"]
                    game.game_state = GameState.OPONENTE_ESCOLHENDO_2
            elif game.game_state == GameState.OPONENTE_ESCOLHENDO_2:
                jogada_oponente = client.receber_segunda_escolha_oponente()
                if jogada_oponente is not None:
                    game.escolhas_atuais.append(
                        game.board.cards[jogada_oponente["coluna"]][
                            jogada_oponente["linha"]
                        ]
                    )
                    game.escolhas_atuais[1].numero = jogada_oponente["valor"]
                    game.game_state = GameState.AGUARDANDO_RESULTADO_OPONENTE
            elif game.game_state == GameState.AGUARDANDO_RESULTADO_OPONENTE:
                message = processar_resultado_rodada(client, game, message)

    pygame.quit()


def verifica_segunda_escolha_valida(
    client: Client, game: Game, escolha_temp: Card, message: str
):
    confirmacao = client.confirma_carta_valida()
    if confirmacao is not None:
        if confirmacao["valida"]:
            game.escolhas_atuais.append(escolha_temp)
            escolha_temp.numero = confirmacao["valor"]
            game.game_state = GameState.AGUARDANDO_MEU_RESULTADO
        else:
            game.game_state = GameState.ESCOLHENDO_2
            message = "Carta inválida! Escolha outra."
        escolha_temp = None
    return escolha_temp, message


def verifica_primeira_escolha_valida(
    client: Client, game: Game, escolha_temp: Card, message: str
):
    confirmacao = client.confirma_carta_valida()
    if confirmacao is not None:
        if confirmacao["valida"]:
            game.escolhas_atuais.append(escolha_temp)
            escolha_temp.numero = confirmacao["valor"]
            game.game_state = GameState.ESCOLHENDO_2
        else:
            game.resetar_jogada()
            message = "Carta inválida! Escolha outra."
        escolha_temp = None
    return escolha_temp, message


def processar_click_mouse(
    client: Client,
    janela: pygame.display,
    game: Game,
    escolha_temp: Card,
    event: pygame.event,
):
    if not game.escolha_1_foi_feita() and game.game_state == GameState.ESCOLHENDO_1:
        escolha_temp = game.board.click(pygame.mouse.get_pos(), janela)
        if escolha_temp:
            client.enviar_primeira_escolha(escolha_temp.x, escolha_temp.y)
            game.game_state = GameState.VERIFICANDO_1
    elif (
        game.escolha_1_foi_feita()
        and not game.escolha_2_foi_feita()
        and game.game_state == GameState.ESCOLHENDO_2
    ):
        escolha_temp = game.board.click(event.pos, janela)
        if escolha_temp:
            client.enviar_segunda_escolha(escolha_temp.x, escolha_temp.y)
            game.game_state = GameState.VERIFICANDO_2
    return escolha_temp


def processar_resultado_rodada(client: Client, game: Game, message: str):
    pygame.time.delay(1000)
    resultado = client.receber_resultado_jogada()
    if resultado is not None:
        if resultado["username"] == game.player_names[0]:
            if resultado["acertou"]:
                message = "Você acertou! Jogue novamente!"
                game.pontuar(
                    player=0, new_points=resultado["pontuacao"]
                )  # Já reseta a jogada
            else:
                message = "Você errou! Vez do oponente!"
                game.pontuacao[0] = resultado["pontuacao"]
                game.iniciar_vez_oponente()
        elif resultado["acertou"]:
            game.pontuar(
                player=1, new_points=resultado["pontuacao"]
            )  # Já reseta a jogada
            message = "O oponente acertou! Ele jogará novamente!"
        else:
            message = "O oponente errou! Sua vez!"
            game.pontuacao[1] = resultado["pontuacao"]
            game.iniciar_minha_vez()
    return message


if __name__ == "__main__":
    main()