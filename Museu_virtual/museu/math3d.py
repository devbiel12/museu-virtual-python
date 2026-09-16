"""Matemática 3D: vetores, transformações, câmera com cache e projeção perspectiva.

Otimizações desta versão:
- A câmera guarda seno/cosseno de yaw e pitch pré-calculados uma vez por quadro,
  em vez de recalcular quatro funções trigonométricas para cada vértice.
- As projeções devolvem coordenadas em ponto flutuante (sem arredondar para int),
  o que elimina o tremor de 1 pixel durante movimentos lentos da câmera.
- Projeção e transformação em lote, com o laço todo em variáveis locais.
"""
import math

from .config import LARGURA, ALTURA, FOCO, PLANO_PROXIMO

MEIO_X = LARGURA * 0.5
MEIO_Y = ALTURA * 0.5


# -----------------------------------------------------------------------------
# VETORES
# -----------------------------------------------------------------------------

def vet_sub(v1, v2):
    return (v1[0] - v2[0], v1[1] - v2[1], v1[2] - v2[2])


def vet_produto_vetorial(u, v):
    return (
        u[1] * v[2] - u[2] * v[1],
        u[2] * v[0] - u[0] * v[2],
        u[0] * v[1] - u[1] * v[0],
    )


def vet_produto_escalar(u, v):
    return u[0] * v[0] + u[1] * v[1] + u[2] * v[2]


def vet_normalizar(v):
    mag = math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2])
    if mag < 1e-7:
        return (0.0, 1.0, 0.0)
    inv = 1.0 / mag
    return (v[0] * inv, v[1] * inv, v[2] * inv)


def rotacionar_ponto(p, rot):
    """Rotaciona um ponto sequencialmente nos eixos X, Y e Z."""
    x, y, z = p
    rx, ry, rz = rot
    if rx:
        cx, sx = math.cos(rx), math.sin(rx)
        y, z = y * cx - z * sx, y * sx + z * cx
    if ry:
        cy, sy = math.cos(ry), math.sin(ry)
        x, z = x * cy + z * sy, -x * sy + z * cy
    if rz:
        cz, sz = math.cos(rz), math.sin(rz)
        x, y = x * cz - y * sz, x * sz + y * cz
    return (x, y, z)


def transformar_vertice(p, pos, rot, escala):
    """Aplica escala -> rotação -> translação em um vértice local."""
    x = p[0] * escala[0]
    y = p[1] * escala[1]
    z = p[2] * escala[2]
    rx, ry, rz = rotacionar_ponto((x, y, z), rot)
    return (rx + pos[0], ry + pos[1], rz + pos[2])


def transformar_vertices(vertices, pos, rot, escala):
    """Versão em lote de transformar_vertice.

    Quando a rotação é apenas em Y — o caso de praticamente todos os objetos da
    cena — usa um caminho rápido com um único par seno/cosseno para a malha toda.
    """
    sx, sy, sz = escala
    ox, oy, oz = pos
    rx, ry, rz = rot

    if not rx and not rz:
        c = math.cos(ry)
        s = math.sin(ry)
        saida = []
        anexar = saida.append
        for p in vertices:
            x = p[0] * sx
            y = p[1] * sy
            z = p[2] * sz
            anexar((x * c + z * s + ox, y + oy, -x * s + z * c + oz))
        return saida

    return [transformar_vertice(p, pos, rot, escala) for p in vertices]


# -----------------------------------------------------------------------------
# CÂMERA COM CACHE POR QUADRO
# -----------------------------------------------------------------------------

