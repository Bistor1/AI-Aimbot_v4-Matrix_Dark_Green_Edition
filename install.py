#!/usr/bin/env python3
"""
Automatischer Installer für AI-Aimbot mit Fallback
Testet zuerst CUDA 11.8 (alte GPUs), dann normale Installation
"""

import subprocess
import sys

def run_pip(args):
    cmd = [sys.executable, "-m", "pip", "install"] + args
    print(f"→ Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0, result.stdout + result.stderr

def main():
    print("=" * 60)
    print("AI-Aimbot Installer mit GPU Fallback")
    print("=" * 60)

    # Zuerst versuchen: CUDA 11.8 (für alte GPUs wie GTX 1050 Ti)
    print("\n[1/2] Versuche Installation mit CUDA 11.8 (für alte NVIDIA GPUs)...")
    success, output = run_pip(["-r", "requirements-cuda11.txt"])

    if success:
        print("\n✅ Erfolgreich mit CUDA 11.8 installiert!")
        print("   Deine alte GPU sollte jetzt unterstützt werden.")
        return

    print("\n⚠️  CUDA 11.8 Installation fehlgeschlagen.")
    print("   Fallback auf Standard-Installation...\n")

    # Fallback: Normale Installation
    print("[2/2] Installiere Standard-Version...")
    success, output = run_pip(["-r", "requirements.txt"])

    if success:
        print("\n✅ Standard-Installation erfolgreich!")
        print("   (Wird wahrscheinlich CPU-Modus verwenden)")
    else:
        print("\n❌ Installation fehlgeschlagen.")
        print("   Bitte manuell prüfen.")
        print(output)

if __name__ == "__main__":
    main()
