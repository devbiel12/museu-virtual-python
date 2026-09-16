"""Laço principal da aplicação: eventos, atualização e desenho do quadro.

Otimizações desta versão:
- O passo de tempo é limitado por DT_MAXIMO. Um engasgo do sistema operacional
  deixa de virar um salto brusco da câmera — a cena apenas continua de onde
  parou, que é o que o olho percebe como movimento suave.
- Vários eventos de mouse do mesmo quadro são somados e aplicados de uma vez,
  em vez de sacudir a câmera evento por evento.
- O desenho do quadro fica isolado em desenhar_frame().
"""
import sys
import pygame

from .config import *


class AppMixin:

        def executar(self):
            """Laço principal: processa eventos, atualiza a lógica e desenha."""
            rodando = True
            while rodando:
                dt = self.relogio.tick(FPS) / 1000.0
                if dt > DT_MAXIMO:
                    dt = DT_MAXIMO

                rodando = self.processar_eventos()
                self.atualizar(dt)
                self.desenhar_frame()
                pygame.display.flip()

            pygame.quit()
            sys.exit()

        # ---------------------------------------------------------------------
        # EVENTOS
        # ---------------------------------------------------------------------

        def processar_eventos(self):
            """Trata a fila de eventos. Retorna False quando a aplicação deve encerrar."""
            mouse_dx = 0
            mouse_dy = 0

            for evento in pygame.event.get():
                tipo = evento.type

                if tipo == pygame.QUIT:
                    return False

                elif tipo == pygame.KEYDOWN:
                    if not self.tratar_tecla(evento.key):
                        return False

                elif tipo == pygame.MOUSEBUTTONDOWN:
                    if evento.button == 1:
                        self.mouse_arrastando = True
                        self.mouse_ultimo_pos = evento.pos

                elif tipo == pygame.MOUSEBUTTONUP:
                    if evento.button == 1:
                        self.mouse_arrastando = False

                elif tipo == pygame.MOUSEMOTION:
                    arrastando = self.mouse_arrastando or (
                        self.modo_operacao == self.MODO_NAVEGACAO_LIVRE
                        and pygame.mouse.get_pressed()[0])
                    if arrastando:
                        # Acumula o deslocamento de todos os eventos do quadro.
                        mouse_dx += evento.pos[0] - self.mouse_ultimo_pos[0]
                        mouse_dy += evento.pos[1] - self.mouse_ultimo_pos[1]
                    self.mouse_ultimo_pos = evento.pos

            if mouse_dx or mouse_dy:
                self.cam_yaw_atual += mouse_dx * self.sensibilidade_mouse
                pitch = self.cam_pitch_atual - mouse_dy * self.sensibilidade_mouse
                self.cam_pitch_atual = -1.1 if pitch < -1.1 else (1.1 if pitch > 1.1 else pitch)

            return True

        def tratar_tecla(self, tecla):
            """Aplica o comando de uma tecla. Retorna False para encerrar a aplicação."""
            if tecla == pygame.K_ESCAPE:
                return False

            # [M] Alterna entre apresentação AP1 e navegação livre
            if tecla == pygame.K_m:
                if self.modo_operacao == self.MODO_APRESENTACAO:
                    self.modo_operacao = self.MODO_NAVEGACAO_LIVRE
                    for porta in self.portas:
                        porta.fechar()
                else:
                    self.modo_operacao = self.MODO_APRESENTACAO
                    self.reiniciar()

            # [ESPAÇO] Inicia, pausa ou retoma a visita guiada
            elif tecla == pygame.K_SPACE:
                if self.estado_atual == self.ESTADO_PARADO:
                    self._iniciar_visita()
                elif self.estado_atual == self.ESTADO_PAUSADO:
                    self.estado_atual = self.ESTADO_EXECUTANDO
                elif self.estado_atual == self.ESTADO_EXECUTANDO:
                    self.estado_atual = self.ESTADO_PAUSADO
                elif self.estado_atual == self.ESTADO_CONCLUIDO:
                    self.reiniciar()
                    self._iniciar_visita()

            # [R] Reinicia a cena
            elif tecla == pygame.K_r:
                self.reiniciar()

            # [P] Pausa ou retoma a rotação automática da escultura
            elif tecla == pygame.K_p and self.modo_operacao == self.MODO_APRESENTACAO:
                self.escultura_rodando = not self.escultura_rodando

            # [C] Alterna o modo de câmera da apresentação
            elif tecla == pygame.K_c and self.modo_operacao == self.MODO_APRESENTACAO:
                self.submodo_cam = (self.MODO_CAM_FOCO
                                    if self.submodo_cam == self.MODO_CAM_GERAL
                                    else self.MODO_CAM_GERAL)

            # [1, 2, 3] Seleção direta das obras
            elif tecla in (pygame.K_1, pygame.K_2, pygame.K_3):
                indice = {pygame.K_1: 0, pygame.K_2: 1, pygame.K_3: 2}[tecla]
                self.obra_foco_idx = indice
                if self.modo_operacao == self.MODO_APRESENTACAO:
                    self.preparar_portas_para_obra(indice)
                    foco = self.info_obras[indice]
                    self.cam_pos_alvo = list(foco["pos_foco_cam"])
                    self.cam_yaw_alvo = foco["yaw_foco"]
                    self.cam_pitch_alvo = foco["pitch_foco"]
                    self.submodo_cam = self.MODO_CAM_FOCO

            # [K] Tela de créditos   [F] Contador de quadros por segundo
            elif tecla == pygame.K_k:
                self.exibir_creditos = not self.exibir_creditos
            elif tecla == pygame.K_f:
                self.mostrar_fps = not self.mostrar_fps

            return True

        def _iniciar_visita(self):
            self.obra_foco_idx = 0
            self.tempo_animacao = 0.0
            self.preparar_portas_para_obra(0)
            self.submodo_cam = self.MODO_CAM_FOCO
            self.estado_atual = self.ESTADO_EXECUTANDO

        # ---------------------------------------------------------------------
        # DESENHO DO QUADRO
        # ---------------------------------------------------------------------

        def desenhar_frame(self):
            """Monta um quadro completo, do fundo para a frente."""
            self.tela.fill(COR_FUNDO)

            # Tela de créditos cobre tudo: nada atrás dela precisa ser desenhado.
            if self.exibir_creditos:
                self.desenhar_tela_creditos()
                return

            # 1. Piso em grade
            self.desenhar_piso_museu()

            # 2. Paredes, portais e portas articuladas
            self.desenhar_arquitetura_paredes()

            # 3. Pedestais, moldura e vitrine
            for pedestal in self.pedestais:
                self.desenhar_objeto_3d(pedestal)
            self.desenhar_objeto_3d(self.moldura_toteninsel)
            self.desenhar_objeto_3d(self.vitrine_papiro)
            self.desenhar_objeto_3d(self.papiro_ani_obj)

            # 4. Obras rasterizadas (pintura e papiro)
            self.desenhar_superficies_artisticas_rasterizadas()

            # 5. Redoma de vidro sobre o papiro
            self.desenhar_objeto_3d(self.redoma_papiro)

            # 6. Busto escultórico
            self.desenhar_objeto_3d(self.busto_nefertiti)

            # 7. Placas de identificação em bronze
            for placa in self.placas:
                self.desenhar_objeto_3d(placa)

            # 8. Luminárias e feixes de luz
            self.desenhar_feixes_spotlights()

            # 9. Interface sobreposta
            self.desenhar_hud()
