import json
import socket


class Client:

    def __init__(self, server_ip: str, server_port: int, username: str):
        self.conexao = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_ip = server_ip
        self.server_port = server_port
        self.username = username
        self.conectar()

    def conectar(self):
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