class Camera:
    """Pose da câmera com a trigonometria já resolvida.

    sincronizar() é chamado uma vez por quadro; daí em diante todas as projeções
    reaproveitam os mesmos cossenos e senos.
    """

    __slots__ = ("px", "py", "pz", "yaw", "pitch", "foco",
                 "cos_yaw", "sin_yaw", "cos_pitch", "sin_pitch")

    def __init__(self, pos=(0.0, 0.0, 0.0), yaw=0.0, pitch=0.0, foco=FOCO):
        self.sincronizar(pos, yaw, pitch, foco)

    def sincronizar(self, pos, yaw, pitch, foco=FOCO):
        self.px, self.py, self.pz = pos[0], pos[1], pos[2]
        self.yaw = yaw
        self.pitch = pitch
        self.foco = foco
        self.cos_yaw = math.cos(yaw)
        self.sin_yaw = math.sin(yaw)
        self.cos_pitch = math.cos(pitch)
        self.sin_pitch = math.sin(pitch)

    @property
    def pos(self):
        return (self.px, self.py, self.pz)

    def chave(self):
        """Assinatura arredondada da pose — invalida os caches de quadro."""
        return (round(self.px, 3), round(self.py, 3), round(self.pz, 3),
                round(self.yaw, 4), round(self.pitch, 4))

    # -- espaço de câmera ---------------------------------------------------

    def para_camera(self, ponto):
        dx = ponto[0] - self.px
        dy = ponto[1] - self.py
        dz = ponto[2] - self.pz
        z1 = dx * self.sin_yaw + dz * self.cos_yaw
        return (dx * self.cos_yaw - dz * self.sin_yaw,
                dy * self.cos_pitch - z1 * self.sin_pitch,
                dy * self.sin_pitch + z1 * self.cos_pitch)

    # -- projeção -----------------------------------------------------------

    def projetar(self, ponto):
        """Ponto do mundo -> (x_tela, y_tela, z_camera) ou None se atrás da câmera."""
        dx = ponto[0] - self.px
        dy = ponto[1] - self.py
        dz = ponto[2] - self.pz
        z1 = dx * self.sin_yaw + dz * self.cos_yaw
        z_cam = dy * self.sin_pitch + z1 * self.cos_pitch
        if z_cam <= PLANO_PROXIMO:
            return None
        k = self.foco / z_cam
        return (MEIO_X + (dx * self.cos_yaw - dz * self.sin_yaw) * k,
                MEIO_Y - (dy * self.cos_pitch - z1 * self.sin_pitch) * k,
                z_cam)

    def projetar_lista(self, pontos):
        """Projeta uma malha inteira de uma vez, com tudo em variáveis locais."""
        px, py, pz = self.px, self.py, self.pz
        cy, sy = self.cos_yaw, self.sin_yaw
        cp, sp = self.cos_pitch, self.sin_pitch
        foco = self.foco
        proximo = PLANO_PROXIMO
        mx, my = MEIO_X, MEIO_Y

        saida = []
        anexar = saida.append
        for p in pontos:
            dx = p[0] - px
            dy = p[1] - py
            dz = p[2] - pz
            z1 = dx * sy + dz * cy
            z_cam = dy * sp + z1 * cp
            if z_cam <= proximo:
                anexar(None)
                continue
            k = foco / z_cam
            anexar((mx + (dx * cy - dz * sy) * k,
                    my - (dy * cp - z1 * sp) * k,
                    z_cam))
        return saida

    def projetar_poligono(self, vertices):
        """Projeta um polígono com recorte no plano próximo.

        Retorna (pontos_2d, profundidade_média) ou (None, None) se invisível.
        """
        pontos_camera = [self.para_camera(v) for v in vertices]
        dentro = [p[2] > PLANO_PROXIMO for p in pontos_camera]

        if all(dentro):
            recortado = pontos_camera            # caminho rápido, sem recorte
        elif not any(dentro):
            return None, None
        else:
            recortado = []
            n = len(pontos_camera)
            for i in range(n):
                atual = pontos_camera[i]
                j = (i + 1) % n
                proximo = pontos_camera[j]
                if dentro[i] != dentro[j]:
                    fator = (PLANO_PROXIMO - atual[2]) / (proximo[2] - atual[2])
                    recortado.append((
                        atual[0] + fator * (proximo[0] - atual[0]),
                        atual[1] + fator * (proximo[1] - atual[1]),
                        PLANO_PROXIMO,
                    ))
                if dentro[j]:
                    recortado.append(proximo)
            if len(recortado) < 3:
                return None, None

        foco = self.foco
        pontos_2d = []
        anexar = pontos_2d.append
        soma_z = 0.0
        for x, y, z in recortado:
            k = foco / z
            anexar((MEIO_X + x * k, MEIO_Y - y * k))
            soma_z += z
        return pontos_2d, soma_z / len(recortado)


# -----------------------------------------------------------------------------
# COMPATIBILIDADE COM AS CHAMADAS ANTIGAS (mesma assinatura de antes)
# -----------------------------------------------------------------------------

_camera_compat = Camera()


def _camera_para(cam_pos, cam_yaw, cam_pitch, foco):
    c = _camera_compat
    if (c.px != cam_pos[0] or c.py != cam_pos[1] or c.pz != cam_pos[2]
            or c.yaw != cam_yaw or c.pitch != cam_pitch or c.foco != foco):
        c.sincronizar(cam_pos, cam_yaw, cam_pitch, foco)
    return c


def projetar_para_camera(ponto_mundo, cam_pos, cam_yaw, cam_pitch, foco=FOCO):
    return _camera_para(cam_pos, cam_yaw, cam_pitch, foco).projetar(ponto_mundo)


def transformar_para_camera(ponto_mundo, cam_pos, cam_yaw, cam_pitch):
    return _camera_para(cam_pos, cam_yaw, cam_pitch, FOCO).para_camera(ponto_mundo)


def projetar_poligono_solido(vertices, cam_pos, cam_yaw, cam_pitch, foco=FOCO):
    return _camera_para(cam_pos, cam_yaw, cam_pitch, foco).projetar_poligono(vertices)


# -----------------------------------------------------------------------------
# VISIBILIDADE ENTRE SALAS
# -----------------------------------------------------------------------------

def _setor(x):
    """0 = sala oeste, 1 = sala central, 2 = sala leste."""
    if x < -4.5:
        return 0
    if x > 4.5:
        return 2
    return 1


def linha_desimpedida(cam_pos, alvo_pos, portas=None):
    """True se existe linha de visão direta entre a câmera e o alvo.

    As divisórias ficam em x = ±4.5 e o vão do portal é z ∈ [2.5, 7.0] e
    y ∈ [-1.2, 2.8]. Se a reta cruza a divisória fora do vão — ou dentro dele
    com a porta fechada — a visão está bloqueada.
    """
    x1, y1, z1 = cam_pos[0], cam_pos[1], cam_pos[2]
    x2, y2, z2 = alvo_pos[0], alvo_pos[1], alvo_pos[2]

    # Atalho: câmera e alvo na mesma sala, nenhuma divisória entre eles.
    if _setor(x1) == _setor(x2):
        return True

    for x_wall in (-4.5, 4.5):
        if (x1 < x_wall < x2) or (x2 < x_wall < x1):
            dx = x2 - x1
            if abs(dx) < 1e-9:
                continue
            t = (x_wall - x1) / dx
            z_cross = z1 + t * (z2 - z1)
            y_cross = y1 + t * (y2 - y1)
            if not (2.5 <= z_cross <= 7.0 and -1.2 <= y_cross <= 2.8):
                return False
            if portas:
                porta = min(portas, key=lambda item: abs(item.parede_x - x_wall))
                if porta.bloqueia_passagem(z_cross, y_cross):
                    return False
    return True
