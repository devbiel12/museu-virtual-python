"""Atualização por quadro: máquina de estados, câmera, movimentação e animações.

Otimizações desta versão:
- A câmera usa amortecimento exponencial (1 - e^(-k·dt)) no lugar de uma
  interpolação linear multiplicada por dt. A anterior mudava de velocidade
  conforme a taxa de quadros; esta chega ao alvo no mesmo tempo a 30, 60 ou
  144 FPS, o que é o que faz o movimento parecer suave.
- Quando a câmera chega ao destino, os valores são travados no alvo. Isso
  elimina o micro-tremor residual e ainda mantém válidos os caches de textura.
"""
import math
import pygame

from .config import *
from .math3d import *
from .geometry import *
from .objects import *

DOIS_PI = math.pi * 2.0


def _aproximar(atual, alvo, fator):
    return atual + (alvo - atual) * fator


def _aproximar_angulo(atual, alvo, fator):
    """Interpola pelo menor arco, sem dar a volta completa ao cruzar ±π."""
    diff = (alvo - atual + math.pi) % DOIS_PI - math.pi
    return atual + diff * fator


class AnimationMixin:
        def atualizar(self, dt):
            """Avança a simulação em dt segundos e deixa a câmera pronta para o desenho."""
            if self.estado_atual != self.ESTADO_PAUSADO:
                for porta in self.portas:
                    porta.atualizar(dt)

            # 1. Máquina de estados e cronômetro da visita guiada
            if self.estado_atual == self.ESTADO_EXECUTANDO:
                self.tempo_animacao += dt
                etapa = int(self.tempo_animacao / self.duracao_etapa)
                if etapa < len(self.info_obras):
                    if self.obra_foco_idx != etapa:
                        self.obra_foco_idx = etapa
                        self.preparar_portas_para_obra(etapa)
                else:
                    self.estado_atual = self.ESTADO_CONCLUIDO
                    self.submodo_cam = self.MODO_CAM_GERAL

            # 2. Câmera
            if self.modo_operacao == self.MODO_APRESENTACAO:
                self._atualizar_camera_apresentacao(dt)
            else:
                self._atualizar_navegacao_livre(dt)

            # 3. Animações dos modelos
            self._atualizar_animacoes_modelos(dt)

            # 4. Iluminação binária
            self.testar_iluminacao_binaria()

            # 5. Trigonometria da câmera, resolvida uma vez para o quadro inteiro
            self.sincronizar_camera()

        # ---------------------------------------------------------------------
        # CÂMERA DA APRESENTAÇÃO
        # ---------------------------------------------------------------------

        def _mover_camera(self, dt, suavidade):
            """Amortecimento exponencial até o alvo, independente da taxa de quadros."""
            fator = 1.0 - math.exp(-suavidade * dt)
            pos = self.cam_pos_atual
            alvo = self.cam_pos_alvo
            for i in range(3):
                pos[i] = _aproximar(pos[i], alvo[i], fator)
            self.cam_yaw_atual = _aproximar_angulo(self.cam_yaw_atual, self.cam_yaw_alvo, fator)
            self.cam_pitch_atual = _aproximar(self.cam_pitch_atual, self.cam_pitch_alvo, fator)

            # Trava no alvo quando a diferença some: sem tremor residual.
            if (abs(pos[0] - alvo[0]) < 1e-3 and abs(pos[1] - alvo[1]) < 1e-3
                    and abs(pos[2] - alvo[2]) < 1e-3
                    and abs(self.cam_yaw_atual - self.cam_yaw_alvo) < 1e-4
                    and abs(self.cam_pitch_atual - self.cam_pitch_alvo) < 1e-4):
                self.cam_pos_atual = list(alvo)
                self.cam_yaw_atual = self.cam_yaw_alvo
                self.cam_pitch_atual = self.cam_pitch_alvo

        def _atualizar_camera_apresentacao(self, dt):
            voltando_para_inicio = (self.estado_atual == self.ESTADO_CONCLUIDO
                                    or self.submodo_cam == self.MODO_CAM_GERAL)

            if not voltando_para_inicio and (self.submodo_cam == self.MODO_CAM_FOCO
                                             or self.estado_atual == self.ESTADO_EXECUTANDO):
                foco = self.info_obras[self.obra_foco_idx]
                self.cam_pos_alvo = list(foco["pos_foco_cam"])
                self.cam_yaw_alvo = foco["yaw_foco"]
                self.cam_pitch_alvo = foco["pitch_foco"]

                # A câmera só avança depois que a porta terminou de abrir.
                if self.portas_prontas_para_obra(self.obra_foco_idx):
                    self._mover_camera(dt, SUAVIDADE_CAM_FOCO)
                return

            # Visão geral panorâmica (tela inicial)
            self.cam_pos_alvo = list(self.cam_pos_geral)
            self.cam_yaw_alvo = 0.0
            self.cam_pitch_alvo = 0.0

            # Mantém aberta a porta da sala de onde a câmera está voltando.
            if self.cam_pos_atual[0] > 4.2:
                self.portas[1].abrir()
            elif self.cam_pos_atual[0] < -4.2:
                self.portas[0].abrir()
            else:
                for porta in self.portas:
                    porta.fechar()

            self._mover_camera(dt, SUAVIDADE_CAM_GERAL)

            dist = math.dist(self.cam_pos_atual, self.cam_pos_geral)
            if dist < 0.08 and abs(self.cam_yaw_atual) < 0.03:
                self.cam_pos_atual = list(self.cam_pos_geral)
                self.cam_yaw_atual = 0.0
                self.cam_pitch_atual = 0.0
                if self.estado_atual == self.ESTADO_CONCLUIDO:
                    self.estado_atual = self.ESTADO_PARADO

        # ---------------------------------------------------------------------
        # NAVEGAÇÃO LIVRE
        # ---------------------------------------------------------------------

        def _atualizar_navegacao_livre(self, dt):
            teclas = pygame.key.get_pressed()
            velocidade = 4.2 * dt  # metros por segundo

            frente_x = math.sin(self.cam_yaw_atual)
            frente_z = math.cos(self.cam_yaw_atual)
            lado_x = math.cos(self.cam_yaw_atual)
            lado_z = -math.sin(self.cam_yaw_atual)

            dx = dz = 0.0
            if teclas[pygame.K_w] or teclas[pygame.K_UP]:
                dx += frente_x; dz += frente_z
            if teclas[pygame.K_s] or teclas[pygame.K_DOWN]:
                dx -= frente_x; dz -= frente_z
            if teclas[pygame.K_a] or teclas[pygame.K_LEFT]:
                dx -= lado_x; dz -= lado_z
            if teclas[pygame.K_d] or teclas[pygame.K_RIGHT]:
                dx += lado_x; dz += lado_z

            # Normaliza a diagonal: andar em dois eixos não pode ser mais rápido.
            comprimento = math.hypot(dx, dz)
            if comprimento > 1e-6:
                escala = velocidade / comprimento
                dx *= escala
                dz *= escala

            nova_pos = [self.cam_pos_atual[0] + dx, self.cam_pos_atual[1], self.cam_pos_atual[2] + dz]
            self.abrir_porta_proxima(nova_pos)
            self.cam_pos_atual = self.aplicar_colisoes_navegacao(nova_pos)

            # Obra mais próxima define o cartão didático exibido no HUD.
            menor_dist = float("inf")
            mais_proxima = self.obra_foco_idx
            for i, spot in enumerate(self.spots_led):
                alvo = spot["alvo"]
                d = (self.cam_pos_atual[0] - alvo[0]) ** 2 + (self.cam_pos_atual[2] - alvo[2]) ** 2
                if d < menor_dist:
                    menor_dist = d
                    mais_proxima = i
            self.obra_foco_idx = mais_proxima

        # ---------------------------------------------------------------------
        # ANIMAÇÕES DOS MODELOS
        # ---------------------------------------------------------------------

        def _atualizar_animacoes_modelos(self, dt):
            # A) Rotação do busto de Nefertiti em torno do eixo Y
            if self.modo_operacao == self.MODO_APRESENTACAO and self.obra_foco_idx == 0:
                if self.escultura_rodando:
                    self.busto_nefertiti.rot[1] += 0.85 * dt
                teclas = pygame.key.get_pressed()
                if teclas[pygame.K_LEFT]:
                    self.busto_nefertiti.rot[1] += 1.8 * dt
                if teclas[pygame.K_RIGHT]:
                    self.busto_nefertiti.rot[1] -= 1.8 * dt
            elif (self.estado_atual == self.ESTADO_EXECUTANDO
                  or self.modo_operacao == self.MODO_NAVEGACAO_LIVRE):
                self.busto_nefertiti.rot[1] += 0.85 * dt

            # Mantém o ângulo em [0, 2π) para não perder precisão com o tempo.
            if self.busto_nefertiti.rot[1] >= DOIS_PI or self.busto_nefertiti.rot[1] <= -DOIS_PI:
                self.busto_nefertiti.rot[1] %= DOIS_PI

            # B) Pulsação do cone de luz do spot ativo
            if self.estado_atual == self.ESTADO_EXECUTANDO:
                pulso = 1.0 + math.sin(self.tempo_animacao * 3.5) * 0.04
                self.spots_led[self.obra_foco_idx]["raio_cone"] = 2.2 * pulso
