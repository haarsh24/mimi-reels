# mimi-reels voice maker
Push `voice-requests/<id>.txt` (Devanagari Hinglish text) -> GitHub Actions calls Sarvam -> `voice/<id>.wav` appears.
The Sarvam key lives only in the repo secret `SARVAM_API_KEY`. Never commit a key. Delete `voice/<id>.wav` to remake one.
