# Demo Assets

Use this package to produce launch visuals:

- `assets/ui-home.png`
- `assets/coach-mode.gif`
- `assets/demo-video.mp4`

## Video Outline (2-3 minutes)

1. Problem (20s): static notes fail to show idea evolution.
2. Product (20s): C-OS turns notes into temporal cognitive memory.
3. Flow (80s):
   - load sample dataset
   - ask memory query
   - run coach mode
   - open weekly summary
   - open quality dashboard + evaluation run
4. Result (20s): actionable guidance + measurable quality.

## Recording Checklist

1. Start app: `uvicorn cos.app:app --reload`
2. Open: `http://127.0.0.1:8000/`
3. Load starter or sample dataset.
4. Capture both:
   - UI journey recording (`demo-video.mp4`)
   - short GIF for README (`coach-mode.gif`)

## Voiceover Script

See [DEMO_VIDEO_SCRIPT.md](DEMO_VIDEO_SCRIPT.md).
