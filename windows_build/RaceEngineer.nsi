Unicode true
Name "KerbSignal"
OutFile "../KerbSignal_0.15.exe"
InstallDir "$LOCALAPPDATA\Programs\RaceEngineer"
RequestExecutionLevel user
SilentInstall silent
AutoCloseWindow true
SetCompressor zlib
Icon "raceengineer.ico"
VIProductVersion "0.15.0.0"
VIAddVersionKey "ProductName" "KerbSignal"
VIAddVersionKey "FileDescription" "KerbSignal - install and launch"
VIAddVersionKey "FileVersion" "0.15.0"
VIAddVersionKey "ProductVersion" "0.15.0"
VIAddVersionKey "LegalCopyright" "KerbSignal contributors - GPL-3.0"
!include "x64.nsh"
!include "FileFunc.nsh"
Var VerifyInstall
Section
  StrCpy $VerifyInstall 0
  ${GetParameters} $R0
  ClearErrors
  ${GetOptions} $R0 "/VERIFY" $R1
  ${IfNot} ${Errors}
    StrCpy $VerifyInstall 1
  ${EndIf}
  ${IfNot} ${RunningX64}
    MessageBox MB_OK|MB_ICONSTOP "KerbSignal requires 64-bit Windows 10 or Windows 11."
    SetErrorLevel 1
    Quit
  ${EndIf}
check_running:
  StrCmp $VerifyInstall 1 not_running
  System::Call 'kernel32::OpenMutexW(i 0x100000, i 0, w "Local\RaceEngineerApp") p .r0'
  StrCmp $0 0 not_running
  System::Call 'kernel32::CloseHandle(p r0)'
  MessageBox MB_RETRYCANCEL|MB_ICONINFORMATION "Close KerbSignal / Race Engineer before updating, then choose Retry. Your history and settings will be kept." IDRETRY check_running
  SetErrorLevel 1
  Quit
not_running:
  # Versions are separate. An interrupted install cannot replace the previous runtime.
  SetOutPath "$INSTDIR\versions\0.15.0"
  ClearErrors
  File /r "payload/*"
  IfErrors install_error
  SetOutPath "$INSTDIR"
  File "LaunchRaceEngineer.exe"
  IfErrors install_error
  # Publish the new version pointer only after all payload files were extracted.
  WriteINIStr "$INSTDIR\current.next.ini" "App" "Version" "0.15.0"
  IfErrors install_error
  System::Call 'kernel32::MoveFileExW(w "$INSTDIR\current.next.ini", w "$INSTDIR\current.ini", i 9) i .r0'
  StrCmp $0 0 install_error
  # Verification installs extract to an explicitly supplied workspace directory.
  # They never create user shortcuts or start the app.
  StrCmp $VerifyInstall 1 verified
  CreateDirectory "$SMPROGRAMS\KerbSignal"
  CreateShortcut "$SMPROGRAMS\KerbSignal\KerbSignal.lnk" "$INSTDIR\LaunchRaceEngineer.exe"
  CreateShortcut "$DESKTOP\KerbSignal.lnk" "$INSTDIR\LaunchRaceEngineer.exe"
  Delete "$DESKTOP\Apex Relay.lnk"
  Delete "$SMPROGRAMS\Apex Relay\Apex Relay.lnk"
  Delete "$DESKTOP\Race Engineer.lnk"
  Delete "$SMPROGRAMS\Race Engineer\Race Engineer.lnk"
  Exec '"$INSTDIR\LaunchRaceEngineer.exe"'
verified:
  Quit
install_error:
  MessageBox MB_OK|MB_ICONSTOP "KerbSignal could not finish installing. Close the app and run the installer again. Existing history and settings were preserved."
  SetErrorLevel 1
SectionEnd
