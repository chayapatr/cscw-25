import json

def parse_key_list(key):
    t = key.type
    s = key.subtype
    f = key.feature
    
    keys = []
    
    if(not s and not f):
        keys = [f"{t}"]
    elif(not s):
        # keys = [f"{t}", f"{t}>{f}"]
        keys = [ f"{t}", f"{t}>{f.split(":")[0]}"] #, f"{t}>{f.split(":")[0]}"]
    elif(not f):
        # keys = [f"{t}", f"{t}|{s}"]
        keys = [f"{t}", f"{t}|{s.split(":")[0]}"]
    else:
        # keys= [f"{t}", f"{t}|{s}", f"{t}|{s}>{f}"]
        keys= [f"{t}", f"{t}|{s.split(":")[0]}"] #, f"{t}|{s.split(":")[0]}>{f.split(":")[0]}"]
    
    return [ k.replace("-", "_").replace(" ", "_") for k in keys ]

def parse_key(key, full=False):
    t = key['type']
    s = key['subtype']
    f = key['feature']
    
    if(not s and not f):
        return f"{t}"
    elif(not s):
        return f"{t}>{f}".replace("-", "_").replace(" ", "_") if full else f"{t}>{f.split(":")[0]}".replace("-", "_").replace(" ", "_")
    elif(not f):
        return f"{t}|{s}".replace("-", "_").replace(" ", "_") if full else f"{t}|{s.split(":")[0]}".replace("-", "_").replace(" ", "_")
    else:
        return f"{t}|{s}>{f}".replace("-", "_").replace(" ", "_") if full else f"{t}|{s.split(":")[0]}".replace("-", "_").replace(" ", "_")

def parse_subject(s):
    return json.dumps({
        "type": s.type,
        "subtype": s.subtype,
        "feature": s.feature,
    })