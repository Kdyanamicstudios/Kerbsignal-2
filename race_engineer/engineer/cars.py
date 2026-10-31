"""Car identity comes from the player's SDK entry, not a hard-coded car list."""
import math


def car_identity(meta,data):
    if not meta.get('car_path') or meta.get('car') in (None,'','Unknown'):return None
    controls={k:v for k,v in data.items() if k.startswith('dc') and isinstance(v,(int,float)) and math.isfinite(v)}
    return dict(name=meta['car'],path=meta['car_path'],id=meta.get('car_id',''),track_id=meta.get('track_id'),layout=meta.get('config'),
        car_class=meta.get('car_class',''),class_id=meta.get('car_class_id',''),
        player_index=data.get('PlayerCarIdx',meta.get('player_car_idx')),
        setup_name=meta.get('setup_name',''),reported_controls=controls,
        setup_values=dict(list(meta.get('car_setup',{}).items())[:60]),
        capability_note='Reported controls are observations; missing channels do not prove equipment is absent. Ranges and adjustment directions are unverified unless explicitly provided.')


def identity_key(identity):
    if not identity:return None
    return tuple(identity.get(k) for k in ('id','path','player_index','track_id','layout'))
