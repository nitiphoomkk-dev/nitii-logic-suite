import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import wiki_sync as w

C = '58eda825-302c-4f4a-bf84-8759cfce769f'
A = '00000000-0000-4000-8000-000000000001'
B = '00000000-0000-4000-8000-000000000002'

def doc(id=A, text='ไทย\r\n| A | B |\n', revision=1):
    return dict(id=id,title='ตัวอย่าง',url='/doc/example-'+id,collectionId=C,
                parentDocumentId=None,revision=revision,updatedAt='2026-10-19T01:00:00Z',
                publishedAt='2026-10-19T00:00:00Z',archivedAt=None,deletedAt=None,text=text)

class API:
    def __init__(self, docs):
        self.docs=copy.deepcopy(docs); self.calls=[]; self.drift=False
    def call(self, method, payload):
        self.calls.append((method,copy.deepcopy(payload)))
        if method=='collections.info':
            return {'ok':True,'data':{'id':payload['id'],'archivedAt':None,'deletedAt':None}}
        ds=[d for d in self.docs if d['collectionId']==payload.get('collectionId',payload.get('id')) and d['publishedAt'] and not d['archivedAt']]
        if method=='collections.documents':
            return {'ok':True,'data':[{'id':d['id'],'title':d['title'],'url':d['url'],'children':[]} for d in ds]}
        if method=='documents.list':
            if payload.get('sort') not in ('createdAt','updatedAt','publishedAt','index','title','popularityScore'):
                raise w.SyncError('Unsupported Outline sort field')
            if self.drift and len([c for c in self.calls if c[0]=='documents.list' and c[1]['collectionId']==C])>1:
                ds=[{**d,'revision':99} for d in ds]
            start=payload['offset']; limit=payload['limit']
            return {'ok':True,'data':ds[start:start+limit], 'pagination':{'offset':start,'limit':limit,'nextPath':None}}
        if method=='documents.info':
            return {'ok':True,'data':next(d for d in self.docs if d['id']==payload['id'])}
        raise AssertionError(method)

