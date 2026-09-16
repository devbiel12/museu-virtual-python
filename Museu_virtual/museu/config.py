"""Configurações globais, caminhos, parâmetros de desempenho e paleta do Museu Virtual."""
import os
import pygame

# -----------------------------------------------------------------------------
# JANELA: TAMANHO PROPORCIONAL À TELA DO USUÁRIO
# -----------------------------------------------------------------------------
# O projeto foi desenhado para 1150 x 740. Em vez de fixar esse tamanho,
# escolhemos uma janela do mesmo formato (~1.55:1) ocupando uma fração
# confortável da tela de quem está executando, com limites para não ficar
# minúscula em um monitor 4K nem maior que a tela em um notebook pequeno.
_LARGURA_BASE, _ALTURA_BASE = 1150, 740
_PROPORCAO_BASE = _LARGURA_BASE / _ALTURA_BASE

_FRACAO_TELA = 0.80
_LARGURA_MIN, _ALTURA_MIN = 960, round(960 / _PROPORCAO_BASE)
_LARGURA_MAX, _ALTURA_MAX = 1680, round(1680 / _PROPORCAO_BASE)


def _detectar_resolucao_janela():
    """Calcula (largura, altura) a partir da resolução do monitor atual.

    Consulta o monitor antes de abrir a janela. Se a consulta falhar — por
    exemplo, em uma execução sem vídeo real, como em testes automatizados —
    cai de volta no tamanho original do projeto.
    """
    try:
        pygame.display.init()
        info = pygame.display.Info()
        tela_w, tela_h = info.current_w, info.current_h
    except pygame.error:
        tela_w = tela_h = 0

    if tela_w <= 0 or tela_h <= 0:
        return _LARGURA_BASE, _ALTURA_BASE

    largura = tela_w * _FRACAO_TELA
    altura = largura / _PROPORCAO_BASE
    if altura > tela_h * _FRACAO_TELA:
        altura = tela_h * _FRACAO_TELA
        largura = altura * _PROPORCAO_BASE

    # Teto de conforto, sem nunca passar do tamanho real da tela.
    largura = min(largura, _LARGURA_MAX, tela_w)
    altura = largura / _PROPORCAO_BASE
    if altura > tela_h:
        altura = tela_h
        largura = altura * _PROPORCAO_BASE

    # Piso de conforto, também sem nunca passar do tamanho real da tela —
    # em uma tela muito pequena é melhor ficar abaixo do mínimo do que abrir
    # uma janela maior que o monitor.
    largura = max(largura, min(_LARGURA_MIN, tela_w))
    altura = largura / _PROPORCAO_BASE
    if altura > tela_h:
        altura = tela_h
        largura = altura * _PROPORCAO_BASE

    return round(largura), round(altura)


LARGURA, ALTURA = _detectar_resolucao_janela()

# Fator único de escala: 1.0 no tamanho original (1150 px de largura).
# Fontes, painéis do HUD e a distância focal usam este fator para crescer ou
# encolher junto com a janela, mantendo a mesma aparência proporcional.
ESCALA = LARGURA / _LARGURA_BASE

FPS = 60

# Distância focal da projeção perspectiva e plano de recorte próximo.
# A distância focal escala com a janela para preservar o campo de visão.
FOCO = 620.0 * ESCALA
PLANO_PROXIMO = 0.25

# Tenta sincronizar com o monitor (elimina tearing). Se o driver não suportar,
# a aplicação cai automaticamente para o modo sem vsync.
USAR_VSYNC = True

# Limite superior do passo de tempo. Sem isso, um engasgo do sistema operacional
# vira um salto brusco da câmera; com o limite, a animação apenas "espera".
DT_MAXIMO = 1.0 / 20.0

# Suavização exponencial da câmera (unidade: 1/segundo). Valores maiores =
# aproximação mais rápida do alvo. Independente da taxa de quadros.
SUAVIDADE_CAM_FOCO = 3.8
SUAVIDADE_CAM_GERAL = 3.0
SUAVIDADE_PORTA = 7.0

# Rasterização das obras 2D: número de fatias verticais é escolhido por quadro
# entre o mínimo e o máximo, conforme o tamanho da obra na tela. Como o foco
# já escala com a janela, a obra ocupa uma fração de tela parecida em
# qualquer resolução e este valor não precisa mudar.
FATIAS_MIN = 6
FATIAS_MAX_PINTURA = 28
FATIAS_MAX_PAPIRO = 20
PIXELS_POR_FATIA = 18

# Descarta faces cuja área projetada é menor que este valor (em pixels²).
# Escala em ESCALA² porque é uma área, não uma distância.
AREA_MINIMA_FACE = 1.5 * ESCALA * ESCALA

DIR_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR_ASSETS = os.path.join(DIR_BASE, "assets")
PATH_TOTENINSEL = os.path.join(DIR_ASSETS, "toteninsel.jpg")
PATH_PAPYRUS = os.path.join(DIR_ASSETS, "papyrus_ani.jpg")
PATH_NEFERTITI = os.path.join(DIR_ASSETS, "nefertiti_bust.obj")

# -----------------------------------------------------------------------------
# PALETA
# -----------------------------------------------------------------------------
COR_FUNDO          = (10, 14, 22)
COR_PISO_GRADE     = (28, 38, 54)
COR_PISO_LINHAS    = (45, 60, 85)
COR_PAREDE         = (205, 205, 198)
COR_PAREDE_ALT     = (185, 188, 184)
COR_PAREDE_BORDA   = (175, 175, 165)
COR_TETO           = (205, 185, 145)
COR_RODAPE         = (20, 25, 34)
COR_PORTAL         = (85, 100, 125)
COR_PORTA          = (38, 48, 65)
COR_PORTA_FRAME    = (38, 48, 65)
COR_PORTA_BORDA    = (85, 100, 125)
COR_PORTA_PAINEL   = (26, 34, 48)
COR_PORTA_FRISO    = (195, 155, 45)
COR_PORTA_VIDRO    = (145, 190, 220)
COR_PORTA_PUXADOR  = (220, 180, 50)

COR_MARMORE_PED    = (165, 172, 185)
COR_MOGNO_VITRINE  = (85, 45, 25)
COR_VIDRO_BORDA    = (160, 220, 240)
COR_VIDRO_FACE     = (180, 230, 255, 40)
COR_VIDRO_VITRINE_BORDA = (150, 215, 255)
COR_VIDRO_VITRINE_FACE  = (125, 195, 255, 55)
COR_MOLDURA_OURO   = (195, 155, 45)
COR_PLACA_BRONZE   = (175, 130, 40)
COR_TEXTO_PLACA    = (255, 245, 220)

COR_LUZ_LED        = (255, 250, 220)
COR_CONE_LUZ       = (255, 245, 190, 30)
COR_TEXTO_HUD      = (240, 245, 255)
COR_DESTAQUE_HUD   = (255, 205, 50)
COR_HUD_BG         = (14, 20, 32, 220)
