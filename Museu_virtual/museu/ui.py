"""Módulo de ui da aplicação."""
import math
import os
import sys
import pygame

from .config import *
from .math3d import *
from .geometry import *
from .objects import *


class UIMixin:
        def desenhar_hud(self):
            """Interface sobreposta com status, cronômetro, barra de progresso e comandos."""
            # Painel Superior: Título do Museu e Identificação da Galeria
            painel_top = pygame.Surface((LARGURA - 40, 78), pygame.SRCALPHA)
            painel_top.fill(COR_HUD_BG)
            self.tela.blit(painel_top, (20, 12))

            txt_tit = self.fonte_titulo.render("MUSEU VIRTUAL 3D — HISTÓRIA DA ARTE E DA ANTIGUIDADE", True, COR_DESTAQUE_HUD)
            self.tela.blit(txt_tit, (36, 18))

            sala_nome = self.info_obras[self.obra_foco_idx]["sala"]
            txt_sub = f"{sala_nome}  |  Estado: [{self.estado_atual}]  |  Modo: [{self.modo_operacao}]"
            self.tela.blit(self.fonte_hud.render(txt_sub, True, COR_TEXTO_HUD), (36, 45))

            # Barra de Progresso da Visita Guiada (Requisito AP1 3.8)
            tempo_total = len(self.info_obras) * self.duracao_etapa
            progresso = min(1.0, self.tempo_animacao / tempo_total) if tempo_total > 0 else 0.0
            
            largura_barra = 320
            pygame.draw.rect(self.tela, (40, 50, 70), (LARGURA - 360, 48, largura_barra, 12), border_radius=4)
            pygame.draw.rect(self.tela, COR_DESTAQUE_HUD, (LARGURA - 360, 48, int(largura_barra * progresso), 12), border_radius=4)
            txt_prog = f"Progresso Tour: {int(progresso*100)}%"
            self.tela.blit(self.fonte_pequena.render(txt_prog, True, COR_TEXTO_HUD), (LARGURA - 360, 28))

            # Painel Inferior Esquerdo: Controles do Teclado e Mouse
            painel_cmd = pygame.Surface((510, 120), pygame.SRCALPHA)
            painel_cmd.fill(COR_HUD_BG)
            self.tela.blit(painel_cmd, (20, ALTURA - 135))

            self.tela.blit(self.fonte_subtitulo.render("Painel de Comandos e Controles:", True, COR_DESTAQUE_HUD), (32, ALTURA - 130))
            comandos = [
                "[M] Alternar Modo: Apresentação AP1 <-> Navegação Livre (WASD + Mouse)",
                "[ESPAÇO] Iniciar/Pausar/Retomar Visita  |  [R] Reiniciar  |  [C] Câmera",
                "[1, 2, 3] Focar Obra Específica (Escultura, Pintura, Papiro)",
                "[P] Parar/Continuar rotação da escultura  |  [← →] Girar manualmente",
                "[N] / [B] Próxima / Anterior  |  [K] Créditos da Equipe  |  [ESC] Sair"
            ]
            for idx, cmd in enumerate(comandos):
                self.tela.blit(self.fonte_pequena.render(cmd, True, COR_TEXTO_HUD), (32, ALTURA - 105 + idx * 19))

            # Painel Inferior Direito: Cartão Didático da Obra / Placa de Proximidade
            obra_atual = self.info_obras[self.obra_foco_idx]
            painel_obra = pygame.Surface((580, 185), pygame.SRCALPHA)
            painel_obra.fill(COR_HUD_BG)
            self.tela.blit(painel_obra, (LARGURA - 600, ALTURA - 195))

            # Título da Obra e Artista
            t_obra = self.fonte_subtitulo.render(obra_atual["titulo"], True, COR_DESTAQUE_HUD)
            a_obra = self.fonte_hud.render(f"Autor: {obra_atual['artista']}", True, (255, 235, 170))
            p_obra = self.fonte_pequena.render(f"Período / Data: {obra_atual['periodo']} ({obra_atual['data']})", True, COR_TEXTO_HUD)
            m_obra = self.fonte_pequena.render(f"Material: {obra_atual['material']}  |  {obra_atual['localizacao']}", True, (190, 210, 230))

            self.tela.blit(t_obra, (LARGURA - 585, ALTURA - 188))
            self.tela.blit(a_obra, (LARGURA - 585, ALTURA - 165))
            self.tela.blit(p_obra, (LARGURA - 585, ALTURA - 146))
            self.tela.blit(m_obra, (LARGURA - 585, ALTURA - 128))

            # Descrição multilinha sem sobreposição
            linhas_desc = [l.strip() for l in obra_atual["desc"].split("\n") if l.strip()]
            y_desc = ALTURA - 110
            for l_txt in linhas_desc[:2]:
                self.tela.blit(self.fonte_pequena.render(l_txt, True, COR_TEXTO_HUD), (LARGURA - 585, y_desc))
                y_desc += 16

            # Status do Traçado de Raio / Iluminação Binária
            status_luz = "1 - ILUMINADA POR LED" if (
                (self.obra_foco_idx == 0 and self.busto_nefertiti.iluminado) or
                (self.obra_foco_idx == 1 and self.moldura_toteninsel.iluminado) or
                (self.obra_foco_idx == 2 and self.vitrine_papiro.iluminado)
            ) else "0 - PENUMBRA AMBIENTE"
            st_ilum = f"Visibilidade Binária (Spotlight): [{status_luz}]"
            self.tela.blit(self.fonte_hud.render(st_ilum, True, COR_DESTAQUE_HUD), (LARGURA - 585, ALTURA - 50))


        def desenhar_tela_creditos(self):
            """Tela sobreposta de Créditos e Referências da Atividade AP1 (Requisito 3.10)."""
            overlay = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
            overlay.fill((8, 12, 20, 240))
            self.tela.blit(overlay, (0, 0))

            txt_tit = self.fonte_titulo.render("PROJETO AP1 — COMPUTAÇÃO GRÁFICA E RA/RV", True, COR_DESTAQUE_HUD)
            self.tela.blit(txt_tit, (LARGURA//2 - txt_tit.get_width()//2, 50))

            sub_tit = self.fonte_subtitulo.render("Mundo Virtual Animado: Museu de História da Arte e da Antiguidade", True, (210, 230, 255))
            self.tela.blit(sub_tit, (LARGURA//2 - sub_tit.get_width()//2, 85))

            # Divisão de Responsabilidades dos 4 Integrantes
            integrantes = [
                ("Integrante 1 (Coordenação e Integração)", "Estrutura do código, pipeline gráfico 3D->2D, compatibilidade e testes."),
                ("Integrante 2 (Modelagem e Cena 3D)", "Salas temáticas, malha OBJ de Nefertiti, moldura 3D, vitrine e instâncias de pedestais."),
                ("Integrante 3 (Animação e Estados)", "Máquina de 4 estados, sequenciamento temporal Delta t, rotações e transições."),
                ("Integrante 4 (Câmera, Luz e Interface)", "Modos de câmera (Apresentação e WASD/Mouse), iluminação binária e HUD.")
            ]

            self.tela.blit(self.fonte_subtitulo.render("Equipe de Alunos e Responsabilidades:", True, COR_DESTAQUE_HUD), (120, 130))
            for i, (nome, desc) in enumerate(integrantes):
                txt_n = self.fonte_hud.render(f"• {nome}:", True, (255, 230, 160))
                txt_d = self.fonte_pequena.render(f"   {desc}", True, COR_TEXTO_HUD)
                self.tela.blit(txt_n, (140, 160 + i * 42))
                self.tela.blit(txt_d, (140, 180 + i * 42))

            # Referências das Obras e Materiais Didáticos
            refs = [
                "Variação Temática: Variação 1 — Museu Virtual (Abertura de salas, iluminação binária, visita guiada e rotação).",
                "Obra 1 (Pintura): 'A Ilha dos Mortos' (Arnold Böcklin, 1880) — Domínio Público (Alte Nationalgalerie Berlin).",
                "Obra 2 (Escultura): 'Busto de Nefertiti' (c. 1345 a.C.) — Digitalização 3D Fraunhofer IGD / CultLab3D (CC BY-NC).",
                "Obra 3 (Manuscrito): 'Papiro de Ani - Livro dos Mortos' (c. 1250 a.C.) — British Museum / Wikimedia Commons.",
                "Tecnologias: Python 3 + Pygame (Projeção Perspectiva Pura e Sombreamento Lambertiano sem OpenGL).",
                "Referência Curricular: Aulas 01 a 10 de Computação Gráfica — Prof. Alex Torquato Souza Carneiro."
            ]

            self.tela.blit(self.fonte_subtitulo.render("Referências dos Materiais e Tecnologias:", True, COR_DESTAQUE_HUD), (120, 360))
            for i, ref in enumerate(refs):
                self.tela.blit(self.fonte_pequena.render(f"• {ref}", True, (200, 215, 235)), (140, 395 + i * 26))

            txt_fechar = self.fonte_hud.render("Pressione [K] para fechar esta tela e retornar ao museu.", True, COR_DESTAQUE_HUD)
            self.tela.blit(txt_fechar, (LARGURA//2 - txt_fechar.get_width()//2, ALTURA - 70))

        # -------------------------------------------------------------------------
        # LAÇO PRINCIPAL E GERENCIAMENTO DE EVENTOS
        # -------------------------------------------------------------------------
