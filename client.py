import json
import socket


class Client:

    def __init__(self, server_ip: str, server_port: int, username: str):
        self.conexao = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_ip = server_ip
        self.server_port = server_port
        self.username = username
        self.conectar_e_registrar()

    def conectar_e_registrar(self):
        try:
            self.conexao.connect((self.server_ip, self.server_port))
        except socket.error as e:
            print(f"Não foi possível conectar ao servidor {self.server_ip}:{self.server_port}.")
            raise e

        self.conexao.send(str.encode(json.dumps({"tipo": "registrar_jogador", "dados": {"username": self.username}})))
        reply = json.loads(self.conexao.recv(2048).decode("utf-8"))
        if reply and reply['tipo'] == "jogador_registrado" and reply["dados"]["registrado"] is True:
            print("Conectado ao servidor.")
            return True
        else:
            print("Não foi possível se conectar usando o nome de usuário fornecido.")
            return False

    def enviar_primeira_escolha(self, coord_x, coord_y):
        return self._enviar_escolha("primeira", coord_x, coord_y)

    def enviar_segunda_escolha(self, coord_x, coord_y):
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

