#!/bin/bash
# Скачать источник подборки: путь внутри «Монтаж!» или «id:<ID файла на Диске>» (архив Google Фото и др.)
set -e
S="$1"; O="$2"
if [[ "$S" == id:* ]]; then
  d=$(mktemp -d); rclone backend copyid montazh: "${S#id:}" "$d/" && mv "$d"/* "$O" && rmdir "$d"
else
  rclone copyto "montazh:$S" "$O"
fi
