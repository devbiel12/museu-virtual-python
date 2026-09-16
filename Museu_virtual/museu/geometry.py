"""Geometrias, carregamento de OBJ e modelos estáticos da cena."""
import os
import math
def carregar_obj(caminho):
    """Carrega uma malha 3D simples em formato OBJ."""
    vertices = []
    faces = []
    if not os.path.exists(caminho):
        return None, None

    with open(caminho, "r", encoding="utf-8", errors="ignore") as f:
        for linha in f:
            linha = linha.strip()
            if linha.startswith("v "):
                partes = linha.split()
                vertices.append((float(partes[1]), float(partes[2]), float(partes[3])))
            elif linha.startswith("f "):
                partes = linha.split()[1:]
                indices = [int(p.split("/")[0]) - 1 for p in partes]
                if len(indices) >= 3:
                    faces.append(tuple(indices))
    return vertices, faces

def gerar_malha_busto_fallback():
    """Gera uma geometria de busto escultórico procedural caso o OBJ não esteja presente."""
    verts = [
        # Base e tronco
        (-0.5, 0.0, -0.3), (0.5, 0.0, -0.3), (0.4, 0.6, -0.2), (-0.4, 0.6, -0.2),
        (-0.5, 0.0,  0.3), (0.5, 0.0,  0.3), (0.4, 0.6,  0.2), (-0.4, 0.6,  0.2),
        # Pescoço e queixo
        (-0.2, 0.6, -0.15), (0.2, 0.6, -0.15), (0.2, 1.0, -0.15), (-0.2, 1.0, -0.15),
        (-0.2, 0.6,  0.15), (0.2, 0.6,  0.15), (0.2, 1.0,  0.15), (-0.2, 1.0,  0.15),
        # Cabeça / Coroa de Nefertiti
        (-0.35, 1.0, -0.2), (0.35, 1.0, -0.2), (0.45, 1.8, -0.35), (-0.45, 1.8, -0.35),
        (-0.35, 1.0,  0.2), (0.35, 1.0,  0.2), (0.45, 1.8,  0.35), (-0.45, 1.8,  0.35),
        ( 0.0,  1.9,  0.0) # Topo da coroa
    ]
    faces = [
        (0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (3, 2, 6, 7), (1, 5, 6, 2), (0, 3, 7, 4),
        (8, 9, 10, 11), (12, 15, 14, 13), (8, 12, 13, 9), (11, 10, 14, 15),
        (16, 17, 18, 19), (20, 23, 22, 21), (16, 20, 21, 17), (19, 18, 22, 23),
        (18, 19, 24), (19, 23, 24), (23, 22, 24), (22, 18, 24)
    ]
    return verts, faces

# Definição do Modelo do Pedestal (Base, Coluna e Capitel - Instanciável)
VERTICES_PEDESTAL_COMPLETO = [
    # 1. Base Inferior Larga (0 a 7)
    (-0.9, 0.0, -0.9), ( 0.9, 0.0, -0.9), ( 0.9, 0.3, -0.9), (-0.9, 0.3, -0.9),
    (-0.9, 0.0,  0.9), ( 0.9, 0.0,  0.9), ( 0.9, 0.3,  0.9), (-0.9, 0.3,  0.9),
    # 2. Coluna Central (8 a 15)
    (-0.6, 0.3, -0.6), ( 0.6, 0.3, -0.6), ( 0.6, 1.5, -0.6), (-0.6, 1.5, -0.6),
    (-0.6, 0.3,  0.6), ( 0.6, 0.3,  0.6), ( 0.6, 1.5,  0.6), (-0.6, 1.5,  0.6),
    # 3. Capitel Superior (16 a 23)
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

# Definição do Modelo da Moldura 3D de A Ilha dos Mortos (Sala 1)
VERTICES_MOLDURA_PINTURA = [
    # Moldura Externa (0 a 7)
    (-2.8, -1.6, -0.15), ( 2.8, -1.6, -0.15), ( 2.8,  1.6, -0.15), (-2.8,  1.6, -0.15),
    (-2.8, -1.6,  0.10), ( 2.8, -1.6,  0.10), ( 2.8,  1.6,  0.10), (-2.8,  1.6,  0.10),
    # Friso Interno de Apoio da Tela (8 a 11)
    (-2.4, -1.3, 0.05), ( 2.4, -1.3, 0.05), ( 2.4,  1.3, 0.05), (-2.4,  1.3, 0.05),
    # Haste da Luminária Superior (12 a 15)
    (-0.8, 1.6, 0.0), (0.8, 1.6, 0.0), (0.8, 2.0, 0.5), (-0.8, 2.0, 0.5)
]
FACES_MOLDURA_PINTURA = [
    # Borda externa
    (0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (3, 2, 6, 7), (1, 5, 6, 2), (0, 3, 7, 4),
    # Tela frontal
    (8, 9, 10, 11),
    # Luminária superior
    (12, 13, 14, 15)
]

# Definição do Modelo da Vitrine e Suporte de Manuscritos (Sala 3)
VERTICES_VITRINE_MANUSCRITO = [
    # Mesa de Madeira / Gabinete Inferior (0 a 7)
    (-1.6, -0.4, -1.0), ( 1.6, -0.4, -1.0), ( 1.6, 1.0, -1.0), (-1.6, 1.0, -1.0),
    (-1.6, -0.4,  1.0), ( 1.6, -0.4,  1.0), ( 1.6, 1.0,  1.0), (-1.6, 1.0,  1.0),
    # Tampo Inclinado de Apoio ao Papiro (8 a 11)
    (-1.4, 1.0, -0.8), ( 1.4, 1.0, -0.8), ( 1.4, 1.3,  0.7), (-1.4, 1.3,  0.7),
    # Cilindros/Hastes Laterais do Papiro (12 a 15)
    (-1.45, 1.0, -0.85), (-1.45, 1.3, 0.75), ( 1.45, 1.0, -0.85), ( 1.45, 1.3, 0.75),
    # Cúpula / Redoma de Vidro Transparente 3D (16 a 23)
    (-1.5, 1.0, -0.9), ( 1.5, 1.0, -0.9), ( 1.5, 1.7, -0.9), (-1.5, 1.7, -0.9),
    (-1.5, 1.0,  0.9), ( 1.5, 1.0,  0.9), ( 1.5, 1.7,  0.9), (-1.5, 1.7,  0.9)
]
FACES_VITRINE_MANUSCRITO = [
    # Gabinete de Madeira
    (0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (3, 2, 6, 7), (1, 5, 6, 2), (0, 3, 7, 4),
    # Tampo Inclinado com Manuscrito
    (8, 9, 10, 11),
    # Redoma de Vidro (Faces translúcidas)
    (16, 17, 18, 19), (20, 23, 22, 21), (16, 20, 21, 17), (19, 18, 22, 23), (17, 21, 22, 18), (16, 19, 23, 20)
]

# Folha fina do papiro, fisicamente apoiada sobre o tampo inclinado da vitrine.
# A geometria permanece fixa no mundo 3D; a câmera nunca altera sua transformação.
# O eixo Z acompanha a inclinação do tampo e Y é calculado pela relação:
#     y = 1.16 + 0.20*z
# com um pequeno afastamento para evitar z-fighting.
_PAP_OFFSET_Y = 0.025

def _y_tampo_papiro(z):
    return 1.16 + 0.20 * z + _PAP_OFFSET_Y

VERTICES_PAPIRO_ANI = [
    (-1.10, _y_tampo_papiro(-0.70), -0.70),
    ( 1.10, _y_tampo_papiro(-0.70), -0.70),
    ( 1.10, _y_tampo_papiro( 0.70),  0.70),
    (-1.10, _y_tampo_papiro( 0.70),  0.70),
    # Segunda face com espessura física mínima (~2 cm).
    (-1.10, _y_tampo_papiro(-0.70) + 0.02, -0.70),
    ( 1.10, _y_tampo_papiro(-0.70) + 0.02, -0.70),
    ( 1.10, _y_tampo_papiro( 0.70) + 0.02,  0.70),
    (-1.10, _y_tampo_papiro( 0.70) + 0.02,  0.70)
]
FACES_PAPIRO_ANI = [
    (0, 1, 2, 3), (4, 5, 6, 7),
    (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)
]

# Objeto Simples sem partes: Placa de Identificação de Bronze (Requisito 3.2)
VERTICES_PLACA = [
    (-0.7, -0.25, 0.0), (0.7, -0.25, 0.0), (0.7, 0.25, 0.0), (-0.7, 0.25, 0.0)
]
FACES_PLACA = [(0, 1, 2, 3)]


# -----------------------------------------------------------------------------
# 4. CLASSE DE OBJETO 3D E COMPOSIÇÃO DE CENA
# -----------------------------------------------------------------------------
