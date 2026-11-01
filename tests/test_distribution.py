import unittest,tempfile,json,hashlib,io,sys
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'app'));sys.path.insert(0,str(ROOT/'tools'))
from updater import *
from make_manifest import make
from build_release import validate,source_archive

class Response(io.BytesIO):
    def __init__(self,data,url):super().__init__(data);self.url=url
    def geturl(self):return self.url

class DistributionTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
        self.binary=b'MZ'+b'test setup payload'*40;self.url='https://updates.example.org/Setup.exe'
        self.data=dict(product_id=PRODUCT_ID,version='2.2.0',platform='windows-x64',download_url=self.url,sha256=hashlib.sha256(self.binary).hexdigest(),size=len(self.binary),notes='New release')
    def test_release_version_and_product(self):
        self.assertTrue(validate_release(self.data,{'updates.example.org'})['newer'])
        self.assertFalse(validate_release(dict(self.data,version=VERSION),{'updates.example.org'})['newer'])
        self.assertFalse(validate_release(dict(self.data,version='1.0.0'),{'updates.example.org'})['newer'])
        for changed in [dict(product_id='other'),dict(platform='linux'),dict(size=True),dict(size=MAX_INSTALLER+1),dict(sha256='no'),dict(version='2.bad'),dict(download_url='https://evil.example.org/setup.exe')]:
            with self.subTest(changed=changed),self.assertRaises(UpdateError):validate_release(dict(self.data,**changed),{'updates.example.org'})
    def test_https_credentials_redirects(self):
        for url in ['http://updates.example.org','file:///tmp/file','https://user:pass@example.org','https://example.org:1234/path']:
            with self.subTest(url=url),self.assertRaises(UpdateError):https_host(url)
        guard=TrustedRedirect({'updates.example.org'})
        with self.assertRaises(UpdateError):guard.redirect_request(None,None,302,'',{},'https://evil.example.org/file')
    def test_check_manifest_and_limits(self):
        config=dict(manifest_url='https://updates.example.org/update.json',allowed_download_hosts=[])
        with patch('updater.open_trusted',return_value=Response(json.dumps(self.data).encode(),config['manifest_url'])):
            self.assertEqual(check_release(config)['version'],'2.2.0')
        for content in [b'NOT JSON',b'x'*(MAX_MANIFEST+1)]:
            with patch('updater.open_trusted',return_value=Response(content,config['manifest_url'])),self.assertRaises(UpdateError):check_release(config)
        with self.assertRaises(UpdateError):check_release(dict(manifest_url='',allowed_download_hosts=[]))
    def test_download_verified_progress(self):
        events=[]
        with patch('updater.open_trusted',return_value=Response(self.binary,self.url)):
            target=download_release(self.data,self.root,{'updates.example.org'},lambda f,n:events.append((f,n)))
        self.assertEqual(target.read_bytes(),self.binary);self.assertEqual(events[-1],(1,len(self.binary)))
        self.assertFalse(list(self.root.glob('*.part')))
    def test_failed_or_cancelled_download_no_partial(self):
        for payload,cancelled in [(self.binary[:-1],lambda:False),(self.binary+b'extra',lambda:False),(b'X'*len(self.binary),lambda:False),(self.binary,lambda:True)]:
            with self.subTest(size=len(payload)),patch('updater.open_trusted',return_value=Response(payload,self.url)),self.assertRaises(UpdateError):download_release(self.data,self.root,{'updates.example.org'},cancelled=cancelled)
            self.assertFalse(list(self.root.iterdir()))
    def test_release_manifest_generated_from_actual_setup(self):
        installer=self.root/'setup.exe';installer.write_bytes(self.binary)
        result=make(installer,self.url,'Notes',self.root/'update.json');data=json.loads(result.read_text())
        self.assertEqual(data['size'],len(self.binary));self.assertEqual(data['sha256'],hashlib.sha256(self.binary).hexdigest());self.assertEqual(data['version'],VERSION)
    def test_package_models_and_sources(self):
        self.assertTrue(validate());archive=self.root/'sources.zip';source_archive(archive)
        import zipfile
        with zipfile.ZipFile(archive) as z:
            self.assertIsNone(z.testzip());self.assertIn('Convertitore_Universale/Setup.bat',z.namelist());self.assertTrue(any('eng.traineddata' in p for p in z.namelist()))
            self.assertFalse(any('__pycache__' in p or '/.venv/' in p for p in z.namelist()))

    def test_download_rechecked_before_launch(self):
        path=self.root/'setup.exe';path.write_bytes(self.binary);self.assertTrue(verify_installer(path,self.data))
        path.write_bytes(b'X'*len(self.binary))
        with self.assertRaises(UpdateError):verify_installer(path,self.data)
