import heapq
import itertools
import sys


class Aleatorios:
    """Método Congruente Linear: X(i+1) = (a*X(i) + c) mod M."""

    A, C, M = 1664525, 1013904223, 2 ** 32

    def __init__(self, semente, limite):
        self.x = semente
        self.limite = limite
        self.usados = 0

    def uniforme(self, a, b):
        if self.usados == self.limite:
            raise StopIteration  
        self.usados += 1
        self.x = (self.A * self.x + self.C) % self.M
        return a + (b - a) * self.x / self.M


class Fila:
    def __init__(self, nome, cfg):
        self.nome = nome
        self.servidores = cfg["servers"]
        self.capacidade = cfg.get("capacity")  # None = infinita
        self.min_serv, self.max_serv = cfg["minService"], cfg["maxService"]
        self.min_cheg, self.max_cheg = cfg.get("minArrival"), cfg.get("maxArrival")
        self.rotas = []
        self.populacao = 0
        self.perdas = 0
        self.tempos = [0.0]


class Simulador:
    def __init__(self, cfg):
        self.filas = {n: Fila(n, q) for n, q in cfg["queues"].items()}
        for r in cfg.get("network") or []:
            self.filas[r["source"]].rotas.append((r["target"], r["probability"]))
        for f in self.filas.values():  # o que falta para 1 é saída do sistema
            resto = 1 - sum(p for _, p in f.rotas)
            if resto > 1e-9:
                f.rotas.append((None, resto))
        self.rnd = Aleatorios(cfg["seeds"][0], cfg["rndnumbersPerSeed"])
        self.relogio = 0.0
        self.eventos = []
        self.seq = itertools.count()  
        for nome, t in cfg["arrivals"].items():
            self.agenda(t, "CHEGADA", nome)

    def agenda(self, t, tipo, fila):
        heapq.heappush(self.eventos, (t, next(self.seq), tipo, fila))

    def destino(self, f):
        """Sorteia para onde vai o cliente que acabou de ser atendido em f."""
        if len(f.rotas) == 1:
            return f.rotas[0][0]
        u, acum = self.rnd.uniforme(0, 1), 0.0
        for d, p in f.rotas:
            acum += p
            if u < acum:
                return d
        return f.rotas[-1][0]

    def atende(self, f):
        self.agenda(self.relogio + self.rnd.uniforme(f.min_serv, f.max_serv), "SAIDA", f.nome)

    def entra(self, f):
        if f.capacidade is None or f.populacao < f.capacidade:
            f.populacao += 1
            if f.populacao <= f.servidores:
                self.atende(f)
        else:
            f.perdas += 1

    def sai(self, f):
        f.populacao -= 1
        if f.populacao >= f.servidores:
            self.atende(f)

    def executar(self):
        try:
            while self.eventos:
                t, _, tipo, nome = heapq.heappop(self.eventos)
                for f in self.filas.values():  
                    while len(f.tempos) <= f.populacao:
                        f.tempos.append(0.0)
                    f.tempos[f.populacao] += t - self.relogio
                self.relogio = t
                f = self.filas[nome]
                if tipo == "CHEGADA":
                    self.entra(f)
                    self.agenda(t + self.rnd.uniforme(f.min_cheg, f.max_cheg), "CHEGADA", nome)
                else: 
                    d = self.destino(f)
                    self.sai(f)
                    if d is not None:  
                        self.entra(self.filas[d])
        except StopIteration:
            pass

    def relatorio(self):
        for f in self.filas.values():
            k = f"/{f.capacidade}" if f.capacidade is not None else ""
            n_max = f.capacidade if f.capacidade is not None else len(f.tempos) - 1
            f.tempos += [0.0] * (n_max + 1 - len(f.tempos))
            print(f"Fila {f.nome} (G/G/{f.servidores}{k})")
            print(f"{'Estado':>8} {'Tempo acumulado':>18} {'Probabilidade':>15}")
            for n in range(n_max + 1):
                print(f"{n:>8} {f.tempos[n]:>18.4f} {100 * f.tempos[n] / self.relogio:>14.2f}%")
            print(f"Perdas: {f.perdas}\n")
        print(f"Tempo global da simulação: {self.relogio:.4f}")



def _valor(txt):
    txt = txt.strip().strip("'\"")
    for tipo in (int, float):
        try:
            return tipo(txt)
        except ValueError:
            pass
    return txt


def ler_yaml(caminho):
    linhas = []
    with open(caminho, encoding="utf-8") as arq:
        for l in arq:
            l = l.split("#", 1)[0].rstrip()
            if l.strip() and not l.strip().startswith("!"):
                linhas.append(l)

    cfg, secao, item, sub, ind_sub = {}, None, None, None, 0
    for l in linhas:
        ind = len(l) - len(l.lstrip())
        txt = l.strip()
        if ind == 0 and not txt.startswith("-"): 
            chave, _, resto = txt.partition(":")
            secao = chave.strip()
            cfg[secao] = _valor(resto) if resto.strip() else None
            item, sub, ind_sub = None, None, 0
        elif txt.startswith("-"):  
            txt = txt[1:].strip()
            if cfg[secao] is None:
                cfg[secao] = []
            if ":" in txt:
                item = {}
                cfg[secao].append(item)
                chave, _, v = txt.partition(":")
                item[chave.strip()] = _valor(v)
            else:
                cfg[secao].append(_valor(txt))
        elif item is not None:  
            chave, _, v = txt.partition(":")
            item[chave.strip()] = _valor(v)
        else:  
            if cfg[secao] is None:
                cfg[secao] = {}
            chave, _, v = txt.partition(":")
            if v.strip():
                alvo = cfg[secao][sub] if sub is not None and ind > ind_sub else cfg[secao]
                alvo[chave.strip()] = _valor(v)
            else:
                sub, ind_sub = chave.strip(), ind
                cfg[secao][sub] = {}
    return cfg


if __name__ == "__main__":
    sim = Simulador(ler_yaml(sys.argv[1]))
    sim.executar()
    sim.relatorio()
