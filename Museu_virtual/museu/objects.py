"""Objetos interativos da cena: objetos 3D e portas articuladas."""
import math
from museu.config import *
class Objeto3D:
    def __init__(self, nome, vertices, faces, pos, escala=(1.0, 1.0, 1.0), rot=(0.0, 0.0, 0.0),
                 cor_base=(160, 160, 160), eh_vidro=False, eh_superficie_arte=False):
        self.nome = nome
        self.vertices = vertices
        self.faces = faces
        self.pos_base = list(pos)
        self.pos = list(pos)
        self.escala_base = list(escala)
        self.escala = list(escala)
        self.rot_base = list(rot)
        self.rot = list(rot)
        self.cor_base = cor_base
        self.eh_vidro = eh_vidro
        self.eh_superficie_arte = eh_superficie_arte
        self.iluminado = False # Flag para teste de iluminação binária (Requisito 3.9)

        # Pré-cálculo de normais e centros de faces locais para otimização extrema do render 3D
        self.normais_locais = []
        self.centros_locais = []
        for face in self.faces:
            if len(face) >= 3:
                p0 = self.vertices[face[0]]
                p1 = self.vertices[face[1]]
                p2 = self.vertices[face[2]]
                v1 = (p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2])
                v2 = (p2[0] - p0[0], p2[1] - p0[1], p2[2] - p0[2])
                nx = v1[1]*v2[2] - v1[2]*v2[1]
                ny = v1[2]*v2[0] - v1[0]*v2[2]
                nz = v1[0]*v2[1] - v1[1]*v2[0]
                comprimento = math.sqrt(nx*nx + ny*ny + nz*nz)
                inv_c = 1.0 / comprimento if comprimento > 1e-8 else 1.0
                self.normais_locais.append((nx * inv_c, ny * inv_c, nz * inv_c))
                self.centros_locais.append((
                    (p0[0] + p1[0] + p2[0]) / 3.0,
                    (p0[1] + p1[1] + p2[1]) / 3.0,
                    (p0[2] + p1[2] + p2[2]) / 3.0
                ))
            else:
                self.normais_locais.append((0.0, 1.0, 0.0))
                self.centros_locais.append((0.0, 0.0, 0.0))

    def resetar(self):
        self.pos = list(self.pos_base)
        self.escala = list(self.escala_base)
        self.rot = list(self.rot_base)
        self.iluminado = False


