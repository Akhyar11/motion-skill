#!/usr/bin/env python3
"""
Pollinations Image Generator CLI
100% Gratis, tanpa API Key (atau opsi dengan Free Key untuk bypass cooldown).
Menggunakan model FLUX & SDXL dari Pollinations.ai.
"""

import sys
import os
import argparse
import urllib.request
import urllib.parse
import urllib.error
import json
import time

MODELS = [
    "flux",             # Default: FLUX.1 (schnell) kualitas tinggi
    "flux-realism",     # Realistis / foto tajam
    "flux-anime",       # Kartun / Anime
    "flux-3d",          # Render 3D / Clay / Isometric
    "flux-cablyai",     # CablyAI style
    "turbo",            # SDXL Turbo
]

ASPECT_RATIOS = {
    "16:9": (1280, 720),
    "9:16": (720, 1280),
    "1:1": (1024, 1024),
    "4:3": (1024, 768),
    "3:4": (768, 1024),
    "21:9": (1344, 576),
    "1080p": (1920, 1080),
    "vertical-hd": (1080, 1920),
}

def generate_image(prompt: str, out_path: str, model="flux", width=1280, height=720,
                   seed=None, nologo=True, enhance=False, api_key=None, auto_retry=True, quiet=False):
    base_url = "https://image.pollinations.ai/prompt/"
    encoded_prompt = urllib.parse.quote(prompt)

    params = {
        "model": model,
        "width": width,
        "height": height,
        "nologo": "true" if nologo else "false",
        "enhance": "true" if enhance else "false",
    }
    if seed is not None:
        params["seed"] = seed

    query_str = urllib.parse.urlencode(params)
    full_url = f"{base_url}{encoded_prompt}?{query_str}"

    if not quiet:
        print(f"Generating image via Pollinations (FLUX)...")
        print(f"  Prompt : \"{prompt}\"")
        print(f"  Model  : {model}")
        print(f"  Ukuran : {width}x{height}")
        if seed is not None:
            print(f"  Seed   : {seed}")
        print(f"  Output : {out_path}")

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)

    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; PollinationsCLI/1.0)",
    }
    key = api_key or os.environ.get("POLLINATIONS_API_KEY")
    if key:
        headers["Authorization"] = f"Bearer {key}"

    req = urllib.request.Request(full_url, headers=headers)

    max_attempts = 3 if auto_retry else 1
    for attempt in range(1, max_attempts + 1):
        t0 = time.time()
        try:
            with urllib.request.urlopen(req, timeout=120) as response, open(out_path, "wb") as f:
                f.write(response.read())
            elapsed = time.time() - t0
            if not quiet:
                size_kb = os.path.getsize(out_path) / 1024
                print(f" Berhasil dalam {elapsed:.2f}s ({size_kb:.1f} KB) -> {out_path}")
            return True
        except urllib.error.HTTPError as err:
            body = ""
            try:
                body = err.read().decode('utf-8')
            except Exception:
                pass

            if err.code == 402 and "Free limit reached" in body:
                wait_time = 45
                # Try to parse wait time from JSON if present
                try:
                    data = json.loads(body)
                    msg = data.get("error", {}).get("message", "")
                except Exception:
                    pass

                if auto_retry and attempt < max_attempts:
                    print(f"\n[Info] Cooldown free tier aktif (1 gambar / 45 dtk per IP).")
                    print(f"Menunggu {wait_time} detik sebelum mencoba kembali...")
                    for s in range(wait_time, 0, -5):
                        print(f"  Mencoba kembali dalam {s}s...", end="\r", flush=True)
                        time.sleep(5)
                    print("  Mengulang request sekarang...       ")
                    continue
                else:
                    print(f"\n[Limit] Batas gratis anonim: 1 gambar per 45 detik.", file=sys.stderr)
                    print(f"Tips: Tunggu 45 detik, atau daftarkan key gratis di https://enter.pollinations.ai/", file=sys.stderr)
                    return False
            else:
                print(f"\nHTTP Error {err.code}: {err.reason}", file=sys.stderr)
                if body:
                    print(f"Detail: {body[:300]}", file=sys.stderr)
                return False
        except Exception as e:
            print(f"\nError: {e}", file=sys.stderr)
            return False

    return False

def main():
    parser = argparse.ArgumentParser(description="Generate gambar gratis via Pollinations.ai (FLUX/SDXL)")
    parser.add_argument("prompt", help="Teks deskripsi gambar (bahasa Inggris atau Indonesia)")
    parser.add_argument("-o", "--out", default="generated.jpg", help="Path file output (default: generated.jpg)")
    parser.add_argument("-m", "--model", choices=MODELS, default="flux", help="Model AI (default: flux)")
    parser.add_argument("-a", "--aspect", choices=list(ASPECT_RATIOS.keys()), default="16:9",
                        help="Rasio aspek (16:9, 9:16, 1:1, 4:3, 1080p, dll.)")
    parser.add_argument("-W", "--width", type=int, help="Lebar piksel custom (menimpa --aspect)")
    parser.add_argument("-H", "--height", type=int, help="Tinggi piksel custom (menimpa --aspect)")
    parser.add_argument("-s", "--seed", type=int, help="Seed deterministik (angka bebas)")
    parser.add_argument("--key", help="API Key opsional (bila punya dari enter.pollinations.ai)")
    parser.add_argument("--no-retry", action="store_true", help="Jangan otomatis tunggu bila terkena cooldown 45s")
    parser.add_argument("--enhance", action="store_true", help="Otomatis tingkatkan detail prompt via LLM")
    parser.add_argument("--with-logo", action="store_true", help="Sertakan watermark logo Pollinations")
    parser.add_argument("-q", "--quiet", action="store_true", help="Mode hening")

    args = parser.parse_args()

    width, height = ASPECT_RATIOS[args.aspect]
    if args.width:
        width = args.width
    if args.height:
        height = args.height

    success = generate_image(
        prompt=args.prompt,
        out_path=args.out,
        model=args.model,
        width=width,
        height=height,
        seed=args.seed,
        nologo=not args.with_logo,
        enhance=args.enhance,
        api_key=args.key,
        auto_retry=not args.no_retry,
        quiet=args.quiet
    )

    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
