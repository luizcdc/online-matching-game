"""Board for a matching game"""
import pygame
from random import shuffle
from game import constants
pygame.init()
fonte_numeros = pygame.font.SysFont("comicsans", 42)

class Board:
    def __init__(self, position: tuple = constants.BOARD_POS):
        self.cards = []
        self.acertos = []
        for i in range(constants.NUM_LINHAS):
            self.cards.append([])
            for j in range(constants.NUM_LINHAS):
                rect = pygame.Rect(100 + position[0] + j * (Card.size[0] + 10), 25 + position[1] + i * (Card.size[1] + 10), *Card.size)
                self.cards[i].append(Card(rect))
        self.embaralhar_cartas()
        self.posicao = position

    def embaralhar_cartas(self):
        options = [i for i in range(1, constants.NUM_LINHAS ** 2 // 2 + 1)]
        options = options + options
        shuffle(options)
        for i in range(constants.NUM_LINHAS):
            for j in range(constants.NUM_LINHAS):
                self.cards[i][j].numero = options.pop()

    def draw(self, janela, escolhas):
        for i in range(constants.NUM_LINHAS):
            for j in range(constants.NUM_LINHAS):
                self.cards[i][j].draw(janela, self.cards[i][j] in escolhas)

    def click(self, mouse_pos, janela):
        for i in range(constants.NUM_LINHAS):
            for j in range(constants.NUM_LINHAS):
                if self.cards[i][j].rect.collidepoint(mouse_pos):
                    self.cards[i][j].draw(janela, True)
                    return self.cards[i][j]

    def check(self, escolhas):
        if escolhas[0].numero == escolhas[1].numero and escolhas[0] not in self.acertos:
            for i in range(constants.NUM_LINHAS):
                for j in range(constants.NUM_LINHAS):
                    if self.cards[i][j] in escolhas:
                        self.cards[i][j].virada = True
                        self.acertos.append(self.cards[i][j])
            return True
        return False


class Card:
    size = (constants.BOARD_POS[2] // constants.NUM_LINHAS - 60, constants.BOARD_POS[2] // constants.NUM_LINHAS - 60)

    def __init__(self, rect: pygame.Rect, numero: int = 0):
        self.numero = numero
        self.rect = rect
        self.virada = False

    def draw(self, janela, escolhida: bool = False):
        pygame.draw.rect(janela, constants.BRANCO, self.rect, border_radius=10)
        if self.virada:
            pygame.draw.rect(janela, constants.VERDE, self.rect, 2, border_radius=10)
            self.draw_numero(janela)
        elif escolhida:
            pygame.draw.rect(janela, constants.AZUL, self.rect, 2, border_radius=10)
            self.draw_numero(janela)
        else:
            pygame.draw.rect(janela, constants.PRETO, self.rect, 2, border_radius=10)
            self.draw_numero(janela, constants.CINZA)

    def draw_numero(self, janela, color: tuple = constants.PRETO):
        numero_imprimir = fonte_numeros.render(str(self.numero), True, color)
        janela.blit(numero_imprimir, (self.rect.centerx - numero_imprimir.get_width() // 2,
                                      self.rect.centery - numero_imprimir.get_height() // 2))