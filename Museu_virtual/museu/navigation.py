"""Módulo de navigation da aplicação."""
import math
import os
import sys
import pygame

from .config import *
from .math3d import *
from .geometry import *
from .objects import *


class NavigationMixin:
        def abrir_porta_proxima(self, posicao):
            """Abre a porta com boa antecedência conforme o visitante se aproxima."""
            for porta in self.portas:
                perto_do_portal = (
                    abs(posicao[0] - porta.parede_x) <= 2.8 and
                    porta.z_inicio - 1.2 <= posicao[2] <= porta.z_fim + 1.2
                )
                if perto_do_portal:
                    porta.abrir()
                elif abs(posicao[0] - porta.parede_x) > 3.6:
                    porta.fechar()


        def preparar_portas_para_obra(self, indice_obra):
            """Abre a passagem da sala escolhida e fecha as demais."""
            for porta in self.portas:
                porta.fechar()
            if indice_obra == 0:
                self.portas[0].abrir()  # Sala 1: Escultura (Oeste)
            elif indice_obra == 1:
                pass  # Sala 2: Pintura (Central - ambas fecham)
            elif indice_obra == 2:
                self.portas[1].abrir()  # Sala 3: Papiro (Leste)


        def portas_prontas_para_obra(self, indice_obra):
            """Indica se a arquitetura terminou a transição antes da câmera avançar."""
            if indice_obra == 0:
                return self.portas[0].aberta and not self.portas[1].aberta
            if indice_obra == 1:
                return all(not porta.aberta for porta in self.portas)
            if indice_obra == 2:
                return self.portas[1].aberta and not self.portas[0].aberta
            return all(not porta.aberta for porta in self.portas)


        def aplicar_colisoes_navegacao(self, nova_pos):
            """
            Garante que o visitante não consiga atravessar as paredes externas,
            paredes divisórias (respeitando as passagens dos portais) e pedestais/vitrines.
            """
            x, y, z = nova_pos
            raio_visitante = 0.45

            # 1. Limites das Paredes Externas
            x = max(-12.4 + raio_visitante, min(12.4 - raio_visitante, x))
            z = max(-2.9  + raio_visitante, min(12.9 - raio_visitante, z))
            y = max(-0.2, min(3.2, y)) # Altura dos olhos do visitante

            # 2. Divisórias laterais: passagem liberada suavemente quando a porta começa a abrir
            for porta in self.portas:
                if abs(x - porta.parede_x) < raio_visitante:
                    dentro_do_portal = porta.z_inicio + raio_visitante <= z <= porta.z_fim - raio_visitante
                    if not dentro_do_portal or not porta.permite_passagem:
                        if self.cam_pos_atual[0] < porta.parede_x:
                            x = porta.parede_x - raio_visitante
                        else:
                            x = porta.parede_x + raio_visitante

            # 4. Caixas Delimitadoras (AABB) de Pedestais e Vitrines
            # Caixa da Escultura Nefertiti (Sala 1: x = -8.0, z = 8.5)
            if abs(x - (-8.0)) < 1.3 and abs(z - 8.5) < 1.3:
                dx = x - (-8.0)
                dz = z - 8.5
                if abs(dx) > abs(dz):
                    x = -8.0 + (1.3 if dx > 0 else -1.3)
                else:
                    z = 8.5 + (1.3 if dz > 0 else -1.3)

            # Caixa da Vitrine de Manuscritos (Sala 3: x = 8.0, z = 8.5)
            if abs(x - 8.0) < 1.8 and abs(z - 8.5) < 1.4:
                dx = x - 8.0
                dz = z - 8.5
                if abs(dx) > abs(dz):
                    x = 8.0 + (1.8 if dx > 0 else -1.8)
                else:
                    z = 8.5 + (1.4 if dz > 0 else -1.4)

            return [x, y, z]

        # -------------------------------------------------------------------------
        # ATUALIZAÇÃO DA LÓGICA, ANIMAÇÕES E CÂMERA (Δt)
        # -------------------------------------------------------------------------
