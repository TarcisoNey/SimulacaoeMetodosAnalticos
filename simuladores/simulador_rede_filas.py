import math
import random
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


@dataclass
class ParametrosFila:
    id: object
    servidores: int
    capacidade: int
    atendimento_min: float
    atendimento_max: float
    chegada_min: Optional[float] = None
    chegada_max: Optional[float] = None
    primeira_chegada: Optional[float] = None

    @property
    def tem_chegada_externa(self):
        return self.chegada_min is not None and self.chegada_max is not None


class _EstadoFila:
    def __init__(self, params: ParametrosFila):
        self.params = params
        self.n_sistema = 0
        self.servidores_ocupados = 0
        self.partidas_agendadas: List[float] = []
        self.tempo_por_estado = [0.0] * (params.capacidade + 1)
        self.perdidos = 0
        self.proxima_chegada_externa = (
            params.primeira_chegada if params.tem_chegada_externa else math.inf
        )

    def probabilidades(self, tempo_total):
        if tempo_total == 0:
            return [0.0] * len(self.tempo_por_estado)
        return [t / tempo_total for t in self.tempo_por_estado]


Roteamento = Dict[object, List[Tuple[Optional[object], float]]]


class RedeFilas:
    def __init__(
        self,
        filas: List[ParametrosFila],
        roteamento: Roteamento,
        total_numeros_aleatorios: int = 100_000,
        seed=None,
    ):
        self.filas: Dict[object, _EstadoFila] = {p.id: _EstadoFila(p) for p in filas}
        self.roteamento = roteamento
        self.total_numeros_aleatorios = total_numeros_aleatorios
        self.rng = random.Random(seed)
        self.contador = 0
        self.limite_atingido = False
        self.relogio = 0.0

    def _sortear_uniforme(self, a, b):
        x = self.rng.random()
        self.contador += 1
        if self.contador >= self.total_numeros_aleatorios:
            self.limite_atingido = True
        return a + (b - a) * x

    def _escolher_destino(self, fila_id):
        opcoes = self.roteamento.get(fila_id, [(None, 1.0)])
        if len(opcoes) == 1:
            return opcoes[0][0]
        if self.limite_atingido:
            return None
        r = self._sortear_uniforme(0.0, 1.0)
        acumulado = 0.0
        for destino, prob in opcoes:
            acumulado += prob
            if r <= acumulado:
                return destino
        return opcoes[-1][0]

    def _processar_chegada(self, fila: _EstadoFila, tempo_atual):
        p = fila.params
        if fila.n_sistema < p.capacidade:
            fila.n_sistema += 1
            if fila.servidores_ocupados < p.servidores:
                fila.servidores_ocupados += 1
                if not self.limite_atingido:
                    duracao = self._sortear_uniforme(p.atendimento_min, p.atendimento_max)
                    fila.partidas_agendadas.append(tempo_atual + duracao)
        else:
            fila.perdidos += 1

    def simular(self):
        while not self.limite_atingido:
            proximo_tempo = math.inf
            proximo_tipo = None
            proxima_fila_id = None
            proxima_partida_valor = None

            for fila_id, fila in self.filas.items():
                if fila.proxima_chegada_externa < proximo_tempo:
                    proximo_tempo = fila.proxima_chegada_externa
                    proximo_tipo = "chegada_externa"
                    proxima_fila_id = fila_id
                    proxima_partida_valor = None
                for t in fila.partidas_agendadas:
                    if t < proximo_tempo:
                        proximo_tempo = t
                        proximo_tipo = "partida"
                        proxima_fila_id = fila_id
                        proxima_partida_valor = t

            if proximo_tipo is None:
                break

            dt = proximo_tempo - self.relogio
            for fila in self.filas.values():
                fila.tempo_por_estado[fila.n_sistema] += dt
            self.relogio = proximo_tempo

            fila = self.filas[proxima_fila_id]

            if proximo_tipo == "chegada_externa":
                self._processar_chegada(fila, self.relogio)
                if not self.limite_atingido:
                    p = fila.params
                    fila.proxima_chegada_externa = self.relogio + self._sortear_uniforme(
                        p.chegada_min, p.chegada_max
                    )
                else:
                    fila.proxima_chegada_externa = math.inf
            else:
                fila.partidas_agendadas.remove(proxima_partida_valor)
                fila.n_sistema -= 1
                fila.servidores_ocupados -= 1
                if fila.n_sistema > fila.servidores_ocupados:
                    fila.servidores_ocupados += 1
                    if not self.limite_atingido:
                        p = fila.params
                        duracao = self._sortear_uniforme(p.atendimento_min, p.atendimento_max)
                        fila.partidas_agendadas.append(self.relogio + duracao)

                destino = self._escolher_destino(proxima_fila_id)
                if destino is not None:
                    self._processar_chegada(self.filas[destino], self.relogio)

        return self.relatorio()

    def relatorio(self):
        return {
            "tempo_total": self.relogio,
            "numeros_aleatorios_usados": self.contador,
            "filas": {
                fila_id: {
                    "params": fila.params,
                    "tempo_por_estado": fila.tempo_por_estado,
                    "probabilidades": fila.probabilidades(self.relogio),
                    "perdidos": fila.perdidos,
                }
                for fila_id, fila in self.filas.items()
            },
        }


