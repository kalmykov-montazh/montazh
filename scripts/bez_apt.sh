#!/bin/bash
# 11.11.2026: сбой DNS у машин GitHub — серверы Ubuntu не отвечают, apt не работает.
# Ставим ffmpeg (готовая сборка BtbN с github.com) и шрифт Inter (github.com/rsms/inter) без apt.
set -e
cd /tmp
if ! command -v ffmpeg >/dev/null; then
  curl -fsSL --retry 3 -o ff.tar.xz https://github.com/BtbN/FFmpeg-Builds/releases/latest/download/ffmpeg-n8.1-latest-linux64-gpl-8.1.tar.xz
  tar xf ff.tar.xz && sudo cp ffmpeg-n8.1*/bin/ffmpeg ffmpeg-n8.1*/bin/ffprobe /usr/local/bin/
fi
if ! fc-list | grep -qi "Inter.*Black"; then
  curl -fsSL --retry 3 -o inter.zip https://github.com/rsms/inter/releases/download/v4.1/Inter-4.1.zip
  mkdir -p inter && unzip -oq inter.zip -d inter
  sudo mkdir -p /usr/share/fonts/truetype/inter && sudo find inter -name "Inter-*.ttf" -o -name "Inter*.otf" | sudo xargs -I{} cp {} /usr/share/fonts/truetype/inter/ 2>/dev/null || true
  sudo find inter -path "*extras/ttf*" -name "*.ttf" -exec cp {} /usr/share/fonts/truetype/inter/ \; 2>/dev/null || true
  sudo fc-cache -f >/dev/null
fi
# шрифт DejaVu для подписей на листах проверки
[ -f /usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf ] || true
echo "::notice::без apt: $(ffmpeg -version | head -1 | cut -d' ' -f1-3), Inter: $(fc-list | grep -ci inter)"
