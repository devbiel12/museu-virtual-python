"""Módulo de renderer da aplicação."""
import math
import os
import sys
import pygame

from .config import *
from .math3d import *
from .geometry import *
from .objects import *


class RendererMixin:
        def desenhar_piso_museu(self):
            """Desenha a malha do piso com ladrilhos de mármore escuro em perspectiva."""
            y_piso = -1.2
            # Linhas em Z
            for x in range(-13, 14, 2):
                p1 = projetar_para_camera((x, y_piso, -3.5), self.cam_pos_atual, self.cam_yaw_atual, self.cam_pitch_atual)
                p2 = projetar_para_camera((x, y_piso, 13.5), self.cam_pos_atual, self.cam_yaw_atual, self.cam_pitch_atual)
                if p1 and p2:
                    pygame.draw.line(self.tela, COR_PISO_GRADE, (p1[0], p1[1]), (p2[0], p2[1]), 1)

            # Linhas em X
            for z in range(-3, 14, 2):
                p1 = projetar_para_camera((-13.0, y_piso, z), self.cam_pos_atual, self.cam_yaw_atual, self.cam_pitch_atual)
                p2 = projetar_para_camera(( 13.0, y_piso, z), self.cam_pos_atual, self.cam_yaw_atual, self.cam_pitch_atual)
                if p1 and p2:
                    pygame.draw.line(self.tela, COR_PISO_GRADE, (p1[0], p1[1]), (p2[0], p2[1]), 1)


        def desenhar_arquitetura_paredes(self):
            """Renderiza os painéis murais e portais separadores das galerias."""
            elementos = []

            def adicionar_elemento(vertices, cor, cor_borda, largura_borda=2):
                poligono, profundidade = projetar_poligono_solido(
                    vertices,
                    self.cam_pos_atual,
                    self.cam_yaw_atual,
                    self.cam_pitch_atual
                )
                if poligono and profundidade is not None:
                    elementos.append((profundidade, poligono, cor, cor_borda, largura_borda))

            for teto in self.teto_faces:
                adicionar_elemento(teto, COR_TETO, COR_PAREDE_BORDA)

            for indice, parede in enumerate(self.paredes_faces):
                cor_parede = COR_PAREDE_ALT if indice % 2 else COR_PAREDE
                adicionar_elemento(parede, cor_parede, COR_PAREDE_BORDA)

            for porta in self.portas:
                for v_elem, c_face, c_borda, larg in porta.elementos():
                    adicionar_elemento(v_elem, c_face, c_borda, larg)

            # Painter's algorithm: elementos distantes primeiro, próximos por último.
            elementos.sort(key=lambda item: item[0], reverse=True)
            for _, poligono, cor, cor_borda, largura_borda in elementos:
                pygame.draw.polygon(self.tela, cor, poligono)
                pygame.draw.polygon(self.tela, cor_borda, poligono, largura_borda)


        def desenhar_objeto_3d(self, obj):
            """
            Aplica transformações geométricas locais (Escala, Rotação, Translação),
            calcula sombreamento difuso por iluminação direcional e desenha as faces.
            """
            # Objetos de outra sala ficam ocultos quando a divisória não tem portal
            # entre a câmera e a obra. Isso evita enxergar através das paredes.
            if not linha_desimpedida(self.cam_pos_atual, obj.pos, self.portas):
                return

            # 1. Transformar vértices locais para o mundo
            verts_mundo = [transformar_vertice(v, obj.pos, obj.rot, obj.escala) for v in obj.vertices]
            verts_proj  = [projetar_para_camera(v, self.cam_pos_atual, self.cam_yaw_atual, self.cam_pitch_atual) for v in verts_mundo]

            # Fonte de luz associada (Spot LED mais próximo da galeria)
            idx_spot = 1  # Padrão: Sala 2 (Pintura Central)
            if obj.pos[0] < -4.0: idx_spot = 0   # Sala 1: Escultura (Oeste)
            elif obj.pos[0] > 4.0: idx_spot = 2  # Sala 3: Papiro (Leste)
            luz_pos = self.spots_led[idx_spot]["pos"]

            # Fator de brilho geral da iluminação binária
            fator_luz_binaria = 1.0 if obj.iluminado else 0.40

            # Otimização de projeção e sombreamento com normais pré-computadas
            ry = obj.rot[1]
            cos_y = math.cos(ry)
            sin_y = math.sin(ry)
            ox, oy, oz = obj.pos
            sx, sy, sz = obj.escala
            lx, ly, lz = luz_pos
            r_base, g_base, b_base = obj.cor_base

            faces_para_desenhar = []
            tem_normais = hasattr(obj, 'normais_locais') and len(obj.normais_locais) == len(obj.faces)

            for i, face in enumerate(obj.faces):
                p0 = verts_proj[face[0]]
                p1 = verts_proj[face[1]]
                p2 = verts_proj[face[2]]
                if p0 is None or p1 is None or p2 is None:
                    continue

                if len(face) == 4:
                    p3 = verts_proj[face[3]]
                    if p3 is None:
                        continue
                    z_medio = (p0[2] + p1[2] + p2[2] + p3[2]) * 0.25
                    poly_2d = ((p0[0], p0[1]), (p1[0], p1[1]), (p2[0], p2[1]), (p3[0], p3[1]))
                else:
                    z_medio = (p0[2] + p1[2] + p2[2]) * 0.333333
                    poly_2d = ((p0[0], p0[1]), (p1[0], p1[1]), (p2[0], p2[1]))

                if tem_normais:
                    lnx, lny, lnz = obj.normais_locais[i]
                    nx = lnx * cos_y + lnz * sin_y
                    ny = lny
                    nz = -lnx * sin_y + lnz * cos_y

                    lcx, lcy, lcz = obj.centros_locais[i]
                    cx = ox + (lcx * cos_y + lcz * sin_y) * sx
                    cy = oy + lcy * sy
                    cz = oz + (-lcx * sin_y + lcz * cos_y) * sz
                else:
                    p0_m = verts_mundo[face[0]]
                    p1_m = verts_mundo[face[1]]
                    p2_m = verts_mundo[face[2]]
                    v1 = (p1_m[0] - p0_m[0], p1_m[1] - p0_m[1], p1_m[2] - p0_m[2])
                    v2 = (p2_m[0] - p0_m[0], p2_m[1] - p0_m[1], p2_m[2] - p0_m[2])
                    nx = v1[1]*v2[2] - v1[2]*v2[1]
                    ny = v1[2]*v2[0] - v1[0]*v2[2]
                    nz = v1[0]*v2[1] - v1[1]*v2[0]
                    comprimento = math.sqrt(nx*nx + ny*ny + nz*nz)
                    inv_c = 1.0 / comprimento if comprimento > 1e-8 else 1.0
                    nx, ny, nz = nx * inv_c, ny * inv_c, nz * inv_c
                    cx = (p0_m[0] + p1_m[0] + p2_m[0]) / 3.0
                    cy = (p0_m[1] + p1_m[1] + p2_m[1]) / 3.0
                    cz = (p0_m[2] + p1_m[2] + p2_m[2]) / 3.0

                dx = lx - cx
                dy = ly - cy
                dz = lz - cz
                dist_sq = dx*dx + dy*dy + dz*dz
                inv_dist = 1.0 / math.sqrt(dist_sq) if dist_sq > 1e-8 else 1.0

                dot = nx * (dx * inv_dist) + ny * (dy * inv_dist) + nz * (dz * inv_dist)
                if dot < 0.0:
                    dot = 0.0

                brilho = (0.35 + 0.65 * dot) * fator_luz_binaria
                cr = int(r_base * brilho)
                cg = int(g_base * brilho)
                cb = int(b_base * brilho)
                cor_face = (min(255, cr), min(255, cg), min(255, cb))
                cor_aresta = (min(255, int(cr * 1.25)), min(255, int(cg * 1.25)), min(255, int(cb * 1.25)))

                faces_para_desenhar.append((z_medio, poly_2d, cor_face, cor_aresta, obj.eh_vidro))

            # Ordenar faces da mais distante para a mais próxima (Painter's algorithm)
            faces_para_desenhar.sort(key=lambda item: item[0], reverse=True)

            # Desenhar faces na tela
            for _, poly, cor_f, cor_a, eh_vidro in faces_para_desenhar:
                if eh_vidro:
                    # Superfície semitransparente de vidro
                    surf_vidro = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
                    pygame.draw.polygon(surf_vidro, COR_VIDRO_FACE, poly)
                    pygame.draw.polygon(surf_vidro, COR_VIDRO_BORDA, poly, 1)
                    self.tela.blit(surf_vidro, (0, 0))
                else:
                    pygame.draw.polygon(self.tela, cor_f, poly)
                    pygame.draw.polygon(self.tela, cor_a, poly, 1)


        def desenhar_superficies_artisticas_rasterizadas(self):
            """
            Projeta e rasteriza as obras bidimensionais com perspectiva 3D real:
            - A tela de A Ilha dos Mortos: fatias verticais projetadas na parede com oclusão.
            - O Papiro de Ani: fatias projetadas sobre o tampo inclinado da vitrine com
              comportamento angular realista (visível de frente/trás, perfil fino nas laterais).
            """
            N_FATIAS = 28  # Número de fatias verticais para ambas as obras

            # =====================================================================
            # 1. PINTURA: A Ilha dos Mortos (Arnold Böcklin) — Sala 1, Parede Norte
            # =====================================================================
            # Teste de oclusão: só renderiza se a câmera tem linha de visão direta
            centro_pintura = (0.0, 1.7, 12.85)
            if linha_desimpedida(self.cam_pos_atual, centro_pintura, self.portas):
                # Vértices 3D calibrados com o vão interno da moldura dourada
                # BL = Bottom-Left, BR = Bottom-Right, TR = Top-Right, TL = Top-Left
                PIN_BL = (-2.4, 0.4, 12.85)
                PIN_BR = ( 2.4, 0.4, 12.85)
                PIN_TR = ( 2.4, 3.0, 12.85)
                PIN_TL = (-2.4, 3.0, 12.85)

                W_img = self.img_toteninsel.get_width()
                H_img = self.img_toteninsel.get_height()

                # Projetar os 4 cantos para verificação rápida de visibilidade
                p_bl = projetar_para_camera(PIN_BL, self.cam_pos_atual, self.cam_yaw_atual, self.cam_pitch_atual)
                p_br = projetar_para_camera(PIN_BR, self.cam_pos_atual, self.cam_yaw_atual, self.cam_pitch_atual)
                p_tr = projetar_para_camera(PIN_TR, self.cam_pos_atual, self.cam_yaw_atual, self.cam_pitch_atual)
                p_tl = projetar_para_camera(PIN_TL, self.cam_pos_atual, self.cam_yaw_atual, self.cam_pitch_atual)

                # Pelo menos 2 cantos visíveis para tentar renderizar
                cantos_pin = [p_bl, p_br, p_tr, p_tl]
                cantos_validos = sum(1 for p in cantos_pin if p is not None)

                if cantos_validos >= 2:
                    # Renderização por fatias verticais com perspectiva real
                    for i in range(N_FATIAS):
                        u0 = i / N_FATIAS
                        u1 = (i + 1) / N_FATIAS

                        # Interpolar posições 3D ao longo da borda inferior e superior
                        bot0 = (PIN_BL[0] + u0 * (PIN_BR[0] - PIN_BL[0]),
                                PIN_BL[1] + u0 * (PIN_BR[1] - PIN_BL[1]),
                                PIN_BL[2])
                        bot1 = (PIN_BL[0] + u1 * (PIN_BR[0] - PIN_BL[0]),
                                PIN_BL[1] + u1 * (PIN_BR[1] - PIN_BL[1]),
                                PIN_BL[2])
                        top0 = (PIN_TL[0] + u0 * (PIN_TR[0] - PIN_TL[0]),
                                PIN_TL[1] + u0 * (PIN_TR[1] - PIN_TL[1]),
                                PIN_TL[2])
                        top1 = (PIN_TL[0] + u1 * (PIN_TR[0] - PIN_TL[0]),
                                PIN_TL[1] + u1 * (PIN_TR[1] - PIN_TL[1]),
                                PIN_TL[2])

                        pb0 = projetar_para_camera(bot0, self.cam_pos_atual, self.cam_yaw_atual, self.cam_pitch_atual)
                        pb1 = projetar_para_camera(bot1, self.cam_pos_atual, self.cam_yaw_atual, self.cam_pitch_atual)
                        pt0 = projetar_para_camera(top0, self.cam_pos_atual, self.cam_yaw_atual, self.cam_pitch_atual)
                        pt1 = projetar_para_camera(top1, self.cam_pos_atual, self.cam_yaw_atual, self.cam_pitch_atual)

                        if pb0 and pb1 and pt0 and pt1:
                            sx = min(pb0[0], pb1[0], pt0[0], pt1[0])
                            sy = min(pb0[1], pb1[1], pt0[1], pt1[1])
                            sw = max(1, max(pb0[0], pb1[0], pt0[0], pt1[0]) - sx + 1)
                            sh = max(1, max(pb0[1], pb1[1], pt0[1], pt1[1]) - sy + 1)

                            src_x = int(u0 * W_img)
                            src_w = max(1, int((u1 - u0) * W_img))
                            if src_x + src_w > W_img:
                                src_w = W_img - src_x

                            sub = self.img_toteninsel.subsurface((src_x, 0, src_w, H_img))
                            strip = pygame.transform.scale(sub, (sw, sh))

                            if not self.moldura_toteninsel.iluminado:
                                sombra = pygame.Surface((sw, sh), pygame.SRCALPHA)
                                sombra.fill((0, 0, 0, 140))
                                strip.blit(sombra, (0, 0))

                            self.tela.blit(strip, (sx, sy))

                    # Moldura interna decorativa (borda dourada ao redor da tela)
                    if all(p is not None for p in cantos_pin):
                        borda_2d = [(p[0], p[1]) for p in [p_bl, p_br, p_tr, p_tl]]
                        pygame.draw.polygon(self.tela, (140, 110, 30), borda_2d, 2)

            # =====================================================================
            # 2. PAPIRO DE ANI (Livro dos Mortos) — superfície 3D texturizada
            # =====================================================================
            if not linha_desimpedida(self.cam_pos_atual, self.vitrine_papiro.pos, self.portas):
                return

            # IMPORTANTE: não desenhar mais a imagem como uma bounding box 2D.
            # Cada faixa da textura é projetada a partir de quatro pontos 3D fixos,
            # permitindo que a folha tenha perspectiva real ao redor da vitrine.
            # A quantidade de faixas é deliberadamente maior que a da pintura para
            # reduzir a aparência de deformação entre as colunas.
            # Menos fatias reduzem bastante as alocações e transformações por quadro
            # em máquinas simples, mantendo a perspectiva da superfície.
            N_FATIAS_PAPIRO = 20
            W_img = self.img_papiro.get_width()
            H_img = self.img_papiro.get_height()

            # Usa exatamente a mesma geometria física do objeto 3D, evitando que a
            # textura e a malha tenham posições/escala diferentes.
            verts_pap_mundo = [
                transformar_vertice(v, self.papiro_ani_obj.pos, self.papiro_ani_obj.rot, self.papiro_ani_obj.escala)
                for v in self.papiro_ani_obj.vertices[:4]
            ]

            pts_cantos = [
                projetar_para_camera(v, self.cam_pos_atual, self.cam_yaw_atual, self.cam_pitch_atual)
                for v in verts_pap_mundo
            ]

            if all(p is not None for p in pts_cantos):
                for i in range(N_FATIAS_PAPIRO):
                    u0 = i / N_FATIAS_PAPIRO
                    u1 = (i + 1) / N_FATIAS_PAPIRO

                    # Quatro cantos 3D da faixa atual, interpolados na própria folha.
                    bl = verts_pap_mundo[0]
                    br = verts_pap_mundo[1]
                    tr = verts_pap_mundo[2]
                    tl = verts_pap_mundo[3]

                    bot0 = tuple(bl[k] + u0 * (br[k] - bl[k]) for k in range(3))
                    bot1 = tuple(bl[k] + u1 * (br[k] - bl[k]) for k in range(3))
                    top0 = tuple(tl[k] + u0 * (tr[k] - tl[k]) for k in range(3))
                    top1 = tuple(tl[k] + u1 * (tr[k] - tl[k]) for k in range(3))

                    pb0 = projetar_para_camera(bot0, self.cam_pos_atual, self.cam_yaw_atual, self.cam_pitch_atual)
                    pb1 = projetar_para_camera(bot1, self.cam_pos_atual, self.cam_yaw_atual, self.cam_pitch_atual)
                    pt0 = projetar_para_camera(top0, self.cam_pos_atual, self.cam_yaw_atual, self.cam_pitch_atual)
                    pt1 = projetar_para_camera(top1, self.cam_pos_atual, self.cam_yaw_atual, self.cam_pitch_atual)

                    if not (pb0 and pb1 and pt0 and pt1):
                        continue

                    quad = [(pb0[0], pb0[1]), (pb1[0], pb1[1]),
                            (pt1[0], pt1[1]), (pt0[0], pt0[1])]
                    sx = min(p[0] for p in quad)
                    sy = min(p[1] for p in quad)
                    ex = max(p[0] for p in quad)
                    ey = max(p[1] for p in quad)
                    sw = max(1, ex - sx + 1)
                    sh = max(1, ey - sy + 1)

                    if sw > 2500 or sh > 1800:
                        continue

                    src_x = min(W_img - 1, int(u0 * W_img))
                    src_x2 = min(W_img, max(src_x + 1, int(u1 * W_img)))
                    src_w = src_x2 - src_x
                    sub = self.img_papiro.subsurface((src_x, 0, src_w, H_img))

                    strip_rgb = pygame.transform.scale(sub, (sw, sh))

                    # Reutilização de buffers para evitar alocações contínuas de memória
                    if not hasattr(self, '_scratch_strip') or self._scratch_strip.get_width() < sw or self._scratch_strip.get_height() < sh:
                        self._scratch_strip = pygame.Surface((max(sw, 350), max(sh, 350)), pygame.SRCALPHA, 32)
                        self._scratch_mascara = pygame.Surface((max(sw, 350), max(sh, 350)), pygame.SRCALPHA, 32)

                    strip = self._scratch_strip.subsurface((0, 0, sw, sh))
                    strip.fill((0, 0, 0, 0))
                    strip.blit(strip_rgb, (0, 0))

                    if not self.vitrine_papiro.iluminado:
                        strip.fill((150, 150, 150, 255), special_flags=pygame.BLEND_RGBA_MULT)

                    mascara = self._scratch_mascara.subsurface((0, 0, sw, sh))
                    mascara.fill((0, 0, 0, 0))
                    quad_local = [(round(x - sx), round(y - sy)) for x, y in quad]
                    pygame.draw.polygon(mascara, (255, 255, 255, 255), quad_local)
                    strip.blit(mascara, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

                    self.tela.blit(strip, (sx, sy))


        def desenhar_feixes_spotlights(self):
            """
            Desenha as luminárias de LED no teto e os cones/raios translúcidos
            de iluminação direcionados para as obras.
            """
            for i, spot in enumerate(self.spots_led):
                p_proj = projetar_para_camera(spot["pos"], self.cam_pos_atual, self.cam_yaw_atual, self.cam_pitch_atual)
                a_proj = projetar_para_camera(spot["alvo"], self.cam_pos_atual, self.cam_yaw_atual, self.cam_pitch_atual)

                if p_proj and a_proj:
                    eh_ativo = (i == self.obra_foco_idx)
                    cor_luz = spot["cor"] if eh_ativo else (90, 100, 120)

                    # Ponto do projetor no teto (círculo emissor)
                    pygame.draw.circle(self.tela, cor_luz, (p_proj[0], p_proj[1]), 7 if eh_ativo else 4)
                    pygame.draw.circle(self.tela, (255, 255, 255), (p_proj[0], p_proj[1]), 3 if eh_ativo else 2)

                    # Desenhar feixe de raio do refletor até o foco
                    if eh_ativo:
                        # Linha do raio de luz principal
                        pygame.draw.line(self.tela, COR_LUZ_LED, (p_proj[0], p_proj[1]), (a_proj[0], a_proj[1]), 2)
                        
                        # Linhas periféricas representando o cone de iluminação
                        dx_cone = 45
                        pygame.draw.line(self.tela, (255, 250, 200), (p_proj[0], p_proj[1]), (a_proj[0] - dx_cone, a_proj[1]), 1)
                        pygame.draw.line(self.tela, (255, 250, 200), (p_proj[0], p_proj[1]), (a_proj[0] + dx_cone, a_proj[1]), 1)

        # -------------------------------------------------------------------------
        # INTERFACE SOBREPOSTA HUD, CARTÕES DE PROXIMIDADE E CRÉDITOS
        # -------------------------------------------------------------------------
