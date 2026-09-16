# Museu Virtual 3D

Ambiente interativo de museu em Python com Pygame, feito para a AP1 de Computação Gráfica e RA/RV. A cena 3D é montada do zero: projeção em perspectiva, sombreamento e recorte são todos implementados no próprio código, sem OpenGL nem motor gráfico externo.

O visitante percorre três galerias com obras históricas, portas que abrem conforme a aproximação, iluminação por spots LED e uma visita guiada automática com máquina de estados.

## Obras e galerias

| Sala | Obra | Técnica de renderização |
|---|---|---|
| Oeste | Busto de Nefertiti (c. 1345 a.C.) | Malha OBJ de 452 vértices e 894 faces, com rotação animada |
| Central | A Ilha dos Mortos, Arnold Böcklin (1880) | Textura rasterizada em fatias verticais dentro de uma moldura 3D |
| Leste | Papiro de Ani, Livro dos Mortos (c. 1250 a.C.) | Textura com perspectiva real sobre tampo inclinado, sob redoma de vidro |

## Como executar

Requisitos: Python 3.9 ou superior e Pygame.

A janela se ajusta sozinha à tela de quem está executando: ocupa uma fração confortável do monitor, mantendo a proporção original do projeto, com um tamanho mínimo (960 × 618) e máximo (1680 × 1081) para não ficar minúscula em notebooks pequenos nem maior que a tela em monitores grandes. Fontes e painéis do HUD escalam junto.

```bash
pip install pygame
python Museu_virtual/main.py
```

Se preferir entrar na pasta do projeto:

```bash
cd Museu_virtual
python main.py
```

Os arquivos da cena já vêm no repositório. Para baixar ou regenerar imagens e o modelo 3D:

```bash
python Museu_virtual/assets/download_assets.py
```

O script cria versões de fallback quando os arquivos externos não estão disponíveis, então a aplicação roda mesmo sem acesso à internet.

## Controles

### Modo apresentação

| Tecla | Ação |
|---|---|
| `Espaço` | Inicia, pausa ou retoma a visita guiada |
| `1` `2` `3` | Vai direto para a escultura, a pintura ou o papiro |
| `C` | Alterna entre visão geral e foco na obra |
| `P` | Para ou retoma a rotação automática da escultura |
| `←` `→` | Gira a escultura manualmente |
| `R` | Reinicia a cena |
| `M` | Troca para o modo de navegação livre |
| `K` | Abre e fecha a tela de créditos |
| `F` | Mostra o contador de quadros por segundo |
| `Esc` | Encerra a aplicação |

### Modo navegação livre

| Controle | Ação |
|---|---|
| `W` `S` | Anda para frente e para trás |
| `A` `D` | Desloca lateralmente |
| Mouse (arrastar) | Gira a visão em yaw e pitch |
| `M` | Volta ao modo apresentação |

As portas abrem sozinhas quando o visitante se aproxima, e o sistema de colisão impede atravessar paredes, pedestais e vitrines.

## Estrutura do projeto

```text
museu-virtual-python/
├── README.md
├── .gitignore
└── Museu_virtual/
    ├── main.py
    ├── museu/
    │   ├── __init__.py
    │   ├── museum.py
    │   ├── config.py
    │   ├── math3d.py
    │   ├── geometry.py
    │   ├── objects.py
    │   ├── scene.py
    │   ├── navigation.py
    │   ├── animation.py
    │   ├── renderer.py
    │   ├── ui.py
    │   └── app.py
    └── assets/
        ├── download_assets.py
        ├── nefertiti_bust.obj
        ├── papyrus_ani.jpg
        └── toteninsel.jpg
```

| Módulo | Responsabilidade |
|---|---|
| `main.py` | Ponto de entrada |
| `museu/museum.py` | Monta a classe `MuseuVirtual3D` a partir dos mixins |
| `museu/config.py` | Dimensões, FPS, parâmetros de desempenho, caminhos e paleta |
| `museu/math3d.py` | Vetores, transformações, câmera com cache e projeção perspectiva |
| `museu/geometry.py` | Modelos estáticos, carregamento de OBJ e orientação de malhas |
| `museu/objects.py` | `Objeto3D` e `PortaArticulada` |
| `museu/scene.py` | Inicialização da cena, assets, spots e iluminação binária |
| `museu/navigation.py` | Movimento do visitante, colisões e abertura de portas |
| `museu/animation.py` | Máquina de estados, câmera e animações por Δt |
| `museu/renderer.py` | Piso, paredes, objetos, obras rasterizadas e spotlights |
| `museu/ui.py` | HUD e tela de créditos |
| `museu/app.py` | Laço principal, eventos e desenho do quadro |

## Desempenho

A versão atual passou por uma otimização focada em duas coisas: reduzir o custo de cada quadro e eliminar os engasgos que aparecem como travadas durante o movimento da câmera.

| Cenário | Antes | Depois |
|---|---|---|
| Visita guiada completa | 11,1 ms por quadro (90 FPS) | 5,9 ms por quadro (168 FPS) |
| Sala da escultura | 10,4 ms (97 FPS) | 6,2 ms (160 FPS) |
| Sala do papiro | 17,4 ms (58 FPS) | 7,1 ms (140 FPS) |
| Pior quadro da visita | 83 ms | 11 ms |

