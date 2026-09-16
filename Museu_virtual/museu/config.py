"""Configurações globais, caminhos e paleta do Museu Virtual."""
import os

LARGURA, ALTURA = 1150, 740
FPS = 60

DIR_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR_ASSETS = os.path.join(DIR_BASE, "assets")
PATH_TOTENINSEL = os.path.join(DIR_ASSETS, "toteninsel.jpg")
PATH_PAPYRUS = os.path.join(DIR_ASSETS, "papyrus_ani.jpg")
PATH_NEFERTITI = os.path.join(DIR_ASSETS, "nefertiti_bust.obj")

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
COR_MOLDURA_OURO   = (195, 155, 45)
COR_PLACA_BRONZE   = (175, 130, 40)
COR_TEXTO_PLACA    = (255, 245, 220)

COR_LUZ_LED        = (255, 250, 220)
COR_CONE_LUZ       = (255, 245, 190, 30)
COR_TEXTO_HUD      = (240, 245, 255)
COR_DESTAQUE_HUD   = (255, 205, 50)
COR_HUD_BG         = (14, 20, 32, 220)