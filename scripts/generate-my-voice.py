#!/usr/bin/env python3
"""
CLI Voice Cloning Lokal Bahasa Indonesia
100% Gratis, 100% Offline di CPU Anda, Mengkloning Suara Anda Sendiri.
Menggunakan Model: anak10thn/pocket-tts-indonesian
"""

import sys
import os
import argparse
import time
import torch
import soundfile as sf
from pocket_tts import TTSModel

DEFAULT_CONFIG = os.path.expanduser("/home/akhyar/Dokumen/YouTube/models/pocket-tts-indonesian/indonesian_6l.yaml")
DEFAULT_VOICE = os.path.expanduser("/home/akhyar/Dokumen/YouTube/assets/voice/reference_voice.wav")

def split_into_paragraphs(text: str, max_chars: int = 150):
    """
    Pecah teks menjadi potongan kalimat agar intonasi alami dan tidak kepanjangan per batch.
    """
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    chunks = []
    for line in lines:
        if len(line) <= max_chars:
            chunks.append(line)
        else:
            # Pecah per kalimat tanda baca
            sentences = [s.strip() for s in line.replace("?", "?|").replace(".", ".|").replace("!", "!|").split("|") if s.strip()]
            cur = ""
            for s in sentences:
                if len(cur) + len(s) + 1 <= max_chars:
                    cur = (cur + " " + s).strip()
                else:
                    if cur:
                        chunks.append(cur)
                    cur = s
            if cur:
                chunks.append(cur)
    return chunks

def generate_cloned_voice(text: str, out_path: str, voice_path: str = DEFAULT_VOICE,
                          config_path: str = DEFAULT_CONFIG):
    if not os.path.exists(config_path):
        print(f"Error: Config model tidak ditemukan di: {config_path}", file=sys.stderr)
        return False
    if not os.path.exists(voice_path):
        print(f"Error: File rekaman suara Anda tidak ditemukan di: {voice_path}", file=sys.stderr)
        return False

    chunks = split_into_paragraphs(text)
    total = len(chunks)

    print("\n" + "="*50)
    print("  POCKET-TTS INDONESIA: VOICE CLONING LOKAL")
    print("="*50)
    print(f"  Sampel Suara : {voice_path}")
    print(f"  Total Kalimat: {total} bagian naskah")
    print(f"  Output       : {out_path}")
    print("="*50 + "\n")

    print("[1/3] Memuat model bahasa Indonesia ke memori...")
    t0 = time.time()
    model = TTSModel.load_model(config=config_path)

    print("[2/3] Mengekstraksi karakteristik timbre suara Anda...")
    voice_state = model.get_state_for_audio_prompt(voice_path)

    print("[3/3] Mengenerate audio narasi...")
    audio_tensors = []
    
    # Tambahkan hening kecil (0.3s) antar kalimat
    silence = torch.zeros((1, int(model.sample_rate * 0.3)), dtype=torch.float32)

    for idx, chunk in enumerate(chunks, 1):
        print(f"  [{idx}/{total}] \"{chunk[:45]}...\"")
        chunk_audio = model.generate_audio(voice_state, chunk, copy_state=True)
        audio_tensors.append(chunk_audio)
        if idx < total:
            audio_tensors.append(silence)

    full_audio = torch.cat(audio_tensors, dim=-1)

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    sf.write(out_path, full_audio.squeeze().numpy(), model.sample_rate)

    dur = full_audio.shape[-1] / model.sample_rate
    elapsed = time.time() - t0
    print(f"\n Berhasil! Audio narasi ({dur:.1f} detik) tersimpan di:\n👉 {out_path}")
    print(f"   (Waktu render total: {elapsed:.1f} detik)\n")
    return True

def main():
    parser = argparse.ArgumentParser(description="Kloning Suara Sendiri Berbahasa Indonesia (Lokal & Gratis)")
    parser.add_argument("text", nargs="?", help="Teks narasi langsung")
    parser.add_argument("-f", "--file", help="File naskah (.txt / .md)")
    parser.add_argument("-o", "--out", default="assets/audio/narasi_kloning.wav", help="Path file output (.wav)")
    parser.add_argument("-v", "--voice", default=DEFAULT_VOICE, help="Path audio master suara Anda (.wav)")
    parser.add_argument("-c", "--config", default=DEFAULT_CONFIG, help="Path config model")

    args = parser.parse_args()

    content = ""
    if args.file:
        if not os.path.exists(args.file):
            print(f"Error: File {args.file} tidak ditemukan.", file=sys.stderr)
            sys.exit(1)
        with open(args.file, "r", encoding="utf-8") as f:
            content = f.read()
    elif args.text:
        content = args.text
    else:
        parser.print_help()
        sys.exit(1)

    success = generate_cloned_voice(
        text=content,
        out_path=args.out,
        voice_path=args.voice,
        config_path=args.config
    )
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
