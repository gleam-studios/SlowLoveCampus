# Native Windows bootstrap: no preinstalled Python is required.
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$toolDir = $PSScriptRoot
$nativeArchitecture = $env:PROCESSOR_ARCHITECTURE
if ($env:PROCESSOR_ARCHITEW6432) { $nativeArchitecture = $env:PROCESSOR_ARCHITEW6432 }
if ($nativeArchitecture -ne 'AMD64') { throw 'Only Windows x64 is supported.' }
$manifest = Get-Content -LiteralPath (Join-Path $toolDir '部署锁定.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$platform = $manifest.platforms.'windows-x64'
$pythonRoot = Join-Path $toolDir $platform.python.directory
$pythonExe = Join-Path $toolDir $platform.python.executable
if (Test-Path -LiteralPath $pythonExe) { exit 0 }
if (Test-Path -LiteralPath $pythonRoot) { throw 'Incomplete existing Python directory; preserved. Check it before retrying.' }
$cache = Join-Path $toolDir '.cache/downloads'
New-Item -ItemType Directory -Force -Path $cache | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $toolDir 'Python') | Out-Null
$lockPath = Join-Path $toolDir '.cache/python-windows-x64.lock'
$lock = [IO.File]::Open($lockPath, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::None)
$stage = Join-Path $toolDir ('Python/.install-' + [Guid]::NewGuid().ToString('N'))
function Get-PinnedFile($url, $sha, $extension) {
    $destination = Join-Path $cache ($sha + $extension)
    if ((Test-Path -LiteralPath $destination) -and ((Get-FileHash -LiteralPath $destination -Algorithm SHA256).Hash.ToLowerInvariant() -eq $sha)) { return $destination }
    $partial = $destination + '.part'
    if (!(Test-Path -LiteralPath $partial) -or ((Get-FileHash -LiteralPath $partial -Algorithm SHA256).Hash.ToLowerInvariant() -ne $sha)) {
        [Console]::Error.WriteLine('Downloading pinned project runtime...')
        & curl.exe --fail --location --show-error --silent --retry 2 --connect-timeout 30 --continue-at - --output $partial $url
        if ($LASTEXITCODE -in @(22,33,36)) {
            & curl.exe --fail --location --show-error --silent --retry 2 --connect-timeout 30 --output $partial $url
        }
        if ($LASTEXITCODE -ne 0) { throw 'Runtime download interrupted. Run the entry again to resume.' }
    }
    if ((Get-FileHash -LiteralPath $partial -Algorithm SHA256).Hash.ToLowerInvariant() -ne $sha) {
        Remove-Item -LiteralPath $partial -Force
        throw 'Runtime SHA-256 mismatch; corrupt partial removed.'
    }
    Move-Item -LiteralPath $partial -Destination $destination -Force
    return $destination
}
try {
    $archive = Get-PinnedFile $platform.python.url $platform.python.sha256 '.tar.gz'
    New-Item -ItemType Directory -Path $stage | Out-Null
    & tar.exe -xzf $archive --strip-components=1 -C $stage
    if ($LASTEXITCODE -ne 0) { throw 'Python archive extraction failed.' }
    if (!(Test-Path -LiteralPath (Join-Path $stage 'python.exe'))) { throw 'Python archive lacks the expected executable.' }
    $runtimeWheel = Get-PinnedFile $platform.msvc.url $platform.msvc.sha256 '.whl'
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $zip = [IO.Compression.ZipFile]::OpenRead($runtimeWheel)
    try {
        foreach ($item in $platform.msvc.files) {
            $entry = $zip.Entries | Where-Object { $_.Name -eq $item.filename } | Select-Object -First 1
            if (!$entry) { throw 'MSVC archive lacks a required DLL.' }
            $target = Join-Path $stage $item.filename
            [IO.Compression.ZipFileExtensions]::ExtractToFile($entry, $target, $true)
            if ((Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLowerInvariant() -ne $item.sha256) { throw 'MSVC DLL SHA-256 mismatch.' }
        }
        $license = $zip.Entries | Where-Object { $_.Name -eq 'LICENSE' } | Select-Object -First 1
        if ($license) {
            New-Item -ItemType Directory -Force -Path (Join-Path $stage 'licenses-msvc') | Out-Null
            [IO.Compression.ZipFileExtensions]::ExtractToFile($license, (Join-Path $stage 'licenses-msvc/LICENSE'), $true)
        }
    } finally { $zip.Dispose() }
    Move-Item -LiteralPath $stage -Destination $pythonRoot
} finally {
    if (Test-Path -LiteralPath $stage) { Remove-Item -LiteralPath $stage -Recurse -Force }
    $lock.Dispose()
    Remove-Item -LiteralPath $lockPath -Force
}
