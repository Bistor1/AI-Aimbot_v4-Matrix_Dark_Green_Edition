# AI-Aimbot v4 - Matrix Dark Green Edition

Saubere, moderne Version mit **dunkel-grünem Matrix Theme**.

## Features
- Triggerbot + sanfter Aim Assist
- Echtzeit-Preview im GUI
- Vollständig einstellbar (Confidence, Aim Strength, etc.)
- Matrix Dark Green Design
- Einstellungen werden gespeichert
- Automatische GPU-Erkennung (NVIDIA / AMD / CPU)

## Installation

### Für neue GPUs (RTX 20xx / 30xx / 40xx und neuer):
```bash
pip install -r requirements.txt
```

### Für alte GPUs (GTX 10xx / 16xx Serie, z.B. GTX 1050 Ti):
```bash
pip install -r requirements-cuda11.txt
```

Danach starten:
```bash
python main.py
```

## Hinweise
- Funktioniert nur unter X11 (nicht Wayland)
- Benötigt `xdotool`
- Bei alten GPUs wird automatisch CPU-Modus verwendet
