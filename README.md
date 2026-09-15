# Museu Virtual

Projeto de Computação Gráfica em Python com Pygame, desenvolvido como ambiente interativo inspirado em um museu virtual com três salas, obras históricas e navegação 3D simplificada.

## Visão geral

Este projeto cria uma cena 3D em perspectiva utilizando cálculos matemáticos próprios para:

- projeção de pontos 3D em 2D
- rotação, escala e translação de objetos
- câmera com modos de visualização
- colisão básica e portas articuladas
- renderização de superfícies, linhas e polígonos
- apresentação de obras em uma galeria virtual

A aplicação atual implementa três exposições principais:

1. Sala central: A Ilha dos Mortos
2. Sala oeste: Busto de Nefertiti
3. Sala leste: Papiro de Ani

## Estrutura do projeto

```text
museu-virtual-python-devbiel12-patch-1/
├── README.md
├── Museu_virtual/
│   ├── main.py
│   └── assets/
│       ├── download_assets.py
│       ├── nefertiti_bust.obj
│       ├── papyrus_ani.jpg
│       └── toteninsel.jpg
└── .gitignore
```

> O arquivo principal do projeto está em `Museu_virtual/main.py` e o downloader de assets em `Museu_virtual/assets/download_assets.py`.

## Requisitos

- Python 3.9+
- Pygame

Instale as dependências com:

```bash
pip install pygame
```

## Como executar

A partir da raiz do projeto:

```bash
python Museu_virtual/main.py
```

Ou, se preferir entrar na pasta do projeto:

```bash
cd Museu_virtual
python main.py
```

## Download e preparação dos assets

O script de assets pode ser executado manualmente para baixar ou regenerar os arquivos da cena, caso estejam ausentes:

```bash
python Museu_virtual/assets/download_assets.py
```

Esse script tenta baixar imagens e processar o modelo 3D da Nefertiti, criando arquivos de fallback se necessário.

## Controles

### Modo apresentação

- `Espaço`: inicia, pausa ou retoma a visita guiada
- `R`: reinicia a cena
- `C`: alterna entre visão geral e foco na obra
- `1`, `2`, `3`: vai para cada sala
- `N` / `B`: avança ou retorna entre salas
- `K`: alterna a tela de créditos
- `M`: troca entre o modo de apresentação e o modo livre
- `Esc`: fecha a aplicação

### Modo livre

- `W` / `S`: anda para frente e para trás
- `A` / `D`: desloca lateralmente
- Mouse: gira a câmera
- Sistema de colisão: impede atravessar paredes e pedestais

## Observações

- O projeto foi construído sem uso de motores 3D externos.
- A criação dos ativos é feita em grande parte no próprio código e em assets locais baixados pelo script de preparação.
- O README foi ajustado para refletir a estrutura real do repositório e os caminhos corretos dos arquivos.

## Licenças e materiais

Os recursos visuais do projeto podem incluir imagens e modelos públicos, e o script de backup tenta manter o projeto funcional mesmo quando os arquivos externos não estão disponíveis.
