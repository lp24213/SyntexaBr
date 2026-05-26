; SYNTEXA NSIS CUSTOM INSTALLER SCRIPT V45.1
; Installer nativo que não abre com WinRAR

!macro customInstall
  ; Cria atalho na área de trabalho
  CreateShortCut "$DESKTOP\Syntexa AI.lnk" "$INSTDIR\${APP_EXECUTABLE_FILENAME}.exe"
!macroend

!macro customUnInstall
  ; Remove atalho
  Delete "$DESKTOP\Syntexa AI.lnk"
!macroend