class SyncTests(unittest.TestCase):
    def test_new_unicode_and_empty_pages_are_byte_exact(self):
        m,b=w.capture(API([doc(),doc(B,'')]))
        self.assertEqual(b[A],b'\xe0\xb9\x84\xe0\xb8\x97\xe0\xb8\xa2\r\n| A | B |\n')
        self.assertEqual(b[B],b'')
        self.assertEqual(m['documentCount'],2)
        self.assertEqual(m['collections'],{'solution':2,'develop':0})

    def test_unchanged_body_is_cached_but_new_revision_is_read(self):
        with tempfile.TemporaryDirectory() as t:
            m,b=w.capture(API([doc()]))
            root=w.publish(Path(t),m,b)
            api=API([doc(),doc(B,'new')]); newer,_=w.capture(api,root)
            reads=[p['id'] for name,p in api.calls if name=='documents.info']
            self.assertEqual(reads,[B])
            old=next(d for d in m['documents'] if d['id']==A)
            new=next(d for d in newer['documents'] if d['id']==A)
            self.assertEqual(old['checkedAtUtc'],new['checkedAtUtc'])
            api=API([doc(revision=2)]); w.capture(api,root)
            self.assertIn(('documents.info',{'id':A}),api.calls)

    def test_corrupt_cache_is_not_silently_reused(self):
        with tempfile.TemporaryDirectory() as t:
            m,b=w.capture(API([doc()])); root=w.publish(Path(t),m,b)
            (root/'pages'/f'{A}.md').write_bytes(b'bad')
            with self.assertRaises(w.SyncError): w.capture(API([doc()]),root)

    def test_inventory_drift_never_replaces_latest(self):
        with tempfile.TemporaryDirectory() as t:
            m,b=w.capture(API([doc()])); w.publish(Path(t),m,b)
            before=(Path(t)/'latest.json').read_bytes()
            api=API([doc()]); api.drift=True
            with self.assertRaises(w.SyncError): w.capture(api)
            self.assertEqual((Path(t)/'latest.json').read_bytes(),before)

    def test_missing_unexplained_page_stops_publication(self):
        with tempfile.TemporaryDirectory() as t:
            m,b=w.capture(API([doc()])); root=w.publish(Path(t),m,b)
            api=API([])
            with self.assertRaises(w.SyncError): w.capture(api,root)

    def test_explicit_archive_removes_active_but_keeps_receipt(self):
        with tempfile.TemporaryDirectory() as t:
            m,b=w.capture(API([doc(),doc(B)])); root=w.publish(Path(t),m,b)
            archived=doc(); archived['archivedAt']='2026-10-19T02:00:00Z'
            m,b=w.capture(API([archived,doc(B)]),root)
            self.assertEqual([d['id'] for d in m['documents']],[B])
            self.assertEqual(m['removals'][0]['id'],A)

    def test_tree_mismatch_and_duplicate_pagination_are_rejected(self):
        for problem in ['tree','duplicate']:
            api=API([doc()]); original=api.call
            def call(method,payload):
                r=original(method,payload)
                if problem=='tree' and method=='collections.documents' and payload['id']==C: r['data']=[]
                if problem=='duplicate' and method=='documents.list' and payload['collectionId']==C: r['data']*=2
                return r
            api.call=call
            with self.assertRaises(w.SyncError): w.capture(api)

    def test_full_metadata_pagination_includes_page_after_first_hundred(self):
        docs=[doc(f'00000000-0000-4000-8000-{i:012d}') for i in range(1,106)]
        api=API(docs); m,b=w.capture(api)
        self.assertEqual(m['documentCount'],105)
        self.assertIn('00000000-0000-4000-8000-000000000105',b)
        offsets=[p['offset'] for n,p in api.calls if n=='documents.list' and p['collectionId']==C]
        self.assertEqual(offsets,[0,100,0,100])

    def test_credential_payload_is_not_published_or_in_error(self):
        secret='ol_api_'+'a'*38
        with self.assertRaises(w.SyncError) as cm: w.capture(API([doc(text=secret)]))
        self.assertNotIn(secret,str(cm.exception))

    def test_snapshot_paths_immutable_and_pointer_hashes_match(self):
        with tempfile.TemporaryDirectory() as t:
            m,b=w.capture(API([doc()])); root=w.publish(Path(t),m,b)
            pointer=json.loads((Path(t)/'latest.json').read_bytes())
            self.assertEqual(hashlib.sha256((root/'manifest.json').read_bytes()).hexdigest(),pointer['manifestSha256'])
            self.assertEqual(hashlib.sha256((root/'knowledge.zip').read_bytes()).hexdigest(),pointer['archiveSha256'])
            before=(root/'manifest.json').read_bytes()
            w.publish(Path(t),m,b)
            self.assertEqual((root/'manifest.json').read_bytes(),before)

    def test_corrupt_existing_zip_is_not_endorsed_by_new_pointer(self):
        with tempfile.TemporaryDirectory() as t:
            m,b=w.capture(API([doc()])); root=w.publish(Path(t),m,b)
            prior=(Path(t)/'latest.json').read_bytes()
            (root/'knowledge.zip').write_bytes(b'not a ZIP')
            with self.assertRaises(w.SyncError): w.publish(Path(t),m,b)
            self.assertEqual((Path(t)/'latest.json').read_bytes(),prior)

    def test_oversize_snapshot_leaves_prior_pointer(self):
        with tempfile.TemporaryDirectory() as t:
            m,b=w.capture(API([doc()])); w.publish(Path(t),m,b)
            prior=(Path(t)/'latest.json').read_bytes()
            m,b=w.capture(API([doc(text='x'*50000,revision=2)]))
            with patch.object(w,'MAX_EXPANDED',10000,create=True):
                with self.assertRaises(w.SyncError): w.publish(Path(t),m,b)
            self.assertEqual((Path(t)/'latest.json').read_bytes(),prior)

if __name__=='__main__': unittest.main()