O ganho mais importante é o último: o quadro mais lento caiu de 83 ms para 11 ms. É esse pico, e não a média, que o olho percebe como travada.

### O que foi feito na renderização

- **Câmera com trigonometria em cache.** Seno e cosseno de yaw e pitch são calculados uma vez por quadro, e não quatro vezes por vértice projetado.
- **Descarte de faces traseiras.** Um passo de orientação de malha, executado uma única vez no carregamento, percorre a geometria por adjacência de arestas e usa o volume com sinal para decidir o lado de fora. Nas malhas fechadas isso corta cerca de metade dos triângulos por quadro — no busto de Nefertiti, quase 450 dos 894. Em malhas abertas, como a moldura da pintura, o descarte se desativa sozinho para que nenhuma face legítima suma da tela.
- **Buffer de vidro reaproveitado.** A redoma do papiro criava uma superfície do tamanho da tela por face translúcida: seis alocações e seis composições de tela cheia por quadro. Agora um único buffer é reutilizado e só o retângulo ocupado pela face é limpo e composto.
- **Cache das obras rasterizadas.** As fatias da pintura e do papiro ficam prontas e só são recalculadas quando a câmera ou a iluminação mudam. O número de fatias se ajusta ao tamanho da obra na tela.
- **Filtros antes do desenho.** Faces fora da tela, pequenas demais ou atrás do plano próximo são descartadas antes de qualquer chamada de rasterização.
- **HUD pré-renderizado.** Painéis translúcidos e textos fixos são desenhados uma vez e guardados como superfícies prontas; os textos variáveis passam por um cache por conteúdo. A tela de créditos virou um único blit.

### O que foi feito na suavidade

- **Amortecimento exponencial no lugar de interpolação linear.** A câmera usa `1 - e^(-k·Δt)`. A fórmula anterior mudava de velocidade conforme a taxa de quadros; esta chega ao alvo no mesmo tempo a 30, 60 ou 144 FPS, que é o que faz o movimento parecer suave.
- **Passo de tempo limitado.** Um engasgo do sistema operacional deixa de virar um salto brusco da câmera: a cena apenas continua de onde parou.
- **Projeção em ponto flutuante.** As coordenadas de tela não são mais arredondadas para inteiro, o que elimina o tremor de um pixel em movimentos lentos.
- **Trava no alvo.** Quando a câmera chega ao destino, os valores são fixados, acabando com o micro-tremor residual.
- **Interpolação de ângulo pelo menor arco**, sem dar a volta completa ao cruzar ±π.
- **Diagonal normalizada** no modo livre: andar em dois eixos deixou de ser mais rápido que andar em um.
- **Vsync e double buffer** quando o driver aceita, com queda automática para o modo sem vsync.

### Ajustes disponíveis

Os parâmetros ficam em `museu/config.py`:

| Parâmetro | Efeito |
|---|---|
| `_FRACAO_TELA` | Fração da tela do monitor ocupada pela janela |
| `_LARGURA_MIN` / `_LARGURA_MAX` | Limites mínimo e máximo da janela, em pixels |
| `USAR_VSYNC` | Sincroniza com o monitor e elimina tearing |
| `DT_MAXIMO` | Teto do passo de tempo, evita saltos após engasgos |
| `SUAVIDADE_CAM_FOCO` / `SUAVIDADE_CAM_GERAL` | Velocidade de aproximação da câmera |
| `PIXELS_POR_FATIA` | Densidade das fatias das obras rasterizadas (menor = mais nítido, mais caro) |
| `AREA_MINIMA_FACE` | Limite de área para descartar faces minúsculas |

Em máquinas mais fracas, subir `PIXELS_POR_FATIA` para 26 e `AREA_MINIMA_FACE` para 3 dá mais alguns quadros por segundo com perda visual pequena.

## Conceitos de computação gráfica implementados

- Pipeline 3D para 2D completo: escala, rotação, translação, espaço de câmera e projeção perspectiva
- Recorte no plano próximo com interpolação de vértices
- Algoritmo do pintor para ordenação por profundidade
- Sombreamento difuso de Lambert com atenuação por distância
- Descarte de faces traseiras a partir de orientação de malha
- Iluminação binária por teste cone-esfera, inspirado em traçado de raio simplificado
- Oclusão entre salas por teste de linha de visão contra as divisórias e portas
- Mapeamento de textura com perspectiva por fatias verticais
- Detecção de colisão por AABB e por limites de parede
- Animação temporal por Δt com máquina de quatro estados

## Créditos e materiais

Equipe de quatro integrantes, com a divisão de responsabilidades detalhada na tela de créditos da aplicação (tecla `K`).

- **A Ilha dos Mortos**, Arnold Böcklin, 1880 — domínio público, Alte Nationalgalerie Berlin
- **Busto de Nefertiti**, c. 1345 a.C. — digitalização 3D Fraunhofer IGD / CultLab3D (CC BY-NC)
- **Papiro de Ani**, c. 1250 a.C. — British Museum / Wikimedia Commons
- Tecnologias: Python 3 e Pygame, com projeção perspectiva e sombreamento implementados manualmente
