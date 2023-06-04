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
from game.board import Board
from client import Client


mesa = Board()

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


def desenha_tabuleiro(janela, escolhas):
    area_tabuleiro = pygame.draw.rect(janela, CINZA, BOARD_POS, border_radius=10)
    mesa.draw(janela, escolhas)


def desenhar_janela(janela, message: str, escolhas: tuple, scores: tuple):
    janela.fill(BRANCO)
    desenha_letreiro_superior(janela, message)
    desenha_tabuleiro(janela, escolhas)
    desenha_menu_inferior(janela, scores)
    pygame.display.update()


frame_clock = pygame.time.Clock()


def main():
    rodando = True
    escolha_temp = None
    escolha_1 = None
    escolha_2 = None
    client = Client(SERVER_IP, SERVER_PORT)
    start_new_thread(client.thread_cliente, ())
    estado_jogo = "registrando_username"
    while username := input(
        "Digite seu nome de usuário para conectar-se ao servidor: "
    ):
        print(f"Tentando registrar com username {username}")
        if client.registrar_username(username):
            print(f"Conectado ao servidor como {username}.")
            estado_jogo = "esperando_oponente"
            break
        print("O nome de usuário já está sendo utilizado, tente outro.")
        print()

    # inicializar pygame e a janela de jogo
    pygame.init()
    janela = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption(
        f"Jogo da Memória Multiplayer: conectado como {username}."
    )

    my_points = 0
    their_points = 0
    print("Bom jogo!")

    while True:
        reply_jogador_inicial = client.receber_jogador_inicial()
        if reply_jogador_inicial is not None:
            break
    minha_vez, nome_oponente = reply_jogador_inicial

    message = f"O jogo irá começar! Quem joga primeiro é {username if minha_vez else nome_oponente}"
    desenhar_janela(janela, message, (escolha_1, escolha_2), (my_points, their_points))
    pygame.time.delay(2000)

    estado_jogo = "escolher_primeira" if minha_vez else "oponente_escolhendo_primeira"
    message = "Sua vez!" if minha_vez else "Vez do oponente!"

    while rodando:
        frame_clock.tick(60)
        if client.fim_de_jogo:
            try:
                fim_de_jogo = client.fila_recebidos.get_nowait()
                if fim_de_jogo["tipo"] != "fim_do_jogo":
                    continue
                fim_de_jogo = fim_de_jogo["dados"]["pontuacao"]
                my_points, their_points = (
                    fim_de_jogo[username],
                    fim_de_jogo[nome_oponente],
                )
                if my_points > their_points:
                    message = "Você venceu"
                elif my_points < their_points:
                    message = "Você perdeu"
                else:
                    message = "Empate"
                message += " por desistência!" if their_points < 0 else "!"

                desenhar_janela(
                    janela,
                    message,
                    (escolha_1, escolha_2),
                    (my_points, max(0, their_points)),
                )
                # desenha_letreiro_superior(janela, message)  # TODO: ver se desenhar a janela inteira dá certo
                pygame.display.update()
                pygame.time.delay(5000)
                rodando = False
                break
            except queue.Empty:
                continue

        desenhar_janela(
            janela, message, (escolha_1, escolha_2), (my_points, their_points)
        )
        if minha_vez:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    rodando = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    (
                        escolha_1,
                        escolha_2,
                        escolha_temp,
                        estado_jogo,
                        minha_vez,
                        my_points,
                    ) = processar_click_mouse(
                        client,
                        janela,
                        escolha_1,
                        escolha_2,
                        escolha_temp,
                        estado_jogo,
                        event,
                        minha_vez,
                        my_points,
                    )
            if estado_jogo == "verificando_primeira":
                (
                    escolha_1,
                    escolha_temp,
                    estado_jogo,
                    message,
                ) = verifica_primeira_escolha_valida(
                    client, escolha_1, escolha_temp, estado_jogo, message
                )
            elif estado_jogo == "verificando_segunda":
                (
                    escolha_2,
                    escolha_temp,
                    estado_jogo,
                    message,
                ) = verifica_segunda_escolha_valida(
                    client, escolha_2, escolha_temp, estado_jogo, message
                )
            elif estado_jogo == "aguardar_resultado_minha_jogada":
                (
                    escolha_1,
                    escolha_2,
                    message,
                    minha_vez,
                    my_points,
                    their_points,
                    estado_jogo,
                ) = processar_resultado_rodada(
                    client,
                    escolha_1,
                    escolha_2,
                    message,
                    minha_vez,
                    my_points,
                    their_points,
                    username,
                    estado_jogo,
                )

        else:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    rodando = False
            if estado_jogo == "oponente_escolhendo_primeira":
                jogada_oponente = client.receber_primeira_escolha_oponente()
                if jogada_oponente is not None:
                    escolha_1 = mesa.cards[jogada_oponente["coluna"]][
                        jogada_oponente["linha"]
                    ]
                    escolha_1.numero = jogada_oponente["valor"]
                    estado_jogo = "oponente_escolhendo_segunda"
            elif estado_jogo == "oponente_escolhendo_segunda":
                jogada_oponente = client.receber_segunda_escolha_oponente()
                if jogada_oponente is not None:
                    escolha_2 = mesa.cards[jogada_oponente["coluna"]][
                        jogada_oponente["linha"]
                    ]
                    escolha_2.numero = jogada_oponente["valor"]
                    estado_jogo = "aguardar_resultado_oponente"
            elif estado_jogo == "aguardar_resultado_oponente":
                (
                    escolha_1,
                    escolha_2,
                    message,
                    minha_vez,
                    my_points,
                    their_points,
                    estado_jogo,
                ) = processar_resultado_rodada(
                    client,
                    escolha_1,
                    escolha_2,
                    message,
                    minha_vez,
                    my_points,
                    their_points,
                    username,
                    estado_jogo,
                )

    pygame.quit()


