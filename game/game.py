from typing import Optional

from .board import Board, ServerBoard, Card
from enum import Enum


class GameState(str, Enum):
    # Este jogador está escolhendo a primeira carta
    ESCOLHENDO_1 = "escolher_primeira"
    # Este jogador está escolhendo a segunda carta
    ESCOLHENDO_2 = "escolher_segunda"
    # O oponente está escolhendo a primeira carta
    OPONENTE_ESCOLHENDO_1 = "oponente_escolhendo_primeira"
    # O oponente está escolhendo a segunda carta
    OPONENTE_ESCOLHENDO_2 = "oponente_escolhendo_segunda"
    # O servidor está validando a primeira carta escolhida pelo jogador
    VERIFICANDO_1 = "verificando_primeira"
    # O servidor está validando a primeira carta escolhida pelo jogador
    VERIFICANDO_2 = "verificando_segunda"
    # O servidor está verificando se as cartas escolhidas pelo jogador são iguais
    AGUARDANDO_MEU_RESULTADO = "aguardar_resultado_minha_jogada"
    # O servidor está verificando se as cartas escolhidas pelo oponente são iguais
    AGUARDANDO_RESULTADO_OPONENTE = "aguardar_resultado_oponente"


class Game:
    def __init__(self, client=False):
        self.is_client = client
        self.player_names: list[str] = []
        self.pontuacao: list[int] = [0, 0]
        self.escolhas_atuais: list[Card] = []
        self.board = Board() if client else ServerBoard()
        self.minha_vez = False if client else None
        self.game_state: Optional[GameState] = None

    def add_player(self, player_name: str):
        assert len(self.player_names) < 2, "Já existem dois jogadores"
        self.player_names.append(player_name)

    def start_game(self, *, eu_comeco: Optional[bool] = None):
        assert len(self.player_names) == 2, "Não há dois jogadores"
        assert self.is_client or eu_comeco is None
        if self.is_client:
            self.minha_vez = eu_comeco
        self.resetar_jogada()

    def resetar_jogada(self):
        self.escolhas_atuais = []
        if self.is_client:
            self.game_state = GameState.ESCOLHENDO_1 if self.minha_vez else GameState.OPONENTE_ESCOLHENDO_1

    def iniciar_vez_oponente(self):
        assert self.is_client
        assert self.minha_vez
        self.minha_vez = False
        self.game_state = GameState.OPONENTE_ESCOLHENDO_1
        self.resetar_jogada()

    def iniciar_minha_vez(self):
        assert self.is_client
        assert self.minha_vez is False
        self.minha_vez = True
        self.game_state = GameState.ESCOLHENDO_1
        self.resetar_jogada()

    def pontuar(self, *, player: int, new_points: int = None):
        """Pontua e permite que o jogador faça outra jogada"""
        assert player in {0, 1}
        assert self.is_client is False or new_points is not None
        self.pontuacao[player] = new_points if self.is_client else self.pontuacao[player] + 1
        self.escolhas_atuais[0].virada = self.escolhas_atuais[1].virada = True
        self.escolhas_atuais[0].player_1_virou = self.escolhas_atuais[1].player_1_virou = player == 0
        self.resetar_jogada()

    def escolha_1_foi_feita(self):
        return self.escolhas_atuais and len(self.escolhas_atuais) == 1

    def escolha_2_foi_feita(self):
        return self.escolhas_atuais and len(self.escolhas_atuais) == 2
