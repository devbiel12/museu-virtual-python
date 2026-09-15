"""
Script de preparação e download de assets para o Museu Virtual 3D (AP1).
Baixa as imagens das obras em alta resolução e a malha 3D do Busto de Nefertiti,
otimizando-a para execução leve em 60 FPS com Pygame.
"""

import os
import sys
import struct
import json
import urllib.request
import pygame

ASSETS_DIR = os.path.dirname(os.path.abspath(__file__))

URL_TOTENINSEL = "https://upload.wikimedia.org/wikipedia/commons/6/65/Arnold_B%C3%B6cklin_-_Die_Toteninsel_III_%28Alte_Nationalgalerie%2C_Berlin%29.jpg"
URL_PAPYRUS = "https://upload.wikimedia.org/wikipedia/commons/c/c9/Papyrus_of_Ani_BM_Sheet_12.jpg"
URL_NEFERTITI = "https://raw.githubusercontent.com/mrdoob/three.js/dev/examples/models/gltf/Nefertiti/Nefertiti.glb"

PATH_TOTENINSEL = os.path.join(ASSETS_DIR, "toteninsel.jpg")
PATH_PAPYRUS = os.path.join(ASSETS_DIR, "papyrus_ani.jpg")
PATH_NEFERTITI_OBJ = os.path.join(ASSETS_DIR, "nefertiti_bust.obj")

