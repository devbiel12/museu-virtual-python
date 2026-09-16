"""Geometrias estáticas da cena, carregamento de OBJ e orientação de malhas."""
import os
import math
from collections import defaultdict, deque


def carregar_obj(caminho):
    """Lê um arquivo OBJ e retorna (vertices, faces). (None, None) se não existir."""
    vertices = []
    faces = []
    if not os.path.exists(caminho):
        return None, None

    with open(caminho, "r", encoding="utf-8", errors="ignore") as f:
        for linha in f:
            if linha.startswith("v "):
                partes = linha.split()
                vertices.append((float(partes[1]), float(partes[2]), float(partes[3])))
            elif linha.startswith("f "):
                partes = linha.split()[1:]
                indices = [int(p.split("/")[0]) - 1 for p in partes]
                if len(indices) >= 3:
                    faces.append(tuple(indices))
    return vertices, faces


# -----------------------------------------------------------------------------
# ORIENTAÇÃO DE MALHAS (pré-requisito do descarte de faces traseiras)
# -----------------------------------------------------------------------------

def orientar_malha(vertices, faces):
    """Deixa a orientação das faces coerente e voltada para fora.

    Percorre a malha por adjacência de arestas, invertendo a ordem dos vértices
    sempre que dois triângulos vizinhos discordam. Depois usa o volume com sinal
    de cada componente conexo para decidir o lado de fora.

    Retorna (faces_orientadas, confiavel). `confiavel` só é True quando a malha
    é fechada o suficiente para que o descarte de faces traseiras seja seguro —
    ou seja, quando quase toda aresta é compartilhada por exatamente duas faces.
    """
    if not faces:
        return list(faces), False

    arestas = defaultdict(list)
    for indice, face in enumerate(faces):
        n = len(face)
        for k in range(n):
            a, b = face[k], face[(k + 1) % n]
            arestas[(a, b) if a < b else (b, a)].append((indice, a < b))

    pareadas = sum(1 for lista in arestas.values() if len(lista) == 2)
    fechada = pareadas >= 0.9 * len(arestas)
    if not fechada:
        # Malha aberta (planos soltos, molduras): manter como está e desenhar
        # os dois lados, senão faces legítimas sumiriam da tela.
        return list(faces), False

    vizinhos = defaultdict(list)
    for lista in arestas.values():
        if len(lista) != 2:
            continue
        (f1, sentido1), (f2, sentido2) = lista
        precisa_inverter = (sentido1 == sentido2)
        vizinhos[f1].append((f2, precisa_inverter))
        vizinhos[f2].append((f1, precisa_inverter))

    faces_mut = [list(f) for f in faces]
    visitado = [False] * len(faces_mut)

    for semente in range(len(faces_mut)):
        if visitado[semente]:
            continue
        visitado[semente] = True
        componente = [semente]
        fila = deque([semente])
        while fila:
            atual = fila.popleft()
            for vizinho, precisa_inverter in vizinhos[atual]:
                if visitado[vizinho]:
                    continue
                visitado[vizinho] = True
                if precisa_inverter:
                    faces_mut[vizinho].reverse()
                componente.append(vizinho)
                fila.append(vizinho)

        # Volume com sinal: negativo significa malha "virada do avesso".
        volume = 0.0
        for indice in componente:
            face = faces_mut[indice]
            p0 = vertices[face[0]]
            for k in range(1, len(face) - 1):
                p1 = vertices[face[k]]
                p2 = vertices[face[k + 1]]
                volume += (p0[0] * (p1[1] * p2[2] - p1[2] * p2[1])
                           - p0[1] * (p1[0] * p2[2] - p1[2] * p2[0])
                           + p0[2] * (p1[0] * p2[1] - p1[1] * p2[0]))
        if volume < 0.0:
            for indice in componente:
                faces_mut[indice].reverse()

    return [tuple(f) for f in faces_mut], True


