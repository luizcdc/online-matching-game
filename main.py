# A pygame program for an online matching game
from time import sleep

import pygame
from game.constants import SCREEN_W, SCREEN_H, BOARD_POS, NUM_LINHAS, BRANCO, PRETO, CINZA, AZUL
from game.board import Board
from client import Client
import os

# inicializar pygame e a janela de jogo
pygame.init()
janela = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption("Jogo da Memória Multiplayer")
mesa = Board()

SERVER_IP = "127.0.0.1"
SERVER_PORT = 5555

def desenha_letreiro_superior(janela, message: str = ""):
    fill_superior = pygame.draw.rect(janela, AZUL, (10, 10, SCREEN_W - 20, 50), border_radius=10)
    borda_superior = pygame.draw.rect(janela, PRETO, (10, 10, SCREEN_W - 20, 50), 3, border_radius=10)
    if message:
        fonte = pygame.font.SysFont("comicsans", 30)
        texto = fonte.render(message, 1, PRETO)
        janela.blit(texto, (fill_superior.centerx - texto.get_width() // 2,
                            fill_superior.centery - texto.get_height() // 2))


def desenha_menu_inferior(janela, scores):
    fill_inferior = pygame.draw.rect(janela, AZUL, (0, SCREEN_H - 100, SCREEN_W, 100))
    borda_inferior = pygame.draw.rect(janela, PRETO, (0, SCREEN_H - 100, SCREEN_W, 100), 3)
    fonte = pygame.font.SysFont("comicsans", 30)
    # print score on left side
    score_me = fonte.render("Você: " + str(scores[0]), 1, PRETO)
    janela.blit(score_me, (10, fill_inferior.centery - score_me.get_height() // 2))
    score_them = fonte.render("Oponente: " + str(scores[1]), 1, PRETO)
    janela.blit(score_them, (SCREEN_W - score_them.get_width() - 10,
                             fill_inferior.centery - score_them.get_height() // 2))


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
    escolha_1 = None
    escolha_2 = None
    client = Client(SERVER_IP, SERVER_PORT)
    while username := input("Digite seu nome de usuário para conectar-se ao servidor: "):

        if client.registrar_username(username):
            print(f"Conectado ao servidor como {username}.")
            break
        print("O nome de usuário já está sendo utilizado, tente outro.")
        print()

    my_points = 0
    their_points = 0
    message = "Bom jogo!"
    minha_vez, nome_oponente = client.receber_jogador_inicial()
    print("O jogo irá começar! Quem joga primeiro é {}")
    sleep(5)
    desenhar_janela(janela, message, (escolha_1, escolha_2), (my_points, their_points))
    pygame.time.delay(1000)
    while rodando:
        frame_clock.tick(60)
        desenhar_janela(janela, message, (escolha_1, escolha_2), (my_points, their_points))
        if minha_vez :
            message = "Sua vez!"
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    rodando = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if not escolha_1:
                        escolha = mesa.click(pygame.mouse.get_pos(), janela)
                        if escolha:
                            escolha_1 = escolha
                    elif escolha_1 and not escolha_2:
                        escolha = mesa.click(event.pos, janela)
                        if escolha and escolha != escolha_1 and escolha not in mesa.acertos:
                            escolha_2 = escolha
                            if mesa.check((escolha_1, escolha_2)):
                                my_points += 1
                                pygame.display.update()
                            else:
                                vez = 1
                            escolha_1 = None
                            escolha_2 = None
                        pygame.display.update()
                        pygame.time.delay(1000)
        elif vez == 1:
            message = "Vez do oponente!"
            desenhar_janela(janela, message, (escolha_1, escolha_2), (my_points, their_points))
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    rodando = False

        if len(mesa.acertos) == NUM_LINHAS ** 2:
            if my_points > their_points:
                message = "Você venceu!"
            elif my_points < their_points:
                message = "Você perdeu!"
            else:
                message = "Empate!"
            desenha_letreiro_superior(janela, message)
            pygame.display.update()
            pygame.time.delay(5000)
            rodando = False

    pygame.quit()


if __name__ == "__main__":
    main()
