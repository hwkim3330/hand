# 3D Hand Tracking

**Demo:** https://hwkim3330.github.io/hand/ (needs a webcam)

Real-time hand tracking in the browser. MediaPipe Hands detects 21 landmarks per hand from the webcam, and the landmarks drive the bones of a rigged 3D hand model rendered with Three.js.

## Features

- Up to two hands, with per-hand confidence, depth and pinch readouts, and per-finger state.
- View modes: skeleton, skinned 3D model, or both; grid and palm helpers; camera preview.
- Mirror and left/right swap options; FPS display.

## Files

| File | Role |
|---|---|
| `index.html` | App (MediaPipe Hands + Three.js 0.160, single file) |
| `models/hand.glb` | Rigged hand model |
| `export_hand.py`, `export_skinned.py` | Blender scripts used to export the hand-only skinned GLB |

## Run locally

```bash
python3 -m http.server 8000   # open http://localhost:8000 and allow camera access
```

Deployed with GitHub Pages (`.github/workflows/pages.yml`).

**Status:** working demo.
