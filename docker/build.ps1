param([switch]$Native, [string]$Tag = 'local', [string]$GuicedeeVersion,
      [string]$MavenRepository, [ValidateSet('standard','wrapped')][string]$QuarkusDependencies = 'standard')
$ErrorActionPreference = 'Stop'
$benchmarkRoot = Split-Path $PSScriptRoot -Parent
$buildOptions = @('--docker','--runtime','both','--tag',$Tag,'--quarkus-dependencies',$QuarkusDependencies)
if ($Native) { $buildOptions += '--native' }
if ($GuicedeeVersion) { $buildOptions += @('--guicedee-version',$GuicedeeVersion) }
if ($MavenRepository) { $buildOptions += @('--maven-repository',$MavenRepository) }
& python (Join-Path $benchmarkRoot 'tools/build.py') @buildOptions
if ($LASTEXITCODE) { throw 'Benchmark image build failed' }
