# Склейщик: собирает видео.mp4 из кусков .part1, .part2 ... во всех папках «Монтаж!»
# Рядом с кусками лежит файл видео.mp4.parts: "число_кусков размер_в_байтах [замаскировано_байт]". Он пишется последним.
$root = Split-Path $PSScriptRoot -Parent
$log = Join-Path $PSScriptRoot 'склейка.log'
$ready = Get-ChildItem -LiteralPath $root -Directory | Where-Object { $_.Name -like 'Готовые*' } | Select-Object -First 1
if (-not $ready) { exit }
Get-ChildItem -LiteralPath $root -Recurse -Filter '*.parts' | ForEach-Object {
  try {
    $m = $_; $dir = $m.DirectoryName
    $base = $m.Name.Substring(0, $m.Name.Length - 6)
    $info = (Get-Content -LiteralPath $m.FullName -Raw).Trim().Split(' ')
    $n = [int]$info[0]; $size = [int64]$info[1]
    $parts = @(1..$n | ForEach-Object { Join-Path $dir "$base.part$_" })
    if (@($parts | Where-Object { -not (Test-Path -LiteralPath $_) }).Count -gt 0) { return }
    $sum = ($parts | ForEach-Object { (Get-Item -LiteralPath $_).Length } | Measure-Object -Sum).Sum
    if ($sum -ne $size) { return }
    $tmp = Join-Path $dir "$base.tmp"
    $out = [IO.File]::Create($tmp)
    $mask = 0; if ($info.Count -gt 2) { $mask = [int]$info[2] }
    foreach ($p in $parts) {
      if ($mask -gt 0 -and $p -eq $parts[0]) {
        # начало первого куска замаскировано (XOR 0x5A), иначе передача портит видеофайл
        $b = [IO.File]::ReadAllBytes($p)
        for ($i = 0; $i -lt $mask; $i++) { $b[$i] = $b[$i] -bxor 0x5A }
        $out.Write($b, 0, $b.Length)
      } else { $in = [IO.File]::OpenRead($p); $in.CopyTo($out); $in.Close() }
    }
    $out.Close()
    $final = Join-Path $dir $base
    if (Test-Path -LiteralPath $final) { Remove-Item -LiteralPath $final -Force }
    Move-Item -LiteralPath $tmp -Destination $final
    $parts | ForEach-Object { Remove-Item -LiteralPath $_ -Force }
    Remove-Item -LiteralPath $m.FullName -Force
    Add-Content -LiteralPath $log -Value "$(Get-Date -Format 'yyyy-MM-dd HH:mm') склеил: $final ($size байт)" -Encoding UTF8
  } catch {
    Add-Content -LiteralPath $log -Value "$(Get-Date -Format 'yyyy-MM-dd HH:mm') ошибка: $($m.FullName): $_" -Encoding UTF8
  }
}
