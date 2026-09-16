"""Módulo de animation da aplicação."""
import math
import os
import sys
import pygame

from .config import *
from .math3d import *
from .geometry import *
from .objects import *


class AnimationMixin:
        def atualizar(self, dt):
            if self.estado_atual != self.ESTADO_PAUSADO:
                for porta in self.portas:
                    porta.atualizar(dt)

            # 1. Atualizar Máquina de Estados e Temporizador da Visita Guiada (Requisito 3.6)
            if self.estado_atual == self.ESTADO_EXECUTANDO:
                self.tempo_animacao += dt

                # Avanço temporal sequencial entre as 3 salas temáticas: 0 (Escultura) -> 1 (Pintura) -> 2 (Papiro)
                etapa_calculada = int(self.tempo_animacao / self.duracao_etapa)
                if etapa_calculada < len(self.info_obras):
                    if self.obra_foco_idx != etapa_calculada:
                        self.obra_foco_idx = etapa_calculada
                        self.preparar_portas_para_obra(self.obra_foco_idx)
                else:
                    # Conclusão do tour: retorna suavemente à tela inicial sem travar
                    self.estado_atual = self.ESTADO_CONCLUIDO
                    self.submodo_cam = self.MODO_CAM_GERAL

            # 2. Atualizar Câmera conforme o Modo de Apresentação
            if self.modo_operacao == self.MODO_APRESENTACAO:
                retornando_tela_inicial = (self.estado_atual == self.ESTADO_CONCLUIDO or self.submodo_cam == self.MODO_CAM_GERAL)

                if not retornando_tela_inicial and (self.submodo_cam == self.MODO_CAM_FOCO or self.estado_atual == self.ESTADO_EXECUTANDO):
                    # Foco dinâmico na obra ativa da visita
                    foco_info = self.info_obras[self.obra_foco_idx]
                    self.cam_pos_alvo = list(foco_info["pos_foco_cam"])
                    self.cam_yaw_alvo = foco_info["yaw_foco"]
                    self.cam_pitch_alvo = foco_info["pitch_foco"]

                    # A câmera aguarda a abertura da porta antes de avançar para a obra
                    if self.portas_prontas_para_obra(self.obra_foco_idx):
                        velocidade_lerp = 3.5 * dt
                        for i in range(3):
                            self.cam_pos_atual[i] += (self.cam_pos_alvo[i] - self.cam_pos_atual[i]) * velocidade_lerp
                        self.cam_yaw_atual += (self.cam_yaw_alvo - self.cam_yaw_atual) * velocidade_lerp
                        self.cam_pitch_atual += (self.cam_pitch_alvo - self.cam_pitch_atual) * velocidade_lerp
                else:
                    # Visão geral panorâmica (Tela Inicial)
                    self.cam_pos_alvo = list(self.cam_pos_geral)
                    self.cam_yaw_alvo = 0.0
                    self.cam_pitch_alvo = 0.0

                    # Gerenciamento dinâmico das portas durante o retorno à tela inicial:
                    # Se a câmera estiver voltando da sala leste (papiro), mantém a porta leste aberta para atravessar!
                    if self.cam_pos_atual[0] > 4.2:
                        self.portas[1].abrir()
                    # Se a câmera estiver voltando da sala oeste (escultura), mantém a porta oeste aberta!
                    elif self.cam_pos_atual[0] < -4.2:
                        self.portas[0].abrir()
                    else:
                        # Câmera já voltou com segurança para a sala central: fecha as portas
                        for porta in self.portas:
                            porta.fechar()

                    # A câmera se desloca suavemente de volta à entrada sem travar
                    velocidade_lerp = 2.8 * dt
                    for i in range(3):
                        self.cam_pos_atual[i] += (self.cam_pos_alvo[i] - self.cam_pos_atual[i]) * velocidade_lerp
                    self.cam_yaw_atual += (self.cam_yaw_alvo - self.cam_yaw_atual) * velocidade_lerp
                    self.cam_pitch_atual += (self.cam_pitch_alvo - self.cam_pitch_atual) * velocidade_lerp

                    # Chegada suave e fixação na tela inicial
                    dist_origem = math.sqrt(sum((self.cam_pos_atual[i] - self.cam_pos_geral[i])**2 for i in range(3)))
                    if dist_origem < 0.08 and abs(self.cam_yaw_atual) < 0.03:
                        self.cam_pos_atual = list(self.cam_pos_geral)
                        self.cam_yaw_atual = 0.0
                        self.cam_pitch_atual = 0.0
                        if self.estado_atual == self.ESTADO_CONCLUIDO:
                            self.estado_atual = self.ESTADO_PARADO

            elif self.modo_operacao == self.MODO_NAVEGACAO_LIVRE:
                # Na navegação livre, as teclas contínuas W/A/S/D movimentam o visitante
                keys = pygame.key.get_pressed()
                velocidade_andar = 4.2 * dt # Metros por segundo

                frente_x = math.sin(self.cam_yaw_atual)
                frente_z = math.cos(self.cam_yaw_atual)
                lado_x   = math.cos(self.cam_yaw_atual)
                lado_z   = -math.sin(self.cam_yaw_atual)

                dx, dz = 0.0, 0.0
                if keys[pygame.K_w] or keys[pygame.K_UP]:
                    dx += frente_x * velocidade_andar
                    dz += frente_z * velocidade_andar
                if keys[pygame.K_s] or keys[pygame.K_DOWN]:
                    dx -= frente_x * velocidade_andar
                    dz -= frente_z * velocidade_andar
                if keys[pygame.K_a] or keys[pygame.K_LEFT]:
                    dx -= lado_x * velocidade_andar
                    dz -= lado_z * velocidade_andar
                if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
                    dx += lado_x * velocidade_andar
                    dz += lado_z * velocidade_andar

                nova_pos = [self.cam_pos_atual[0] + dx, self.cam_pos_atual[1], self.cam_pos_atual[2] + dz]
                self.abrir_porta_proxima(nova_pos)
                self.cam_pos_atual = self.aplicar_colisoes_navegacao(nova_pos)

                # Determina qual obra está mais próxima no modo livre para atualizar informações
                menor_dist = 9999.0
                mais_proxima = self.obra_foco_idx
                for i, spot in enumerate(self.spots_led):
                    alvo = spot["alvo"]
                    d = math.sqrt((self.cam_pos_atual[0] - alvo[0])**2 + (self.cam_pos_atual[2] - alvo[2])**2)
                    if d < menor_dist:
                        menor_dist = d
                        mais_proxima = i
                self.obra_foco_idx = mais_proxima

            # 3. Animações Espaciais dos Modelos (Requisito 3.4 & 3.6):
            # A) Rotação suave da Escultura (Busto de Nefertiti) em torno do eixo Y
            if self.modo_operacao == self.MODO_APRESENTACAO and self.obra_foco_idx == 0:
                if self.escultura_rodando:
                    self.busto_nefertiti.rot[1] += 0.85 * dt
                # Rotação manual livre pelas setas em apresentação
                keys = pygame.key.get_pressed()
                if keys[pygame.K_LEFT]:
                    self.busto_nefertiti.rot[1] += 1.8 * dt
                if keys[pygame.K_RIGHT]:
                    self.busto_nefertiti.rot[1] -= 1.8 * dt
            elif self.estado_atual == self.ESTADO_EXECUTANDO or self.modo_operacao == self.MODO_NAVEGACAO_LIVRE:
                self.busto_nefertiti.rot[1] += 0.85 * dt

            # B) Leve oscilação de escala / pulsação do cone de luz (Requisito 3.4)
            if self.estado_atual == self.ESTADO_EXECUTANDO:
                fator_pulso = 1.0 + math.sin(self.tempo_animacao * 3.5) * 0.04
                self.spots_led[self.obra_foco_idx]["raio_cone"] = 2.2 * fator_pulso

            # 4. Executa o Teste de Visibilidade / Iluminação Binária
            self.testar_iluminacao_binaria()

        # -------------------------------------------------------------------------
        # RENDERIZAÇÃO DA CENA 3D (PAREDES, PISO, OBJETOS E SPOTLIGHTS)
        # -------------------------------------------------------------------------
