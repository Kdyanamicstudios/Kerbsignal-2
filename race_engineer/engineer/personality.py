"""User-selected radio style. Critical driving cues remain clear and concise."""
import json
from pathlib import Path

STYLES=('Clean','Mild','Unfiltered')

class Personality:
    def __init__(self,style='Clean'):
        self.style=style if style in STYLES else 'Clean'
        self.calls=0

    def decorate(self,text):
        self.calls+=1
        if self.style=='Mild' and self.calls%3==0:
            return 'Bloody hell. '+text
        if self.style=='Unfiltered':
            prefixes=('Fuck, ','Damn it, ','','Fuck me, ')
            return prefixes[(self.calls-1)%len(prefixes)]+text
        return text


class VoiceSettings:
    def __init__(self,path):
        self.path=Path(path);self.voice_id='';self.label='Windows default';self.style='Clean'
        try:
            data=json.loads(self.path.read_text(encoding='utf-8'))
            self.voice_id=self.valid_id(data.get('voice_id',''))
            self.label=str(data.get('label','Windows default'))[:200]
            self.style=data.get('style','Clean') if data.get('style') in STYLES else 'Clean'
        except (OSError,ValueError,TypeError):pass

    @staticmethod
    def valid_id(value):
        if not isinstance(value,str) or len(value)>2048 or any(ord(c)<32 for c in value):
            raise ValueError('Invalid voice identifier.')
        return value

    def save(self,voice_id,label,style):
        voice_id=self.valid_id(voice_id)
        if style not in STYLES:raise ValueError('Choose a valid language style.')
        data=dict(voice_id=voice_id,label=str(label)[:200],style=style)
        self.path.parent.mkdir(parents=True,exist_ok=True)
        temporary=self.path.with_suffix('.tmp');temporary.write_text(json.dumps(data),encoding='utf-8');temporary.replace(self.path)
        self.voice_id=voice_id;self.label=data['label'];self.style=style