def simular_rede(filas, roteamento, total_numeros_aleatorios=100_000, seed=None):
    rede = RedeFilas(filas, roteamento, total_numeros_aleatorios, seed)
    return rede.simular()


def imprimir_relatorio(relatorio):
    print("=" * 70)
    print("RESULTADO DA SIMULAÇÃO DA REDE DE FILAS")
    print("=" * 70)
    print(f"Tempo global de simulação   : {relatorio['tempo_total']:.4f}")
    print(f"Números aleatórios usados   : {relatorio['numeros_aleatorios_usados']}")
    print()

    perdas_totais = 0
    for fila_id, dados in relatorio["filas"].items():
        p = dados["params"]
        tipo = "externa" if p.tem_chegada_externa else "somente por roteamento interno"
        print("-" * 70)
        print(f"Fila {fila_id}: G/G/{p.servidores}/{p.capacidade}  (chegada: {tipo})")
        print("-" * 70)
        print(f"{'Estado (n)':<12}{'Tempo acumulado':<20}{'Probabilidade':<15}")
        probs = dados["probabilidades"]
        tempos = dados["tempo_por_estado"]
        for n in range(p.capacidade + 1):
            print(f"{n:<12}{tempos[n]:<20.4f}{probs[n]:<15.6f}")
        print(f"{'Soma':<12}{sum(tempos):<20.4f}{sum(probs):<15.6f}")
        print(f"Clientes perdidos nesta fila: {dados['perdidos']}")
        print()
        perdas_totais += dados["perdidos"]

    print("=" * 70)
    print(f"Total de clientes perdidos na rede: {perdas_totais}")
    print(f"Tempo global da simulação          : {relatorio['tempo_total']:.4f}")
    print("=" * 70)


def cenario_tandem():
    filas = [
        ParametrosFila(
            id=1,
            servidores=2,
            capacidade=3,
            atendimento_min=4,
            atendimento_max=5,
            chegada_min=1,
            chegada_max=5,
            primeira_chegada=2.5,
        ),
        ParametrosFila(
            id=2,
            servidores=1,
            capacidade=5,
            atendimento_min=1,
            atendimento_max=3,
        ),
    ]

    roteamento = {
        1: [(2, 1.0)],
        2: [(None, 1.0)],
    }

    return filas, roteamento


def main():
    filas, roteamento = cenario_tandem()
    relatorio = simular_rede(
        filas,
        roteamento,
        total_numeros_aleatorios=100_000,
        seed=42,
    )
    imprimir_relatorio(relatorio)


if __name__ == "__main__":
    main()