def baixar_arquivo(url, destino):
    print(f"Baixando: {url} -> {os.path.basename(destino)}...")
    req = urllib.request.Request(url, headers={"User-Agent": "VirtualMuseumEduProject/1.0 (academic computer graphics project)"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        with open(destino, "wb") as f:
            f.write(resp.read())
    print(f"Salvo: {destino} ({os.path.getsize(destino)} bytes)")

def processar_nefertiti():
    if os.path.exists(PATH_NEFERTITI_OBJ) and os.path.getsize(PATH_NEFERTITI_OBJ) > 1000:
        print("nefertiti_bust.obj já existe. Pulando conversão.")
        return

    print("Baixando e processando modelo 3D do Busto de Nefertiti...")
    req = urllib.request.Request(URL_NEFERTITI, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = resp.read()

    # Parser simples de GLB
    c0_len, _ = struct.unpack("<II", data[12:20])
    gltf = json.loads(data[20:20+c0_len].decode("utf-8"))
    c1_offset = 20 + c0_len
    c1_data = data[c1_offset+8:]

    prim = gltf["meshes"][0]["primitives"][0]
    pos_acc = gltf["accessors"][prim["attributes"]["POSITION"]]
    pos_bv = gltf["bufferViews"][pos_acc["bufferView"]]
    idx_acc = gltf["accessors"][prim["indices"]]
    idx_bv = gltf["bufferViews"][idx_acc["bufferView"]]

    pos_offset = pos_bv.get("byteOffset", 0) + pos_acc.get("byteOffset", 0)
    raw_positions = [struct.unpack_from("<fff", c1_data, pos_offset + i * 12) for i in range(pos_acc["count"])]

    idx_offset = idx_bv.get("byteOffset", 0) + idx_acc.get("byteOffset", 0)
    if idx_acc["componentType"] == 5123: # UNSIGNED_SHORT
        raw_indices = [struct.unpack_from("<H", c1_data, idx_offset + i * 2)[0] for i in range(idx_acc["count"])]
    else:
        raw_indices = [struct.unpack_from("<I", c1_data, idx_offset + i * 4)[0] for i in range(idx_acc["count"])]

    # Centralizar e normalizar escala
    min_x = min(p[0] for p in raw_positions); max_x = max(p[0] for p in raw_positions)
    min_y = min(p[1] for p in raw_positions); max_y = max(p[1] for p in raw_positions)
    min_z = min(p[2] for p in raw_positions); max_z = max(p[2] for p in raw_positions)

    cx = (min_x + max_x) / 2.0
    cy = min_y # Base no y=0
    cz = (min_z + max_z) / 2.0
    altura = max_y - min_y
    fator_escala = 2.0 / (altura if altura > 0 else 1.0)

    normalized_positions = [
        ((p[0] - cx) * fator_escala, (p[1] - cy) * fator_escala, (p[2] - cz) * fator_escala)
        for p in raw_positions
    ]

    # Grid clustering decimation
    res = 12
    n_min_x = min(p[0] for p in normalized_positions); n_max_x = max(p[0] for p in normalized_positions)
    n_min_y = min(p[1] for p in normalized_positions); n_max_y = max(p[1] for p in normalized_positions)
    n_min_z = min(p[2] for p in normalized_positions); n_max_z = max(p[2] for p in normalized_positions)

    def get_cell(p):
        return (
            int((p[0] - n_min_x) / (n_max_x - n_min_x + 1e-6) * (res - 1)),
            int((p[1] - n_min_y) / (n_max_y - n_min_y + 1e-6) * (res - 1)),
            int((p[2] - n_min_z) / (n_max_z - n_min_z + 1e-6) * (res - 1))
        )

    clusters = {}
    v_map = {}
    for i, p in enumerate(normalized_positions):
        c = get_cell(p)
        clusters.setdefault(c, []).append(p)
        v_map[i] = c

    new_vertices = []
    c_to_idx = {}
    for i, (c, pts) in enumerate(clusters.items()):
        avg_p = (
            sum(p[0] for p in pts) / len(pts),
            sum(p[1] for p in pts) / len(pts),
            sum(p[2] for p in pts) / len(pts)
        )
        new_vertices.append(avg_p)
        c_to_idx[c] = i

    new_faces = []
    seen = set()
    for t in range(0, len(raw_indices), 3):
        c1 = c_to_idx[v_map[raw_indices[t]]]
        c2 = c_to_idx[v_map[raw_indices[t+1]]]
        c3 = c_to_idx[v_map[raw_indices[t+2]]]
        if c1 != c2 and c2 != c3 and c1 != c3:
            tri = tuple(sorted([c1, c2, c3]))
            if tri not in seen:
                seen.add(tri)
                new_faces.append((c1 + 1, c2 + 1, c3 + 1))

    with open(PATH_NEFERTITI_OBJ, "w", encoding="utf-8") as f:
        f.write("# Busto de Nefertiti - Digitalizado por Fraunhofer IGD (CC BY-NC)\n")
        f.write("# Otimizado para Computacao Grafica Didatica AP1\n")
        f.write(f"# Vertices: {len(new_vertices)}, Faces: {len(new_faces)}\n")
        for v in new_vertices:
            f.write(f"v {v[0]:.4f} {v[1]:.4f} {v[2]:.4f}\n")
        for face in new_faces:
            f.write(f"f {face[0]} {face[1]} {face[2]}\n")

    print(f"Salvo modelo 3D {PATH_NEFERTITI_OBJ}: {len(new_vertices)} vértices, {len(new_faces)} faces.")

def gerar_fallbacks_se_necessario():
    pygame.init()
    if not os.path.exists(PATH_TOTENINSEL):
        print("Gerando representação artística de fallback para A Ilha dos Mortos...")
        surf = pygame.Surface((800, 500))
        surf.fill((15, 25, 40))
        for y in range(300):
            cor = (15 + y//15, 25 + y//12, 45 + y//10)
            pygame.draw.line(surf, cor, (0, y), (800, y))
        pygame.draw.rect(surf, (10, 20, 30), (0, 300, 800, 200))
        pygame.draw.polygon(surf, (25, 30, 35), [(200, 320), (350, 140), (450, 130), (600, 320)])
        for cx in range(320, 480, 15):
            pygame.draw.polygon(surf, (10, 25, 15), [(cx, 310), (cx+7, 160), (cx+14, 310)])
        pygame.draw.polygon(surf, (40, 35, 30), [(460, 360), (510, 360), (495, 375), (450, 375)])
        pygame.draw.rect(surf, (240, 240, 250), (480, 340, 10, 22))
        pygame.image.save(surf, PATH_TOTENINSEL)

    if not os.path.exists(PATH_PAPYRUS):
        print("Gerando representação de fallback para o Papiro de Ani...")
        surf = pygame.Surface((800, 400))
        surf.fill((215, 185, 135))
        fonte = pygame.font.SysFont("Arial", 18, bold=True)
        txt = fonte.render("[ PAPIRO DE ANI — LIVRO DOS MORTOS (1250 a.C.) ]", True, (70, 45, 20))
        surf.blit(txt, (150, 40))
        for y in range(80, 360, 25):
            pygame.draw.line(surf, (120, 90, 50), (60, y), (740, y), 2)
        pygame.image.save(surf, PATH_PAPYRUS)

def main():
    try:
        if not os.path.exists(PATH_TOTENINSEL):
            baixar_arquivo(URL_TOTENINSEL, PATH_TOTENINSEL)
    except Exception as e:
        print(f"Aviso: Não foi possível baixar imagem de A Ilha dos Mortos: {e}")

    try:
        if not os.path.exists(PATH_PAPYRUS):
            baixar_arquivo(URL_PAPYRUS, PATH_PAPYRUS)
    except Exception as e:
        print(f"Aviso: Não foi possível baixar imagem do Papiro: {e}")

    try:
        processar_nefertiti()
    except Exception as e:
        print(f"Aviso ao processar Nefertiti: {e}")

    gerar_fallbacks_se_necessario()
    print("Preparação de assets concluída com sucesso!")

if __name__ == "__main__":
    main()
