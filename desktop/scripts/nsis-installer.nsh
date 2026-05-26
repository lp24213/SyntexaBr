; NSIS Custom Installer Script - Cria instalador real não self-extracting
; Como Cursor/Claude/VSCode - abre wizard de instalação

!macro customInstall
  ; Instalação personalizada
  SetShellVarContext all
  CreateShortCut "$DESKTOP\Syntexa AI.lnk" "$INSTDIR\${APP_EXECUTABLE_FILENAME}.exe"
  
  ; Registra aplicação no Windows
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_GUID}" "DisplayName" "Syntexa AI"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_GUID}" "UninstallString" "$INSTDIR\Uninstall ${APP_EXECUTABLE_FILENAME}.exe"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_GUID}" "DisplayIcon" "$INSTDIR\${APP_EXECUTABLE_FILENAME}.exe"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_GUID}" "Publisher" "SyntexaBR"
!macroend

!macro customUnInstall
  ; Remove atalhos e registros
  Delete "$DESKTOP\Syntexa AI.lnk"
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_GUID}"
!macroend

; Configurações para evitar self-extracting behavior
!pragma warning disable
SetCompressor lzma
CRCCheck on
