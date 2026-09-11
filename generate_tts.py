import argparse
from pathlib import Path
from language_ai.config import Settings
from language_ai.tts import synthesize

parser = argparse.ArgumentParser()
parser.add_argument("text", type=Path)
parser.add_argument("output", type=Path)
args = parser.parse_args()
if not synthesize(args.text.read_text(encoding="utf-8"), args.output, Settings.from_env().tts_command):
    raise SystemExit("TTS was not generated; configure LANGUAGE_TTS_COMMAND")

