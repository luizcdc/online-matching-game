from typing import Optional

from .board import Board, ServerBoard
from enum import Enum


class GameState(Enum, str):
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

    def __init__(self, client = False):
        self.is_client = client
        self.player_names: list[str] = []
        self.pontuacao: list[int] = [0, 0]
        self.escolhas_atuais: list[tuple[int, int]] = []
        self.board = Board() if client else ServerBoard()
        self.minha_vez = False if client else None
        self.game_state = GameState.REGISTRANDO if client else None

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

    def desfazer_segunda(self):
        assert self.is_client
        assert len(self.escolhas_atuais) == 2
        self.escolhas_atuais.pop()
        if self.is_client:
            self.game_state = GameState.ESCOLHENDO_2 if self.minha_vez else GameState.OPONENTE_ESCOLHENDO_2

    def pontuar(self, *, player: int):
        """Pontua e permite que o jogador faça outra jogada"""
        assert player in {0, 1}
        self.pontuacao[player] += 1
        self.resetar_jogada()