def verifica_segunda_escolha_valida(
    client, escolha_2, escolha_temp, estado_jogo, message
):
    confirmacao = client.confirma_carta_valida()
    if confirmacao is not None:
        if confirmacao["valida"]:
            escolha_2 = escolha_temp
            escolha_2.numero = confirmacao["valor"]
            estado_jogo = "aguardar_resultado_minha_jogada"
        else:
            estado_jogo = "escolher_segunda"
            message = "Carta inválida! Escolha outra."
        escolha_temp = None
    return escolha_2, escolha_temp, estado_jogo, message


def verifica_primeira_escolha_valida(
    client, escolha_1, escolha_temp, estado_jogo, message
):
    confirmacao = client.confirma_carta_valida()
    if confirmacao is not None:
        if confirmacao["valida"]:
            escolha_1 = escolha_temp
            escolha_1.numero = confirmacao["valor"]
            estado_jogo = "escolher_segunda"
        else:
            estado_jogo = "escolher_primeira"
            message = "Carta inválida! Escolha outra."
        escolha_temp = None
    return escolha_1, escolha_temp, estado_jogo, message


def processar_click_mouse(
    client,
    janela,
    escolha_1,
    escolha_2,
    escolha_temp,
    estado_jogo,
    event,
    minha_vez,
    my_points,
):
    if not escolha_1 and estado_jogo == "escolher_primeira":
        escolha_temp = mesa.click(pygame.mouse.get_pos(), janela)
        if escolha_temp:
            client.enviar_primeira_escolha(escolha_temp.x, escolha_temp.y)
            estado_jogo = "verificando_primeira"
    elif escolha_1 and not escolha_2 and estado_jogo == "escolher_segunda":
        escolha_temp = mesa.click(event.pos, janela)
        if escolha_temp:
            client.enviar_segunda_escolha(escolha_temp.x, escolha_temp.y)
            estado_jogo = "verificando_segunda"
    return escolha_1, escolha_2, escolha_temp, estado_jogo, minha_vez, my_points


def processar_resultado_rodada(
    client,
    escolha_1,
    escolha_2,
    message,
    minha_vez,
    my_points,
    their_points,
    username,
    estado_jogo,
):
    pygame.time.delay(1000)
    resultado = client.receber_resultado_jogada()
    if resultado is not None:
        if resultado["username"] == username:
            my_points = resultado["pontuacao"]
            if resultado["acertou"]:
                escolha_1.virada = escolha_2.virada = True
                message = "Você acertou! Jogue novamente!"
                estado_jogo = "escolher_primeira"
            else:
                message = "Você errou! Vez do oponente!"
                minha_vez = False
                estado_jogo = "oponente_escolhendo_primeira"
        else:
            their_points = resultado["pontuacao"]
            if resultado["acertou"]:
                escolha_1.virada = escolha_2.virada = True
                message = "O oponente acertou! Ele jogará novamente!"
                estado_jogo = "oponente_escolhendo_primeira"
            else:
                message = "O oponente errou! Sua vez!"
                minha_vez = True
                estado_jogo = "escolher_primeira"
        escolha_1, escolha_2 = None, None
    return (
        escolha_1,
        escolha_2,
        message,
        minha_vez,
        my_points,
        their_points,
        estado_jogo,
    )


if __name__ == "__main__":
    main()