class PortaArticulada:
    """
    Porta dupla monumental de museu de arte/história com folhas articuladas,
    caixilhos em azul-ardósia escuro de galeria, almofadas inferiores entalhadas,
    painéis superiores de vidro translúcido com frisos dourados e puxadores verticais em latão.
    """
    def __init__(self, nome, parede_x, abre_para, sentido_abertura_x):
        self.nome = nome
        self.parede_x = parede_x
        self.abre_para = abre_para
        self.sentido_abertura_x = sentido_abertura_x
        self.z_inicio = 2.5
        self.z_fim = 7.0
        self.y_base = -1.2
        self.altura = 2.8
        self.largura_folha = (self.z_fim - self.z_inicio) / 2.0
        self.angulo_atual = 0.0
        self.angulo_alvo = 0.0

    @property
    def aberta(self):
        """Indica se a porta atingiu a abertura quase completa (para fim de transição)."""
        return self.angulo_atual >= math.radians(65.0)

    @property
    def permite_passagem(self):
        """Indica se a abertura já é suficiente para passagem suave do visitante (sem travar)."""
        return self.angulo_atual >= math.radians(26.0)

    def abrir(self):
        self.angulo_alvo = math.radians(86.0)

    def fechar(self):
        self.angulo_alvo = 0.0

    def atualizar(self, dt):
        """Atualização de rotação com amortecimento suave contínuo (elimina travamentos e trancos)."""
        diff = self.angulo_alvo - self.angulo_atual
        if abs(diff) > 0.001:
            taxa = 1.0 - math.exp(-7.0 * dt)
            self.angulo_atual += diff * taxa
        else:
            self.angulo_atual = self.angulo_alvo

    def resetar(self):
        self.angulo_atual = 0.0
        self.angulo_alvo = 0.0

    def bloqueia_passagem(self, z, y):
        return self.y_base <= y <= self.y_base + self.altura and not self.permite_passagem

    def folhas(self):
        """Retorna os quadriláteros das folhas principais (para compatibilidade)."""
        return [elem[0] for elem in self.elementos() if elem[1] == COR_PORTA_FRAME]

    def elementos(self):
        """
        Gera os elementos arquitetônicos 3D das portas com estética nobre de museu:
        - Moldura principal sólida em tom escuro de galeria
        - Almofada inferior entalhada com friso dourado
        - Painel superior de vidro translúcido com friso dourado
        - Puxadores verticais em latão/ouro polido
        """
        sin_a = math.sin(self.angulo_atual)
        cos_a = math.cos(self.angulo_atual)
        sx = self.sentido_abertura_x
        elementos = []

        def calc_vertice(dobradica, sentido, dist, y):
            x = self.parede_x + sx * dist * sin_a
            z = dobradica + sentido * dist * cos_a
            return (x, y, z)

        for dobradica, sentido in ((self.z_inicio, 1.0), (self.z_fim, -1.0)):
            # 1. Moldura Principal da Folha (madeira laqueada/ardósia escuro de museu)
            v_folha = [
                calc_vertice(dobradica, sentido, 0.0, self.y_base),
                calc_vertice(dobradica, sentido, 0.0, self.y_base + self.altura),
                calc_vertice(dobradica, sentido, self.largura_folha, self.y_base + self.altura),
                calc_vertice(dobradica, sentido, self.largura_folha, self.y_base)
            ]
            elementos.append((v_folha, COR_PORTA_FRAME, COR_PORTA_BORDA, 2))

            # 2. Almofada Inferior Entalhada (boiserie nobre com friso dourado)
            d_min_p, d_max_p = 0.16, self.largura_folha - 0.16
            y_inf_b, y_inf_t = self.y_base + 0.15, self.y_base + 1.05
            v_painel = [
                calc_vertice(dobradica, sentido, d_min_p, y_inf_b),
                calc_vertice(dobradica, sentido, d_min_p, y_inf_t),
                calc_vertice(dobradica, sentido, d_max_p, y_inf_t),
                calc_vertice(dobradica, sentido, d_max_p, y_inf_b)
            ]
            elementos.append((v_painel, COR_PORTA_PAINEL, COR_PORTA_FRISO, 1))

            # 3. Painel Superior de Vidro Translúcido de Museu (com moldura dourada)
            y_vid_b, y_vid_t = self.y_base + 1.20, self.y_base + self.altura - 0.18
            v_vidro = [
                calc_vertice(dobradica, sentido, d_min_p, y_vid_b),
                calc_vertice(dobradica, sentido, d_min_p, y_vid_t),
                calc_vertice(dobradica, sentido, d_max_p, y_vid_t),
                calc_vertice(dobradica, sentido, d_max_p, y_vid_b)
            ]
            elementos.append((v_vidro, COR_PORTA_VIDRO, COR_PORTA_FRISO, 1))

            # 4. Puxador Vertical Tubular de Museu em Latão/Ouro Polido
            d_pux_min = self.largura_folha - 0.22
            d_pux_max = self.largura_folha - 0.13
            y_pux_b = self.y_base + 0.85
            y_pux_t = self.y_base + 1.55
            v_puxador = [
                calc_vertice(dobradica, sentido, d_pux_min, y_pux_b),
                calc_vertice(dobradica, sentido, d_pux_min, y_pux_t),
                calc_vertice(dobradica, sentido, d_pux_max, y_pux_t),
                calc_vertice(dobradica, sentido, d_pux_max, y_pux_b)
            ]
            elementos.append((v_puxador, COR_PORTA_PUXADOR, (255, 225, 110), 1))

        return elementos


# -----------------------------------------------------------------------------
# 5. GERENCIADOR DO MUSEU VIRTUAL 3D (ARQUITETURA COMPLETA)
# -----------------------------------------------------------------------------
