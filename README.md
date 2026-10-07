# Simulador de Redes de Filas

Simulador de eventos discretos para redes de filas com qualquer topologia
(tandem, roteamento probabilístico, retroalimentação, filas finitas ou infinitas).

## Como executar

Requer apenas Python 3.8 ou superior, sem bibliotecas externas.

```bash
python3 simulador.py modelo_t1.yml
```

## Arquivo de entrada (.yml)

Mesmo formato do simulador do módulo 3:

- `arrivals`: tempo da primeira chegada externa em cada fila.
- `queues`: para cada fila, `servers`, `capacity` (omitir = infinita),
  `minService`/`maxService` e, se recebe clientes de fora, `minArrival`/`maxArrival`.
- `network`: roteamento (`source`, `target`, `probability`). O que faltar para
  somar 1 em cada fila é a probabilidade de sair do sistema.
- `rndnumbersPerSeed`: quantidade de aleatórios usados na simulação.
- `seeds`: semente do gerador (é usada a primeira da lista).

## Funcionamento

- Eventos: `CHEGADA` (externa) e `SAIDA` (fim de atendimento). No fim do
  atendimento é sorteado o destino do cliente: outra fila (passagem) ou a saída
  do sistema. Um cliente que chega a uma fila cheia é contado como perda.
- A cada evento, o tempo decorrido é somado ao estado atual de todas as filas.
- Aleatórios: Método Congruente Linear `X(i+1) = (a·X(i) + c) mod M`, com
  `a = 1664525`, `c = 1013904223`, `M = 2^32`.
- A simulação termina quando o último aleatório é usado. São exibidos, para cada
  fila, o tempo acumulado e a probabilidade de cada estado e o número de perdas,
  além do tempo global da simulação.

## Arquivos

| Arquivo | Conteúdo |
|---|---|
| `simulador.py` | simulador genérico (entrega do T1) |
| `modelo_t1.yml` | modelo do T1 |
| `resultado_t1.txt` | resultado da simulação do modelo do T1 |
| `simulador_filas.py` | etapa anterior: fila única G/G/c/K |
| `simulador_rede_filas.py` | etapa anterior: duas filas em tandem |

As etapas anteriores foram mantidas como histórico e usam o gerador padrão do
Python (`random`). O `simulador.py` usa o gerador congruente linear.
