"""Read-only NaYoo Outline -> immutable public knowledge feed. Python 3.9+."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import tempfile
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, build_opener, HTTPRedirectHandler
import uuid
import zipfile

BASE='https://wiki.infonayoo.co'
COLLECTIONS={'58eda825-302c-4f4a-bf84-8759cfce769f':'solution',
             'd08b0730-b2f2-42c2-be89-72f4804def62':'develop'}
MAX_DOCS=5000
MAX_RESPONSE=16*1024*1024
MAX_ARCHIVE=100*1024*1024
MAX_EXPANDED=150*1024*1024
METHODS={'collections.info','collections.documents','documents.list','documents.info'}

class SyncError(Exception): pass

def now(): return datetime.now(timezone.utc).isoformat()
def digest(data): return hashlib.sha256(data).hexdigest()
def encoded(value): return (json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode('utf-8')
def identifier(value):
    try:
        if str(uuid.UUID(value))!=value: raise ValueError()
    except (ValueError,TypeError,AttributeError): raise SyncError('Invalid document identifier') from None
    return value

def check_secret(text, token=None):
    patterns=[r'ol_api_[A-Za-z0-9]{38}',r'gh[pousr]_[A-Za-z0-9]{30,}',r'github_pat_[A-Za-z0-9_]{40,}',
              r'sk-(?:proj-|ant-)?[A-Za-z0-9_-]{30,}',r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----']
    if (token and token in text) or any(re.search(p,text) for p in patterns):
        raise SyncError('Recognizable credential detected; publication blocked (value not logged)')

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs): return None

class Outline:
    def __init__(self,token):
        if not token or '\n' in token or '\r' in token: raise SyncError('WIKI_API_KEY is missing or invalid')
        self.token=token
        self.opener=build_opener(NoRedirect())
    def call(self,method,payload):
        if method not in METHODS: raise SyncError('API method is not read-only allowlisted')
        for attempt in range(4):
            request=Request(BASE+'/api/'+method,data=encoded(payload),method='POST',
                headers={'Authorization':'Bearer '+self.token,'Content-Type':'application/json','Accept':'application/json'})
            try:
                with self.opener.open(request,timeout=45) as response:
                    body=response.read(MAX_RESPONSE+1)
                    if len(body)>MAX_RESPONSE: raise SyncError('Wiki response exceeds limit')
                    value=json.loads(body)
                    if not isinstance(value,dict) or value.get('ok') is False or 'data' not in value:
                        raise SyncError('Wiki response schema not supported')
                    return value
            except HTTPError as exc:
                if exc.code in (429,500,502,503,504) and attempt<3:
                    delay=exc.headers.get('Retry-After','')
                    if delay and (not delay.isdigit() or int(delay)>60):
                        raise SyncError('Retry-After requires a later run') from None
                    time.sleep(int(delay) if delay else 2**attempt)
                    continue
                raise SyncError('Wiki API '+method+' failed with HTTP '+str(exc.code)) from None
            except (URLError,TimeoutError,json.JSONDecodeError):
                if attempt<3: time.sleep(2**attempt); continue
                raise SyncError('Wiki connection/response failed; prior snapshot retained') from None
        raise SyncError('Retry limit reached')

def unwrap(value):
    data=value.get('data')
    if isinstance(data,dict) and isinstance(data.get('document'),dict): data=data['document']
    if not isinstance(data,dict): raise SyncError('Document response is not an object')
    return data

def metadata(d):
    required=('id','title','url','collectionId','revision','updatedAt','publishedAt')
    if any(k not in d for k in required): raise SyncError('Document metadata is incomplete')
    identifier(d['id'])
    if not isinstance(d['title'],str) or not isinstance(d['updatedAt'],str) or not isinstance(d['revision'],int):
        raise SyncError('Invalid document metadata types')
    if d.get('parentDocumentId'): identifier(d['parentDocumentId'])
    url=d['url']
    if not isinstance(url,str): raise SyncError('Invalid Wiki URL')
    if url.startswith('/doc/'): url=BASE+url
    u=urlparse(url)
    if u.scheme!='https' or u.netloc!='wiki.infonayoo.co' or not u.path.startswith('/doc/'):
        raise SyncError('Unexpected source URL')
    return {k:d.get(k) for k in ('id','title','collectionId','revision','updatedAt','publishedAt',
            'archivedAt','deletedAt','parentDocumentId')}|{'url':url}

def inventory(api):
    found={}; trees={}
    for cid,name in COLLECTIONS.items():
        c=unwrap(api.call('collections.info',{'id':cid}))
        if c.get('id')!=cid or c.get('deletedAt') or c.get('archivedAt'):
            raise SyncError('Approved collection unavailable')
        tree=api.call('collections.documents',{'id':cid}).get('data')
        if not isinstance(tree,list): raise SyncError('Collection tree is incomplete')
        nodes={}
        def walk(items,parent=None,trail=()):
            if not isinstance(items,list): raise SyncError('Invalid collection children')
            for index,node in enumerate(items):
                id=identifier(node.get('id'))
                if id in nodes: raise SyncError('Duplicate/cyclic tree identifier')
                if not isinstance(node.get('title'),str) or not isinstance(node.get('children'),list):
                    raise SyncError('Incomplete tree node')
                nodes[id]={'parent':parent,'path':list(trail)+( [node['title']] ),'order':index}
                if len(nodes)>MAX_DOCS: raise SyncError('Document count exceeds scope limit')
                walk(node['children'],id,tuple(nodes[id]['path']))
        walk(tree); trees[cid]=nodes
        listed={}
        for offset in range(0,MAX_DOCS+100,100):
            r=api.call('documents.list',{'collectionId':cid,'limit':100,'offset':offset,'sort':'createdAt','direction':'ASC'})
            batch=r.get('data')
            if not isinstance(batch,list) or len(batch)>100: raise SyncError('Invalid pagination data')
            for item in batch:
                id=identifier(item.get('id'))
                if id in listed: raise SyncError('Duplicate ID across pagination')
                listed[id]=item
            if len(listed)>MAX_DOCS: raise SyncError('Too many documents')
            pagination=r.get('pagination',{})
            if not isinstance(pagination,dict) or pagination.get('offset',offset)!=offset:
                raise SyncError('Pagination position mismatch')
            if len(batch)<100:
                if pagination.get('nextPath'): raise SyncError('Truncated page has continuation')
                break
        else: raise SyncError('Pagination did not terminate')
        active={id:metadata(d) for id,d in listed.items()
                if d.get('publishedAt') and not d.get('archivedAt') and not d.get('deletedAt')}
        if set(active)!=set(nodes): raise SyncError('Published inventory and collection tree disagree')
        for id,d in active.items():
            if id in found or d['collectionId']!=cid or d['parentDocumentId']!=nodes[id]['parent'] or d['title']!=nodes[id]['path'][-1]:
                raise SyncError('Collection identity/parent/title mismatch')
            found[id]={**d,'collection':name,**nodes[id]}
    if not found or len(found)>MAX_DOCS: raise SyncError('Empty or excessive source inventory')
    return found

def fingerprint(inv): return digest(encoded(inv))

def cache_read(root):
    root=Path(root)
    try:
        m=json.loads((root/'manifest.json').read_bytes())
        if m.get('schemaVersion')!='nitii-wiki-snapshot.v1': raise SyncError('Unknown cached schema')
        docs=m['documents']; bodies={}
        for d in docs:
            id=identifier(d['id'])
            if id in bodies or d['bodyPath']!='pages/'+id+'.md': raise SyncError('Invalid cached body path')
            p=root/d['bodyPath']
            if p.is_symlink() or not p.resolve().is_relative_to(root.resolve()): raise SyncError('Unsafe cached page')
            b=p.read_bytes()
            if digest(b)!=d['bodySha256'] or len(b)!=d['bodyBytes']: raise SyncError('Cached body hash/size differs')
            bodies[id]=b
        if len(bodies)!=m['documentCount']: raise SyncError('Cached count mismatch')
        return m,bodies
    except (KeyError,ValueError,OSError,TypeError): raise SyncError('Cached snapshot is incomplete') from None

def capture(api,previous_root=None):
    started=now(); old,before_bodies=cache_read(previous_root) if previous_root else ({'documents':[]},{})
    before=inventory(api); old_docs={d['id']:d for d in old['documents']}; bodies={}; docs=[]; removals=[]
    for id in sorted(set(old_docs)-set(before)):
        try: d=unwrap(api.call('documents.info',{'id':id}))
        except Exception: raise SyncError('Prior document unavailable; removal needs review: '+id) from None
        if d.get('id')!=id or not (d.get('archivedAt') or d.get('deletedAt') or ('publishedAt' in d and not d['publishedAt'])):
            raise SyncError('Unexplained removal needs review: '+id)
        removals.append({'id':id,'archivedAt':d.get('archivedAt'),'deletedAt':d.get('deletedAt'),
                         'publishedAt':d.get('publishedAt'),'confirmedAtUtc':now()})
    for id,item in sorted(before.items()):
        prior=old_docs.get(id)
        if prior and prior.get('revision')==item['revision'] and prior.get('updatedAt')==item['updatedAt']:
            body=before_bodies[id]; read_at=prior['checkedAtUtc']
        else:
            d=unwrap(api.call('documents.info',{'id':id}))
            if metadata(d)!={k:v for k,v in item.items() if k not in ('collection','parent','path','order')}:
                raise SyncError('Document changed during read: '+id)
            if not isinstance(d.get('text'),str): raise SyncError('API did not return Markdown text: '+id)
            body=d['text'].encode('utf-8'); read_at=now()
        check_secret(item['title']+'\n'+item['url']+'\n'+body.decode('utf-8'),getattr(api,'token',None))
        bodies[id]=body
        docs.append({'id':id,'title':item['title'],'url':item['url'],'collection':item['collection'],
                     'parentId':item['parentDocumentId'],'path':item['path'],'order':item['order'],
                     'revision':item['revision'],'updatedAt':item['updatedAt'],'checkedAtUtc':read_at,
                     'metadataCheckedAtUtc':started,'bodyPath':'pages/'+id+'.md',
                     'bodySha256':digest(body),'bodyBytes':len(body),'bodyCharacters':len(body.decode('utf-8')),
                     'evidenceStatus':'copied_wiki_unclassified'})
    after=inventory(api)
    if fingerprint(before)!=fingerprint(after): raise SyncError('Source changed during capture; prior snapshot retained')
    core={'inventory':before,'bodies':{id:digest(b) for id,b in sorted(bodies.items())}}
    m={'schemaVersion':'nitii-wiki-snapshot.v1','snapshotId':fingerprint(core),'capturedAtUtc':now(),
       'readWindowUtc':{'first':started,'last':now()},'documentCount':len(docs),
       'collections':{name:sum(d['collection']==name for d in docs) for name in COLLECTIONS.values()},
       'inventorySha256':fingerprint(before),'bodyBytes':sum(map(len,bodies.values())),
       'sourceCorpusSha256':digest(b''.join(id.encode()+bodies[id] for id in sorted(bodies))),
       'contentPolicy':'Exact Wiki Markdown; classify approval/proposal/conflict per passage.',
       'mediaPolicy':'References preserved; attachment binaries and visual semantics not verified.',
       'scope':'Published accessible Solution and Develop only; external links not followed.',
       'removals':removals,'documents':docs}
    return m,bodies

def validate_artifacts(root,sid):
    try:
        m,_=cache_read(root)
        if m.get('snapshotId')!=sid or (root/'knowledge.zip').is_symlink(): raise SyncError('Snapshot identity mismatch')
        archive=root/'knowledge.zip'
        if archive.stat().st_size>MAX_ARCHIVE: raise SyncError('Archive exceeds size limit')
        files={f['path']:f for f in m['files']}
        if len(files)!=len(m['files']): raise SyncError('Duplicate file inventory')
        with zipfile.ZipFile(archive) as z:
            entries=z.infolist()
            if sum(e.file_size for e in entries)>MAX_EXPANDED: raise SyncError('Expanded archive exceeds size limit')
            names=[e.filename for e in entries]
            if len(names)!=len(set(names)) or set(names)!=set(files)|{'manifest.json'}:
                raise SyncError('Archive entries differ from file inventory')
            if z.read('manifest.json')!=(root/'manifest.json').read_bytes(): raise SyncError('Archive manifest differs')
            for name,item in files.items():
                path=root/name
                if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()): raise SyncError('Unsafe immutable file path')
                b=z.read(name)
                if len(b)!=item['bytes'] or digest(b)!=item['sha256'] or path.read_bytes()!=b:
                    raise SyncError('Immutable file integrity differs')
    except (KeyError,ValueError,OSError,zipfile.BadZipFile,RuntimeError):
        raise SyncError('Immutable snapshot archive is incomplete or corrupt') from None

def publish(feed,manifest,bodies):
    feed=Path(feed); sid=manifest['snapshotId']
    if not re.fullmatch('[0-9a-f]{64}',sid): raise SyncError('Invalid snapshot ID')
    feed.mkdir(parents=True,exist_ok=True); destination=feed/'snapshots'/sid
    stage=Path(tempfile.mkdtemp(prefix='.stage-',dir=feed))
    try:
        (stage/'pages').mkdir(); (stage/'web').mkdir()
        for d in manifest['documents']:
            b=bodies[d['id']]
            if digest(b)!=d['bodySha256'] or len(b)!=d['bodyBytes']: raise SyncError('Body validation failed')
            (stage/d['bodyPath']).write_bytes(b)
        summary={k:v for k,v in manifest.items() if k!='documents'}
        (stage/'snapshot.json').write_bytes(encoded(summary))
        lines=['# NaYoo Wiki knowledge index','',f"Snapshot: {sid}",'']
        for d in manifest['documents']:
            lines.append(f"- {d['id']} | {' / '.join(d['path'])} | revision {d['revision']} | {d['url']}")
        (stage/'INDEX.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
        volume=1; chunks=[]; size=0
        def save_volume():
            (stage/'web'/f'NAYOO_WIKI_{volume:02}.txt').write_bytes(''.join(chunks).encode('utf-8'))
        for d in manifest['documents']:
            text=f"\n\n=== {d['id']} | {d['title']} ===\nSOURCE: {d['url']}\nREVISION: {d['revision']}\nBODY READ: {d['checkedAtUtc']}\n\n"+bodies[d['id']].decode('utf-8')
            if chunks and size+len(text.encode('utf-8'))>1800000:
                save_volume(); volume+=1; chunks=[]; size=0
            chunks.append(text); size+=len(text.encode('utf-8'))
        if chunks: save_volume()
        (stage/'web'/'UPLOAD_INDEX.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8')
        manifest=dict(manifest)
        manifest['files']=[{'path':p.relative_to(stage).as_posix(),'sha256':digest(p.read_bytes()),'bytes':p.stat().st_size}
                           for p in sorted(stage.rglob('*')) if p.is_file()]
        (stage/'manifest.json').write_bytes(encoded(manifest))
        with zipfile.ZipFile(stage/'knowledge.zip','w',compression=zipfile.ZIP_DEFLATED) as z:
            for p in sorted(stage.rglob('*')):
                if p.is_file() and p.name!='knowledge.zip': z.write(p,p.relative_to(stage).as_posix())
        validate_artifacts(stage,sid)
        if destination.exists():
            validate_artifacts(destination,sid)
            # Reuse immutable bytes even when check/read timestamps differ.
        else:
            destination.parent.mkdir(exist_ok=True); stage.rename(destination)
        pointer={'schemaVersion':'nitii-feed.v1','snapshotId':sid,
                 'manifestPath':f'snapshots/{sid}/manifest.json',
                 'manifestSha256':digest((destination/'manifest.json').read_bytes()),
                 'archivePath':f'snapshots/{sid}/knowledge.zip',
                 'archiveSha256':digest((destination/'knowledge.zip').read_bytes()),
                 'checkedAtUtc':now(),'syncedAtUtc':json.loads((destination/'manifest.json').read_bytes())['capturedAtUtc'],
                 'documentCount':manifest['documentCount']}
        temporary=feed/'.latest.tmp'; temporary.write_bytes(encoded(pointer)); os.replace(temporary,feed/'latest.json')
        return destination
    finally:
        if stage.exists(): shutil.rmtree(stage)

def bootstrap(feed,archive):
    """Initialize from the already published, hash-pinned v1.1 asset; never claim a live read."""
    if (Path(feed)/'latest.json').exists(): raise SyncError('Bootstrap refuses to replace an existing feed')
    raw=Path(archive).read_bytes()
    if digest(raw)!='ff7e25c16be0262b7cb4f59135a0dedc27e1c8f384da982dd76bb58262eefb72':
        raise SyncError('Bootstrap release SHA256 mismatch')
    prefix='nitii-logic-suite/plugins/nitii-logic-suite/skills/nitii-knowledge/references/knowledge/'
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        m=json.loads(z.read(prefix+'manifest.json')); bodies={}
        for d in m['documents']:
            id=identifier(d['id'])
            if d['bodyPath']!='pages/'+id+'.md' or id in bodies: raise SyncError('Invalid bootstrap records')
            b=z.read(prefix+d['bodyPath'])
            if digest(b)!=d['bodySha256'] or len(b)!=d['bodyBytes']: raise SyncError('Invalid bootstrap hash')
            check_secret(d['title']+'\n'+b.decode('utf-8')); bodies[id]=b
        if len(bodies)!=m['documentCount']: raise SyncError('Bootstrap count mismatch')
    m['snapshotId']=fingerprint({'baseline':'v1.1.0','documents':m['documents']})
    m['bootstrap']=True
    m['freshnessNote']='Published v1.1.0 baseline; NOT a fresh authenticated Wiki check.'
    root=publish(feed,m,bodies)
    pointer=json.loads((Path(feed)/'latest.json').read_bytes())
    pointer['checkedAtUtc']=None; pointer['bootstrap']=True
    (Path(feed)/'latest.json').write_bytes(encoded(pointer))
    return root

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--feed',type=Path,required=True); p.add_argument('--seed',type=Path)
    p.add_argument('--bootstrap-zip',type=Path)
    args=p.parse_args()
    try:
        if args.bootstrap_zip:
            root=bootstrap(args.feed,args.bootstrap_zip)
            print(json.dumps({'status':'baseline_initialized_not_live_synced','path':str(root)})); return
        previous=args.seed
        if (args.feed/'latest.json').exists():
            latest=json.loads((args.feed/'latest.json').read_bytes()); sid=latest['snapshotId']
            if not re.fullmatch('[0-9a-f]{64}',sid): raise SyncError('Invalid previous pointer')
            previous=args.feed/'snapshots'/sid
        token=os.environ.pop('WIKI_API_KEY',None)
        api=Outline(token)
        try: m,b=capture(api,previous)
        finally: api.token=''; token=None
        result=publish(args.feed,m,b)
        print(json.dumps({'status':'complete','snapshotId':m['snapshotId'],'documents':m['documentCount'],
                          'removals':len(m['removals']),'path':str(result)},ensure_ascii=False))
    except (SyncError,OSError,KeyError,ValueError) as exc:
        # Deliberately no response payload, request headers, or traceback.
        print('Sync stopped: '+str(exc)); raise SystemExit(1)

if __name__=='__main__': main()
