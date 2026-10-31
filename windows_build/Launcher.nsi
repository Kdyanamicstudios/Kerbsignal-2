Unicode true
Name "KerbSignal"
OutFile "LaunchRaceEngineer.exe"
RequestExecutionLevel user
SilentInstall silent
AutoCloseWindow true
SetCompressor lzma
Icon "raceengineer.ico"
VIProductVersion "0.15.0.0"
VIAddVersionKey "ProductName" "KerbSignal"
VIAddVersionKey "FileDescription" "KerbSignal desktop launcher"
VIAddVersionKey "FileVersion" "0.15.0"
VIAddVersionKey "LegalCopyright" "KerbSignal contributors - GPL-3.0"
Section
  ReadINIStr $0 "$EXEDIR\current.ini" "App" "Version"
  StrCmp $0 "" error
  SetOutPath "$EXEDIR\versions\$0"
  ExecWait '"$EXEDIR\versions\$0\pythonw.exe" -I "$EXEDIR\versions\$0\launch.pyw"' $1
  IfErrors error
  SetErrorLevel $1
  Quit
error:
  MessageBox MB_OK|MB_ICONSTOP "KerbSignal could not start. Run the installer again to repair the application. Your lap history is saved separately."
SectionEnd
