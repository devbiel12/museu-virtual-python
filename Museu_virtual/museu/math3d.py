"""Matemática 3D, vetores, câmera e projeção em perspectiva."""
import math
from .config import LARGURA, ALTURA

def vet_sub(v1, v2):
    return (v1[0] - v2[0], v1[1] - v2[1], v1[2] - v2[2])

def vet_produto_vetorial(u, v):
    return (
        u[1]*v[2] - u[2]*v[1],
        u[2]*v[0] - u[0]*v[2],
        u[0]*v[1] - u[1]*v[0]
    )

def vet_produto_escalar(u, v):
    return u[0]*v[0] + u[1]*v[1] + u[2]*v[2]

def vet_normalizar(v):
    mag = math.sqrt(v[0]**2 + v[1]**2 + v[2]**2)
    if mag < 1e-7:
        return (0.0, 1.0, 0.0)
    return (v[0]/mag, v[1]/mag, v[2]/mag)

def rotacionar_ponto(p, rot):
    """Aplica rotação sequencial nos eixos X, Y e Z."""
    x, y, z = p
    rx, ry, rz = rot
    if rx != 0:
        cx, sx = math.cos(rx), math.sin(rx)
        y, z = y*cx - z*sx, y*sx + z*cx
    if ry != 0:
        cy, sy = math.cos(ry), math.sin(ry)
        x, z = x*cy + z*sy, -x*sy + z*cy
    if rz != 0:
        cz, sz = math.cos(rz), math.sin(rz)
        x, y = x*cz - y*sz, x*sz + y*cz
    return (x, y, z)

def transformar_vertice(p, pos, rot, escala):
    """Transformação local do objeto: Escala -> Rotação -> Translação no mundo."""
    x = p[0] * escala[0]
    y = p[1] * escala[1]
    z = p[2] * escala[2]
    rx, ry, rz = rotacionar_ponto((x, y, z), rot)
    return (rx + pos[0], ry + pos[1], rz + pos[2])

def projetar_para_camera(ponto_mundo, cam_pos, cam_yaw, cam_pitch, foco=620.0):
    """
    Transforma coordenadas do Mundo para o Espaço da Câmera (com rotação Yaw e Pitch)
    e em seguida aplica a Projeção Perspectiva para Coordenadas de Tela (2D).
    Retorna: (x_tela, y_tela, z_cam) ou None caso o ponto esteja atrás da câmera.
    """
    # 1. Translação em relação à câmera
    dx = ponto_mundo[0] - cam_pos[0]
    dy = ponto_mundo[1] - cam_pos[1]
    dz = ponto_mundo[2] - cam_pos[2]

    # 2. Rotação de Yaw (olhar esquerda / direita em torno do eixo Y)
    cy, sy = math.cos(cam_yaw), math.sin(cam_yaw)
    x1 = dx * cy - dz * sy
    z1 = dx * sy + dz * cy
    y1 = dy

    # 3. Rotação de Pitch (olhar cima / baixo em torno do eixo X)
    cp, sp = math.cos(cam_pitch), math.sin(cam_pitch)
    y_cam = y1 * cp - z1 * sp
    z_cam = y1 * sp + z1 * cp
    x_cam = x1

    # Plano de corte próximo (near clipping plane)
    if z_cam <= 0.25:
        return None

    tela_x = (LARGURA / 2.0) + (foco * x_cam / z_cam)
    tela_y = (ALTURA / 2.0)  - (foco * y_cam / z_cam)
    return (int(tela_x), int(tela_y), z_cam)

def transformar_para_camera(ponto_mundo, cam_pos, cam_yaw, cam_pitch):
    """Transforma um ponto do mundo para coordenadas da câmera."""
    dx = ponto_mundo[0] - cam_pos[0]
    dy = ponto_mundo[1] - cam_pos[1]
    dz = ponto_mundo[2] - cam_pos[2]

    cy, sy = math.cos(cam_yaw), math.sin(cam_yaw)
    x_cam = dx * cy - dz * sy
    z_cam = dx * sy + dz * cy

    cp, sp = math.cos(cam_pitch), math.sin(cam_pitch)
    y_cam = dy * cp - z_cam * sp
    z_cam = dy * sp + z_cam * cp
    return (x_cam, y_cam, z_cam)

def projetar_poligono_solido(vertices, cam_pos, cam_yaw, cam_pitch, foco=620.0):
    """Recorta e projeta um polígono 3D sem descartar faces parcialmente visíveis."""
    pontos_camera = [
        transformar_para_camera(v, cam_pos, cam_yaw, cam_pitch)
        for v in vertices
    ]
    plano_proximo = 0.25
    recortado = []

    for atual, proximo in zip(pontos_camera, pontos_camera[1:] + pontos_camera[:1]):
        atual_dentro = atual[2] > plano_proximo
        proximo_dentro = proximo[2] > plano_proximo

        if atual_dentro != proximo_dentro:
            fator = (plano_proximo - atual[2]) / (proximo[2] - atual[2])
            recortado.append(tuple(
                atual[i] + fator * (proximo[i] - atual[i])
                for i in range(3)
            ))
        if proximo_dentro:
            recortado.append(proximo)

    if len(recortado) < 3:
        return None, None

    pontos_2d = [
        (
            int((LARGURA / 2.0) + foco * ponto[0] / ponto[2]),
            int((ALTURA / 2.0) - foco * ponto[1] / ponto[2])
        )
        for ponto in recortado
    ]
    profundidade = sum(ponto[2] for ponto in recortado) / len(recortado)
    return pontos_2d, profundidade

def linha_desimpedida(cam_pos, alvo_pos, portas=None):
    """
    Verifica se a linha de visão entre a câmera e o alvo NÃO é bloqueada
    pelas paredes divisórias sólidas do museu (x = -4.5 e x = +4.5).
    Retorna True se a visão é livre (sem obstáculo); False caso contrário.
    Os portais/arcos de passagem estão no intervalo z ∈ [2.5, 7.0], y ∈ [-1.2, 2.8].
    """
    x1, y1, z1 = cam_pos[0], cam_pos[1], cam_pos[2]
    x2, y2, z2 = alvo_pos[0], alvo_pos[1], alvo_pos[2]
    for x_wall in (-4.5, 4.5):
        if (x1 < x_wall < x2) or (x2 < x_wall < x1):
            dx = x2 - x1
            if abs(dx) < 1e-9:
                continue
            t = (x_wall - x1) / dx
            z_cross = z1 + t * (z2 - z1)
            y_cross = y1 + t * (y2 - y1)
            # Portal: z ∈ [2.5, 7.0] e y ∈ [-1.2, 2.8]
            if not (2.5 <= z_cross <= 7.0 and -1.2 <= y_cross <= 2.8):
                return False
            if portas:
                porta = min(portas, key=lambda item: abs(item.parede_x - x_wall))
                if porta.bloqueia_passagem(z_cross, y_cross):
                    return False
    return True


# -----------------------------------------------------------------------------
# 3. CARREGADOR DE MODELOS 3D E MALHAS GEOMÉTRICAS
# -----------------------------------------------------------------------------
