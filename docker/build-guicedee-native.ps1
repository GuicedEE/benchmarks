param([string]$Tag = 'local', [string]$TraceDirectory, [switch]$AuditNative, [switch]$IncludeDesktop,
      [string]$GuicedeeVersion, [string]$MavenRepository)
$ErrorActionPreference = 'Stop'
$benchmarkRoot = Split-Path $PSScriptRoot -Parent
$buildOptions = @('--docker','--framework','guicedee','--runtime','native','--tag',$Tag)
if ($GuicedeeVersion) { $buildOptions += @('--guicedee-version',$GuicedeeVersion) }
if ($MavenRepository) { $buildOptions += @('--maven-repository',$MavenRepository) }
if ($TraceDirectory) { $buildOptions += @('--trace-directory',$TraceDirectory) }
if ($AuditNative) { $buildOptions += '--audit-native' }
if ($IncludeDesktop) { $buildOptions += '--include-desktop' }
& python (Join-Path $benchmarkRoot 'tools/build.py') @buildOptions
if ($LASTEXITCODE) { throw 'GuicedEE native image build failed' }
