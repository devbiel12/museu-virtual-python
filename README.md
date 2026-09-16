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

O código foi dividido em **pacotes e módulos por responsabilidade**, mantendo `main.py` apenas como ponto de entrada:

```text
museu-virtual-python/
├── README.md
├── Museu_virtual/
│   ├── main.py
│   ├── museu/
│   │   ├── __init__.py
│   │   ├── museum.py
│   │   ├── config.py
│   │   ├── math3d.py
│   │   ├── geometry.py
│   │   ├── objects.py
│   │   ├── scene.py
│   │   ├── navigation.py
│   │   ├── animation.py
│   │   ├── renderer.py
│   │   ├── ui.py
│   │   └── app.py
│   └── assets/
│       ├── download_assets.py
│       ├── nefertiti_bust.obj
│       ├── papyrus_ani.jpg
│       └── toteninsel.jpg
└── .gitignore
```

### Responsabilidade dos módulos

| Módulo | Responsabilidade |
|---|---|
| `main.py` | Ponto de entrada da aplicação |
| `museu/museum.py` | Monta a classe `MuseuVirtual3D` |
| `museu/config.py` | Configurações, dimensões, FPS, caminhos e cores |
| `museu/math3d.py` | Vetores, transformações, câmera e projeção 3D |
| `museu/geometry.py` | Geometrias estáticas, modelos e carregamento OBJ |
| `museu/objects.py` | `Objeto3D` e `PortaArticulada` |
| `museu/scene.py` | Criação, inicialização e estado da cena |
| `museu/navigation.py` | Movimento, colisões e portas |
| `museu/animation.py` | Atualização temporal e animações |
| `museu/renderer.py` | Piso, paredes, objetos, obras e iluminação |
| `museu/ui.py` | HUD e tela de créditos |
| `museu/app.py` | Loop principal, eventos e execução da aplicação |

> A classe `MuseuVirtual3D` continua existindo com o mesmo nome. A implementação foi organizada em módulos especializados, facilitando manutenção e evolução do projeto.

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
