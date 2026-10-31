"""Read-only Windows HID/WinMM enumeration. Never changes racing controls."""
import sys

def role(name):
 n=name.casefold()
 if any(w in n for w in ('pedal','srp','crp','heusinkveld','simjack','p1000','p2000','load cell','t-lcm','t3pa','t3pm','csl elite pedals')):return 'Pedals'
 if any(w in n for w in ('wheel','wheelbase','steering','simucube','simagic','moza','fanatec','thrustmaster','g29','g920','g923','csl dd','clubsport','t300','t150','t248','t-gt')):return 'Wheel base / combined controller'
 return 'Controller — confirm role'

def enumerate_controllers():
 if sys.platform!='win32':return []
 import ctypes as c
 from ctypes import wintypes as w
 class Entry(c.Structure):_fields_=[('handle',w.HANDLE),('type',w.DWORD)]
 class HID(c.Structure):_fields_=[('vendor',w.DWORD),('product',w.DWORD),('version',w.DWORD),('page',w.USHORT),('usage',w.USHORT)]
 class InfoUnion(c.Union):_fields_=[('hid',HID),('padding',w.DWORD*6)]
 class Info(c.Structure):_fields_=[('size',w.DWORD),('type',w.DWORD),('u',InfoUnion)]
 u=c.WinDLL('user32',use_last_error=True);k=c.WinDLL('kernel32',use_last_error=True);h=c.WinDLL('hid')
 u.GetRawInputDeviceList.argtypes=[c.POINTER(Entry),c.POINTER(w.UINT),w.UINT];u.GetRawInputDeviceList.restype=w.UINT
 u.GetRawInputDeviceInfoW.argtypes=[w.HANDLE,w.UINT,c.c_void_p,c.POINTER(w.UINT)];u.GetRawInputDeviceInfoW.restype=w.UINT
 k.CreateFileW.argtypes=[w.LPCWSTR,w.DWORD,w.DWORD,c.c_void_p,w.DWORD,w.DWORD,w.HANDLE];k.CreateFileW.restype=w.HANDLE
 k.CloseHandle.argtypes=[w.HANDLE];h.HidD_GetProductString.argtypes=[w.HANDLE,c.c_void_p,w.ULONG];h.HidD_GetProductString.restype=c.c_ubyte
 count=w.UINT();bad=0xffffffff;rows=[]
 for _ in range(3):
  if u.GetRawInputDeviceList(None,c.byref(count),c.sizeof(Entry))==bad:raise OSError('Windows controller enumeration failed')
  if count.value>1024:raise OSError('Unexpected controller count')
  entries=(Entry*count.value)();found=u.GetRawInputDeviceList(entries,c.byref(count),c.sizeof(Entry))
  if found!=bad:break
 else:raise OSError('Controller list changed during scan. Rescan devices.')
 for item in entries[:found]:
  if item.type!=2:continue
  info=Info();info.size=c.sizeof(Info);size=w.UINT(c.sizeof(Info))
  if u.GetRawInputDeviceInfoW(item.handle,0x2000000b,c.byref(info),c.byref(size))==bad:continue
  hid=info.u.hid
  if hid.page!=1 or hid.usage not in (4,5,8):continue
  size=w.UINT()
  if u.GetRawInputDeviceInfoW(item.handle,0x20000007,None,c.byref(size))==bad or size.value>4096:continue
  path=c.create_unicode_buffer(size.value+1)
  if u.GetRawInputDeviceInfoW(item.handle,0x20000007,path,c.byref(size))==bad:continue
  name='';handle=k.CreateFileW(path.value,0,3,None,3,0,None)
  if handle not in (None,c.c_void_p(-1).value):
   try:
    buf=c.create_unicode_buffer(256)
    if h.HidD_GetProductString(handle,buf,c.sizeof(buf)):name=buf.value.strip()
   finally:k.CloseHandle(handle)
  if not name:name=f'HID controller {hid.vendor:04X}:{hid.product:04X}'
  row=dict(name=name[:160],vendor=f'{hid.vendor:04X}',product=f'{hid.product:04X}',role=role(name),source='Windows HID')
  if row not in rows:rows.append(row)
 # WinMM can identify drivers that do not supply a readable HID product string.
 class Caps(c.Structure):_fields_=[('mid',w.WORD),('pid',w.WORD),('name',w.WCHAR*32)]+[(n,w.UINT) for n in ('xmin','xmax','ymin','ymax','zmin','zmax','buttons','pmin','pmax','rmin','rmax','umin','umax','vmin','vmax','caps','maxaxes','axes','maxbuttons')]+[('reg',w.WCHAR*32),('oem',w.WCHAR*260)]
 mm=c.WinDLL('winmm');mm.joyGetDevCapsW.argtypes=[c.c_size_t,c.POINTER(Caps),w.UINT];mm.joyGetDevCapsW.restype=w.UINT
 for idx in range(16):
  caps=Caps()
  if mm.joyGetDevCapsW(idx,c.byref(caps),c.sizeof(caps))!=0:continue
  name=caps.name.strip()
  if name and all(r['name'].casefold()!=name.casefold() for r in rows):rows.append(dict(name=name,role=role(name),source='Windows game controller',axes=caps.axes))
 return rows
