"""Static native dependency check. Does not replace a real Windows launch test."""
from pathlib import Path
import collections
import pefile
import sys

root=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parent/'payload'
files=[p for p in root.rglob('*') if p.suffix.lower() in ('.dll','.pyd','.exe')]
byname=collections.defaultdict(list)
for p in files:byname[p.name.lower()].append(p)
# Components supplied by supported Windows 10/11 installations.
system=set('kernel32.dll kernelbase.dll advapi32.dll user32.dll gdi32.dll gdi32full.dll shell32.dll ole32.dll oleaut32.dll uuid.dll comdlg32.dll comctl32.dll ws2_32.dll bcrypt.dll bcryptprimitives.dll crypt32.dll cryptbase.dll secur32.dll iphlpapi.dll rpcrt4.dll ntdll.dll psapi.dll shlwapi.dll version.dll winmm.dll winspool.drv msvcrt.dll dbghelp.dll setupapi.dll dxgi.dll d3d11.dll d3d12.dll d3dcompiler_47.dll dwmapi.dll normaliz.dll netapi32.dll wtsapi32.dll winhttp.dll powrprof.dll propsys.dll avrt.dll imm32.dll uxtheme.dll mpr.dll dnsapi.dll ncrypt.dll userenv.dll'.split())
# Windows runtime / performance-counter DLLs, shipped by Windows 10 and 11.
system.update(('combase.dll','pdh.dll'))
missing={};symbol_errors=[];exports={}
for p in files:
 pe=pefile.PE(str(p),fast_load=True)
 pe.parse_data_directories(directories=[pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_IMPORT']])
 for imp in getattr(pe,'DIRECTORY_ENTRY_IMPORT',[]):
  name=imp.dll.decode().lower()
  if name.startswith(('api-ms-','ext-ms-')) or name in system:continue
  candidates=byname.get(name)
  if not candidates:
   missing.setdefault(name,[]).append(str(p.relative_to(root)));continue
  provider=next((v for v in candidates if v.parent==root),candidates[0])
  if provider not in exports:
   ep=pefile.PE(str(provider),fast_load=True,max_symbol_exports=100000)
   ep.parse_data_directories(directories=[pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_EXPORT']])
   symbols=getattr(ep,'DIRECTORY_ENTRY_EXPORT',None)
   exports[provider]=({s.name for s in symbols.symbols},{s.ordinal for s in symbols.symbols}) if symbols else (set(),set())
   ep.close()
  names,ordinals=exports[provider]
  for s in imp.imports:
   if (s.name and s.name not in names) or (s.name is None and s.ordinal not in ordinals):symbol_errors.append((p.name,name,s.name or s.ordinal))
 pe.close()
print('Native binaries checked:',len(files))
print('Unresolved non-system DLLs:',missing)
print('Missing imported symbols:',symbol_errors)
assert not missing and not symbol_errors
