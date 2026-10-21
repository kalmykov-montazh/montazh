import json,re,difflib,sys
S={x['id']:x for x in json.load(open('shorts.json'))}
def n(w): return re.sub(r'[^\w]','',w.lower()).replace('ё','е')
for k in sys.argv[1:]:
    d=json.load(open(f'w/{k}/words.json'))
    a=[n(w) for s,w in d['asr']]; b=[n(w) for w in (S[k]['text']+' Всё, пошёл работать').split()]
    out=[]
    for tag,i1,i2,j1,j2 in difflib.SequenceMatcher(None,a,b,autojunk=False).get_opcodes():
        if tag!='equal': out.append(f"{tag}: asr[{' '.join(a[i1:i2])}] txt[{' '.join(b[j1:j2])}]")
    print(k,'|'.join(out))
