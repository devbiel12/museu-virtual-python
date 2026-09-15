# Projeto AP 1 — Mundo Virtual Animado
## Computação Gráfica e RA/RV — Faculdade Impacta
### Tema: Museu Virtual de História da Arte e da Antiguidade (Variação 1)

---

## 1. Visão Geral do Projeto

Este projeto consiste em uma aplicação gráfica tridimensional interativa desenvolvida em **Python + Pygame**, sem o uso de OpenGL, motores 3D ou bibliotecas externas pesadas. O projeto atende rigorosamente a todas as diretrizes didáticas da atividade **AP 1 — Mundo Virtual Animado**, empregando **projeção perspectiva 3D $\to$ 2D por formulação matemática explícita**, transformações lineares (escala, rotação, translação), máquina de estados, teste de visibilidade inspirado em traçado de raio simplificado (iluminação binária) e renderização por superfícies rasterizadas e polígonos sombreados.

O ambiente representa um **Museu Virtual** organizado em três salas/galerias temáticas arquitetonicamente conectadas por portais com portas articuladas, abrigando três obras de categorias e períodos históricos distintos. As paredes e o teto são tratados como geometria física, com recorte de perspectiva, oclusão e colisão para evitar que o visitante veja através da arquitetura.
1. **Sala 1 (Centro) — Galeria de Pinturas Simbolistas**: *A Ilha dos Mortos (Die Toteninsel)* — Arnold Böcklin (1880, Versão III).
2. **Sala 2 (Oeste) — Galeria de Esculturas da Antiguidade**: *Busto de Nefertiti* — Antigo Egito (c. 1345 a.C., XVIII Dinastia).
3. **Sala 3 (Leste) — Galeria de Manuscritos e Documentos Históricos**: *Papiro de Ani (Livro dos Mortos)* — Tebas, Antigo Egito (c. 1250 a.C.).

---

## 2. Estrutura de Arquivos do Projeto

```
./
│
├── museu_virtual_ap1.py       # Código-fonte principal com o motor gráfico 3D e cena
├── README.md                  # Documentação completa de execução e acadêmica
│
└── assets/                    # Diretório de modelos 3D e texturas históricas
    ├── download_assets.py     # Script autônomo para baixar/processar assets
    ├── nefertiti_bust.obj     # Malha 3D da escultura (452 vértices, 894 faces)
    ├── toteninsel.jpg         # Pintura de Arnold Böcklin em alta definição
    └── papyrus_ani.jpg        # Textura autêntica do Papiro de Ani (Livro dos Mortos)
```

---

## 3. Requisitos e Dependências

- **Python 3.8+** (testado e homologado em Python 3.10 a 3.14).
- **Pygame** ou **Pygame-ce** (Community Edition):
  ```bash
  pip install pygame
  # ou
  pip install pygame-ce
  ```
- **Nenhuma biblioteca externa de motores 3D (Three.js, Ursina, Panda3D, PyOpenGL, etc.) é utilizada**, cumprindo 100% da restrição didática da disciplina.

---

## 4. Instruções de Execução

No terminal ou prompt de comando (PowerShell / Bash), navegue até a pasta do projeto e execute:

```bash
python museu_virtual_ap1.py
```

*Nota*: Caso os arquivos de imagem ou 3D precisem ser restabelecidos em qualquer momento, execute `python assets/download_assets.py`.

---

## 5. Modos de Operação e Tabela de Controles

Para harmonizar com precisão **as exigências avaliativas do PDF da AP1** (que exige comandos discretos e proíbe navegação em tempo real durante a avaliação da apresentação) e **a experiência imersiva de museu solicitada** (com movimentação contínua e exploração livre), o sistema possui **dois modos alternáveis instantaneamente pela tecla `[M]`**:

