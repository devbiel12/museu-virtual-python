"""Interface sobreposta (HUD) e tela de créditos.

Otimizações desta versão:
- Painéis translúcidos e textos fixos são desenhados uma única vez e guardados
  como superfícies prontas. Antes, cada quadro criava quatro superfícies com
  canal alfa e rasterizava mais de vinte trechos de texto do zero.
- Os textos variáveis passam por um cache por conteúdo: só rasterizam de novo
  quando a frase realmente muda.
- A tela de créditos inteira é montada uma vez e vira um único blit.

Layout responsivo:
- Painéis, margens e espessuras de traço usam esc(), que aplica o mesmo fator
  ESCALA das fontes (veja config.py). Como a janela é dimensionada conforme a
  tela do usuário, a interface cresce ou encolhe junto, em vez de manter um
  tamanho de painel fixo que ficaria desproporcional em telas muito grandes
  ou muito pequenas.
"""
import pygame

from .config import *


def esc(valor):
    """Escala um valor em pixels pelo mesmo fator da janela. Mínimo de 1."""
    resultado = round(valor * ESCALA)
    return resultado if resultado > 0 else 1


class UIMixin:

        # ---------------------------------------------------------------------
        # CACHE
        # ---------------------------------------------------------------------

        def preparar_cache_hud(self):
            """Monta as partes fixas do HUD uma única vez."""
            self._painel_topo = pygame.Surface((LARGURA - esc(40), esc(78)), pygame.SRCALPHA)
            self._painel_topo.fill(COR_HUD_BG)

            largura_cmd, altura_cmd = esc(510), esc(120)
            self._painel_comandos = pygame.Surface((largura_cmd, altura_cmd), pygame.SRCALPHA)
            self._painel_comandos.fill(COR_HUD_BG)
            self._painel_comandos.blit(
                self.fonte_subtitulo.render("Painel de Comandos e Controles:", True, COR_DESTAQUE_HUD),
                (esc(12), esc(5)))
            comandos = [
                "[M] Alternar Modo: Apresentação AP1 <-> Navegação Livre (WASD + Mouse)",
                "[ESPAÇO] Iniciar/Pausar/Retomar Visita  |  [R] Reiniciar  |  [C] Câmera",
                "[1, 2, 3] Focar Obra Específica (Escultura, Pintura, Papiro)",
                "[P] Parar/Continuar rotação da escultura  |  [← →] Girar manualmente",
                "[K] Créditos da Equipe  |  [F] FPS  |  [ESC] Sair",
            ]
            for i, cmd in enumerate(comandos):
                self._painel_comandos.blit(
                    self.fonte_pequena.render(cmd, True, COR_TEXTO_HUD), (esc(12), esc(30 + i * 19)))

            self._painel_obra = pygame.Surface((esc(580), esc(185)), pygame.SRCALPHA)
            self._painel_obra.fill(COR_HUD_BG)

            self._tela_creditos = self._montar_tela_creditos()

        def _texto(self, fonte, conteudo, cor):
            """Rasteriza um texto só quando ele muda; nas repetições devolve o cache."""
            chave = (id(fonte), conteudo, cor)
            superficie = self._cache_texto.get(chave)
            if superficie is None:
                if len(self._cache_texto) > 400:
                    self._cache_texto.clear()
                superficie = fonte.render(conteudo, True, cor)
                self._cache_texto[chave] = superficie
            return superficie

        # ---------------------------------------------------------------------
        # HUD
        # ---------------------------------------------------------------------

        def desenhar_hud(self):
            """Título, sala atual, barra de progresso, comandos e cartão da obra."""
            tela = self.tela
            obra = self.info_obras[self.obra_foco_idx]

            # Painel superior
            tela.blit(self._painel_topo, (esc(20), esc(12)))
            tela.blit(self._texto(self.fonte_titulo,
                                  "MUSEU VIRTUAL 3D — HISTÓRIA DA ARTE E DA ANTIGUIDADE",
                                  COR_DESTAQUE_HUD), (esc(36), esc(18)))

            subtitulo = f"{obra['sala']}  |  Estado: [{self.estado_atual}]  |  Modo: [{self.modo_operacao}]"
            tela.blit(self._texto(self.fonte_hud, subtitulo, COR_TEXTO_HUD), (esc(36), esc(45)))

            # Barra de progresso da visita guiada
            tempo_total = len(self.info_obras) * self.duracao_etapa
            progresso = min(1.0, self.tempo_animacao / tempo_total) if tempo_total > 0 else 0.0
            largura_barra = esc(320)
            barra_x, barra_y, barra_h = LARGURA - esc(360), esc(48), esc(12)
            pygame.draw.rect(tela, (40, 50, 70), (barra_x, barra_y, largura_barra, barra_h), border_radius=esc(4))
            pygame.draw.rect(tela, COR_DESTAQUE_HUD,
                             (barra_x, barra_y, int(largura_barra * progresso), barra_h), border_radius=esc(4))
            tela.blit(self._texto(self.fonte_pequena,
                                  f"Progresso Tour: {int(progresso * 100)}%",
                                  COR_TEXTO_HUD), (barra_x, esc(28)))

            # Painel de comandos
            tela.blit(self._painel_comandos, (esc(20), ALTURA - esc(135)))

            # Cartão didático da obra
            x = LARGURA - esc(585)
            tela.blit(self._painel_obra, (LARGURA - esc(600), ALTURA - esc(195)))
            tela.blit(self._texto(self.fonte_subtitulo, obra["titulo"], COR_DESTAQUE_HUD), (x, ALTURA - esc(188)))
            tela.blit(self._texto(self.fonte_hud, f"Autor: {obra['artista']}", (255, 235, 170)), (x, ALTURA - esc(165)))
            tela.blit(self._texto(self.fonte_pequena,
                                  f"Período / Data: {obra['periodo']} ({obra['data']})",
                                  COR_TEXTO_HUD), (x, ALTURA - esc(146)))
            tela.blit(self._texto(self.fonte_pequena,
                                  f"Material: {obra['material']}",
                                  (190, 210, 230)), (x, ALTURA - esc(128)))
            tela.blit(self._texto(self.fonte_pequena,
                                  obra["localizacao"],
                                  (190, 210, 230)), (x, ALTURA - esc(112)))

            y = ALTURA - esc(94)
            for linha in [l.strip() for l in obra["desc"].split("\n") if l.strip()][:2]:
                tela.blit(self._texto(self.fonte_pequena, linha, COR_TEXTO_HUD), (x, y))
                y += esc(15)

            # Estado do traçado de raio / iluminação binária
            obras = (self.busto_nefertiti, self.moldura_toteninsel, self.vitrine_papiro)
            acesa = obras[self.obra_foco_idx].iluminado
            status = "1 - ILUMINADA POR LED" if acesa else "0 - PENUMBRA AMBIENTE"
            tela.blit(self._texto(self.fonte_hud,
                                  f"Visibilidade Binária (Spotlight): [{status}]",
                                  COR_DESTAQUE_HUD), (x, ALTURA - esc(50)))

            if self.mostrar_fps:
                fps = self.relogio.get_fps()
                tela.blit(self._texto(self.fonte_pequena, f"{fps:5.1f} FPS", (150, 255, 180)),
                          (LARGURA - esc(90), esc(12)))

        # ---------------------------------------------------------------------
        # CRÉDITOS
        # ---------------------------------------------------------------------

        def _montar_tela_creditos(self):
            """Monta a tela de créditos uma vez; em uso ela vira um único blit."""
            superficie = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
            superficie.fill((8, 12, 20, 240))

            titulo = self.fonte_titulo.render("PROJETO AP1 — COMPUTAÇÃO GRÁFICA E RA/RV", True, COR_DESTAQUE_HUD)
            superficie.blit(titulo, (LARGURA // 2 - titulo.get_width() // 2, esc(50)))

            subtitulo = self.fonte_subtitulo.render(
                "Mundo Virtual Animado: Museu de História da Arte e da Antiguidade",
                True, (210, 230, 255))
            superficie.blit(subtitulo, (LARGURA // 2 - subtitulo.get_width() // 2, esc(85)))

            # Equipe: apenas os nomes dos quatro integrantes.
            integrantes = [
                "Gabriel Araujo Farias",
                "Guilherme Amorim Rocha Lima",
                "Mateus Deziderio Sanches",
                "Richard Bernardino Mendes",
            ]
            superficie.blit(self.fonte_subtitulo.render("Equipe de Alunos:", True, COR_DESTAQUE_HUD),
                            (esc(120), esc(130)))
            for i, nome in enumerate(integrantes):
                superficie.blit(self.fonte_hud.render(f"• {nome}", True, (255, 230, 160)),
                                (esc(140), esc(162) + i * esc(28)))

            referencias = [
                "Variação Temática: Variação 1 — Museu Virtual (Abertura de salas, iluminação binária, visita guiada e rotação).",
                "Obra 1 (Pintura): 'A Ilha dos Mortos' (Arnold Böcklin, 1880) — Domínio Público (Alte Nationalgalerie Berlin).",
                "Obra 2 (Escultura): 'Busto de Nefertiti' (c. 1345 a.C.) — Digitalização 3D Fraunhofer IGD / CultLab3D (CC BY-NC).",
                "Obra 3 (Manuscrito): 'Papiro de Ani - Livro dos Mortos' (c. 1250 a.C.) — British Museum / Wikimedia Commons.",
                "Tecnologias: Python 3 + Pygame (Projeção Perspectiva Pura e Sombreamento Lambertiano sem OpenGL).",
                "Referência Curricular: Aulas 01 a 10 de Computação Gráfica — Prof. Alex Torquato Souza Carneiro.",
            ]
            superficie.blit(self.fonte_subtitulo.render("Referências dos Materiais e Tecnologias:", True, COR_DESTAQUE_HUD),
                            (esc(120), esc(300)))
            for i, ref in enumerate(referencias):
                superficie.blit(self.fonte_pequena.render(f"• {ref}", True, (200, 215, 235)),
                                (esc(140), esc(335) + i * esc(26)))

            fechar = self.fonte_hud.render("Pressione [K] para fechar esta tela e retornar ao museu.", True, COR_DESTAQUE_HUD)
            superficie.blit(fechar, (LARGURA // 2 - fechar.get_width() // 2, ALTURA - esc(70)))
            return superficie

        def desenhar_tela_creditos(self):
            self.tela.blit(self._tela_creditos, (0, 0))
