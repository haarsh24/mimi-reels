#!/usr/bin/env python3
"""Make a Sarvam voiceover for every voice-requests/<id>.txt that has no voice/<id>.wav yet.
The key comes from the SARVAM_API_KEY environment variable (a GitHub Actions secret). It is never printed or stored.
Optional first line in a request file:  #speaker=ritu_hi_reels model=bulbul:v4-flash pace=1.0 temperature=0.7"""
import base64, io, os, sys, wave
from pathlib import Path

from sarvamai import SarvamAI

ROOT = Path(__file__).resolve().parent.parent
key = os.environ.get("SARVAM_API_KEY")
if not key:
    sys.exit("SARVAM_API_KEY is not set (add it under Settings > Secrets and variables > Actions).")
client = SarvamAI(api_subscription_key=key)
(ROOT / "voice").mkdir(exist_ok=True)

todo = [p for p in sorted((ROOT / "voice-requests").glob("*.txt")) if not (ROOT / "voice" / f"{p.stem}.wav").exists()]
if not todo:
    print("nothing to do")
    sys.exit(0)

for req in todo:
    lines = req.read_text().splitlines()
    opts = {"pace": "1.0", "temperature": "0.7"}
    if lines and lines[0].startswith("#"):
        opts.update(dict(kv.split("=", 1) for kv in lines[0][1:].split() if "=" in kv))
        lines = lines[1:]
    text = " ".join(l.strip() for l in lines if l.strip())
    if len(text) > 2500:
        sys.exit(f"{req.name}: {len(text)} chars, Sarvam allows 2500 per call.")
    cands = [(opts["model"], opts["speaker"])] if "model" in opts and "speaker" in opts else [("bulbul:v4-flash", "ritu_hi_reels"), ("bulbul:v3", "ritu")]
    resp = used = None
    for model, speaker in cands:
        for with_temp in (True, False):
            try:
                kw = dict(text=text, language_code="hi-IN", speaker=speaker, model=model, pace=float(opts["pace"]), speech_sample_rate=24000, output_audio_codec="wav")
                if with_temp:
                    kw["temperature"] = float(opts["temperature"])
                resp = client.text_to_speech.convert(**kw)
                used = (model, speaker)
                break
            except Exception as e:
                print(f"[skip] {model}/{speaker} temp={with_temp}: {type(e).__name__} {getattr(e, 'status_code', '')} {str(getattr(e, 'body', None) or e)[:200]}")
        if resp:
            break
    if not resp:
        sys.exit(f"{req.name}: no Sarvam voice combination worked.")
    frames, params = [], None
    for c in (base64.b64decode(x) for x in resp.audios):
        with wave.open(io.BytesIO(c)) as w:
            params = params or w.getparams()
            frames.append(w.readframes(w.getnframes()))
    out = ROOT / "voice" / f"{req.stem}.wav"
    with wave.open(str(out), "wb") as w:
        w.setparams(params)
        w.writeframes(b"".join(frames))
    dur = sum(len(f) for f in frames) / (params.sampwidth * params.nchannels * params.framerate)
    print(f"[ok] {req.stem}: {used[1]} ({used[0]}), pace {opts['pace']}, {dur:.1f}s")