### 5.1 Modo Apresentação Didática AP1 (Padrão de Avaliação)
Projetado para demonstrar os conceitos e atender diretamente à banca avaliadora:
| Tecla / Comando | Ação no Museu |
| :--- | :--- |
| **`[ESPAÇO]`** | Inicia, Pausa ou Retoma a Visita Guiada sequencial pelas salas |
| **`[R]`** | Reinicia todas as posições, rotações, cronômetro e máquina de estados |
| **`[C]`** | Alterna o Modo de Câmera: **Plano Geral** $\leftrightarrow$ **Foco Animado na Obra** |
| **`[1]`** | Abre a passagem oeste e transita suavemente para a **Sala de Esculturas / Busto de Nefertiti** |
| **`[2]`** | Fecha as portas e transita suavemente para a **Sala de Pinturas / A Ilha dos Mortos** |
| **`[3]`** | Abre a passagem leste e transita suavemente para a **Sala de Manuscritos / Papiro de Ani** |
| **`[N]`** | Avança na ordem **Escultura → Pintura → Papiro**, abrindo apenas a porta necessária |
| **`[B]`** | Retorna na ordem inversa, fechando e abrindo as portas correspondentes |
| **`[K]`** | Abre ou fecha a **Tela de Créditos** da Equipe e Referências |
| **`[M]`** | Alterna entre o Modo Apresentação e o Modo Navegação Livre |
| **`[ESC]`** | Encerra a aplicação de forma limpa |

Durante as transições do modo apresentação, a câmera aguarda a animação da porta terminar antes de avançar. Ao iniciar a visita guiada com `[ESPAÇO]`, as portas são acionadas automaticamente. Ao retornar do modo livre para o modo apresentação, o cenário é reiniciado no plano geral, com as portas fechadas.

### 5.2 Modo Navegação Livre do Visitante
Permite caminhar livremente pelos corredores e salas do museu com câmera em primeira pessoa:
| Controle | Ação de Movimentação |
| :--- | :--- |
| **`W`** ou **`Seta Cima`** | Caminha para a frente na direção para onde o visitante olha |
| **`S`** ou **`Seta Baixo`** | Caminha para trás |
| **`A`** ou **`Seta Esquerda`** | Deslocamento lateral (*strafe*) para a esquerda |
| **`D`** ou **`Seta Direita`** | Deslocamento lateral (*strafe*) para a direita |
| **`Mouse (arraste)`** | Rotaciona livremente a visão em 360° (**Yaw**: esquerda/direita, **Pitch**: cima/baixo) |
| **Sistema de Colisão** | Bloqueia o visitante de atravessar paredes externas, divisórias ou entrar nos pedestais |
| **Portas articuladas** | Começam fechadas e abrem automaticamente somente quando o visitante se aproxima do portal correspondente |
| **Placa de Proximidade** | Ao se aproximar a menos de 3,5m de uma obra, surge a placa didática em destaque |

---

## 6. Identificação das Três Obras de Arte e Fontes

### Arquitetura e Portas Articuladas
- **Paredes e teto**: modelados como superfícies 3D fixas, com recorte no plano próximo e ordenação por profundidade.
- **Porta Oeste**: controla a passagem para a sala da escultura.
- **Porta Leste**: controla a passagem para a sala do papiro.
- **Abertura unidirecional**: as duas folhas de cada porta giram para o mesmo lado, em direção à sala da escultura.
- **Oclusão física**: paredes, teto e portas são ordenados pela profundidade da câmera, impedindo portas distantes de aparecerem sobre paredes.
- **Modo livre**: as portas iniciam fechadas, abrem por proximidade e bloqueiam a passagem enquanto ainda estão fechadas.

