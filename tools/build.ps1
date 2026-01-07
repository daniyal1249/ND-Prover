$ErrorActionPreference = "Stop"


function Resolve-Executable($name, $candidatePaths) {
  $cmd = Get-Command $name -ErrorAction SilentlyContinue
  if ($cmd) {
    return $cmd.Source
  }

  foreach ($p in $candidatePaths) {
    if ($p -and (Test-Path $p)) {
      return $p
    }
  }

  return $null
}


$miktexBinCandidates = @(
  (Join-Path $env:ProgramFiles "MiKTeX\miktex\bin\x64"),
  (Join-Path $env:ProgramFiles "MiKTeX\miktex\bin"),
  (Join-Path ${env:ProgramFiles(x86)} "MiKTeX\miktex\bin\x64"),
  (Join-Path $env:LOCALAPPDATA "Programs\MiKTeX\miktex\bin\x64"),
  (Join-Path $env:APPDATA "MiKTeX\miktex\bin\x64")
)

$pdflatexExe = Resolve-Executable "miktex-pdflatex" @(
  $miktexBinCandidates | ForEach-Object { Join-Path $_ "miktex-pdflatex.exe" }
)
if (-not $pdflatexExe) {
  $pdflatexExe = Resolve-Executable "pdflatex" @(
    $miktexBinCandidates | ForEach-Object { Join-Path $_ "pdflatex.exe" }
  )
}

$pdf2svgExe = Resolve-Executable "pdf2svg" @(
  "C:\ProgramData\chocolatey\bin\pdf2svg.exe"
)

if (-not $pdflatexExe) {
  throw "Missing required tool: 'pdflatex'. Ensure MiKTeX/TeX Live is installed and pdflatex is on PATH."
}
if (-not $pdf2svgExe) {
  throw "Missing required tool: 'pdf2svg'. Ensure it is installed and on PATH."
}


$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$toolsDir = (Resolve-Path $PSScriptRoot).Path
$texfDir = Join-Path $toolsDir "texf"
$template = Join-Path $texfDir "rule-template.tex"
$buildDir = Join-Path $toolsDir ".build"
$outDir = Join-Path $repoRoot "site\static\rules"

New-Item -ItemType Directory -Force -Path $buildDir | Out-Null
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

# Clean outputs so removed/renamed rules don't leave stale SVGs behind.
Get-ChildItem -Path $outDir -Filter "*.svg" -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue
# Also clean LaTeX byproducts from previous runs.
Get-ChildItem -Path $buildDir -File -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue

# Ensure pdflatex can resolve the local style files (forallxyyc.sty, latexml.sty, etc.)
$texStylesDir = Join-Path $toolsDir "tex-styles"
if (-not (Test-Path $texStylesDir)) {
  throw "Expected TeX styles directory not found: $texStylesDir"
}

$previousTexInputs = $env:TEXINPUTS
$env:TEXINPUTS = "$texStylesDir;$previousTexInputs"

try {
  $templateText = Get-Content -Path $template -Raw
  if (-not $templateText.Contains('$body$')) {
    throw "Template does not contain expected `$body$ placeholder: $template"
  }

  $texfFiles = Get-ChildItem -Path $texfDir -Filter "*.texf" | Sort-Object Name
  foreach ($texf in $texfFiles) {
    $base = [System.IO.Path]::GetFileNameWithoutExtension($texf.Name)
    $texOut = Join-Path $buildDir "$base.tex"
    $pdfOut = Join-Path $buildDir "$base.pdf"
    $svgOut = Join-Path $outDir "$base.svg"

    Write-Host "Generating $base.svg"

    # Inline the fragment into the template (avoids pandoc template parsing conflicts with $...$ math).
    $body = Get-Content -Path $texf.FullName -Raw
    $tex = $templateText.Replace('$body$', $body)
    Set-Content -Path $texOut -Value $tex -Encoding UTF8

    & $pdflatexExe -interaction=nonstopmode -halt-on-error -file-line-error -output-directory $buildDir $texOut | Out-Null

    if (-not (Test-Path $pdfOut)) {
      throw "pdflatex did not produce expected PDF: $pdfOut"
    }

    & $pdf2svgExe $pdfOut $svgOut

    # Clean per-rule build artifacts.
    Remove-Item -Force -ErrorAction SilentlyContinue `
      $texOut, $pdfOut, `
      (Join-Path $buildDir "$base.aux"), `
      (Join-Path $buildDir "$base.log"), `
      (Join-Path $buildDir "$base.out"), `
      (Join-Path $buildDir "$base.synctex.gz"), `
      (Join-Path $buildDir "$base.fls"), `
      (Join-Path $buildDir "$base.fdb_latexmk")
  }
}
finally {
  $env:TEXINPUTS = $previousTexInputs
}

Write-Host "Done. SVGs are in: $outDir"
