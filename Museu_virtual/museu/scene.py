"""Módulo de scene da aplicação."""
import math
import os
import sys
import pygame

from .config import *
from .math3d import *
from .geometry import *
from .objects import *


class SceneMixin:
        def __init__(self):
            pygame.init()
            pygame.display.set_caption("Museu Virtual 3D — História da Arte e da Antiguidade (AP1)")
            self.tela = pygame.display.set_mode((LARGURA, ALTURA))
            self.relogio = pygame.time.Clock()

            # Fontes Tipográficas
            self.fonte_titulo = pygame.font.SysFont("Georgia", 22, bold=True)
            self.fonte_subtitulo = pygame.font.SysFont("Arial", 16, bold=True)
            self.fonte_hud = pygame.font.SysFont("Arial", 15)
            self.fonte_pequena = pygame.font.SysFont("Arial", 12)
            self.fonte_placa = pygame.font.SysFont("Georgia", 11, bold=True)

            # Máquina de Estados da Visita Guiada (Requisito Obrigatório AP1)
            self.ESTADO_PARADO = "PARADO"
            self.ESTADO_EXECUTANDO = "EXECUTANDO"
            self.ESTADO_PAUSADO = "PAUSADO"
            self.ESTADO_CONCLUIDO = "CONCLUIDO"
            self.estado_atual = self.ESTADO_PARADO

            # Modos de Apresentação e Navegação da Câmera
            self.MODO_APRESENTACAO = "APRESENTAÇÃO AP1 (DISCRETO)"
            self.MODO_NAVEGACAO_LIVRE = "NAVEGAÇÃO LIVRE (WASD + MOUSE)"
            self.modo_operacao = self.MODO_APRESENTACAO

            # Submodos de Câmera da Apresentação
            self.MODO_CAM_GERAL = "PLANO_GERAL"
            self.MODO_CAM_FOCO  = "FOCO_ANIMADO"
            self.submodo_cam = self.MODO_CAM_GERAL

            # Coordenadas e Ângulos da Câmera
            self.cam_pos_geral = [0.0, 1.8, -1.8]
            self.cam_pos_atual = list(self.cam_pos_geral)
            self.cam_pos_alvo  = list(self.cam_pos_geral)
            self.cam_yaw_atual = 0.0
            self.cam_yaw_alvo  = 0.0
            self.cam_pitch_atual = 0.0
            self.cam_pitch_alvo  = 0.0

            # Mouse look
            self.mouse_arrastando = False
            self.mouse_ultimo_pos = (0, 0)
            self.sensibilidade_mouse = 0.0035

            # Cronômetro e Etapas
            self.obra_foco_idx = 0
            self.tempo_animacao = 0.0
            self.duracao_etapa = 7.5 # Segundos por sala na visita guiada
            self.exibir_creditos = False

            # Controles específicos da apresentação da escultura
            self.escultura_rodando = True
            self.escultura_rot_manual = 0.0

            # Carregar Texturas/Imagens das Obras de Arte
            self.carregar_imagens_obras()

            # Inicializar Cena 3D, Galerias, Modelos e Spots
            self.inicializar_obras_e_galerias()

        # -------------------------------------------------------------------------
        # INICIALIZAÇÃO DE ASSETS E MATERIAIS
        # -------------------------------------------------------------------------

        def carregar_imagens_obras(self):
            """Carrega e prepara as superfícies das obras históricas em domínio público."""
            # 1. A Ilha dos Mortos
            if os.path.exists(PATH_TOTENINSEL):
                img_bruta = pygame.image.load(PATH_TOTENINSEL).convert()
                # Escala prévia para manter alto desempenho no laço principal
                self.img_toteninsel = pygame.transform.smoothscale(img_bruta, (860, 480))
            else:
                self.img_toteninsel = pygame.Surface((860, 480))
                self.img_toteninsel.fill((20, 30, 45))
                pygame.draw.circle(self.img_toteninsel, (200, 220, 255), (430, 200), 70)

            # 2. Papiro de Ani (Livro dos Mortos)
            if os.path.exists(PATH_PAPYRUS):
                img_bruta = pygame.image.load(PATH_PAPYRUS).convert()
                self.img_papiro = pygame.transform.smoothscale(img_bruta, (780, 420))
            else:
                self.img_papiro = pygame.Surface((780, 420))
                self.img_papiro.fill((210, 180, 130))


        def inicializar_obras_e_galerias(self):
            """Monta a planta baixa do museu com 3 salas temáticas e objetos 3D."""
            # Metadados Didáticos e Históricos das Três Obras (1: Escultura, 2: Pintura, 3: Papiro)
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

            # 3 Luminárias LED no Teto com feixes cônicos (Sala 1: Escultura, Sala 2: Pintura, Sala 3: Papiro)
            self.spots_led = [
                {"pos": [-8.0, 3.8,  8.5], "alvo": [-8.0, 1.4,  8.5], "cor": self.info_obras[0]["cor_spot"], "raio_cone": 2.0},
                {"pos": [ 0.0, 3.8, 11.2], "alvo": [ 0.0, 1.6, 12.8], "cor": self.info_obras[1]["cor_spot"], "raio_cone": 2.4},
                {"pos": [ 8.0, 3.8,  8.5], "alvo": [ 8.0, 2.0,  8.5], "cor": self.info_obras[2]["cor_spot"], "raio_cone": 2.5}
            ]

            # ---------------------------------------------------------------------
            # CRIAÇÃO DOS OBJETOS DA CENA (Atende ao Requisito 3 da AP1)
            # ---------------------------------------------------------------------
            self.objetos = []

            # 1. Três Instâncias de Pedestais com parâmetros diferentes (Requisito 3.1):
            # Pedestal 1: Sala de Pinturas (suporte decorativo/banco central)
            ped1 = Objeto3D("Pedestal_Sala1", VERTICES_PEDESTAL_COMPLETO, FACES_PEDESTAL_COMPLETO,
                            pos=(0.0, -1.2, 5.0), escala=(0.8, 0.45, 0.8), cor_base=(100, 110, 130))
            # Pedestal 2: Sala de Esculturas (pedestal de mármore esbelto para Nefertiti)
            ped2 = Objeto3D("Pedestal_Sala2", VERTICES_PEDESTAL_COMPLETO, FACES_PEDESTAL_COMPLETO,
                            pos=(-8.0, -1.2, 8.5), escala=(1.0, 0.9, 1.0), cor_base=COR_MARMORE_PED)
            # Pedestal 3: Sala de Manuscritos (base de apoio arquitetônica, apoiada no piso)
            ped3 = Objeto3D("Pedestal_Sala3", VERTICES_PEDESTAL_COMPLETO, FACES_PEDESTAL_COMPLETO,
                            pos=(8.0, -1.2, 11.5), escala=(0.7, 0.9, 0.7), cor_base=(110, 80, 60))
            # Mantém apenas o pedestal da escultura; os pilares auxiliares foram removidos.
            self.pedestais = [ped2]
            self.objetos.extend(self.pedestais)

            # 2. Obra 1 (Pintura): Moldura 3D clássica na parede norte da Sala Central
            self.moldura_toteninsel = Objeto3D(
                "Moldura_Toteninsel", VERTICES_MOLDURA_PINTURA, FACES_MOLDURA_PINTURA,
                pos=(0.0, 1.7, 12.8), escala=(1.0, 1.0, 1.0), cor_base=COR_MOLDURA_OURO, eh_superficie_arte=True
            )
            self.objetos.append(self.moldura_toteninsel)

            # 3. Obra 2 (Escultura): Busto de Nefertiti na Sala Oeste
            # Carrega o OBJ otimizado (452 vértices / 894 faces) ou fallback
            v_nef, f_nef = carregar_obj(PATH_NEFERTITI)
            if v_nef is None or len(v_nef) == 0:
                v_nef, f_nef = gerar_malha_busto_fallback()
            
            # Posicionada no topo do pedestal da Sala 2 (y_pedestal topo = -1.2 + 1.7*0.9 ≈ 0.33)
            self.busto_nefertiti = Objeto3D(
                "Busto_Nefertiti", v_nef, f_nef,
                pos=(-8.0, 0.35, 8.5), escala=(0.85, 0.85, 0.85), cor_base=(215, 195, 160)
            )
            self.objetos.append(self.busto_nefertiti)

            # 4. Obra 3 (Manuscrito): Vitrine de Madeira Nobre e Redoma 3D na Sala Leste
            # Objeto Composto por Múltiplas Estruturas (Requisito 3.3)
            self.vitrine_papiro = Objeto3D(
                "Vitrine_Papiro", VERTICES_VITRINE_MANUSCRITO, FACES_VITRINE_MANUSCRITO,
                pos=(8.0, -0.55, 8.5), escala=(1.1, 1.65, 1.1), cor_base=COR_MOGNO_VITRINE, eh_superficie_arte=True
            )
            self.objetos.append(self.vitrine_papiro)

            # Folha de papiro como objeto 3D físico e fixo sobre o suporte da vitrine.
            # A transformação é constante no mundo e não depende da câmera.
            self.papiro_ani_obj = Objeto3D(
                "Papiro_Ani", VERTICES_PAPIRO_ANI, FACES_PAPIRO_ANI,
                # Mesma origem da vitrine: os vértices locais já acompanham o tampo inclinado.
                pos=(8.0, -0.55, 8.5), escala=(1.0, 1.0, 1.0),
                rot=(0.0, 0.0, 0.0), cor_base=(210, 185, 120)
            )
            self.objetos.append(self.papiro_ani_obj)

            # 5. Objetos Simples sem partes: Três Placas de Identificação em Bronze (Requisito 3.2)
            placa1 = Objeto3D("Placa_Sala1", VERTICES_PLACA, FACES_PLACA, pos=(0.0, -0.25, 12.75), escala=(0.8, 0.8, 1.0), cor_base=COR_PLACA_BRONZE)
            placa2 = Objeto3D("Placa_Sala2", VERTICES_PLACA, FACES_PLACA, pos=(-8.0, -0.65, 7.55), escala=(0.7, 0.7, 1.0), cor_base=COR_PLACA_BRONZE)
            placa3 = Objeto3D("Placa_Sala3", VERTICES_PLACA, FACES_PLACA, pos=(8.0, -0.15, 7.35), escala=(0.7, 0.7, 1.0), cor_base=COR_PLACA_BRONZE)
            self.placas = [placa1, placa2, placa3]
            self.objetos.extend(self.placas)

            # 6. Paredes e Portais Arquitetônicos das Salas
            self.inicializar_arquitetura_paredes()


        def inicializar_arquitetura_paredes(self):
            """Gera as faces 3D das paredes externas e divisórias com portais/arcos."""
            # Paredes delimitadoras:
            # Paredes de Fundo (Norte: z = 13.5), Laterais (x = -13.0 e +13.0), Sul (z = -3.5)
            # Divisórias entre salas em x = -4.5 e x = +4.5 com abertura de passagem (z entre 2.5 e 7.0)
            y_chao, y_teto = -1.2, 4.0
            self.paredes_faces = [
                # Parede Norte Central (atrás de Toteninsel)
                [(-4.5, y_chao, 13.5), (4.5, y_chao, 13.5), (4.5, y_teto, 13.5), (-4.5, y_teto, 13.5)],
                # Parede Norte Sala 2 (Esculturas)
                [(-13.0, y_chao, 13.5), (-4.5, y_chao, 13.5), (-4.5, y_teto, 13.5), (-13.0, y_teto, 13.5)],
                # Parede Norte Sala 3 (Manuscritos)
                [(4.5, y_chao, 13.5), (13.0, y_chao, 13.5), (13.0, y_teto, 13.5), (4.5, y_teto, 13.5)],
                # Paredes Laterais Externas
                [(-13.0, y_chao, -3.5), (-13.0, y_chao, 13.5), (-13.0, y_teto, 13.5), (-13.0, y_teto, -3.5)],
                [(13.0, y_chao, 13.5), (13.0, y_chao, -3.5), (13.0, y_teto, -3.5), (13.0, y_teto, 13.5)],
                # Parede Sul (Frente da Galeria)
                [(13.0, y_chao, -3.5), (-13.0, y_chao, -3.5), (-13.0, y_teto, -3.5), (13.0, y_teto, -3.5)],
                # Divisória Oeste: Trecho Fundo (z: 7.0 a 13.5)
                [(-4.5, y_chao, 7.0), (-4.5, y_chao, 13.5), (-4.5, y_teto, 13.5), (-4.5, y_teto, 7.0)],
                # Divisória Oeste: Trecho Frente (z: -3.5 a 2.5)
                [(-4.5, y_chao, -3.5), (-4.5, y_chao, 2.5), (-4.5, y_teto, 2.5), (-4.5, y_teto, -3.5)],
                # Portal Oeste: Viga Superior do Arco (z: 2.5 a 7.0, y: 2.8 a 4.0)
                [(-4.5, 2.8, 2.5), (-4.5, 2.8, 7.0), (-4.5, y_teto, 7.0), (-4.5, y_teto, 2.5)],
                # Divisória Leste: Trecho Fundo (z: 7.0 a 13.5)
                [(4.5, y_chao, 13.5), (4.5, y_chao, 7.0), (4.5, y_teto, 7.0), (4.5, y_teto, 13.5)],
                # Divisória Leste: Trecho Frente (z: -3.5 a 2.5)
                [(4.5, y_chao, 2.5), (4.5, y_chao, -3.5), (4.5, y_teto, -3.5), (4.5, y_teto, 2.5)],
                # Portal Leste: Viga Superior do Arco (z: 2.5 a 7.0, y: 2.8 a 4.0)
                [(4.5, 2.8, 7.0), (4.5, 2.8, 2.5), (4.5, y_teto, 2.5), (4.5, y_teto, 7.0)],
            ]
            self.teto_faces = [[
                (-13.0, y_teto, -3.5),
                (13.0, y_teto, -3.5),
                (13.0, y_teto, 13.5),
                (-13.0, y_teto, 13.5)
            ]]
            self.portas = [
                # Ambas as portas abrem suas folhas para dentro de suas respectivas galerias
                PortaArticulada("Porta_Oeste", -4.5, -1.0, -1.0),
                PortaArticulada("Porta_Leste", 4.5, 1.0, 1.0)
            ]

        # -------------------------------------------------------------------------
        # REINICIALIZAÇÃO DO MUSEU
        # -------------------------------------------------------------------------

        def reiniciar(self):
            """Reseta máquinas de estados, tempos, objetos e posicionamentos."""
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

            for porta in self.portas:
                porta.resetar()

            for obj in self.objetos:
                obj.resetar()

        # -------------------------------------------------------------------------
        # TESTE DE VISIBILIDADE / ILUMINAÇÃO BINÁRIA (REQUISITO 3.9)
        # Inspirado em Traçado de Raio Simplificado (Ray Casting Cone-Sphere)
        # -------------------------------------------------------------------------

        def testar_iluminacao_binaria(self):
            """
            Calcula o traçado do raio de luz partindo de cada refletor LED no teto.
            Se a distância entre o eixo central do feixe de luz ativo e a obra for
            menor que o raio do cone de luz, a obra é marcada com ILUMINADO = 1 (True);
            caso contrário, ILUMINADO = 0 (False - permanece na penumbra ambiente).
            """
            # Obra ativa recebe o foco do holofote principal
            for i, spot in enumerate(self.spots_led):
                # A iluminação do spot i se ativa prioritariamente na etapa da sua sala
                eh_spot_ativo = (i == self.obra_foco_idx)
                
                # Ponto de origem do raio no projetor e alvo no chão/objeto
                origem_raio = spot["pos"]
                alvo_spot   = spot["alvo"]

                # Distância euclidiana entre a obra correspondente e o eixo do raio
                obra = None
                if i == 0: obra = self.busto_nefertiti
                elif i == 1: obra = self.moldura_toteninsel
                elif i == 2: obra = self.vitrine_papiro

                dist = math.sqrt(
                    (obra.pos[0] - alvo_spot[0])**2 +
                    (obra.pos[1] - alvo_spot[1])**2 +
                    (obra.pos[2] - alvo_spot[2])**2
                )

                # Teste Binário de Interseção Cone-Objeto
                obra.iluminado = (eh_spot_ativo and dist <= spot["raio_cone"])

        # -------------------------------------------------------------------------
        # SISTEMA DE COLISÃO DO VISITANTE (MODO NAVEGAÇÃO LIVRE)
        # -------------------------------------------------------------------------
