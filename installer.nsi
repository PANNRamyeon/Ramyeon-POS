; NSIS Installer Script for PANN POS System
; Alternative to Inno Setup
; Requires NSIS: https://nsis.sourceforge.io/Download

!define APP_NAME "PANN POS System"
!define APP_VERSION "1.0.0"
!define APP_PUBLISHER "PANN Systems"
!define APP_URL "https://www.pann.com"
!define APP_EXECUTABLE "PANN_POS_System.exe"
!define APP_INSTALL_DIR "$PROGRAMFILES64\PANN\POS_System"

!include "MUI2.nsh"

!define MUI_ABORTWARNING

; Installer pages
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "LICENSE"
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

; Uninstaller pages
!insertmacro MUI_UNPAGE_WELCOME
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

; Languages
!insertmacro MUI_LANGUAGE "English"

Name "${APP_NAME}"
OutFile "installer_output\PANN_POS_System_Setup.exe"
InstallDir "${APP_INSTALL_DIR}"
RequestExecutionLevel admin

; Version info
VIProductVersion "${APP_VERSION}.0"
VIAddVersionKey "ProductName" "${APP_NAME}"
VIAddVersionKey "ProductVersion" "${APP_VERSION}"
VIAddVersionKey "CompanyName" "${APP_PUBLISHER}"
VIAddVersionKey "FileVersion" "${APP_VERSION}"

Section "Application Files" SecMain
    SectionIn RO
    
    ; Check for MongoDB
    Call CheckMongoDB
    
    ; Install files
    SetOutPath "$INSTDIR"
    File "backend\dist\${APP_EXECUTABLE}"
    
    ; Create directories
    CreateDirectory "$INSTDIR"
    
    ; Create shortcuts
    CreateShortcut "$DESKTOP\${APP_NAME}.lnk" "$INSTDIR\${APP_EXECUTABLE}"
    CreateShortcut "$SMPROGRAMS\${APP_NAME}\${APP_NAME}.lnk" "$INSTDIR\${APP_EXECUTABLE}"
    CreateShortcut "$SMPROGRAMS\${APP_NAME}\Uninstall.lnk" "$INSTDIR\Uninstall.exe"
    
    ; Write uninstaller
    WriteUninstaller "$INSTDIR\Uninstall.exe"
    
    ; Registry entries
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "DisplayName" "${APP_NAME}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "UninstallString" "$INSTDIR\Uninstall.exe"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "Publisher" "${APP_PUBLISHER}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "DisplayVersion" "${APP_VERSION}"
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "NoModify" 1
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "NoRepair" 1
    
SectionEnd

Section "Desktop Shortcut" SecDesktop
    ; Already created in main section
SectionEnd

Section "Start Menu Shortcut" SecStartMenu
    ; Already created in main section
SectionEnd

Section -Uninstall
    ; Remove files
    Delete "$INSTDIR\${APP_EXECUTABLE}"
    Delete "$INSTDIR\Uninstall.exe"
    
    ; Remove shortcuts
    Delete "$DESKTOP\${APP_NAME}.lnk"
    RMDir /r "$SMPROGRAMS\${APP_NAME}"
    
    ; Remove registry entries
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}"
    
    ; Remove directory
    RMDir "$INSTDIR"
SectionEnd

Function CheckMongoDB
    ; Check common MongoDB paths
    IfFileExists "C:\Program Files\MongoDB\Server\8.0\bin\mongod.exe" found
    IfFileExists "C:\Program Files\MongoDB\Server\7.0\bin\mongod.exe" found
    IfFileExists "C:\Program Files\MongoDB\Server\6.0\bin\mongod.exe" found
    IfFileExists "C:\Program Files\MongoDB\Server\5.0\bin\mongod.exe" found
    
    ; MongoDB not found
    MessageBox MB_YESNO|MB_ICONQUESTION \
        "MongoDB Community Edition was not detected.$\n$\n" \
        "PANN POS System requires MongoDB to function.$\n$\n" \
        "Please install MongoDB Community Edition before running the application.$\n$\n" \
        "Download: https://www.mongodb.com/try/download/community$\n$\n" \
        "Continue installation anyway?" \
        IDYES found
    Abort
    
    found:
FunctionEnd

; Component descriptions
LangString DESC_SecMain ${LANG_ENGLISH} "Core application files"
LangString DESC_SecDesktop ${LANG_ENGLISH} "Create desktop shortcut"
LangString DESC_SecStartMenu ${LANG_ENGLISH} "Create start menu shortcut"

!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
!insertmacro MUI_DESCRIPTION_TEXT ${SecMain} $(DESC_SecMain)
!insertmacro MUI_DESCRIPTION_TEXT ${SecDesktop} $(DESC_SecDesktop)
!insertmacro MUI_DESCRIPTION_TEXT ${SecStartMenu} $(DESC_SecStartMenu)
!insertmacro MUI_FUNCTION_DESCRIPTION_END


