# Bear Chess

![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?logo=python&logoColor=white)
![Pygame](https://img.shields.io/badge/Pygame-UI%20Engine-1f6f8b)

[中文 README](./README.md)

A chess project built with Python + Pygame, featuring local play, AI battle, opening study, and Lichess online mode.

## Features

- Local two-player mode
- AI mode powered by Stockfish (UCI)
- Opening encyclopedia from `openings.json`
- External opening book hints from `engine/human.bin`
- Time controls (`5+2`, `10+0`, `15+10`, unlimited)
- Pawn promotion selection (Q/R/B/N)
- Lichess online play (token login, quick match, challenge, accept challenge)

## Requirements

- Python 3.9+
- Windows (default engine path points to Windows Stockfish executable)

## Quick Start

### 1) Install dependencies

```bash
pip install -r requirements.txt
```

### 2) Run

```bash
python main.py
```

## Lichess Online Mode

1. Open Online Mode in the main menu.
2. Input your Lichess API token.
3. After connected, you can:
- Start quick match
- Challenge a user
- View and accept incoming challenges

## Core Structure

```text
Bear-Chess/
  main.py          # App entry and state machine
  logic.py         # Game logic, engine integration, coordinate mapping
  renderer.py      # UI rendering
  network.py       # Lichess API integration
  constants.py     # Constants and paths
  openings.json    # Opening lines
  images/          # Piece and UI assets
  engine/          # Stockfish binary, opening book, engine source
```

## Key Paths

Defined in `constants.py`:

- `./engine/stockfish-windows-x86-64-avx2.exe`
- `./engine/human.bin`
- `./openings.json`

## Troubleshooting

### Engine does not respond

- Ensure `engine/stockfish-windows-x86-64-avx2.exe` exists.
- On non-Windows systems, update engine path to your local Stockfish executable.

### Lichess connection fails

- Ensure `requests` is installed.
- Ensure network can access `https://lichess.org`.
- Ensure your token is valid and not expired.
