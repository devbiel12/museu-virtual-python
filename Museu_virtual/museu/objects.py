"""Objetos da cena: malhas 3D genéricas e portas articuladas.

Otimizações desta versão:
- Normais, centros de face e esfera envolvente são calculados uma única vez na
  construção do objeto, nunca por quadro.
- Malhas fechadas ganham orientação coerente e passam a descartar faces
  traseiras na renderização (no busto de Nefertiti isso corta cerca de metade
  dos 894 triângulos por quadro).
- A geometria das portas é reconstruída só quando o ângulo realmente muda.
"""
import math

from .config import (COR_PORTA_FRAME, COR_PORTA_BORDA, COR_PORTA_PAINEL,
                     COR_PORTA_FRISO, COR_PORTA_VIDRO, COR_PORTA_PUXADOR,
                     SUAVIDADE_PORTA)
from .geometry import orientar_malha


class Objeto3D:
    def __init__(self, nome, vertices, faces, pos, escala=(1.0, 1.0, 1.0), rot=(0.0, 0.0, 0.0),
                 cor_base=(160, 160, 160), eh_vidro=False, eh_superficie_arte=False,
                 orientar=True):
        self.nome = nome
        self.vertices = list(vertices)

        # Malha fechada: orienta as faces para fora e libera o descarte traseiro.
        if orientar and not eh_vidro:
            faces, fechada = orientar_malha(self.vertices, faces)
        else:
            faces, fechada = list(faces), False

        self.faces = faces
        self.descartar_traseiras = fechada

        self.pos_base = list(pos)
        self.pos = list(pos)
        self.escala_base = list(escala)
        self.escala = list(escala)
        self.rot_base = list(rot)
        self.rot = list(rot)
        self.cor_base = cor_base
        self.eh_vidro = eh_vidro
        self.eh_superficie_arte = eh_superficie_arte
        self.iluminado = False

        self._precalcular_normais()
        self._precalcular_esfera()

    # -- pré-cálculos ------------------------------------------------------

    def _precalcular_normais(self):
        """Normais e centros de face no espaço local, calculados uma só vez."""
        self.normais_locais = []
        self.centros_locais = []
        for face in self.faces:
            if len(face) < 3:
                self.normais_locais.append((0.0, 1.0, 0.0))
                self.centros_locais.append((0.0, 0.0, 0.0))
                continue

            p0 = self.vertices[face[0]]
            p1 = self.vertices[face[1]]
            p2 = self.vertices[face[2]]
            v1 = (p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2])
            v2 = (p2[0] - p0[0], p2[1] - p0[1], p2[2] - p0[2])
            nx = v1[1] * v2[2] - v1[2] * v2[1]
            ny = v1[2] * v2[0] - v1[0] * v2[2]
            nz = v1[0] * v2[1] - v1[1] * v2[0]
            comprimento = math.sqrt(nx * nx + ny * ny + nz * nz)
            inv = 1.0 / comprimento if comprimento > 1e-8 else 1.0
            self.normais_locais.append((nx * inv, ny * inv, nz * inv))

            n = len(face)
            sx = sy = sz = 0.0
            for indice in face:
                v = self.vertices[indice]
                sx += v[0]
                sy += v[1]
                sz += v[2]
            self.centros_locais.append((sx / n, sy / n, sz / n))

    def _precalcular_esfera(self):
        """Centro e raio da esfera envolvente local (descarte grosseiro rápido)."""
        if not self.vertices:
            self.centro_local = (0.0, 0.0, 0.0)
            self.raio_local = 0.0
            return
        n = len(self.vertices)
        cx = sum(v[0] for v in self.vertices) / n
        cy = sum(v[1] for v in self.vertices) / n
        cz = sum(v[2] for v in self.vertices) / n
        self.centro_local = (cx, cy, cz)
        self.raio_local = max(
            math.sqrt((v[0] - cx) ** 2 + (v[1] - cy) ** 2 + (v[2] - cz) ** 2)
            for v in self.vertices
        )

    def raio_mundo(self):
        return self.raio_local * max(abs(e) for e in self.escala)

    # -- estado ------------------------------------------------------------

    def resetar(self):
        """Volta o objeto para a posição, escala e rotação iniciais."""
        self.pos = list(self.pos_base)
        self.escala = list(self.escala_base)
        self.rot = list(self.rot_base)
        self.iluminado = False


