param(
 [Parameter(Mandatory=$true)][string]$PgBin,
 [Parameter(Mandatory=$true)][string]$Python,
 [Parameter(Mandatory=$true)][string]$Node,
 [Parameter(Mandatory=$true)][string]$StateDirectory
)
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$state=[IO.Path]::GetFullPath($StateDirectory)
New-Item -ItemType Directory -Force $state | Out-Null
foreach($port in @(55459,18764,3119)) {
 if(Get-NetTCPConnection -State Listen -LocalPort $port -ErrorAction SilentlyContinue){throw "Port $port already occupied; inspect existing demo instead of replacing it."}
}
$env:POSTGRES_DB='rodada_demo'; $env:POSTGRES_USER='rodada'; if(!$env:POSTGRES_PASSWORD){throw 'Set POSTGRES_PASSWORD locally before starting the test stack'}
$env:PGPASSWORD=$env:POSTGRES_PASSWORD; $env:POSTGRES_HOST='127.0.0.1'; $env:POSTGRES_PORT='55459'
$env:DJANGO_SETTINGS_MODULE='rodada_api.settings'; $env:DJANGO_ALLOWED_HOSTS='localhost,127.0.0.1,10.0.2.2'
$env:RODADA_PAYMENT_SIMULATION='false'
$data=Join-Path $state 'pgdata'
if(!(Test-Path (Join-Path $data 'PG_VERSION'))){
 $pw=Join-Path $state 'init-password.txt'
 [IO.File]::WriteAllText($pw,$env:POSTGRES_PASSWORD)
 try { & (Join-Path $PgBin 'initdb.exe') -D $data -U rodada --encoding=UTF8 --locale=C --auth=scram-sha-256 --pwfile=$pw
 if($LASTEXITCODE -ne 0){throw 'initdb failed'} } finally {Remove-Item -LiteralPath $pw -ErrorAction SilentlyContinue}
}
& (Join-Path $PgBin 'pg_ctl.exe') -D $data -l (Join-Path $state 'postgres.log') -o '-h 127.0.0.1 -p 55459' -w start
if($LASTEXITCODE -ne 0){throw 'PostgreSQL start failed'}
$dbExists=& (Join-Path $PgBin 'psql.exe') -U rodada -h 127.0.0.1 -p 55459 -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='rodada_demo'"
if($LASTEXITCODE -ne 0){throw 'Database probe failed'}
if($dbExists -ne '1'){ & (Join-Path $PgBin 'createdb.exe') -U rodada -h 127.0.0.1 -p 55459 rodada_demo; if($LASTEXITCODE -ne 0){throw 'createdb failed'} }
Push-Location (Join-Path $root 'apps/api')
try {
 foreach($command in @(@('migrate','--noinput'),@('seed_demo'),@('seed_release_demo'),@('check'),@('makemigrations','--check','--dry-run'))){
  & $Python manage.py @command; if($LASTEXITCODE -ne 0){throw "Django gate failed: $command"}
 }
 $api=Start-Process -FilePath $Python -ArgumentList '-m uvicorn rodada_api.asgi:application --host 127.0.0.1 --port 18764' -WorkingDirectory (Get-Location).Path -WindowStyle Hidden -RedirectStandardOutput (Join-Path $state 'api.out.log') -RedirectStandardError (Join-Path $state 'api.err.log') -PassThru
 $dispatcher=Start-Process -FilePath $Python -ArgumentList 'manage.py dispatch_realtime' -WorkingDirectory (Get-Location).Path -WindowStyle Hidden -RedirectStandardOutput (Join-Path $state 'dispatcher.out.log') -RedirectStandardError (Join-Path $state 'dispatcher.err.log') -PassThru
} finally {Pop-Location}
$env:RODADA_API_BASE_URL='http://127.0.0.1:18764'
$web=Start-Process -FilePath $Node -ArgumentList 'node_modules/next/dist/bin/next start --hostname 127.0.0.1 --port 3119' -WorkingDirectory (Join-Path $root 'apps/web') -WindowStyle Hidden -RedirectStandardOutput (Join-Path $state 'web.out.log') -RedirectStandardError (Join-Path $state 'web.err.log') -PassThru
@{api=$api.Id;dispatcher=$dispatcher.Id;web=$web.Id;root=$root;data=$data;ports=@(55459,18764,3119)} | ConvertTo-Json | Set-Content (Join-Path $state 'runtime.json')
$ready=$false
for($attempt=0;$attempt -lt 30;$attempt++){
 try{Invoke-WebRequest 'http://127.0.0.1:18764/ready/' -UseBasicParsing -TimeoutSec 2 | Out-Null;Invoke-WebRequest 'http://127.0.0.1:3119/staff' -UseBasicParsing -TimeoutSec 2 | Out-Null;$ready=$true;break}catch{Start-Sleep -Seconds 1}
}
if(!$ready){throw "Demo not ready; inspect logs and runtime.json in $state. No data deleted."}
Write-Output 'Demo ready: http://127.0.0.1:3119/staff (test data and MANUAL_TEST money only).'
