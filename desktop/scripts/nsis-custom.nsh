; SYNTEXA NSIS CUSTOM INSTALLER SCRIPT V45
; Extensões do instalador NSIS para Windows Enterprise

!macro customInit
  ; Verifica se já existe instalação anterior e remove corretamente
  ReadRegStr $0 HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_GUID}" "UninstallString"
  StrCmp $0 "" done
  MessageBox MB_OKCANCEL|MB_ICONEXCLAMATION "Uma versão anterior do Syntexa AI foi detectada.$\nDeseja removê-la antes de continuar?" IDOK uninstall IDCANCEL done
uninstall:
  ExecWait '$0 /S'
done:
!macroend

!macro customInstall
  ; Cria atalho na área de trabalho para todos os usuários (se admin)
  SetShellVarContext all
  CreateShortCut "$DESKTOP\Syntexa AI.lnk" "$INSTDIR\${APP_EXECUTABLE_FILENAME}.exe" "" "$INSTDIR\${APP_EXECUTABLE_FILENAME}.exe" 0

  ; Associa extensões de arquivo (opcional)
  WriteRegStr HKCU "Software\Classes\.syntexa" "" "SyntexaAI.Document"
  WriteRegStr HKCU "Software\Classes\SyntexaAI.Document" "" "Syntexa AI Document"
  WriteRegStr HKCU "Software\Classes\SyntexaAI.Document\shell\open\command" "" '"$INSTDIR\${APP_EXECUTABLE_FILENAME}.exe" "%1"'
!macroend

!macro customUnInstall
  ; Remove atalhos
  Delete "$DESKTOP\Syntexa AI.lnk"
  Delete "$SMPROGRAMS\Syntexa AI.lnk"

  ; Remove associações
  DeleteRegKey HKCU "Software\Classes\.syntexa"
  DeleteRegKey HKCU "Software\Classes\SyntexaAI.Document"
!macroend