def gerar_malha_busto_fallback():
    """Geometria procedural do busto, usada quando o OBJ não é encontrado."""
    verts = [
        # Base e tronco
        (-0.5, 0.0, -0.3), (0.5, 0.0, -0.3), (0.4, 0.6, -0.2), (-0.4, 0.6, -0.2),
        (-0.5, 0.0,  0.3), (0.5, 0.0,  0.3), (0.4, 0.6,  0.2), (-0.4, 0.6,  0.2),
        # Pescoço e queixo
        (-0.2, 0.6, -0.15), (0.2, 0.6, -0.15), (0.2, 1.0, -0.15), (-0.2, 1.0, -0.15),
        (-0.2, 0.6,  0.15), (0.2, 0.6,  0.15), (0.2, 1.0,  0.15), (-0.2, 1.0,  0.15),
        # Cabeça / coroa de Nefertiti
        (-0.35, 1.0, -0.2), (0.35, 1.0, -0.2), (0.45, 1.8, -0.35), (-0.45, 1.8, -0.35),
        (-0.35, 1.0,  0.2), (0.35, 1.0,  0.2), (0.45, 1.8,  0.35), (-0.45, 1.8,  0.35),
        (0.0, 1.9, 0.0)  # topo da coroa
    ]
    faces = [
        (0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (3, 2, 6, 7), (1, 5, 6, 2), (0, 3, 7, 4),
        (8, 9, 10, 11), (12, 15, 14, 13), (8, 12, 13, 9), (11, 10, 14, 15),
        (16, 17, 18, 19), (20, 23, 22, 21), (16, 20, 21, 17), (19, 18, 22, 23),
        (18, 19, 24), (19, 23, 24), (23, 22, 24), (22, 18, 24)
    ]
    return verts, faces


# -----------------------------------------------------------------------------
# MODELOS PRÉ-DEFINIDOS
# -----------------------------------------------------------------------------

# Pedestal instanciável (base larga, coluna e capitel)
VERTICES_PEDESTAL_COMPLETO = [
    # 1. Base inferior larga (0 a 7)
    (-0.9, 0.0, -0.9), ( 0.9, 0.0, -0.9), ( 0.9, 0.3, -0.9), (-0.9, 0.3, -0.9),
    (-0.9, 0.0,  0.9), ( 0.9, 0.0,  0.9), ( 0.9, 0.3,  0.9), (-0.9, 0.3,  0.9),
    # 2. Coluna central (8 a 15)
    (-0.6, 0.3, -0.6), ( 0.6, 0.3, -0.6), ( 0.6, 1.5, -0.6), (-0.6, 1.5, -0.6),
    (-0.6, 0.3,  0.6), ( 0.6, 0.3,  0.6), ( 0.6, 1.5,  0.6), (-0.6, 1.5,  0.6),
    # 3. Capitel superior (16 a 23)
    (-0.8, 1.5, -0.8), ( 0.8, 1.5, -0.8), ( 0.8, 1.7, -0.8), (-0.8, 1.7, -0.8),
    (-0.8, 1.5,  0.8), ( 0.8, 1.5,  0.8), ( 0.8, 1.7,  0.8), (-0.8, 1.7,  0.8)
]
FACES_PEDESTAL_COMPLETO = [
    # Base
    (0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (3, 2, 6, 7), (1, 5, 6, 2), (0, 3, 7, 4),
    # Coluna
    (8, 9, 10, 11), (12, 15, 14, 13), (8, 12, 13, 9), (11, 10, 14, 15), (9, 13, 14, 10), (8, 11, 15, 12),
    # Capitel
    (16, 17, 18, 19), (20, 23, 22, 21), (16, 20, 21, 17), (19, 18, 22, 23), (17, 21, 22, 18), (16, 19, 23, 20)
]

# Moldura 3D de "A Ilha dos Mortos"
VERTICES_MOLDURA_PINTURA = [
    # Moldura externa (0 a 7)
    (-2.8, -1.6, -0.15), ( 2.8, -1.6, -0.15), ( 2.8,  1.6, -0.15), (-2.8,  1.6, -0.15),
    (-2.8, -1.6,  0.10), ( 2.8, -1.6,  0.10), ( 2.8,  1.6,  0.10), (-2.8,  1.6,  0.10),
    # Friso interno de apoio da tela (8 a 11)
    (-2.4, -1.3, 0.05), ( 2.4, -1.3, 0.05), ( 2.4,  1.3, 0.05), (-2.4,  1.3, 0.05),
    # Haste da luminária superior (12 a 15)
    (-0.8, 1.6, 0.0), (0.8, 1.6, 0.0), (0.8, 2.0, 0.5), (-0.8, 2.0, 0.5)
]
FACES_MOLDURA_PINTURA = [
    (0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (3, 2, 6, 7), (1, 5, 6, 2), (0, 3, 7, 4),
    (8, 9, 10, 11),
    (12, 13, 14, 15)
]

# Vitrine de manuscritos com redoma de vidro
VERTICES_VITRINE_MANUSCRITO = [
    # Gabinete inferior de madeira (0 a 7)
    (-1.6, -0.4, -1.0), ( 1.6, -0.4, -1.0), ( 1.6, 1.0, -1.0), (-1.6, 1.0, -1.0),
    (-1.6, -0.4,  1.0), ( 1.6, -0.4,  1.0), ( 1.6, 1.0,  1.0), (-1.6, 1.0,  1.0),
    # Tampo inclinado de apoio ao papiro (8 a 11)
    (-1.4, 1.0, -0.8), ( 1.4, 1.0, -0.8), ( 1.4, 1.3,  0.7), (-1.4, 1.3,  0.7),
    # Hastes laterais (12 a 15)
    (-1.45, 1.0, -0.85), (-1.45, 1.3, 0.75), ( 1.45, 1.0, -0.85), ( 1.45, 1.3, 0.75),
    # Redoma de vidro (16 a 23)
    (-1.5, 1.0, -0.9), ( 1.5, 1.0, -0.9), ( 1.5, 1.7, -0.9), (-1.5, 1.7, -0.9),
    (-1.5, 1.0,  0.9), ( 1.5, 1.0,  0.9), ( 1.5, 1.7,  0.9), (-1.5, 1.7,  0.9)
]
FACES_VITRINE_MANUSCRITO = [
    (0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (3, 2, 6, 7), (1, 5, 6, 2), (0, 3, 7, 4),
    (8, 9, 10, 11),
    (16, 17, 18, 19), (20, 23, 22, 21), (16, 20, 21, 17), (19, 18, 22, 23), (17, 21, 22, 18), (16, 19, 23, 20)
]
FACES_VITRINE_BASE = FACES_VITRINE_MANUSCRITO[:7]
FACES_VITRINE_REDOMA = FACES_VITRINE_MANUSCRITO[7:]


# Folha de papiro apoiada sobre o tampo inclinado: y = 1.16 + 0.20*z,
# com um pequeno afastamento para evitar z-fighting com o tampo.
_PAP_OFFSET_Y = 0.025


def _y_tampo_papiro(z):
    return 1.16 + 0.20 * z + _PAP_OFFSET_Y


VERTICES_PAPIRO_ANI = [
    (-1.10, _y_tampo_papiro(-0.70), -0.70),
    ( 1.10, _y_tampo_papiro(-0.70), -0.70),
    ( 1.10, _y_tampo_papiro( 0.70),  0.70),
    (-1.10, _y_tampo_papiro( 0.70),  0.70),
    # Segunda face com espessura física mínima (~2 cm)
    (-1.10, _y_tampo_papiro(-0.70) + 0.02, -0.70),
    ( 1.10, _y_tampo_papiro(-0.70) + 0.02, -0.70),
    ( 1.10, _y_tampo_papiro( 0.70) + 0.02,  0.70),
    (-1.10, _y_tampo_papiro( 0.70) + 0.02,  0.70)
]
FACES_PAPIRO_ANI = [
    (0, 1, 2, 3), (4, 5, 6, 7),
    (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)
]

# Placa de identificação em bronze (objeto simples, sem partes)
VERTICES_PLACA = [
    (-0.7, -0.25, 0.0), (0.7, -0.25, 0.0), (0.7, 0.25, 0.0), (-0.7, 0.25, 0.0)
]
FACES_PLACA = [(0, 1, 2, 3)]