class PortaArticulada:
    """Porta dupla de museu com folhas articuladas, vidro, almofadas e puxadores."""

    def __init__(self, nome, parede_x, abre_para, sentido_abertura_x):
        self.nome = nome
        self.parede_x = parede_x
        self.abre_para = abre_para
        self.sentido_abertura_x = sentido_abertura_x
        self.z_inicio = 2.5
        self.z_fim = 7.0
        self.y_base = -1.2
        self.altura = 4.0
        self.largura_folha = (self.z_fim - self.z_inicio) / 2.0
        self.angulo_atual = 0.0
        self.angulo_alvo = 0.0

        self._cache_angulo = None
        self._cache_elementos = None

        self._limite_aberta = math.radians(65.0)
        self._limite_passagem = math.radians(26.0)
        self._angulo_maximo = math.radians(86.0)

    @property
    def aberta(self):
        return self.angulo_atual >= self._limite_aberta

    @property
    def permite_passagem(self):
        return self.angulo_atual >= self._limite_passagem

    def abrir(self):
        self.angulo_alvo = self._angulo_maximo

    def fechar(self):
        self.angulo_alvo = 0.0

    def atualizar(self, dt):
        """Amortecimento exponencial: mesma suavidade em qualquer taxa de quadros."""
        diff = self.angulo_alvo - self.angulo_atual
        if abs(diff) > 1e-4:
            self.angulo_atual += diff * (1.0 - math.exp(-SUAVIDADE_PORTA * dt))
        elif self.angulo_atual != self.angulo_alvo:
            self.angulo_atual = self.angulo_alvo

    def resetar(self):
        self.angulo_atual = 0.0
        self.angulo_alvo = 0.0
        self._cache_angulo = None

    def bloqueia_passagem(self, z, y):
        return self.y_base <= y <= self.y_base + self.altura and not self.permite_passagem

    def folhas(self):
        """Só os quadriláteros das folhas principais (moldura da porta)."""
        return [elem[0] for elem in self.elementos() if elem[1] == COR_PORTA_FRAME]

    def elementos(self):
        """Geometria 3D das folhas: moldura, almofada, vidro e puxador.

        O resultado é memorizado: enquanto a porta está parada (a maior parte do
        tempo), nenhum seno, cosseno ou lista nova é criado por quadro.
        """
        if self._cache_angulo is not None and abs(self._cache_angulo - self.angulo_atual) < 1e-5:
            return self._cache_elementos

        sin_a = math.sin(self.angulo_atual)
        cos_a = math.cos(self.angulo_atual)
        sx = self.sentido_abertura_x
        parede_x = self.parede_x
        elementos = []

        def calc_vertice(dobradica, sentido, dist, y):
            return (parede_x + sx * dist * sin_a, y, dobradica + sentido * dist * cos_a)

        for dobradica, sentido in ((self.z_inicio, 1.0), (self.z_fim, -1.0)):
            # 1. Moldura principal da folha
            elementos.append(([
                calc_vertice(dobradica, sentido, 0.0, self.y_base),
                calc_vertice(dobradica, sentido, 0.0, self.y_base + self.altura),
                calc_vertice(dobradica, sentido, self.largura_folha, self.y_base + self.altura),
                calc_vertice(dobradica, sentido, self.largura_folha, self.y_base),
            ], COR_PORTA_FRAME, COR_PORTA_BORDA, 2))

            d_min_p, d_max_p = 0.16, self.largura_folha - 0.16

            # 2. Almofada inferior entalhada
            y_inf_b, y_inf_t = self.y_base + 0.20, self.y_base + 1.25
            elementos.append(([
                calc_vertice(dobradica, sentido, d_min_p, y_inf_b),
                calc_vertice(dobradica, sentido, d_min_p, y_inf_t),
                calc_vertice(dobradica, sentido, d_max_p, y_inf_t),
                calc_vertice(dobradica, sentido, d_max_p, y_inf_b),
            ], COR_PORTA_PAINEL, COR_PORTA_FRISO, 1))

            # 3. Painel superior de vidro translúcido
            y_vid_b, y_vid_t = self.y_base + 1.45, self.y_base + self.altura - 0.20
            elementos.append(([
                calc_vertice(dobradica, sentido, d_min_p, y_vid_b),
                calc_vertice(dobradica, sentido, d_min_p, y_vid_t),
                calc_vertice(dobradica, sentido, d_max_p, y_vid_t),
                calc_vertice(dobradica, sentido, d_max_p, y_vid_b),
            ], COR_PORTA_VIDRO, COR_PORTA_FRISO, 1))

            # 4. Puxador vertical em latão
            d_pux_min = self.largura_folha - 0.22
            d_pux_max = self.largura_folha - 0.13
            y_pux_b, y_pux_t = self.y_base + 1.10, self.y_base + 1.95
            elementos.append(([
                calc_vertice(dobradica, sentido, d_pux_min, y_pux_b),
                calc_vertice(dobradica, sentido, d_pux_min, y_pux_t),
                calc_vertice(dobradica, sentido, d_pux_max, y_pux_t),
                calc_vertice(dobradica, sentido, d_pux_max, y_pux_b),
            ], COR_PORTA_PUXADOR, (255, 225, 110), 1))

        self._cache_angulo = self.angulo_atual
        self._cache_elementos = elementos
        return elementos
