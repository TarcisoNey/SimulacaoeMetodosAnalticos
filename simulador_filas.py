import random
import math


class ResultadoSimulacao:
    def __init__(self, capacidade):
        self.tempo_por_estado = [0.0] * (capacidade + 1)
        self.perdidos = 0
        self.tempo_total = 0.0
        self.numeros_aleatorios_usados = 0

    def probabilidades(self):
        if self.tempo_total == 0:
            return [0.0] * len(self.tempo_por_estado)
        return [t / self.tempo_total for t in self.tempo_por_estado]


def simular_fila_ggck(
    servidores,
    capacidade,
    chegada_min, chegada_max,
    atendimento_min, atendimento_max,
    primeira_chegada,
    total_numeros_aleatorios=100_000,
    seed=None,
):
    rng = random.Random(seed)

    contador = [0]
    limite_atingido = [False]

    def sortear_uniforme(a, b):
        x = rng.random()
        contador[0] += 1
        if contador[0] >= total_numeros_aleatorios:
            limite_atingido[0] = True
        return a + (b - a) * x

    resultado = ResultadoSimulacao(capacidade)

    relogio = 0.0
    n_sistema = 0
    servidores_ocupados = 0
    partidas_agendadas = []

    proxima_chegada = primeira_chegada

    while not limite_atingido[0]:
        proxima_partida = min(partidas_agendadas) if partidas_agendadas else math.inf
        if proxima_chegada <= proxima_partida:
            instante_evento = proxima_chegada
            tipo_evento = "chegada"
        else:
            instante_evento = proxima_partida
            tipo_evento = "partida"

        resultado.tempo_por_estado[n_sistema] += instante_evento - relogio
        relogio = instante_evento

        if tipo_evento == "chegada":
            if n_sistema < capacidade:
                n_sistema += 1
                if servidores_ocupados < servidores:
                    servidores_ocupados += 1
                    if not limite_atingido[0]:
                        tempo_atendimento = sortear_uniforme(atendimento_min, atendimento_max)
                        partidas_agendadas.append(relogio + tempo_atendimento)
            else:
                resultado.perdidos += 1

            if not limite_atingido[0]:
                tempo_entre_chegadas = sortear_uniforme(chegada_min, chegada_max)
                proxima_chegada = relogio + tempo_entre_chegadas
            else:
                proxima_chegada = math.inf

        else:
            partidas_agendadas.remove(instante_evento)
            n_sistema -= 1
            servidores_ocupados -= 1
            if n_sistema > servidores_ocupados:
                servidores_ocupados += 1
                if not limite_atingido[0]:
                    tempo_atendimento = sortear_uniforme(atendimento_min, atendimento_max)
                    partidas_agendadas.append(relogio + tempo_atendimento)

    resultado.tempo_total = relogio
    resultado.numeros_aleatorios_usados = contador[0]
    return resultado



def imprimir_resultado(titulo, servidores, capacidade, resultado):
    print("=" * 60)
    print(titulo)
    print("=" * 60)
    print(f"Servidores (c)            : {servidores}")
    print(f"Capacidade (K)             : {capacidade}")
    print(f"Números aleatórios usados : {resultado.numeros_aleatorios_usados}")
    print(f"Tempo total de simulação  : {resultado.tempo_total:.4f}")
    print(f"Clientes perdidos          : {resultado.perdidos}")
    print()
    print(f"{'Estado (n)':<12}{'Tempo acumulado':<20}{'Probabilidade':<15}")
    print("-" * 47)
    probs = resultado.probabilidades()
    for n in range(capacidade + 1):
        print(f"{n:<12}{resultado.tempo_por_estado[n]:<20.4f}{probs[n]:<15.6f}")
    print(f"{'Soma':<12}{sum(resultado.tempo_por_estado):<20.4f}{sum(probs):<15.6f}")
    print()


def imprimir_resumo(nome, servidores, capacidade, resultado):
    probs = resultado.probabilidades()
    print(f"--- {nome} ---")
    print(f"c = {servidores}, K = {capacidade}")
    print(f"Tempo total de simulação: {resultado.tempo_total:.4f}")
    print(f"Números aleatórios usados: {resultado.numeros_aleatorios_usados}")
    print(f"Clientes perdidos: {resultado.perdidos}")
    for n in range(capacidade + 1):
        print(f"  P(N={n}) = {probs[n]:.6f}  (tempo acumulado = {resultado.tempo_por_estado[n]:.4f})")
    print()


def main():
    CAPACIDADE = 5
    CHEGADA_MIN, CHEGADA_MAX = 3, 5
    ATENDIMENTO_MIN, ATENDIMENTO_MAX = 4, 5
    PRIMEIRA_CHEGADA = 3.0
    TOTAL_NUMEROS_ALEATORIOS = 100_000
    SEED = 42

    resultado_1_servidor = simular_fila_ggck(
        servidores=1,
        capacidade=CAPACIDADE,
        chegada_min=CHEGADA_MIN, chegada_max=CHEGADA_MAX,
        atendimento_min=ATENDIMENTO_MIN, atendimento_max=ATENDIMENTO_MAX,
        primeira_chegada=PRIMEIRA_CHEGADA,
        total_numeros_aleatorios=TOTAL_NUMEROS_ALEATORIOS,
        seed=SEED,
    )

    resultado_2_servidores = simular_fila_ggck(
        servidores=2,
        capacidade=CAPACIDADE,
        chegada_min=CHEGADA_MIN, chegada_max=CHEGADA_MAX,
        atendimento_min=ATENDIMENTO_MIN, atendimento_max=ATENDIMENTO_MAX,
        primeira_chegada=PRIMEIRA_CHEGADA,
        total_numeros_aleatorios=TOTAL_NUMEROS_ALEATORIOS,
        seed=SEED,
    )

    imprimir_resultado("Cenário 1: G/G/1/5 (1 atendente, capacidade 5)", 1, CAPACIDADE, resultado_1_servidor)
    imprimir_resultado("Cenário 2: G/G/2/5 (2 atendentes, capacidade 5)", 2, CAPACIDADE, resultado_2_servidores)

    print("#" * 60)
    print("RESUMO PARA A ATIVIDADE")
    print("#" * 60)
    print()
    imprimir_resumo("G/G/1/5", 1, CAPACIDADE, resultado_1_servidor)
    imprimir_resumo("G/G/2/5", 2, CAPACIDADE, resultado_2_servidores)


if __name__ == "__main__":
    main()
