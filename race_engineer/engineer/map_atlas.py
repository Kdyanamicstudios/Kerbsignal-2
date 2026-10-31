"""Exact internal SDK TrackName matching only. Never guess a layout by venue."""
from pathlib import Path
import json,gzip,re
class MapAtlas:
 def __init__(self,folder=None):self.folder=Path(folder) if folder else Path(__file__).with_name('maps')
 def load(self,meta):
  name=str(meta.get('track_name','')).strip().replace(' ','_').replace('\\','_').replace('/','_').lower()
  if not name or not re.fullmatch(r'[a-z0-9_.-]+',name):return None
  try:
   index=json.loads((self.folder/'index.json').read_text());filename=index.get(name)
   if not filename:return None
   with gzip.open(self.folder/filename,'rt') as f:return json.load(f)
  except (OSError,ValueError,TypeError):return None
