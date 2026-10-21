#define AppVersion "0.5.0"
[Setup]
AppId={{C07E1123-2DDD-46AE-A297-5B80F1270890}
AppName=Rodada Impressoras (piloto não assinado)
AppVersion={#AppVersion}
AppPublisher=Rodada
DefaultDirName={autopf}\Rodada\Impressoras
DefaultGroupName=Rodada
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0.22000
PrivilegesRequired=admin
OutputDir=..\..\..\dist
OutputBaseFilename=rodada-impressoras-{#AppVersion}-unsigned-pilot
Compression=lzma2
SolidCompression=yes
UninstallDisplayIcon={app}\rodada-impressoras.exe
CloseApplications=no
RestartApplications=no
[Files]
Source: "..\..\..\dist\rodada-impressoras\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
[Icons]
Name: "{group}\Rodada Impressoras"; Filename: "{app}\rodada-impressoras.exe"; Parameters: "status"
[Run]
Filename: "{app}\rodada-impressoras.exe"; Parameters: "status"; Description: "Mostrar código e estado do computador"; Flags: postinstall nowait skipifsilent runasoriginaluser
[UninstallRun]
Filename: "{app}\rodada-impressoras.exe"; Parameters: "quiesce"; Flags: runhidden waituntilterminated; RunOnceId: StopAgent
Filename: "{app}\rodada-impressoras.exe"; Parameters: "service remove"; Flags: runhidden waituntilterminated; RunOnceId: RemoveAgent
[Code]
procedure RunChecked(Args: String);
var Code: Integer;
begin
  if not Exec(ExpandConstant('{app}\rodada-impressoras.exe'), Args, '', SW_HIDE, ewWaitUntilTerminated, Code) then
    RaiseException('Não foi possível executar a configuração do Rodada Impressoras.');
  if Code <> 0 then
    RaiseException('Configuração não concluída. Solicite suporte antes de imprimir. Código: ' + IntToStr(Code));
end;
function PrepareToInstall(var NeedsRestart: Boolean): String;
var Code: Integer;
begin
  Result := '';
  if FileExists(ExpandConstant('{app}\rodada-impressoras.exe')) then begin
    if not Exec(ExpandConstant('{app}\rodada-impressoras.exe'), 'quiesce', '', SW_HIDE, ewWaitUntilTerminated, Code) then
      Result := 'Não foi possível parar o serviço. Solicite suporte.'
    else if Code <> 0 then
      Result := 'O serviço ainda está ocupado. Confira a impressora e tente novamente.';
  end;
end;
procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then begin
    RunChecked('install-service');
    RunChecked('configure --api-origin https://api.rodada.bar');
    RunChecked('service start');
  end;
end;
