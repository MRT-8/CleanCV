import json
import threading
import urllib.request
import urllib.error
from cleancv.web import create_server
from test_core import sample


def test_local_web_api_auth_review_and_clear():
    server,token=create_server(0)
    thread=threading.Thread(target=server.serve_forever,daemon=True)
    thread.start()
    base=f'http://127.0.0.1:{server.server_port}'
    def call(path,data=None,authorized=True,origin=None):
        headers={}
        if authorized:headers['X-CleanCV-Token']=token
        if origin:headers['Origin']=origin
        if isinstance(data,dict):data=json.dumps(data).encode()
        request=urllib.request.Request(base+path,data=data,headers=headers)
        try:
            with urllib.request.urlopen(request,timeout=15) as r:return r.status,r.read(),r.headers
        except urllib.error.HTTPError as e:return e.code,e.read(),e.headers
    try:
        assert call('/')[0]==200
        assert call('/api/open',sample(),False)[0]==403
        assert call('/api/open',sample(),origin='https://evil.example')[0]==403
        status,body,_=call('/api/open',sample());assert status==200
        a=json.loads(body)
        assert call('/api/page/1.png?id='+a['document_sha256'])[0]==200
        payload={'document_id':a['document_sha256'],'regions':a['regions'],'reviewed':False}
        assert call('/api/clean',payload)[0]==400
        payload['reviewed']=True
        status,body,headers=call('/api/clean',payload)
        assert status==200 and body.startswith(b'%PDF')
        assert headers['Cache-Control']=='no-store'
        assert call('/api/clear',{})[0]==200
        assert call('/api/page/1.png?id='+a['document_sha256'])[0]==400
    finally:
        server.shutdown();server.server_close();thread.join(timeout=5)
