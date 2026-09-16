"""Módulo de execução da aplicação."""
import math
import os
import sys
import pygame

from .config import *
from .math3d import *
from .geometry import *
from .objects import *


class AppMixin:
        def executar(self):
            rodando = True
            while rodando:
                dt = self.relogio.tick(FPS) / 1000.0 # Delta tempo em segundos

                # Processamento de Eventos
                for evento in pygame.event.get():
                    if evento.type == pygame.QUIT:
                        rodando = False

                    elif evento.type == pygame.KEYDOWN:
                        if evento.key == pygame.K_ESCAPE:
                            rodando = False

                        # [M] Alternar entre Modo Apresentação AP1 e Modo Navegação Livre
                        elif evento.key == pygame.K_m:
                            if self.modo_operacao == self.MODO_APRESENTACAO:
                                self.modo_operacao = self.MODO_NAVEGACAO_LIVRE
                                for porta in self.portas:
                                    porta.fechar()
                            else:
                                self.modo_operacao = self.MODO_APRESENTACAO
                                self.reiniciar()

                        # [ESPAÇO] Iniciar / Pausar / Retomar Visita Guiada (Comando Discreto AP1)
                        elif evento.key == pygame.K_SPACE:
                            if self.estado_atual == self.ESTADO_PARADO:
                                self.obra_foco_idx = 0
                                self.tempo_animacao = 0.0
                                self.preparar_portas_para_obra(0)
                                self.submodo_cam = self.MODO_CAM_FOCO
                                self.estado_atual = self.ESTADO_EXECUTANDO
                            elif self.estado_atual == self.ESTADO_PAUSADO:
                                self.estado_atual = self.ESTADO_EXECUTANDO
                            elif self.estado_atual == self.ESTADO_EXECUTANDO:
                                self.estado_atual = self.ESTADO_PAUSADO
                            elif self.estado_atual == self.ESTADO_CONCLUIDO:
                                self.reiniciar()
                                self.obra_foco_idx = 0
                                self.preparar_portas_para_obra(0)
                                self.submodo_cam = self.MODO_CAM_FOCO
                                self.estado_atual = self.ESTADO_EXECUTANDO

                        # [R] Reiniciar Aplicação
                        elif evento.key == pygame.K_r:
                            self.reiniciar()

                        # [P] Pausar / retomar rotação automática da escultura (modo apresentação)
                        elif evento.key == pygame.K_p and self.modo_operacao == self.MODO_APRESENTACAO:
                            self.escultura_rodando = not self.escultura_rodando

                        # [C] Alternar Modo de Câmera da Apresentação
                        elif evento.key == pygame.K_c:
                            if self.modo_operacao == self.MODO_APRESENTACAO:
                                if self.submodo_cam == self.MODO_CAM_GERAL:
                                    self.submodo_cam = self.MODO_CAM_FOCO
                                else:
                                    self.submodo_cam = self.MODO_CAM_GERAL

                        # [1, 2, 3] Seleção Direta das Obras
                        elif evento.key in [pygame.K_1, pygame.K_2, pygame.K_3]:
                            mapeamento_teclas = {
                                pygame.K_1: 0,  # 1: Escultura (Sala Oeste)
                                pygame.K_2: 1,  # 2: Pintura (Sala Central)
                                pygame.K_3: 2   # 3: Papiro (Sala Leste)
                            }
                            self.obra_foco_idx = mapeamento_teclas[evento.key]
                            if self.modo_operacao == self.MODO_APRESENTACAO:
                                self.preparar_portas_para_obra(self.obra_foco_idx)
                                foco_info = self.info_obras[self.obra_foco_idx]
                                self.cam_pos_alvo = list(foco_info["pos_foco_cam"])
                                self.cam_yaw_alvo = foco_info["yaw_foco"]
                                self.cam_pitch_alvo = foco_info["pitch_foco"]
                                self.submodo_cam = self.MODO_CAM_FOCO

                        # [N] Próxima Obra / [B] Obra Anterior
                        elif evento.key in (pygame.K_n, pygame.K_b):
                            deslocamento = 1 if evento.key == pygame.K_n else -1
                            self.obra_foco_idx = (self.obra_foco_idx + deslocamento) % len(self.info_obras)
                            if self.modo_operacao == self.MODO_APRESENTACAO:
                                self.preparar_portas_para_obra(self.obra_foco_idx)
                                foco_info = self.info_obras[self.obra_foco_idx]
                                self.cam_pos_alvo = list(foco_info["pos_foco_cam"])
                                self.cam_yaw_alvo = foco_info["yaw_foco"]
                                self.cam_pitch_alvo = foco_info["pitch_foco"]
                                self.submodo_cam = self.MODO_CAM_FOCO

                        # [K] Alternar Tela de Créditos
                        elif evento.key == pygame.K_k:
                            self.exibir_creditos = not self.exibir_creditos

                    # Controles de Mouse para Rotação da Visão (Pitch e Yaw)
                    elif evento.type == pygame.MOUSEBUTTONDOWN:
                        if evento.button == 1: # Botão esquerdo do mouse
                            self.mouse_arrastando = True
                            self.mouse_ultimo_pos = evento.pos

                    elif evento.type == pygame.MOUSEBUTTONUP:
                        if evento.button == 1:
                            self.mouse_arrastando = False

                    elif evento.type == pygame.MOUSEMOTION:
                        if self.mouse_arrastando or (self.modo_operacao == self.MODO_NAVEGACAO_LIVRE and pygame.mouse.get_pressed()[0]):
                            dx = evento.pos[0] - self.mouse_ultimo_pos[0]
                            dy = evento.pos[1] - self.mouse_ultimo_pos[1]
                            self.mouse_ultimo_pos = evento.pos

                            # Rotação da visão do observador
                            self.cam_yaw_atual += dx * self.sensibilidade_mouse
                            self.cam_pitch_atual -= dy * self.sensibilidade_mouse
                            # Limite para não inverter a visão vertical
                            self.cam_pitch_atual = max(-1.1, min(1.1, self.cam_pitch_atual))

                # Atualização da Lógica
                self.atualizar(dt)

                # -----------------------------------------------------------------
                # RENDERIZAÇÃO DA CENA EM PYGAME
                # -----------------------------------------------------------------
                self.tela.fill(COR_FUNDO)

                # 1. Piso com Grade e Ladrilhos de Museu
                self.desenhar_piso_museu()

                # 2. Paredes e Portais Arquitetônicos das Galerias
                self.desenhar_arquitetura_paredes()

                # 3. Desenhar Pedestais e Vitrines
                for ped in self.pedestais:
                    self.desenhar_objeto_3d(ped)

                self.desenhar_objeto_3d(self.moldura_toteninsel)
                self.desenhar_objeto_3d(self.vitrine_papiro)
                self.desenhar_objeto_3d(self.papiro_ani_obj)

                # 4. Desenhar Superfícies Artísticas Rasterizadas (Pintura e Papiro)
                self.desenhar_superficies_artisticas_rasterizadas()

                # 5. Desenhar Busto Escultórico 3D
                self.desenhar_objeto_3d(self.busto_nefertiti)

                # 6. Desenhar Placas de Identificação em Bronze
                for placa in self.placas:
                    self.desenhar_objeto_3d(placa)

                # 7. Desenhar Luminárias e Cones de Luz Spot
                self.desenhar_feixes_spotlights()

                # 8. Desenhar Interface Sobreposta (HUD)
                self.desenhar_hud()

                # 9. Desenhar Tela de Créditos (se acionada)
                if self.exibir_creditos:
                    self.desenhar_tela_creditos()

                pygame.display.flip()

            pygame.quit()
            sys.exit()


    # -----------------------------------------------------------------------------
    # PONTO DE ENTRADA PRINCIPAL DA APLICAÇÃO
    # -----------------------------------------------------------------------------
