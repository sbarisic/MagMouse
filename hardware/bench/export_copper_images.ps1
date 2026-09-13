param(
    [string]$KiCadCli = 'C:/Users/cartm/AppData/Local/Programs/KiCad/10.0/bin/kicad-cli.exe',
    [string]$Node = 'C:/Users/cartm/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe',
    [string]$Sharp = 'C:/Users/cartm/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp'
)
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path "$PSScriptRoot/../..").Path
$output = Join-Path $PSScriptRoot 'copper-images'
New-Item -ItemType Directory -Force -Path $output | Out-Null
$boards = [ordered]@{
    Main = 'hardware/modular/main/Main.kicad_pcb'
    Wheel = 'hardware/modular/wheel/Wheel.kicad_pcb'
    Encoder = 'hardware/encoder/Encoder.kicad_pcb'
    Panel = 'hardware/bench/Panel.kicad_pcb'
}
$entries = @()
foreach ($name in $boards.Keys) {
    $source = Join-Path $root $boards[$name]
    foreach ($layer in @('F.Cu', 'In1.Cu', 'In2.Cu', 'B.Cu')) {
        $stem = "$name-$layer"
        & $KiCadCli pcb export svg --mode-single -l "$layer,Edge.Cuts" --page-size-mode 2 --exclude-drawing-sheet --drill-shape-opt 2 -o "$output/$stem.svg" $source
        if ($LASTEXITCODE -ne 0) { throw "Export failed: $stem" }
        $entries += [ordered]@{ board=$name; layer=$layer; stem=$stem; source=$boards[$name]; sha256=(Get-FileHash $source -Algorithm SHA256).Hash.ToLowerInvariant() }
    }
}
$entries | ConvertTo-Json -Depth 4 | Set-Content "$output/sources.json" -Encoding utf8
& $Node "$PSScriptRoot/render_copper_images.cjs" $output $Sharp
if ($LASTEXITCODE -ne 0) { throw 'Image rendering failed' }
& $Node "$PSScriptRoot/render_router_images.cjs" $PSScriptRoot $Sharp
if ($LASTEXITCODE -ne 0) { throw 'Router image rendering failed' }
$hashes = [ordered]@{}
Get-ChildItem -LiteralPath $output -File | Where-Object Name -ne 'file-sha256.json' | Sort-Object Name | ForEach-Object {
    $hashes[$_.Name] = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
}
$hashes | ConvertTo-Json -Depth 3 | Set-Content "$output/file-sha256.json" -Encoding utf8
Compress-Archive -Path $output,"$PSScriptRoot/router-images" -DestinationPath "$PSScriptRoot/Copper-layer-images.zip" -Force