### Obra 1: A Ilha dos Mortos (*Die Toteninsel*)
- **Autor**: Arnold Böcklin (1827–1901).
- **Período e Data**: Simbolismo do Século XIX (1880, Versão III).
- **Apresentação 3D**: Exposta na parede norte da galeria central em uma moldura clássica entalhada em relevo com detalhes em ouro, com iluminação superior de trilho LED.
- **Fonte do Material**: Alte Nationalgalerie, Berlim / Wikimedia Commons ([Domínio Público](https://commons.wikimedia.org/wiki/File:Arnold_B%C3%B6cklin_-_Die_Toteninsel_III_(Alte_Nationalgalerie,_Berlin).jpg)).

### Obra 2: Busto de Nefertiti
- **Autor / Origem**: Tutmés (Escultor Real), Tel el-Amarna, Antigo Egito.
- **Período e Data**: Império Novo (XVIII Dinastia, c. 1345 a.C.).
- **Apresentação 3D**: Malha tridimensional realista otimizada para software rendering (~894 faces), posicionada sobre um pedestal clássico de mármore com base escalonada e capitel, executando rotação contínua no eixo Y.
- **Fonte do Modelo 3D**: Digitalização 3D de alta precisão realizada pelo Fraunhofer IGD / CultLab3D ([Licença Creative Commons Atribuição-NãoComercial CC BY-NC](http://www.cultlab3d.de/)), adaptada para uso educacional em Computação Gráfica.

### Obra 3: Papiro de Ani (Livro dos Mortos)
- **Autor / Origem**: Escribas e Iluminadores do Templo de Tebas, Antigo Egito.
- **Período e Data**: Império Novo (XIX Dinastia, c. 1250 a.C.).
- **Apresentação 3D**: Vitrine expositora de museu composta por gabinete em madeira nobre (mogno), tampo inclinado ergonômico, pergaminho desenrolado com textura autêntica, hastes cilíndricas laterais e redoma de vidro transparente 3D.
- **Fonte do Material**: British Museum, Londres / Wikimedia Commons ([Domínio Público](https://commons.wikimedia.org/wiki/File:Papyrus_of_Ani_BM_Sheet_12.jpg)).

---

## 7. Conformidade com os Requisitos Obrigatórios da AP1

| Nº | Requisito do Enunciado AP1 | Implementação no Projeto |
| :---: | :--- | :--- |
| **1** | Janela configurável, laço principal, controle de FPS, $\Delta t$ e encerramento | Janela $1150 \times 740$, laço contínuo com `relogio.tick(60)`, `dt = tick/1000.0` e encerramento seguro por `QUIT` e `K_ESCAPE`. |
| **2** | Ao menos 3 tipos de primitivas gráficas | 4 tipos implementados: **Linhas** (grade do piso, contornos, raios de luz), **Polígonos** (faces 3D sombreadas por normais), **Círculos** (luminárias emissores) e **Superfícies Rasterizadas** (tela da pintura e lâmina do papiro). |
| **3** | Ao menos 5 objetos na cena (instâncias, simples e composto) | **8 objetos ativos**: 1 pedestal de mármore para a escultura, 3 placas simples em bronze, moldura 3D, busto de Nefertiti, vitrine composta e papiro físico. A cena também possui paredes, teto e portas articuladas como geometria arquitetônica. |
| **4** | Aplicação de translação, rotação e escala com variação temporal | **Rotação**: Escultura e folhas das portas articuladas; **Translação**: A câmera transita suavemente entre as galerias; **Escala**: Pulsação sutil no cone de luz. |
| **5** | Câmera com ao menos dois modos de apresentação | Modo **Plano Geral**, Modo **Foco Animado** com interpolação suave (LERP) e Modo **Navegação Livre** com WASD e Mouse. |
| **6** | Pelo menos 3 animações distintas | 1) **Transformação Espacial**: Rotação contínua da escultura; 2) **Portas articuladas**: abertura e fechamento gradual por tecla, visita guiada ou proximidade; 3) **Máquina de Estados**: ciclo de vida (`PARADO`, `EXECUTANDO`, `PAUSADO`, `CONCLUIDO`); 4) visita guiada sequenciando as salas com iluminação progressiva. |
| **7** | Comandos discretos de teclado documentados | Teclas `[ESPAÇO]`, `[R]`, `[C]`, `[1, 2, 3]`, `[N]`, `[B]`, `[K]`, `[M]` com ações discretas documentadas no HUD e no README. |
| **8** | Interface sobreposta (HUD) completa | Painel superior com título, sala atual, modo de câmera, estado da animação, tempo decorrido e **barra de progresso visual**; painéis inferiores com comandos e dados da obra. |
| **9** | Visibilidade / Traçado de raio simplificado | Traçado de raio do refletor LED no teto para o centro das obras. Cálculo de cone de abertura angular resultando em **Iluminação Binária** (`1 - ILUMINADA` vs `0 - SOMBRA`), além do feixe visual renderizado. |
| **10** | Tela de créditos da equipe e referências | Tela sobreposta acionada por `[K]` contendo os 4 integrantes, variação temática escolhida e todas as fontes acadêmicas e bibliográficas. |

---

## 8. Equipe de Desenvolvimento e Divisão de Tarefas

1. **Gabriel Araujo Farias**
2. **Guilherme Amorim Rocha Lima**
3. **Mateus Deziderio Sanches**:
4. **Richard Bernardino Mendes**