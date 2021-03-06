;
; RCS-ID: $Id: agtk.iss,v 1.136 2007-09-28 17:16:45 turam Exp $
;

; Set externally
; SourceDir : The location of the AccessGrid Build Tree
; BuildDir : The location of the prebuilt distribution
; AppVersion : what version are you packaging
; DirName : name of program files directory
; VersionInformation: a string indicating the more version information
; PythonSubVersion: a string indicating the version of python (2.2 or 2.3)

;#define SourceDir "\software\AccessGrid\build"
;#define BuildDir "\software\AccessGrid\build\dist-20040908_130651"
;#define AppVersion "3.1"
;#define VersionInformation "Test Final"
;#define PythonSubVersion "4"

#ifndef SourceDir
#error "SourceDir must be defined to build a package."
#endif

#ifndef BuildDir
#error "BuildDir must be defined to build a package."
#endif

#ifndef AppVersion
#error "AppVersion must be defined to build a package."
#endif

#ifndef VersionInformation
#error "VersionInformation must be defined to build a package."
#endif

#ifndef PythonSubVersion
#error "PythonSubVersion must be defined to build a package."
#endif

; used internally
#define AppName "Access Grid Toolkit"
#define AppNameShort "AGTk"
#define DirName "3"

[Setup]
AppVerName={#AppVersion}-{#VersionInformation}
AppVersion={#AppVersion}
SourceDir={#BuildDir}
OutputDir={#SourceDir}
OutputBaseFilename={#AppNameShort}-{#AppVersion}-Bundle-{#VersionInformation}-Py-2.{#PythonSubVersion}

AppName={#AppName}
AppCopyright=Copyright � 2003-2008 Argonne National Laboratory / University of Chicago. All Rights Reserved.
AppPublisher=Futures Laboratory / Argonne National Laboratory
AppPublisherURL=http://www.mcs.anl.gov/fl
AppSupportURL=http://bugzilla.mcs.anl.gov/accessgrid
AppUpdatesURL=http://www.mcs.anl.gov/fl/research/accessgrid
AppID=2CD98D2E-F3D2-438E-91F7-D74860A70953
MinVersion=0,5.0.2195
LicenseFile=COPYING.txt
DisableDirPage=false
DefaultGroupName={#AppName} {#DirName}
DefaultDirName={pf}\{#AppNameShort}-{#DirName}
UsePreviousAppDir=false
UserInfoPage=false
WindowVisible=false

UninstallDisplayName={#AppNameShort} {#AppVersion}
DisableStartupPrompt=true
WindowResizable=false
AlwaysShowComponentsList=false
ShowComponentSizes=true
FlatComponentsList=true
AllowNoIcons=false
DirExistsWarning=auto
DisableFinishedPage=false
DisableReadyMemo=true
UsePreviousUserInfo=false
WindowStartMaximized=false
WizardImageFile=compiler:wizmodernimage.bmp
WizardSmallImageFile=compiler:wizmodernsmallimage.bmp
UninstallFilesDir={app}\uninstall
InfoBeforeFile=Install.WINDOWS
ShowTasksTreeLines=true
PrivilegesRequired=admin
UninstallDisplayIcon={app}\install\ag.ico
DisableReadyPage=true
UsePreviousSetupType=true
UsePreviousTasks=false
UsePreviousGroup=true
ShowLanguageDialog=yes
Compression=lzma


[Files]
; The Python Modules
Source: {#SourceDir}\python-2.4.4c1.msi; DestDir: {tmp}; Check: PythonCheck; Components: Python; AfterInstall: AfterPythonInstall
Source: {#SourceDir}\wxPython2.8-win32-unicode-2.8.3.0-py24.exe; DestDir: {tmp}; Components: wxPython; AfterInstall: AfterWxPythonInstall
Source: Lib\site-packages\agversion.py; DestDir: {reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\Lib\site-packages; Flags: overwritereadonly restartreplace; Components: AccessGrid
Source: Lib\site-packages\_xmlplus\*.*; DestDir: {reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\Lib\site-packages\_xmlplus; Flags: recursesubdirs overwritereadonly restartreplace; Components: AccessGrid
Source: Lib\site-packages\AccessGrid3\*.*; DestDir: {reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\Lib\site-packages\AccessGrid3; Flags: recursesubdirs overwritereadonly restartreplace; Components: AccessGrid
Source: Lib\site-packages\feedparser.py; DestDir: {reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\Lib\site-packages; Flags: recursesubdirs overwritereadonly restartreplace; Components: AccessGrid
Source: Lib\site-packages\ZSI\*.*; DestDir: {reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\Lib\site-packages\ZSI; Flags: recursesubdirs overwritereadonly restartreplace; Components: AccessGrid
Source: Lib\site-packages\zope\*.*; DestDir: {reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\Lib\site-packages\zope; Flags: recursesubdirs overwritereadonly restartreplace; Components: AccessGrid
Source: Lib\site-packages\M2Crypto\*.*; DestDir: {reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\Lib\site-packages\M2Crypto; Flags: recursesubdirs overwritereadonly restartreplace; Components: AccessGrid
Source: Lib\site-packages\twisted\*.*; DestDir: {reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\Lib\site-packages\twisted; Flags: recursesubdirs overwritereadonly restartreplace; Components: AccessGrid
Source: Lib\site-packages\bonjour\*.*; DestDir: {reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\Lib\site-packages\bonjour; Flags: recursesubdirs overwritereadonly restartreplace; Components: AccessGrid
Source: Lib\site-packages\common\*.*; DestDir: {reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\Lib\site-packages\common; Flags: recursesubdirs overwritereadonly restartreplace; Components: AccessGrid
Source: Lib\site-packages\elementtree\*.*; DestDir: {reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\Lib\site-packages\elementtree; Flags: recursesubdirs overwritereadonly restartreplace; Components: AccessGrid
Source: Lib\site-packages\gov\*.*; DestDir: {reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\Lib\site-packages\gov; Flags: recursesubdirs overwritereadonly restartreplace; Components: AccessGrid

; pywin32
Source: Lib\site-packages\isapi\*.*; DestDir: {reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\Lib\site-packages\isapi; Flags: recursesubdirs overwritereadonly restartreplace; Components: AccessGrid; Check: pyWin32Check
Source: Lib\site-packages\pythonwin\*.*; DestDir: {reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\Lib\site-packages\pythonwin; Flags: recursesubdirs overwritereadonly restartreplace; Components: AccessGrid; Check: pyWin32Check
Source: Lib\site-packages\pythoncom.py; DestDir: {reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\Lib\site-packages; Flags: recursesubdirs overwritereadonly restartreplace; Components: AccessGrid; Check: pyWin32Check
Source: Lib\site-packages\pywin32.pth; DestDir: {reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\Lib\site-packages; Flags: recursesubdirs overwritereadonly restartreplace; Components: AccessGrid; Check: pyWin32Check
Source: Lib\site-packages\pywin32.version.txt; DestDir: {reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\Lib\site-packages; Flags: recursesubdirs overwritereadonly restartreplace; Components: AccessGrid; Check: pyWin32Check
Source: Lib\site-packages\pywin32_system32\*.*; DestDir: {reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\Lib\site-packages\pywin32_system32; Flags: recursesubdirs overwritereadonly restartreplace; Components: AccessGrid; Check: pyWin32Check
Source: Lib\site-packages\win32\*.*; DestDir: {reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\Lib\site-packages\win32; Flags: recursesubdirs overwritereadonly restartreplace; Components: AccessGrid; Check: pyWin32Check
Source: Lib\site-packages\win32com\*.*; DestDir: {reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\Lib\site-packages\win32com; Flags: recursesubdirs overwritereadonly restartreplace; Components: AccessGrid; Check: pyWin32Check
Source: Lib\site-packages\win32comext\*.*; DestDir: {reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\Lib\site-packages\win32comext; Flags: recursesubdirs overwritereadonly restartreplace; Components: AccessGrid; Check: pyWin32Check


; Documentation
; Source: doc\Developer\*.*; DestDir: {app}\doc\Developer; Flags: recursesubdirs; Components: AccessGrid

; Certificates for trusted CA's
Source: config\CAcertificates\*.*; DestDir: {app}\config\CAcertificates; Components: AccessGrid

; General setup stuff
Source: COPYING.txt; DestDir: {app}; Components: AccessGrid
Source: README; DestDir: {app}; Flags: isreadme; DestName: README.txt; Components: AccessGrid

; Program Files
Source: bin\*.*; DestDir: {app}\bin; Components: AccessGrid
Source: bin\GoToVenue3.py; DestDir: {app}\bin; DestName: GoToVenue3.pyw; Components: AccessGrid

; Special short cuts to invoke without the python console

Source: bin\CertificateRequestTool3.py; DestDir: {app}\bin; DestName: CertificateRequestTool3.pyw; Components: AccessGrid
Source: bin\NodeManagement3.py; DestDir: {app}\bin; DestName: NodeManagement3.pyw; Components: AccessGrid
Source: bin\NodeSetupWizard3.py; DestDir: {app}\bin; DestName: NodeSetupWizard3.pyw; Components: AccessGrid

; Service packages
Source: NodeServices\*.zip; DestDir: {app}\NodeServices; Components: AccessGrid

; Shared Application packages
Source: SharedApplications\*.agpkg3; DestDir: {app}\SharedApplications; Components: AccessGrid

; Default node configuration
Source: config\nodeConfig\default; DestDir: {app}\config\nodeConfig; Components: AccessGrid

; System wide files, windows wierdness no doubt
Source: install\ag.ico; DestDir: {app}\install; Components: AccessGrid
Source: install\msvcr70.dll; DestDir: {win}\system32; Flags: uninsneveruninstall onlyifdoesntexist; Components: AccessGrid
Source: install\msvcp71.dll; DestDir: {win}\system32; Flags: uninsneveruninstall onlyifdoesntexist; Components: AccessGrid
Source: install\msvcr71.dll; DestDir: {win}\system32; Flags: uninsneveruninstall onlyifdoesntexist; Components: AccessGrid
Source: install\msvcr71d.dll; DestDir: {win}\system32; Flags: uninsneveruninstall onlyifdoesntexist; Components: AccessGrid
;Source: install\ssleay32.dll; DestDir: {win}\system32; Flags: uninsneveruninstall onlyifdoesntexist; Components: AccessGrid
;Source: install\libeay32.dll; DestDir: {win}\system32; Flags: uninsneveruninstall onlyifdoesntexist; Components: AccessGrid
Source: install\ssleay32.dll; DestDir: {reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\Lib\site-packages\M2Crypto; Components: AccessGrid
Source: install\libeay32.dll; DestDir: {reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\Lib\site-packages\M2Crypto; Components: AccessGrid

; end system files

[Components]
Name: AccessGrid; Description: The Access Grid
Name: Python; Description: Python Programming Language; ExtraDiskSpaceRequired: 100
Name: wxPython; Description: Python User Interface Library; ExtraDiskSpaceRequired: 100
Name: pyWin32; Description: Python Windows Library; ExtraDiskSpaceRequired: 100


[Icons]
Name: {group}\View README; Filename: {app}\README.txt; Flags: createonlyiffileexists; Comment: Read the ReadMe.
Name: {group}\Venue Client; Filename: {reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\pythonw.exe; Parameters: """{app}\bin\VenueClient3.py"""; IconFilename: {app}\install\ag.ico; WorkingDir: %APPDATA%\AccessGrid3; Comment: Run the venue client software.
Name: {group}\Venue Client (Debug Mode); IconFilename: {app}\install\ag.ico; Filename: {reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\python.exe; Parameters: """{app}\bin\VenueClient3.py"" -d"; WorkingDir: %APPDATA%\AccessGrid3; Comment: Run the venue client in debugging mode.
Name: {group}\Venue Management Tool; IconFilename: {app}\install\ag.ico; Filename: {reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\pythonw.exe; Parameters: """{app}\bin\VenueManagement3.py"""; WorkingDir: %APPDATA%\AccessGrid3; Comment: Manage venue servers.
Name: {group}\Request a Certificate; Filename: {reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\pythonw.exe; Parameters: """{app}\bin\CertificateRequestTool3.pyw"""; WorkingDir: %APPDATA%\AccessGrid3; IconFilename: {app}\install\ag.ico

Name: {group}\Configure\Node Setup Wizard; Filename: {reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\pythonw.exe; Parameters: """{app}\bin\NodeSetupWizard3.pyw"""; WorkingDir: %APPDATA%\AccessGrid3; IconFilename: {app}\install\ag.ico; Comment: Run the AG Node Configuration Wizard
Name: {group}\Configure\Node Management; Filename: {reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\pythonw.exe; Parameters: """{app}\bin\NodeManagement3.pyw"""; WorkingDir: %APPDATA%\AccessGrid3; IconFilename: {app}\install\ag.ico; Comment: Configure an AG node

Name: {group}\Services\Venue Server (Debug); IconFilename: {app}\install\ag.ico; Filename: {reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\python.exe; Parameters: """{app}\bin\VenueServer3.py"" --debug"; WorkingDir: %APPDATA%\AccessGrid3; Comment: Run the venue server software in debugging mode.
Name: {group}\Services\Venue Server; IconFilename: {app}\install\ag.ico; Filename: {reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\python.exe; Parameters: """{app}\bin\VenueServer3.py"" --debug"; WorkingDir: %APPDATA%\AccessGrid3; Comment: Run the venue server software in debugging mode.
Name: {group}\Services\Service Manager (Debug); IconFilename: {app}\install\ag.ico; Filename: {reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\python.exe; Parameters: """{app}\bin\AGServiceManager3.py"" --debug"; WorkingDir: %APPDATA%\AccessGrid3; Comment: Run the service manager software in debugging mode.
Name: {group}\Services\Service Manager; IconFilename: {app}\install\ag.ico; Filename: {reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\python.exe; Parameters: """{app}\bin\AGServiceManager3.py"" --debug"; WorkingDir: %APPDATA%\AccessGrid3; Comment: Run the venue service manager in debugging mode.
Name: {group}\Services\Node Service (Debug); IconFilename: {app}\install\ag.ico; Filename: {reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\python.exe; Parameters: """{app}\bin\AGServiceManager3.py"" -n --debug"; WorkingDir: %APPDATA%\AccessGrid3; Comment: Run the node service software in debugging mode.
Name: {group}\Services\Node Service; IconFilename: {app}\install\ag.ico; Filename: {reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\python.exe; Parameters: """{app}\bin\AGServiceManager3.py"" -n"; WorkingDir: %APPDATA%\AccessGrid3; Comment: Run the node service software in debugging mode.

Name: {group}\Documentation\View License; IconFilename: {app}\install\ag.ico; Filename: {app}\COPYING.txt; Comment: Read the software license under which the AGTk is distributed
; Name: {group}\Documentation\Developers Documentation; Filename: {app}\doc\Developer\index.html; Comment: epydoc-generated documentation for developers.

Name: {group}\Uninstall the AGTk; Filename: {uninstallexe}; Comment: Uninstall the Access Grid Toolkit.

Name: {userappdata}\Microsoft\Internet Explorer\Quick Launch\Access Grid Venue Client; IconFilename: {app}\install\ag.ico; Filename: {reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\pythonw.exe; Parameters: """{app}\bin\VenueClient3.py"""; WorkingDir: %APPDATA%\AccessGrid3; Tasks: quicklaunchicon

Name: {commondesktop}\Access Grid 3 Venue Client; Filename: {reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\pythonw.exe; Parameters: """{app}\bin\VenueClient3.py"""; IconFilename: {app}\install\ag.ico; WorkingDir: %APPDATA%\AccessGrid3; Tasks: desktopicon; Comment: Run the Venue Client!
Name: {group}\Manage Certificates; Filename: {reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\pythonw.exe; Parameters: """{app}\bin\CertificateManager3.py"""; WorkingDir: %APPDATA%\AccessGrid3; IconFilename: {app}\install\ag.ico

[Registry]
Root: HKLM; Subkey: SOFTWARE\{#AppName} {#DirName}; ValueType: none; Flags: uninsdeletekey
Root: HKLM; Subkey: SOFTWARE\{#AppName} {#DirName}\{#AppVersion}; ValueType: expandsz; ValueName: InstallPath; ValueData: {app}; Flags: uninsdeletekey
Root: HKLM; Subkey: SOFTWARE\{#AppName} {#DirName}\{#AppVersion}; ValueType: expandsz; ValueName: VersionInformation; ValueData: {#VersionInformation}; Flags: uninsdeletekey
Root: HKCR; Subkey: MIME\Database\Content Type\application/x-ag-venueclient; ValueType: string; ValueName: Extension; ValueData: .vv3d
Root: HKCR; Subkey: .vv3d; ValueType: string; ValueData: x-ag-venueclient; Flags: uninsdeletekey
Root: HKCR; Subkey: .vv3d; ValueType: string; ValueName: Content Type; ValueData: application/x-ag-venueclient; Flags: uninsdeletekey
Root: HKCR; Subkey: x-ag-venueclient; ValueType: dword; ValueName: EditFlags; ValueData: 00010000; Flags: uninsdeletekey
Root: HKCR; Subkey: x-ag-venueclient; ValueType: dword; ValueName: BrowserFlags; ValueData: 00000008; Flags: uninsdeletekey
Root: HKCR; Subkey: x-ag-venueclient; ValueType: string; ValueData: Access Grid Virtual Venue Description; Flags: uninsdeletekey
Root: HKCR; Subkey: x-ag-venueclient\shell; ValueType: string; ValueData: Open; Flags: uninsdeletekey
Root: HKCR; Subkey: x-ag-venueclient\shell\Open\command; ValueType: string; ValueData: """{reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\python.exe"" ""{app}\bin\GoToVenue3.py"" --file ""%1"""; Flags: uninsdeletekey

Root: HKCR; Subkey: .agpkg3; ValueType: string; ValueData: x-ag3-pkg; Flags: uninsdeletekey
Root: HKCR; Subkey: .agpkg3; ValueType: string; ValueName: Content Type; ValueData: application/x-ag3-pkg; Flags: uninsdeletekey
Root: HKCR; Subkey: x-ag3-pkg; ValueType: dword; ValueName: EditFlags; ValueData: 00010000; Flags: uninsdeletekey
Root: HKCR; Subkey: x-ag3-pkg; ValueType: dword; ValueName: BrowserFlags; ValueData: 00000008; Flags: uninsdeletekey
Root: HKCR; Subkey: x-ag3-pkg; ValueType: string; ValueData: Access Grid Package; Flags: uninsdeletekey
Root: HKCR; Subkey: x-ag3-pkg\shell; ValueType: string; ValueData: Open; Flags: uninsdeletekey
Root: HKCR; Subkey: x-ag3-pkg\shell\Open\command; ValueType: string; ValueData: """{reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\python.exe"" ""{app}\bin\agpm3.py"" --gui --package ""%1"""; Flags: uninsdeletekey

Root: HKCR; Subkey: .ppt; ValueType: string; ValueData: PowerPoint.Show.8; Flags: uninsdeletekey
;Root: HKCR; Subkey: PowerPoint.Show.8; ValueType: dword; ValueName: EditFlags; ValueData: 00010000; Flags: uninsdeletekey
;Root: HKCR; Subkey: PowerPoint.Show.8; ValueType: dword; ValueName: BrowserFlags; ValueData: 00000008; Flags: uninsdeletekey
Root: HKCR; Subkey: PowerPoint.Show.8\shell\Open in Venue\command; ValueType: string; ValueData: """{reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\python.exe"" ""{app}\SharedApplications\Shared_Presentation\SharedPresentation.py"" --start -f ""%1"""; Flags: uninsdeletekey

[Tasks]
Name: desktopicon; Description: Create &Desktop Icons; GroupDescription: Additional icons:
Name: quicklaunchicon; Description: Create a &Quick Launch Icon; GroupDescription: Additional icons:; Flags: unchecked

[Messages]
DirExists=The directory:%n%n%1%n%nalready exists and appears to have an {#AppName} installation in it.%n%nIt is recommended that you uninstall any existing {#AppName} 3 software before proceeding.  Do you wish to proceed anyway?
WelcomeLabel2=This will install the {#AppName} {#AppVersion} {#VersionInformation} on your computer.%n%nIt is strongly recommended that you uninstall any previous version of the {#AppName} 3 before continuing.%n%nIt is also strongly recommended that you close all other applications you have running before continuing with this installation.%n%nThese steps will help prevent any conflicts during the installation process.

[Run]
; Filename: {tmp}\wxPython2.8-win32-unicode-2.8.3.0-py24.exe; Parameters: "/verysilent "
; Filename: {tmp}\pywin32-210.win32-py2.4.exe; Parameters: "/silent "
Filename: {reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\python.exe; Description: Install shared apps system wide.; Flags: runhidden; Parameters: agpm3.py -s --post-install; WorkingDir: {app}\bin

[UninstallDelete]
Name: {app}; Type: filesandordirs
Name: {app}\bin\*.dat; Type: files
Name: {app}\bin\*.cfg; Type: files
Name: {reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\Lib\site-packages\AccessGrid3; Type: filesandordirs
Name: {reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\Lib\site-packages\common; Type: filesandordirs
Name: {reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\Lib\site-packages\elementtree; Type: filesandordirs
Name: {reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\Lib\site-packages\feedparser; Type: filesandordirs
Name: {reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\Lib\site-packages\gov; Type: filesandordirs
Name: {reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\Lib\site-packages\twisted; Type: filesandordirs
Name: {reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\Lib\site-packages\zope; Type: filesandordirs
Name: {reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\Lib\site-packages\M2Crypto; Type: filesandordirs
Name: {reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\Lib\site-packages\ZSI; Type: filesandordirs
Name: {reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\Lib\site-packages\_xmlplus; Type: filesandordirs
Name: {reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\Lib\site-packages\bonjour; Type: filesandordirs

[Dirs]
Name: {app}\config\nodeConfig
Name: {app}\Logs
Name: {app}\PackageCache
Name: {app}\SharedApplications
Name: {app}\Services
Name: {app}\NodeServices
Name: {app}\Plugins

[Types] 
Name: "custom"; Description: "Custom installation"; Flags: iscustom


[Code]
var
  PythonChecked: Boolean;
  PythonCheckResult: Boolean;
  wxPythonChecked: Boolean;
  wxPythonCheckResult: Boolean;
  pyWin32Checked: Boolean;
  pyWin32CheckResult: Boolean;
  PythonDir : String;
  ResultCode : Integer;

function PythonCheck(): Boolean;
begin
  Result := not DirExists('C:\Python24');
end;

function wxPythonCheck(): Boolean;
begin
  Result := not DirExists('C:\Python24');
end;

function pyWin32Check(): Boolean;
begin
  Result := True;
end;

procedure AfterPythonInstall();
begin
	MsgBox('Installing Python', mbConfirmation, MB_YESNO);    
    Exec('msiexec.exe', ExpandConstant(' /i {tmp}\python-2.4.4c1.msi /quiet'), '', SW_SHOW,
     ewWaitUntilTerminated, ResultCode)
end;


procedure AfterWxPythonInstall();
begin
	MsgBox('Installing wxPython', mbConfirmation, MB_YESNO);
    Exec(ExpandConstant('{tmp}\wxPython2.8-win32-unicode-2.8.3.0-py24.exe'), '/verysilent', '', SW_SHOW,
     ewWaitUntilTerminated, ResultCode)
end;



