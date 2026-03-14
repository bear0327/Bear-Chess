# Bear Chess

[中文 README](./README.md)

Bear Chess is a chess project built with Python + Pygame. It supports local play, AI mode, opening study, and online play.

## Overview

- Local two-player mode
- AI mode powered by Stockfish (UCI)
- Opening study and external opening book hints
- Time controls (`5+2`, `10+0`, `15+10`, unlimited)
- Lichess online mode (token-based login)

## Requirements

- Python 3.9+
- Windows (default setup)

## Quick Start

1. Install dependencies

```bash
pip install -r requirements.txt
```

2. Run from source

```bash
python src/main.py
```

3. Windows one-click launch

- start_app.bat
- create_desktop_shortcut.bat

Notes:

- The desktop icon uses a hidden launcher and does not show cmd/shell.
- start_app.bat only installs dependencies when missing.
- Force reinstall dependencies with: start_app.bat --install

## Build Windows App

Run:

- build_app.bat

The script will:

1. Install build dependencies
2. Build dist/BearChess/BearChess.exe
3. Update the desktop shortcut automatically
4. Launch the executable automatically

Distribution note:

- This uses onedir mode. Keep the whole dist/BearChess folder.

## Project Structure

```text
Bear-Chess/
  src/
    main.py
    logic.py
    renderer.py
    constants.py
    network.py
    private_network.py
    app_event_mixin.py
    app_network_mixin.py
    app_draw_mixin.py
    server.py
  assets/
    images/
    openings.json
  engine/
  start_app.bat
  build_app.bat
  create_desktop_shortcut.bat
  launch_bear_chess_hidden.vbs
```

## Lichess Mode

1. Open Online Mode in the main menu.
2. Input your Lichess API token.
3. You can quick match, challenge users, and accept incoming challenges.

## Troubleshooting

1. App exits right after launch

- Re-run build_app.bat
- Confirm dist/BearChess contains both BearChess.exe and _internal

2. AI mode engine error

- Ensure engine/stockfish-windows-x86-64-avx2.exe exists
- If needed, adjust paths in src/constants.py

3. Lichess connection fails

- Ensure `requests` is installed.
- Ensure network can access `https://lichess.org`.
- Ensure your token is valid and not expired.

## Credits

- python-chess
- Pygame
- Lichess API
- Stockfish
