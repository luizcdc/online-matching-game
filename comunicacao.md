# Padrões de comunicação entre clientes e o servidor

## Introdução

Este documento define os tipos de mensagens que serão trocadas entre clientes e servidor para comunicar as jogadas e 
atualizar o estado do jogo, tais como os formatos que essas mensagens devem seguir.

## Formato das mensagens

O cliente e o servidor estão continuamente conectados através de um socket TCP. Através desse canal, mensagens são
enviadas e recebidas utilizando o formato JSON.

Toda mensagem tem um campo "tipo" que sinaliza o tipo da mensagem, e um campo "dados" que é um dicionário contendo a 
informação que pretende-se transmitir com a mensagem.

```json
{
    "tipo": "tipo_da_mensagem",
    "data": {
        "campo1": "valor1",
        "campo2": "valor2",
        "campo3": "valor3",
        ...
    }
}
```

## Mensagens

### Registrar jogador

**Descrição:** O cliente envia uma mensagem de conexão para o servidor, contendo o nome do jogador (`nome_do_jogador`) que está se conectando.

**De:** cliente

**Para:** servidor

**Resposta esperada:** [Jogador Registrado](#jogador-registrado)

```json
{
    "tipo": "registrar_jogador",
    "dados": {
        "username": "nome_do_jogador"
    }
}
```

### Jogador registrado

**Descrição:** O servidor responde ao cliente com uma mensagem de confirmação de conexão, retornando se o jogador foi registrado com sucesso ou não.

**De:** servidor

**Para:** cliente

**Resposta esperada:** nenhuma

```json
{
    "tipo": "jogador_registrado",
    "dados": {
        "registrado": true
    }
}
```

### Ordem dos jogadores

**Descrição:** Antes do início do jogo, o servidor envia para cada jogador uma mensagem dizendo qual dos dois jogadores é o primeiro e qual é o segundo a jogar.

**De:** servidor

**Para:** ambos os clientes

**Resposta esperada:** nenhuma

**Variáveis:** username_jogador_1 (string), username_jogador_2 (string)

```json
{
    "tipo": "ordem_jogadores",
    "dados": {
        "1": username_jogador_1,
        "2": username_jogador_2
    }
}
```

### Enviar primeira escolha

**Descrição:** No início de cada turno, o jogador indica a posição da primeira das duas cartas da sua jogada.

**De:** cliente

**Para:** servidor

**Resposta esperada:** [Carta Válida](#carta-válida)

**Variáveis:** i (integer), j (integer)
```json
{
    "tipo": "primeira_escolha",
    "dados": {
        "coluna": i,
        "linha": j
    }
}
```

### Carta válida

**Descrição:** O servidor responde ao cliente com uma mensagem de confirmação da jogada, retornando se a carta escolhida é válida ou não, isto é, se ainda não foi revelada. Se não for válida, o cliente terá que escolher outra carta.

**De:** servidor

**Para:** cliente

**Resposta esperada:** nenhuma

**Variáveis:** is_valida (boolean), valor_da_carta (integer)

```json
{
    "tipo": "carta_valida",
    "dados": {
        "valida": is_valida,
        "valor": valor_da_carta
    }
}
```

### Primeira escolha do oponente

**Descrição:** O servidor envia para o cliente a primeira escolha do oponente, para que o cliente possa atualizar o estado do jogo.

**De:** servidor

**Para:** cliente

**Resposta esperada:** nenhuma

```json
{
    "tipo": "primeira_escolha_oponente",
    "dados": {
        "coluna": i,
        "linha": j,
        "valor": valor_da_carta
    }
}
```

### Segunda escolha

**Descrição:** Após enviar uma primeira carta válida, o jogador indica a posição da segunda das duas cartas da sua jogada.

**De:** cliente

**Para:** servidor

**Resposta esperada:** [Carta Válida](#carta-válida)

**Variáveis:** i (integer), j (integer)

```json
{
    "tipo": "segunda_escolha",
    "dados": {
        "coluna": i,
        "linha": j
    }
}
```

### Segunda escolha do oponente

**Descrição:** O servidor envia para o cliente a segunda escolha do oponente, para que o cliente possa atualizar o estado do jogo.

**De:** servidor

**Para:** cliente

**Resposta esperada:** nenhuma

**Variáveis:** coluna (integer), linha (integer), valor_da_carta (integer)

```json
{
    "tipo": "segunda_escolha_oponente",
    "dados": {
        "x": i,
        "y": j,
        "valor": valor_da_carta
    }
}
```

### Resultado da jogada

**Descrição:** O servidor envia para ambos os clientes o resultado da jogada, para que o cliente possam atualizar o estado do jogo.

**De:** servidor

**Para:** ambos os clientes

**Resposta esperada:** nenhuma

**Variáveis:** username (string), nova_pontuacao (integer), acertou (boolean)

```json
{
    "tipo": "resultado_jogada",
    "dados": {
        "username": username,
        "pontuacao": nova_pontuacao,
        "acertou": acertou
    }
}
```

### Fim do jogo

**Descrição:** O servidor envia para ambos os clientes uma mensagem indicando que o jogo terminou, e qual foi o resultado.

**De:** servidor

**Para:** ambos os clientes

**Resposta esperada:** nenhuma

**Variáveis:** username_jogador_1 (string), username_jogador_2 (string), pontuacao1 (integer), pontuacao2 (integer)

```json
{
    "tipo": "fim_do_jogo",
    "dados": {
        "pontuacao": {
            username_jogador_1: pontuacao1,
            username_jogador_2: pontuacao2
        }
    }
}
```

