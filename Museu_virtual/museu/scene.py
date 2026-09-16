"""Inicialização da cena: pygame, câmera, objetos, metadados e iluminação."""
import math
import os
import pygame

from .config import *
from .math3d import *
from .geometry import *
from .objects import *


class SceneMixin:
        def __init__(self):
            pygame.init()
            pygame.display.set_caption("Museu Virtual 3D — História da Arte e da Antiguidade (AP1)")
            self.tela = self._abrir_janela()
            self.relogio = pygame.time.Clock()

            # Só os eventos realmente usados chegam à fila: menos trabalho por quadro.
            pygame.event.set_allowed([pygame.QUIT, pygame.KEYDOWN,
                                      pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP,
                                      pygame.MOUSEMOTION])

            # Fontes tipográficas, dimensionadas junto com o tamanho da janela
            def fonte(nome, tamanho_base, negrito=False):
                tamanho = max(10, round(tamanho_base * ESCALA))
                return pygame.font.SysFont(nome, tamanho, bold=negrito)

            self.fonte_titulo = fonte("Georgia", 22, True)
            self.fonte_subtitulo = fonte("Arial", 16, True)
            self.fonte_hud = fonte("Arial", 15)
            self.fonte_pequena = fonte("Arial", 12)
            self.fonte_placa = fonte("Georgia", 11, True)

            # Máquina de estados da visita guiada
            self.ESTADO_PARADO = "PARADO"
            self.ESTADO_EXECUTANDO = "EXECUTANDO"
            self.ESTADO_PAUSADO = "PAUSADO"
            self.ESTADO_CONCLUIDO = "CONCLUIDO"
            self.estado_atual = self.ESTADO_PARADO

            # Modos de apresentação e navegação
            self.MODO_APRESENTACAO = "APRESENTAÇÃO AP1 (DISCRETO)"
            self.MODO_NAVEGACAO_LIVRE = "NAVEGAÇÃO LIVRE (WASD + MOUSE)"
            self.modo_operacao = self.MODO_APRESENTACAO

            # Submodos de câmera da apresentação
            self.MODO_CAM_GERAL = "PLANO_GERAL"
            self.MODO_CAM_FOCO = "FOCO_ANIMADO"
            self.submodo_cam = self.MODO_CAM_GERAL

            # Coordenadas e ângulos da câmera
            self.cam_pos_geral = [0.0, 1.8, -1.8]
            self.cam_pos_atual = list(self.cam_pos_geral)
            self.cam_pos_alvo = list(self.cam_pos_geral)
            self.cam_yaw_atual = 0.0
            self.cam_yaw_alvo = 0.0
            self.cam_pitch_atual = 0.0
            self.cam_pitch_alvo = 0.0

            # Câmera com trigonometria em cache, sincronizada uma vez por quadro
            self.cam = Camera(self.cam_pos_atual, self.cam_yaw_atual, self.cam_pitch_atual)

            # Mouse look
            self.mouse_arrastando = False
            self.mouse_ultimo_pos = (0, 0)
            self.sensibilidade_mouse = 0.0035

            # Cronômetro e etapas
            self.obra_foco_idx = 0
            self.tempo_animacao = 0.0
            self.duracao_etapa = 7.5  # segundos por sala na visita guiada
            self.exibir_creditos = False
            self.mostrar_fps = False

            # Controles específicos da apresentação da escultura
            self.escultura_rodando = True
            self.escultura_rot_manual = 0.0

            # Buffers reaproveitados entre quadros
            self._buffer_vidro = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA, 32)
            self._scratch_mascara = None
            self._cache_arte = {}
            self._cache_texto = {}

            self.carregar_imagens_obras()
            self.inicializar_obras_e_galerias()
            self.preparar_cache_hud()

        # -------------------------------------------------------------------------
        # JANELA E CÂMERA
        # -------------------------------------------------------------------------

        def _abrir_janela(self):
            """Abre a janela com double buffer e, se possível, com vsync."""
            flags = pygame.DOUBLEBUF
            if USAR_VSYNC:
                try:
                    return pygame.display.set_mode((LARGURA, ALTURA), flags, vsync=1)
                except (TypeError, pygame.error):
                    pass
            return pygame.display.set_mode((LARGURA, ALTURA), flags)

        def sincronizar_camera(self):
            """Recalcula a trigonometria da câmera — uma vez por quadro, não por vértice."""
            self.cam.sincronizar(self.cam_pos_atual, self.cam_yaw_atual, self.cam_pitch_atual)

        # -------------------------------------------------------------------------
        # ASSETS E MATERIAIS
        # -------------------------------------------------------------------------

        def carregar_imagens_obras(self):
            """Carrega as texturas das obras, já no tamanho de trabalho.

            Além da versão iluminada, guarda uma cópia escurecida pronta. Assim a
            penumbra não custa uma superfície nova e uma composição por fatia a
            cada quadro — basta escolher qual imagem usar.
            """
            if os.path.exists(PATH_TOTENINSEL):
                bruta = pygame.image.load(PATH_TOTENINSEL).convert()
                self.img_toteninsel = pygame.transform.smoothscale(bruta, (860, 480))
            else:
                self.img_toteninsel = pygame.Surface((860, 480))
                self.img_toteninsel.fill((20, 30, 45))
                pygame.draw.circle(self.img_toteninsel, (200, 220, 255), (430, 200), 70)
            self.img_toteninsel = self.img_toteninsel.convert()

            sombra = pygame.Surface(self.img_toteninsel.get_size(), pygame.SRCALPHA)
            sombra.fill((0, 0, 0, 140))
            self.img_toteninsel_escura = self.img_toteninsel.copy()
            self.img_toteninsel_escura.blit(sombra, (0, 0))
            self.img_toteninsel_escura = self.img_toteninsel_escura.convert()

            if os.path.exists(PATH_PAPYRUS):
                bruta = pygame.image.load(PATH_PAPYRUS).convert()
                self.img_papiro = pygame.transform.smoothscale(bruta, (780, 420))
            else:
                self.img_papiro = pygame.Surface((780, 420))
                self.img_papiro.fill((210, 180, 130))
            self.img_papiro = self.img_papiro.convert()

            self.img_papiro_escuro = self.img_papiro.copy()
            self.img_papiro_escuro.fill((150, 150, 150), special_flags=pygame.BLEND_MULT)
            self.img_papiro_escuro = self.img_papiro_escuro.convert()

        # -------------------------------------------------------------------------
        # CENA
        # -------------------------------------------------------------------------

        def inicializar_obras_e_galerias(self):
            """Cria e posiciona pedestais, obras, vitrines, placas e portas."""
            self.info_obras = [
                {
                    "sala": "SALA 1: GALERIA DE ESCULTURAS DA ANTIGUIDADE",
                    "titulo": "Busto de Nefertiti",
                    "artista": "Tutmés (Escultor Real da Corte de Amarna)",
                    "periodo": "Novo Império Egípcio (XVIII Dinastia)",
                    "data": "c. 1345 a.C.",
                    "material": "Calcário revestido de estuque policromado (48 cm)",
                    "localizacao": "Museu Egípcio e Coleção de Papiros, Berlim",
                    "desc": "Ícone supremo da arte e da elegância \n clássica egípcia, retratando Nefertiti com sua emblemática \n coroa azul cilíndrica e uraeus real.",
                    "cor_spot": (255, 250, 220),
                    "pos_foco_cam": [-8.0, 1.4, 5.0],
                    "yaw_foco": 0.0,
                    "pitch_foco": 0.02
                },
                {
                    "sala": "SALA 2: GALERIA DE PINTURAS SIMBOLISTAS",
                    "titulo": "A Ilha dos Mortos (Die Toteninsel)",
                    "artista": "Arnold Böcklin (1827–1901)",
                    "periodo": "Simbolismo (Século XIX)",
                    "data": "1880 (Versão III)",
                    "material": "Óleo sobre tela de madeira (111 × 155 cm)",
                    "localizacao": "Alte Nationalgalerie, Berlim",
                    "desc": "Obra-prima mística retratando uma ilha rochosa cercada por ciprestes escuros\n e um barco fúnebre conduzido por Caronte em direção \naos portais da eternidade.",
                    "cor_spot": (255, 245, 200),
                    "pos_foco_cam": [0.0, 1.8, 6.8],
                    "yaw_foco": 0.0,
                    "pitch_foco": 0.09
                },
                {
                    "sala": "SALA 3: GALERIA DE MANUSCRITOS E ANTIGUIDADES",
                    "titulo": "Papiro de Ani (Livro dos Mortos)",
                    "artista": "Escribas Teólogos e Iluminadores de Tebas",
                    "periodo": "Império Novo do Antigo Egito",
                    "data": "c. 1250 a.C. (XIX Dinastia)",
                    "material": "Papiro manuscrito com escrita hieroglífica e vinhetas (23,6 m)",
                    "localizacao": "British Museum, Londres",
                    "desc": "O mais completo e ricamente iluminado rolo funerário\n sobrevivente da antiguidade, contendo hinos, litanias e o julgamento da alma \n(pesagem do coração).",
                    "cor_spot": (255, 240, 195),
                    "pos_foco_cam": [8.0, 2.6, 5.3],
                    "yaw_foco": 0.0,
                    "pitch_foco": -0.54
                }
            ]

            # Luminárias LED no teto, uma por sala temática
            self.spots_led = [
                {"pos": [-8.0, 3.8,  8.5], "alvo": [-8.0, 1.4,  8.5], "cor": self.info_obras[0]["cor_spot"], "raio_cone": 2.0},
                {"pos": [ 0.0, 3.8, 11.2], "alvo": [ 0.0, 1.6, 12.8], "cor": self.info_obras[1]["cor_spot"], "raio_cone": 2.4},
                {"pos": [ 8.0, 3.8,  8.5], "alvo": [ 8.0, 2.0,  8.5], "cor": self.info_obras[2]["cor_spot"], "raio_cone": 2.5}
            ]

            self.objetos = []

            # 1. Pedestal de mármore da escultura (instância do modelo genérico)
            ped_escultura = Objeto3D("Pedestal_Sala2", VERTICES_PEDESTAL_COMPLETO, FACES_PEDESTAL_COMPLETO,
                                     pos=(-8.0, -1.2, 8.5), escala=(1.0, 0.9, 1.0), cor_base=COR_MARMORE_PED)
            self.pedestais = [ped_escultura]
            self.objetos.extend(self.pedestais)

            # 2. Moldura 3D de "A Ilha dos Mortos" na parede norte da sala central
            self.moldura_toteninsel = Objeto3D(
                "Moldura_Toteninsel", VERTICES_MOLDURA_PINTURA, FACES_MOLDURA_PINTURA,
                pos=(0.0, 1.7, 12.8), escala=(1.0, 1.0, 1.0), cor_base=COR_MOLDURA_OURO,
                eh_superficie_arte=True
            )
            self.objetos.append(self.moldura_toteninsel)

            # 3. Busto de Nefertiti (OBJ de 452 vértices / 894 faces, ou fallback)
            v_nef, f_nef = carregar_obj(PATH_NEFERTITI)
            if not v_nef:
                v_nef, f_nef = gerar_malha_busto_fallback()

            self.busto_nefertiti = Objeto3D(
                "Busto_Nefertiti", v_nef, f_nef,
                pos=(-8.0, 0.35, 8.5), escala=(0.85, 0.85, 0.85), cor_base=(215, 195, 160)
            )
            self.objetos.append(self.busto_nefertiti)

            # 4. Vitrine de madeira nobre e redoma translúcida da sala leste
            self.vitrine_papiro = Objeto3D(
                "Vitrine_Papiro", VERTICES_VITRINE_MANUSCRITO, FACES_VITRINE_BASE,
                pos=(8.0, -0.55, 8.5), escala=(1.1, 1.65, 1.1), cor_base=COR_MOGNO_VITRINE,
                eh_superficie_arte=True
            )
            self.objetos.append(self.vitrine_papiro)

            self.redoma_papiro = Objeto3D(
                "Redoma_Papiro", VERTICES_VITRINE_MANUSCRITO, FACES_VITRINE_REDOMA,
                pos=(8.0, -0.55, 8.5), escala=(1.1, 1.65, 1.1), eh_vidro=True
            )
            self.objetos.append(self.redoma_papiro)

            # Folha de papiro apoiada no tampo inclinado da vitrine
            self.papiro_ani_obj = Objeto3D(
                "Papiro_Ani", VERTICES_PAPIRO_ANI, FACES_PAPIRO_ANI,
                pos=(8.0, -0.55, 8.5), escala=(1.0, 1.0, 1.0),
                rot=(0.0, 0.0, 0.0), cor_base=(210, 185, 120)
            )
            self.objetos.append(self.papiro_ani_obj)

            # 5. Placas de identificação em bronze (objetos simples, sem partes)
            self.placas = [
                Objeto3D("Placa_Sala1", VERTICES_PLACA, FACES_PLACA, pos=(0.0, -0.25, 12.75), escala=(0.8, 0.8, 1.0), cor_base=COR_PLACA_BRONZE),
                Objeto3D("Placa_Sala2", VERTICES_PLACA, FACES_PLACA, pos=(-8.0, -0.65, 7.55), escala=(0.7, 0.7, 1.0), cor_base=COR_PLACA_BRONZE),
                Objeto3D("Placa_Sala3", VERTICES_PLACA, FACES_PLACA, pos=(8.0, -0.15, 7.35), escala=(0.7, 0.7, 1.0), cor_base=COR_PLACA_BRONZE),
            ]
            self.objetos.extend(self.placas)

            self.inicializar_arquitetura_paredes()

        def inicializar_arquitetura_paredes(self):
            """Faces das paredes externas, divisórias, portais, teto e grade do piso."""
            y_chao, y_teto = -1.2, 4.0
            self.paredes_faces = [
                # Parede norte central (atrás de Toteninsel)
                [(-4.5, y_chao, 13.5), (4.5, y_chao, 13.5), (4.5, y_teto, 13.5), (-4.5, y_teto, 13.5)],
                # Parede norte da sala de esculturas
                [(-13.0, y_chao, 13.5), (-4.5, y_chao, 13.5), (-4.5, y_teto, 13.5), (-13.0, y_teto, 13.5)],
                # Parede norte da sala de manuscritos
                [(4.5, y_chao, 13.5), (13.0, y_chao, 13.5), (13.0, y_teto, 13.5), (4.5, y_teto, 13.5)],
                # Paredes laterais externas
                [(-13.0, y_chao, -3.5), (-13.0, y_chao, 13.5), (-13.0, y_teto, 13.5), (-13.0, y_teto, -3.5)],
                [(13.0, y_chao, 13.5), (13.0, y_chao, -3.5), (13.0, y_teto, -3.5), (13.0, y_teto, 13.5)],
                # Parede sul (frente da galeria)
                [(13.0, y_chao, -3.5), (-13.0, y_chao, -3.5), (-13.0, y_teto, -3.5), (13.0, y_teto, -3.5)],
                # Divisória oeste: trecho do fundo e da frente
                [(-4.5, y_chao, 7.0), (-4.5, y_chao, 13.5), (-4.5, y_teto, 13.5), (-4.5, y_teto, 7.0)],
                [(-4.5, y_chao, -3.5), (-4.5, y_chao, 2.5), (-4.5, y_teto, 2.5), (-4.5, y_teto, -3.5)],
                # Viga superior do portal oeste
                [(-4.5, 2.8, 2.5), (-4.5, 2.8, 7.0), (-4.5, y_teto, 7.0), (-4.5, y_teto, 2.5)],
                # Divisória leste: trecho do fundo e da frente
                [(4.5, y_chao, 13.5), (4.5, y_chao, 7.0), (4.5, y_teto, 7.0), (4.5, y_teto, 13.5)],
                [(4.5, y_chao, 2.5), (4.5, y_chao, -3.5), (4.5, y_teto, -3.5), (4.5, y_teto, 2.5)],
                # Viga superior do portal leste
                [(4.5, 2.8, 7.0), (4.5, 2.8, 2.5), (4.5, y_teto, 2.5), (4.5, y_teto, 7.0)],
            ]
            self.teto_faces = [[
                (-13.0, y_teto, -3.5),
                (13.0, y_teto, -3.5),
                (13.0, y_teto, 13.5),
                (-13.0, y_teto, 13.5)
            ]]

            # Grade do piso pré-montada: os extremos das linhas não mudam nunca.
            y_piso = -1.2
            self.linhas_piso = [
                ((x, y_piso, -3.5), (x, y_piso, 13.5)) for x in range(-13, 14, 2)
            ] + [
                ((-13.0, y_piso, z), (13.0, y_piso, z)) for z in range(-3, 14, 2)
            ]

            self.portas = [
                # As folhas abrem para a galeria central, sem esbarrar nos expositores
                PortaArticulada("Porta_Oeste", -4.5, 1.0, 1.0),
                PortaArticulada("Porta_Leste", 4.5, -1.0, -1.0)
            ]

        # -------------------------------------------------------------------------
        # REINICIALIZAÇÃO
        # -------------------------------------------------------------------------

        def reiniciar(self):
            """Volta tudo ao estado inicial: câmera, estados, timers, objetos e portas."""
            self.estado_atual = self.ESTADO_PARADO
            self.tempo_animacao = 0.0
            self.obra_foco_idx = 0
            self.submodo_cam = self.MODO_CAM_GERAL
            self.cam_pos_alvo = list(self.cam_pos_geral)
            self.cam_pos_atual = list(self.cam_pos_geral)
            self.cam_yaw_alvo = 0.0
            self.cam_yaw_atual = 0.0
            self.cam_pitch_alvo = 0.0
            self.cam_pitch_atual = 0.0
            self.sincronizar_camera()

            for porta in self.portas:
                porta.resetar()
            for obj in self.objetos:
                obj.resetar()
            self._cache_arte.clear()

        # -------------------------------------------------------------------------
        # ILUMINAÇÃO BINÁRIA (traçado de raio simplificado cone-esfera)
        # -------------------------------------------------------------------------

        def testar_iluminacao_binaria(self):
            """Marca cada obra como iluminada quando ela cai dentro do cone do seu spot."""
            obras = (self.busto_nefertiti, self.moldura_toteninsel, self.vitrine_papiro)
            for i, spot in enumerate(self.spots_led):
                obra = obras[i]
                alvo = spot["alvo"]
                dx = obra.pos[0] - alvo[0]
                dy = obra.pos[1] - alvo[1]
                dz = obra.pos[2] - alvo[2]
                dentro_do_cone = (dx * dx + dy * dy + dz * dz) <= spot["raio_cone"] ** 2
                obra.iluminado = (i == self.obra_foco_idx) and dentro_do_cone
            self.redoma_papiro.iluminado = self.vitrine_papiro.iluminado
