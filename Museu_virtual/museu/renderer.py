"""Renderização 3D: piso, paredes, objetos, texturas e spotlights.

Otimizações desta versão:
- Uma única câmera com trigonometria em cache serve todas as projeções do quadro.
- Descarte de faces traseiras nas malhas fechadas e descarte de faces minúsculas
  ou fora da tela antes de qualquer desenho.
- O vidro usa um buffer translúcido persistente, limpo só na região suja, no
  lugar de alocar uma superfície do tamanho da tela por face de vidro.
- As obras rasterizadas (pintura e papiro) guardam suas fatias prontas e só as
  recalculam quando a câmera ou a iluminação mudam.
"""
import math
import pygame
from operator import itemgetter

from .config import *
from .math3d import *
from .geometry import *
from .objects import *

_primeiro_item = itemgetter(0)


class RendererMixin:

        # ---------------------------------------------------------------------
        # PISO
        # ---------------------------------------------------------------------

        def desenhar_piso_museu(self):
            """Desenha a grade do piso em perspectiva."""
            projetar = self.cam.projetar
            tela = self.tela
            linha = pygame.draw.line
            cor = COR_PISO_GRADE

            for a, b in self.linhas_piso:
                p1 = projetar(a)
                if p1 is None:
                    continue
                p2 = projetar(b)
                if p2 is None:
                    continue
                linha(tela, cor, (p1[0], p1[1]), (p2[0], p2[1]), 1)

        # ---------------------------------------------------------------------
        # PAREDES, TETO E PORTAS
        # ---------------------------------------------------------------------

        def desenhar_arquitetura_paredes(self):
            """Paredes, divisórias e portas pelo algoritmo do pintor."""
            cam = self.cam
            tela = self.tela
            poligono = pygame.draw.polygon

            # O teto vai primeiro, como plano de fundo superior: assim nunca
            # corta as paredes laterais em nenhum ângulo de visão.
            for teto in self.teto_faces:
                pontos, _ = cam.projetar_poligono(teto)
                if pontos:
                    poligono(tela, COR_TETO, pontos)

            elementos = []
            anexar = elementos.append

            for indice, parede in enumerate(self.paredes_faces):
                pontos, profundidade = cam.projetar_poligono(parede)
                if pontos and profundidade is not None:
                    cor = COR_PAREDE_ALT if indice % 2 else COR_PAREDE
                    anexar((profundidade, pontos, cor, COR_PAREDE_BORDA, 2))

            for porta in self.portas:
                for vertices, cor_face, cor_borda, largura in porta.elementos():
                    pontos, profundidade = cam.projetar_poligono(vertices)
                    if pontos and profundidade is not None:
                        anexar((profundidade, pontos, cor_face, cor_borda, largura))

            # Algoritmo do pintor: os distantes primeiro, os próximos por último.
            elementos.sort(key=_primeiro_item, reverse=True)
            for _, pontos, cor, cor_borda, largura in elementos:
                poligono(tela, cor, pontos)
                poligono(tela, cor_borda, pontos, largura)

        # ---------------------------------------------------------------------
        # OBJETOS 3D
        # ---------------------------------------------------------------------

        def desenhar_objeto_3d(self, obj):
            """Renderiza um objeto 3D com iluminação difusa (Lambert).

            Passa por três filtros antes de desenhar qualquer coisa: oclusão por
            parede, esfera envolvente fora do campo de visão e, nas malhas
            fechadas, descarte das faces que estão de costas para a câmera.
            """
            cam = self.cam
            cam_pos = self.cam_pos_atual

            # Filtro 1: objetos de outra sala, sem portal aberto entre nós.
            if not linha_desimpedida(cam_pos, obj.pos, self.portas):
                return

            # Filtro 2: esfera envolvente inteiramente atrás do plano próximo.
            cl = obj.centro_local
            centro_mundo = (obj.pos[0] + cl[0] * obj.escala[0],
                            obj.pos[1] + cl[1] * obj.escala[1],
                            obj.pos[2] + cl[2] * obj.escala[2])
            raio = obj.raio_mundo()
            if cam.para_camera(centro_mundo)[2] < -raio:
                return

            verts_mundo = transformar_vertices(obj.vertices, obj.pos, obj.rot, obj.escala)
            verts_proj = cam.projetar_lista(verts_mundo)

            # Fonte de luz: o spot LED da galeria onde o objeto está.
            idx_spot = 1
            if obj.pos[0] < -4.0:
                idx_spot = 0
            elif obj.pos[0] > 4.0:
                idx_spot = 2
            lx, ly, lz = self.spots_led[idx_spot]["pos"]

            fator_luz = 1.0 if obj.iluminado else 0.40

            ry = obj.rot[1]
            cos_y = math.cos(ry)
            sin_y = math.sin(ry)
            ox, oy, oz = obj.pos
            sx, sy, sz = obj.escala
            r_base, g_base, b_base = obj.cor_base
            cam_x, cam_y, cam_z = cam_pos[0], cam_pos[1], cam_pos[2]

            normais = obj.normais_locais
            centros = obj.centros_locais
            descartar_traseiras = obj.descartar_traseiras
            area_minima = AREA_MINIMA_FACE

            faces_visiveis = []
            anexar = faces_visiveis.append

            for i, face in enumerate(obj.faces):
                p0 = verts_proj[face[0]]
                if p0 is None:
                    continue
                p1 = verts_proj[face[1]]
                if p1 is None:
                    continue
                p2 = verts_proj[face[2]]
                if p2 is None:
                    continue

                # Normal e centro da face no mundo (rotação apenas em Y).
                lnx, lny, lnz = normais[i]
                nx = lnx * cos_y + lnz * sin_y
                ny = lny
                nz = -lnx * sin_y + lnz * cos_y

                lcx, lcy, lcz = centros[i]
                cx = ox + (lcx * cos_y + lcz * sin_y) * sx
                cy = oy + lcy * sy
                cz = oz + (-lcx * sin_y + lcz * cos_y) * sz

                # Filtro 3: face de costas para a câmera (só em malha fechada).
                if descartar_traseiras:
                    if nx * (cam_x - cx) + ny * (cam_y - cy) + nz * (cam_z - cz) <= 0.0:
                        continue

                x0, y0 = p0[0], p0[1]
                x1, y1 = p1[0], p1[1]
                x2, y2 = p2[0], p2[1]

                if len(face) == 4:
                    p3 = verts_proj[face[3]]
                    if p3 is None:
                        continue
                    x3, y3 = p3[0], p3[1]
                    z_medio = (p0[2] + p1[2] + p2[2] + p3[2]) * 0.25
                    poly_2d = ((x0, y0), (x1, y1), (x2, y2), (x3, y3))
                    min_x = x0 if x0 < x1 else x1
                    if x2 < min_x: min_x = x2
                    if x3 < min_x: min_x = x3
                    max_x = x0 if x0 > x1 else x1
                    if x2 > max_x: max_x = x2
                    if x3 > max_x: max_x = x3
                    min_y = y0 if y0 < y1 else y1
                    if y2 < min_y: min_y = y2
                    if y3 < min_y: min_y = y3
                    max_y = y0 if y0 > y1 else y1
                    if y2 > max_y: max_y = y2
                    if y3 > max_y: max_y = y3
                else:
                    z_medio = (p0[2] + p1[2] + p2[2]) * 0.3333333333
                    poly_2d = ((x0, y0), (x1, y1), (x2, y2))
                    min_x = x0 if x0 < x1 else x1
                    if x2 < min_x: min_x = x2
                    max_x = x0 if x0 > x1 else x1
                    if x2 > max_x: max_x = x2
                    min_y = y0 if y0 < y1 else y1
                    if y2 < min_y: min_y = y2
                    max_y = y0 if y0 > y1 else y1
                    if y2 > max_y: max_y = y2

                # Filtro 4: fora da tela ou pequena demais para fazer diferença.
                if max_x < 0 or min_x > LARGURA or max_y < 0 or min_y > ALTURA:
                    continue
                area = (max_x - min_x) * (max_y - min_y)
                if area < area_minima:
                    continue

                # Iluminação difusa de Lambert.
                dx = lx - cx
                dy = ly - cy
                dz = lz - cz
                dist_sq = dx * dx + dy * dy + dz * dz
                inv_dist = 1.0 / math.sqrt(dist_sq) if dist_sq > 1e-8 else 1.0
                dot = (nx * dx + ny * dy + nz * dz) * inv_dist
                if dot < 0.0:
                    dot = 0.0

                brilho = (0.35 + 0.65 * dot) * fator_luz
                cr = int(r_base * brilho)
                cg = int(g_base * brilho)
                cb = int(b_base * brilho)
                if cr > 255: cr = 255
                if cg > 255: cg = 255
                if cb > 255: cb = 255
                cor_face = (cr, cg, cb)
                ar = int(cr * 1.25); ag = int(cg * 1.25); ab = int(cb * 1.25)
                cor_aresta = (ar if ar < 255 else 255,
                              ag if ag < 255 else 255,
                              ab if ab < 255 else 255)

                anexar((z_medio, poly_2d, cor_face, cor_aresta))

            if not faces_visiveis:
                return

            faces_visiveis.sort(key=_primeiro_item, reverse=True)

            if obj.eh_vidro:
                self._desenhar_faces_vidro(faces_visiveis)
                return

            tela = self.tela
            poligono = pygame.draw.polygon
            for _, poly, cor_f, cor_a in faces_visiveis:
                poligono(tela, cor_f, poly)
                poligono(tela, cor_a, poly, 1)

        def _desenhar_faces_vidro(self, faces):
            """Vidro translúcido em um buffer reutilizado, limpo só na região suja.

            Cada face continua sendo composta separadamente — é isso que dá ao
            vidro o acúmulo de translucidez onde as faces se sobrepõem. O que
            mudou é o custo: a versão anterior criava uma superfície do tamanho
            da tela por face e compunha a tela inteira (seis vezes por quadro só
            na redoma do papiro); agora um único buffer é reaproveitado e apenas
            o retângulo ocupado pela face é limpo e composto.
            """
            buffer_vidro = self._buffer_vidro
            tela = self.tela
            poligono = pygame.draw.polygon

            for _, poly, _, _ in faces:
                min_x = min(p[0] for p in poly)
                max_x = max(p[0] for p in poly)
                min_y = min(p[1] for p in poly)
                max_y = max(p[1] for p in poly)

                x0 = max(0, int(min_x) - 2)
                y0 = max(0, int(min_y) - 2)
                x1 = min(LARGURA, int(max_x) + 3)
                y1 = min(ALTURA, int(max_y) + 3)
                if x1 <= x0 or y1 <= y0:
                    continue

                area = pygame.Rect(x0, y0, x1 - x0, y1 - y0)
                buffer_vidro.fill((0, 0, 0, 0), area)
                poligono(buffer_vidro, COR_VIDRO_VITRINE_FACE, poly)
                poligono(buffer_vidro, COR_VIDRO_VITRINE_BORDA, poly, 1)
                tela.blit(buffer_vidro, (x0, y0), area)

        # ---------------------------------------------------------------------
        # OBRAS RASTERIZADAS (PINTURA E PAPIRO)
        # ---------------------------------------------------------------------

        def desenhar_superficies_artisticas_rasterizadas(self):
            """Desenha pintura e papiro com perspectiva real por fatias verticais.

            As fatias prontas ficam guardadas e são apenas recompostas enquanto a
            câmera e a iluminação não mudam — que é a maior parte do tempo em
            pausa, na tela inicial e nos trechos parados da visita.
            """
            self._desenhar_pintura()
            self._desenhar_papiro()

        def _fatias_para(self, pontos, maximo):
            """Escolhe o número de fatias pelo tamanho da obra na tela."""
            largura = max(p[0] for p in pontos) - min(p[0] for p in pontos)
            n = int(largura / PIXELS_POR_FATIA)
            if n < FATIAS_MIN:
                return FATIAS_MIN
            return n if n < maximo else maximo

        def _blitar_cache(self, nome, chave, construir):
            cache = self._cache_arte.get(nome)
            if cache is None or cache[0] != chave:
                tiras = construir()
                self._cache_arte[nome] = (chave, tiras)
            else:
                tiras = cache[1]
            if tiras:
                self.tela.blits(tiras, doreturn=False)

        # -- 1. A Ilha dos Mortos (Böcklin), parede norte da sala central ------

        def _desenhar_pintura(self):
            centro_pintura = (0.0, 1.7, 12.85)
            if not linha_desimpedida(self.cam_pos_atual, centro_pintura, self.portas):
                return

            cam = self.cam
            PIN_BL = (-2.4, 0.4, 12.85)
            PIN_BR = ( 2.4, 0.4, 12.85)
            PIN_TR = ( 2.4, 3.0, 12.85)
            PIN_TL = (-2.4, 3.0, 12.85)

            cantos = [cam.projetar(p) for p in (PIN_BL, PIN_BR, PIN_TR, PIN_TL)]
            validos = [p for p in cantos if p is not None]
            if len(validos) < 2:
                return

            iluminado = self.moldura_toteninsel.iluminado
            n_fatias = self._fatias_para(validos, FATIAS_MAX_PINTURA)
            chave = (cam.chave(), iluminado, n_fatias)

            def construir():
                imagem = self.img_toteninsel if iluminado else self.img_toteninsel_escura
                largura_img = imagem.get_width()
                altura_img = imagem.get_height()
                tiras = []
                for i in range(n_fatias):
                    u0 = i / n_fatias
                    u1 = (i + 1) / n_fatias

                    bot0 = (PIN_BL[0] + u0 * (PIN_BR[0] - PIN_BL[0]), PIN_BL[1], PIN_BL[2])
                    bot1 = (PIN_BL[0] + u1 * (PIN_BR[0] - PIN_BL[0]), PIN_BL[1], PIN_BL[2])
                    top0 = (PIN_TL[0] + u0 * (PIN_TR[0] - PIN_TL[0]), PIN_TL[1], PIN_TL[2])
                    top1 = (PIN_TL[0] + u1 * (PIN_TR[0] - PIN_TL[0]), PIN_TL[1], PIN_TL[2])

                    pb0 = cam.projetar(bot0)
                    pb1 = cam.projetar(bot1)
                    pt0 = cam.projetar(top0)
                    pt1 = cam.projetar(top1)
                    if not (pb0 and pb1 and pt0 and pt1):
                        continue

                    sx = int(min(pb0[0], pb1[0], pt0[0], pt1[0]))
                    sy = int(min(pb0[1], pb1[1], pt0[1], pt1[1]))
                    largura = max(1, int(max(pb0[0], pb1[0], pt0[0], pt1[0])) - sx + 1)
                    altura = max(1, int(max(pb0[1], pb1[1], pt0[1], pt1[1])) - sy + 1)
                    if sx > LARGURA or sy > ALTURA or sx + largura < 0 or sy + altura < 0:
                        continue
                    if largura > 2500 or altura > 1800:
                        continue

                    src_x = int(u0 * largura_img)
                    src_w = max(1, int((u1 - u0) * largura_img))
                    if src_x + src_w > largura_img:
                        src_w = largura_img - src_x

                    sub = imagem.subsurface((src_x, 0, src_w, altura_img))
                    tiras.append((pygame.transform.scale(sub, (largura, altura)), (sx, sy)))
                return tiras

            self._blitar_cache("pintura", chave, construir)

            if all(p is not None for p in cantos):
                borda = [(p[0], p[1]) for p in cantos]
                pygame.draw.polygon(self.tela, (140, 110, 30), borda, 2)

        # -- 2. Papiro de Ani, superfície 3D texturizada sob a redoma ---------

        def _desenhar_papiro(self):
            if not linha_desimpedida(self.cam_pos_atual, self.vitrine_papiro.pos, self.portas):
                return

            cam = self.cam
            papiro = self.papiro_ani_obj
            cantos_mundo = transformar_vertices(papiro.vertices[:4], papiro.pos,
                                                papiro.rot, papiro.escala)
            cantos = [cam.projetar(v) for v in cantos_mundo]
            if not all(p is not None for p in cantos):
                return

            iluminado = self.vitrine_papiro.iluminado
            n_fatias = self._fatias_para(cantos, FATIAS_MAX_PAPIRO)
            chave = (cam.chave(), iluminado, n_fatias)

            def construir():
                imagem = self.img_papiro if iluminado else self.img_papiro_escuro
                largura_img = imagem.get_width()
                altura_img = imagem.get_height()
                bl, br, tr, tl = cantos_mundo
                tiras = []

                for i in range(n_fatias):
                    u0 = i / n_fatias
                    u1 = (i + 1) / n_fatias

                    bot0 = tuple(bl[k] + u0 * (br[k] - bl[k]) for k in range(3))
                    bot1 = tuple(bl[k] + u1 * (br[k] - bl[k]) for k in range(3))
                    top0 = tuple(tl[k] + u0 * (tr[k] - tl[k]) for k in range(3))
                    top1 = tuple(tl[k] + u1 * (tr[k] - tl[k]) for k in range(3))

                    pb0 = cam.projetar(bot0)
                    pb1 = cam.projetar(bot1)
                    pt0 = cam.projetar(top0)
                    pt1 = cam.projetar(top1)
                    if not (pb0 and pb1 and pt0 and pt1):
                        continue

                    quad = ((pb0[0], pb0[1]), (pb1[0], pb1[1]),
                            (pt1[0], pt1[1]), (pt0[0], pt0[1]))
                    sx = int(min(p[0] for p in quad))
                    sy = int(min(p[1] for p in quad))
                    largura = max(1, int(max(p[0] for p in quad)) - sx + 1)
                    altura = max(1, int(max(p[1] for p in quad)) - sy + 1)
                    if largura > 2500 or altura > 1800:
                        continue
                    if sx > LARGURA or sy > ALTURA or sx + largura < 0 or sy + altura < 0:
                        continue

                    src_x = min(largura_img - 1, int(u0 * largura_img))
                    src_x2 = min(largura_img, max(src_x + 1, int(u1 * largura_img)))
                    sub = imagem.subsurface((src_x, 0, src_x2 - src_x, altura_img))

                    tira = pygame.Surface((largura, altura), pygame.SRCALPHA, 32)
                    tira.blit(pygame.transform.scale(sub, (largura, altura)), (0, 0))

                    # Máscara: recorta a tira no formato exato do quadrilátero,
                    # para a folha não vazar do tampo inclinado.
                    mascara = self._mascara_para(largura, altura)
                    pygame.draw.polygon(mascara, (255, 255, 255, 255),
                                        [(x - sx, y - sy) for x, y in quad])
                    tira.blit(mascara, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

                    tiras.append((tira, (sx, sy)))
                return tiras

            self._blitar_cache("papiro", chave, construir)

        def _mascara_para(self, largura, altura):
            """Superfície de máscara reaproveitada entre fatias."""
            rascunho = self._scratch_mascara
            if rascunho is None or rascunho.get_width() < largura or rascunho.get_height() < altura:
                rascunho = pygame.Surface((max(largura, 400), max(altura, 400)),
                                          pygame.SRCALPHA, 32)
                self._scratch_mascara = rascunho
            mascara = rascunho.subsurface((0, 0, largura, altura))
            mascara.fill((0, 0, 0, 0))
            return mascara

        # ---------------------------------------------------------------------
        # SPOTLIGHTS
        # ---------------------------------------------------------------------

        def desenhar_feixes_spotlights(self):
            """Spots LED no teto e o feixe cônico do spot ativo."""
            cam = self.cam
            tela = self.tela
            circulo = pygame.draw.circle
            linha = pygame.draw.line

            for i, spot in enumerate(self.spots_led):
                p_proj = cam.projetar(spot["pos"])
                if p_proj is None:
                    continue
                a_proj = cam.projetar(spot["alvo"])
                if a_proj is None:
                    continue

                eh_ativo = (i == self.obra_foco_idx)
                cor_luz = spot["cor"] if eh_ativo else (90, 100, 120)
                origem = (p_proj[0], p_proj[1])
                alvo = (a_proj[0], a_proj[1])

                circulo(tela, cor_luz, origem, 7 if eh_ativo else 4)
                circulo(tela, (255, 255, 255), origem, 3 if eh_ativo else 2)

                if eh_ativo:
                    linha(tela, COR_LUZ_LED, origem, alvo, 2)
                    dx_cone = 45
                    linha(tela, (255, 250, 200), origem, (alvo[0] - dx_cone, alvo[1]), 1)
                    linha(tela, (255, 250, 200), origem, (alvo[0] + dx_cone, alvo[1]), 1)
