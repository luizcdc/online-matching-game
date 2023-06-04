import json
import socket
import queue


class Client:

    def __init__(self, server_ip: str, server_port: int):
        self.conexao = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_ip = server_ip
        self.server_port = server_port
        self.username = None
        self.fila_recebidos = queue.Queue()
        self.fila_enviar = queue.Queue()
        self.conexao.settimeout(1)
        self.conectar_com_servidor()
        self.fim_de_jogo = False  # o jogo ainda não acabou.

    def conectar_com_servidor(self):
        try:
            self.conexao.connect((self.server_ip, self.server_port))
        except socket.error as e:
            print(f"Não foi possível conectar ao servidor {self.server_ip}:{self.server_port}.")
            raise e

    def thread_cliente(self):
        """Thread que recebe e envia mensagens para o servidor."""
        while not self.fim_de_jogo:
            try:
                reply = json.loads(self.conexao.recv(2048).decode("utf-8"))
                if reply:
                    self.fila_recebidos.put(reply)
                    if reply['tipo'] == "fim_do_jogo":
                        self.fim_de_jogo = True
                        break
            except socket.timeout:
                pass
            try:
                msg = self.fila_enviar.get_nowait()
                if msg:
                    self.conexao.sendall(str.encode(json.dumps(msg)))
            except queue.Empty:
                continue

    def registrar_username(self, username: str) -> bool:
        """Tenta registrar o username no servidor."""
        self.username = username
        self.fila_enviar.put({"tipo": "registrar_jogador", "dados": {"username": self.username}})

        reply = self.fila_recebidos.get(block=True, timeout=15)

        if reply and reply['tipo'] == "jogador_registrado" and reply["dados"]["registrado"] is True:
            return True
        else:
            return False

    def receber_jogador_inicial(self) -> tuple[bool, str] | None:
        """Retorna um bool indicando a ordem dos jogadores e o nome do oponente."""
        try:
            primeiro = self.fila_recebidos.get_nowait()
            if primeiro and primeiro['tipo'] == "ordem_jogadores":
                if primeiro["dados"]["1"] == self.username:
                    sou_primeiro = True
                    nome_oponente = primeiro["dados"]["2"]
                else:
                    sou_primeiro = False
                    nome_oponente = primeiro["dados"]["1"]
                return sou_primeiro, nome_oponente
        except queue.Empty:
            primeiro = None

        self._requeue_caso_fim_do_jogo_else_raise(primeiro)

        return None

    def enviar_primeira_escolha(self, coord_x: int, coord_y: int) -> int:
        """Envia a primeira escolha para o servidor

        Retorna o seu valor, ou None se a escolha tiver sido inválida"""
        self._enviar_escolha("primeira", coord_x, coord_y)

    def enviar_segunda_escolha(self, coord_x: int, coord_y: int) -> int:
        """Envia a segunda carta escolhida para o servidor

        Retorna o seu valor, ou None se a escolha tiver sido inválida"""
        self._enviar_escolha("segunda", coord_x, coord_y)

    def _enviar_escolha(self, num_escolha: str, coord_x, coord_y):
        self.fila_enviar.put({"tipo": f"{num_escolha}_escolha",
                              "dados": {"coluna": coord_x, "linha": coord_y}})

    def confirma_carta_valida(self):
        """Confirma que a carta escolhida foi aceita pelo servidor."""
        try:
            reply = self.fila_recebidos.get_nowait()
            if reply and reply["tipo"] == "carta_valida":
                return reply["dados"]
        except queue.Empty:
            reply = None

        self._requeue_caso_fim_do_jogo_else_raise(reply)

        return None

    def receber_resultado_jogada(self):
        try:
            reply = self.fila_recebidos.get_nowait()
            if reply and reply["tipo"] == "resultado_jogada":
                return reply["dados"]
        except queue.Empty:
            reply = None

        self._requeue_caso_fim_do_jogo_else_raise(reply)

        return None

    def receber_primeira_escolha_oponente(self):
        try:
            reply = self.fila_recebidos.get_nowait()
            if reply and reply["tipo"] == "primeira_escolha_oponente":
                return reply["dados"]
        except queue.Empty:
            reply = None

        self._requeue_caso_fim_do_jogo_else_raise(reply)

        return None

    def receber_segunda_escolha_oponente(self):
        try:
            reply = self.fila_recebidos.get_nowait()
            if reply and reply["tipo"] == "segunda_escolha_oponente":
                return reply["dados"]
        except queue.Empty:
            reply = None

        self._requeue_caso_fim_do_jogo_else_raise(reply)

        return None

    def _requeue_caso_fim_do_jogo_else_raise(self, reply):
        if reply is not None:
            if reply["tipo"] == "fim_do_jogo":
                self.fila_recebidos.put(reply)
            else:
                raise ValueError(f"Reply inesperado: {reply['tipo']}")
