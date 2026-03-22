"""
generate_audio.py — Pre-generate narration MP3 files for all experiments.

Usage:
    python generate_audio.py          # skip existing files
    python generate_audio.py --force  # regenerate all

Dependencies (install with .venv active):
    pip install gtts pydub

Audio files are saved to public/audio/{exp_id}.mp3
Run this locally before deploying to Vercel.
"""

import os
import sys
import json
import argparse
import textwrap

# gTTS: free Google Text-to-Speech
from gtts import gTTS

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EXPS_PATH = os.path.join(BASE_DIR, "data", "exps.json")
AUDIO_DIR = os.path.join(BASE_DIR, "public", "audio")


def load_experiments() -> dict:
    with open(EXPS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def make_narration_text(exp_id: str, exp: dict) -> str:
    """
    Build a natural-sounding narration from the experiment data.
    Uses narration_script if present, otherwise auto-generates from fields.
    Adds pauses via ellipsis and line breaks for more natural delivery.
    """
    script = exp.get("narration_script", "")
    if script:
        # Add natural pauses between paragraphs
        paused = script.replace("\n\n", "... ")
        return paused

    # Fallback: auto-build from structured fields
    lines = []
    apparatus = exp.get("apparatus", exp_id)
    lines.append(f"Welcome to experiment {exp_id}. {apparatus}.")
    lines.append("")

    short = exp.get("short_desc", "")
    if short:
        lines.append(short)
        lines.append("")

    objectives = exp.get("objectives", [])
    if objectives:
        lines.append("The objectives of this experiment are...")
        for obj in objectives[:3]:  # limit to 3 for audio length
            lines.append(f"{obj}.")
        lines.append("")

    key_points = exp.get("key_points", [])
    if key_points:
        lines.append("Key points to remember include...")
        for kp in key_points[:3]:
            lines.append(f"{kp}.")

    return " ".join(lines)


def generate_audio_for_exp(exp_id: str, exp: dict, force: bool = False) -> str:
    """Generate MP3 for a single experiment. Returns output path."""
    os.makedirs(AUDIO_DIR, exist_ok=True)
    out_path = os.path.join(AUDIO_DIR, f"{exp_id}.mp3")

    if os.path.exists(out_path) and not force:
        print(f"  ⏭️  Skipping {exp_id} — already exists ({os.path.getsize(out_path):,} bytes)")
        return out_path

    text = make_narration_text(exp_id, exp)
    if not text.strip():
        print(f"  ⚠️  No narration text for {exp_id} — skipping")
        return ""

    print(f"  🎙️  Generating audio for {exp_id} ({len(text)} chars)…")
    
    # Split long text into chunks (gTTS has ~5000 char limit per call)
    # We split on sentences to keep natural flow
    chunks = split_into_chunks(text, max_chars=4500)
    
    if len(chunks) == 1:
        tts = gTTS(text=chunks[0], lang="en", slow=False)
        tts.save(out_path)
    else:
        # Multiple chunks: save each and concatenate
        import tempfile
        temp_files = []
        for i, chunk in enumerate(chunks):
            tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
            tmp.close()
            gTTS(text=chunk, lang="en", slow=False).save(tmp.name)
            temp_files.append(tmp.name)
        
        # Concatenate MP3 files by binary append (simple approach without pydub)
        with open(out_path, "wb") as out_f:
            for tmp_path in temp_files:
                with open(tmp_path, "rb") as tmp_f:
                    out_f.write(tmp_f.read())
                os.unlink(tmp_path)

    size = os.path.getsize(out_path)
    print(f"  ✅  Saved: {out_path} ({size:,} bytes)")
    return out_path


def split_into_chunks(text: str, max_chars: int = 4500) -> list:
    """Split text into chunks at sentence boundaries."""
    if len(text) <= max_chars:
        return [text]
    
    sentences = text.replace("... ", "…SPLIT…").split(".")
    chunks = []
    current = ""
    
    for sent in sentences:
        sent = sent.replace("…SPLIT…", "... ").strip()
        if not sent:
            continue
        candidate = current + ". " + sent if current else sent
        if len(candidate) <= max_chars:
            current = candidate
        else:
            if current:
                chunks.append(current.strip())
            current = sent
    
    if current:
        chunks.append(current.strip())
    
    return chunks if chunks else [text]


def main():
    parser = argparse.ArgumentParser(description="Generate audio narrations for MQC Lab experiments")
    parser.add_argument("--force", action="store_true", help="Regenerate even if file exists")
    parser.add_argument("--exp", type=str, default=None, help="Generate only for a specific experiment ID")
    args = parser.parse_args()

    exps = load_experiments()
    
    if args.exp:
        if args.exp not in exps:
            print(f"❌ Experiment '{args.exp}' not found in exps.json")
            sys.exit(1)
        targets = {args.exp: exps[args.exp]}
    else:
        targets = exps

    print(f"\n🎙️  MQC Audio Generator — {len(targets)} experiment(s)\n")
    
    success = 0
    failed = 0
    
    for exp_id, exp in targets.items():
        try:
            result = generate_audio_for_exp(exp_id, exp, force=args.force)
            if result:
                success += 1
        except Exception as e:
            print(f"  ❌  Failed for {exp_id}: {e}")
            failed += 1
    
    print(f"\n{'='*50}")
    print(f"✅ Generated: {success}  |  ❌ Failed: {failed}")
    print(f"📂 Output dir: {AUDIO_DIR}")
    print("\n💡 Remember to commit the generated audio files before deploying to Vercel!")


if __name__ == "__main__":
    main()
