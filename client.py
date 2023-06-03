import json
import socket


class Client:

    def __init__(self, server_ip: str, server_port: int):
        self.conexao = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_ip = server_ip
        self.server_port = server_port
        self.username = None
        self.conectar_com_servidor()

    def conectar_com_servidor(self):
        try:
            self.conexao.connect((self.server_ip, self.server_port))
        except socket.error as e:
            print(f"Não foi possível conectar ao servidor {self.server_ip}:{self.server_port}.")
            raise e

    def registrar_username(self, username: str):
        self.username = username
        self.conexao.send(str.encode(json.dumps({"tipo": "registrar_jogador", "dados": {"username": self.username}})))
        reply = json.loads(self.conexao.recv(2048).decode("utf-8"))
        if reply and reply['tipo'] == "jogador_registrado" and reply["dados"]["registrado"] is True:
            return True
        else:
            return False

    def receber_jogador_inicial(self) -> tuple[bool, str]:
        """Retorna um bool indicando se o jogador é o primeiro a jogar, e o nome do oponente."""
        primeiro = json.loads(self.conexao.recv(2048).decode("utf-8"))
        if primeiro and primeiro['tipo'] == "ordem_jogadores":
            if primeiro["dados"]["jogador_1"] == self.username:
                sou_primeiro = True
                nome_oponente = primeiro["dados"]["jogador_2"]
            else:
                sou_primeiro = False
                nome_oponente = primeiro["dados"]["jogador_1"]
            return sou_primeiro, nome_oponente

        raise ValueError("O servidor enviou uma resposta de um tipo inesperado.")

    def enviar_primeira_escolha(self, coord_x: int, coord_y: int) -> int:
        """Envia a primeira escolha para o servidor

        Retorna o seu valor, ou None se a escolha tiver sido inválida"""
        return self._enviar_escolha("primeira", coord_x, coord_y)

    def enviar_segunda_escolha(self, coord_x: int, coord_y: int) -> int:
        """Envia a segunda carta escolhida para o servidor

        Retorna o seu valor, ou None se a escolha tiver sido inválida"""
        return self._enviar_escolha("segunda", coord_x, coord_y)

    def _enviar_escolha(self, num_escolha: str, coord_x, coord_y):
        self.conexao.send(str.encode(json.dumps({"tipo": f"{num_escolha}_escolha",
                                                  "dados": {"coluna": coord_x, "linha": coord_y}})))
        reply = json.loads(self.conexao.recv(2048).decode("utf-8"))
        if reply and reply['tipo'] == "carta_valida" and reply["dados"]["valida"] is True:
            return reply["dados"]["valor"]
        else:
            return None

    def receber_resultado_jogada(self):
        reply = json.loads(self.conexao.recv(2048).decode("utf-8"))
        if reply:
            return reply
        else:
            return None

