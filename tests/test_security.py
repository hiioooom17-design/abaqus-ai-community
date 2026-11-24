import importlib.util, sys, types, unittest, pathlib, threading, socket, json, os, uuid, queue
from unittest.mock import patch
root=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'payload/app'))
from abaqus_mcp_bridge.client import AbaqusBridgeClient
from abaqus_mcp_bridge.protocol import send_message,read_message
class Form:
    ID_LAST=10
    def __init__(self,*a): pass
fake=types.ModuleType('abaqusGui'); fake.AFXForm=Form; fake.AFXMode=types.SimpleNamespace(ID_ACTIVATE=1); fake.SEL_COMMAND=1; fake.SEL_TIMEOUT=2; fake.FXMAPFUNC=lambda *a:None
fake.getAFXApp=lambda:types.SimpleNamespace(getAFXMainWindow=lambda:types.SimpleNamespace(getPluginToolset=lambda:types.SimpleNamespace(registerGuiMenuButton=lambda **kw:None)))
fake.sendCommand=lambda *a:None; fake.showAFXErrorDialog=lambda *a:None
with patch.dict(sys.modules,{'abaqusGui':fake}):
    spec=importlib.util.spec_from_file_location('test_gui',root/'payload/app/abaqus_mcp_bridge/gui_plugin.py'); gui=importlib.util.module_from_spec(spec); spec.loader.exec_module(gui)
COMMUNITY=root.name=='Community' or 'Community' in (root/'README_EN.md').read_text().splitlines()[0]
class SecurityTests(unittest.TestCase):
    def setUp(self):
        gui._AUTH_TOKEN='a'*64; gui._REQUESTS=queue.Queue(); gui._DISPATCHER=object()
        self.server=gui.McpGuiServer(('127.0.0.1',0),gui.McpGuiHandler)
        self.thread=threading.Thread(target=self.server.serve_forever,kwargs={'poll_interval':.01},daemon=True); self.thread.start()
        self.addCleanup(self.server.server_close); self.addCleanup(self.thread.join,1); self.addCleanup(self.server.shutdown)
    def req(self,**kw):
        payload={'id':str(uuid.uuid4()),'method':'ping','params':{},'token':'a'*64};payload.update(kw)
        with socket.create_connection(self.server.server_address,timeout=1) as s:
            send_message(s,payload);return read_message(s)
    def test_wrong_token(self):
        self.assertFalse(self.req(token='b'*64)['ok']);self.assertTrue(gui._REQUESTS.empty())
    def test_missing_token(self):
        self.assertFalse(self.req(token=None)['ok']);self.assertTrue(gui._REQUESTS.empty())
    def test_nonascii_token(self):
        self.assertFalse(self.req(token='é'*64)['ok']);self.assertTrue(gui._REQUESTS.empty())
    def test_unknown_method(self):
        self.assertFalse(self.req(method='unsupported')['ok']);self.assertTrue(gui._REQUESTS.empty())
    def test_nan_timeout(self):
        self.assertFalse(self.req(params={'timeout':'nan'})['ok']);self.assertTrue(gui._REQUESTS.empty())
    def test_invalid_params(self):
        self.assertFalse(self.req(params='invalid')['ok']);self.assertTrue(gui._REQUESTS.empty())
    def test_invalid_id(self):
        self.assertFalse(self.req(id='bad')['ok']);self.assertTrue(gui._REQUESTS.empty())
    def test_authenticated_ping(self):
        def consume():
            item=gui._REQUESTS.get(timeout=2);item.result={'models':['test']};item.event.set()
        t=threading.Thread(target=consume,daemon=True);t.start()
        with patch.dict(os.environ,{'ABAQUS_MCP_TOKEN':'a'*64}):
            result=AbaqusBridgeClient(port=self.server.server_address[1],timeout=1).ping()
        t.join(1);self.assertEqual(result['models'],['test'])
    def test_non_loopback_client(self):
        with self.assertRaises(ValueError):AbaqusBridgeClient(host='192.0.2.1').ping()
    def test_uninstalled_client(self):
        with patch.dict(os.environ,{'ABAQUS_MCP_TOKEN':''}):
            with self.assertRaises(ValueError):AbaqusBridgeClient().ping()
    def test_uninstalled_server(self):
        gui._AUTH_TOKEN='__INSTALL_TOKEN_PLACEHOLDER__'
        with self.assertRaises(RuntimeError):gui.start_gui_agent()
    def test_edition_execution_policy(self):
        if COMMUNITY:
            self.assertFalse(self.req(method='execute',params={'code':'result=1'})['ok']);self.assertTrue(gui._REQUESTS.empty())
            with self.assertRaises(ValueError),patch.dict(os.environ,{'ABAQUS_MCP_TOKEN':'a'*64}):AbaqusBridgeClient().request('execute')
            with self.assertRaises(ValueError):gui._handle_on_gui_thread(gui.GuiRequest('execute',{}))
        else:
            def consume():
                item=gui._REQUESTS.get(timeout=2);item.result={'method':item.method};item.event.set()
            t=threading.Thread(target=consume,daemon=True);t.start(); self.assertEqual(self.req(method='execute',params={'code':'result=1'})['result']['method'],'execute');t.join(1)
    def test_manifest(self):
        import hashlib
        manifest=json.loads((root/'SHA256.json').read_text())
        for name,digest in manifest.items():self.assertEqual(hashlib.sha256((root/name).read_bytes()).hexdigest(),digest)
