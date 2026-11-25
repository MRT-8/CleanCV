#!/usr/bin/env python3
"""Encode the fictional UI recording into GitHub-friendly MP4 and GIF assets."""
from pathlib import Path
import os
import re
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parent.parent
SOURCE=ROOT/'private/demo/walkthrough.webm'
MEDIA=ROOT/'docs/media'
ffmpeg=os.environ.get('FFMPEG_BINARY') or shutil.which('ffmpeg')
if not ffmpeg:
    try:
        import imageio_ffmpeg
        ffmpeg=imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        raise SystemExit('Install FFmpeg or set FFMPEG_BINARY. Optional: pip install imageio-ffmpeg')
if not SOURCE.is_file():
    raise SystemExit('Run scripts/record-demo.cjs first; only its synthetic recording is accepted.')
MEDIA.mkdir(parents=True,exist_ok=True)
base=[ffmpeg,'-y','-hide_banner','-loglevel','error','-threads','2','-filter_threads','2','-filter_complex_threads','2']
subprocess.run(base+['-ss','0.35','-i',str(SOURCE),'-an','-vf','fps=24,scale=1280:-2:flags=lanczos',
    '-c:v','libx264','-preset','medium','-crf','21','-pix_fmt','yuv420p','-movflags','+faststart',
    '-map_metadata','-1','-metadata','title=CleanCV synthetic walkthrough',str(MEDIA/'cleancv-demo.mp4')],check=True)
subprocess.run(base+['-i',str(MEDIA/'cleancv-demo.mp4'),'-filter_complex',
    'fps=10,scale=1040:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=128:stats_mode=diff[p];[b][p]paletteuse=dither=bayer:bayer_scale=3:diff_mode=rectangle',
    '-loop','0','-map_metadata','-1',str(MEDIA/'cleancv-demo.gif')],check=True)
# Review frames stay private and are never published.
audit=ROOT/'private/demo/audit';audit.mkdir(exist_ok=True)
subprocess.run(base+['-i',str(MEDIA/'cleancv-demo.mp4'),'-vf','fps=1/5,scale=720:-2',str(audit/'frame-%02d.png')],check=True)
for name in ['cleancv-demo.mp4','cleancv-demo.gif','cleancv-home.png','cleancv-poster.png']:
    p=MEDIA/name
    print(f'{name}: {p.stat().st_size/1024/1024:.2f} MiB')
