from pathlib import Path
import argparse,importlib.util,json,subprocess,tempfile,zipfile,io
from unittest.mock import patch
repo=Path('/home/moeen/work/ci479-mage-c14-20261004')
dest=repo/'research/c14-reference-20261004'
old=subprocess.check_output(['git','-C',str(repo),'show','2ae9df6f9b1326f61f06b9a22dac5c050f8cd041:.github/ci/mtgjson_reference.py'])
results={}
with tempfile.TemporaryDirectory() as td:
 root=Path(td)
 old_path=root/'old.py';old_path.write_bytes(old)
 for epoch,path in [('before',old_path),('after',repo/'.github/ci/mtgjson_reference.py')]:
  spec=importlib.util.spec_from_file_location('probe_'+epoch,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
  case=root/epoch;case.mkdir()
  for name in m.FILES:
   with zipfile.ZipFile(case/name,'w') as z:z.writestr(name.removesuffix('.zip'),json.dumps({'meta':{'date':'2026-10-04','version':'5.3.0+20261004'},'data':{}}))
  pin_path=case/'pin.json';m.cmd_pin(argparse.Namespace(dir=str(case),repo='moeendres-png/mage',out=str(pin_path)))
  pin=json.loads(pin_path.read_text())
  with zipfile.ZipFile(case/'AtomicCards.json.zip','w') as z:z.writestr('AtomicCards.json',json.dumps({'meta':{'date':'2026-10-03','version':'older'},'data':{}}))
  pin['files']['AtomicCards.json.zip']={'sha256':m.sha256(case/'AtomicCards.json.zip'),'bytes':(case/'AtomicCards.json.zip').stat().st_size};pin_path.write_text(json.dumps(pin))
  # Serve exactly the declared byte identities, so refusal cannot be attributed
  # to network, missing inputs or a digest mismatch.
  def fetch(url,**kwargs):return io.BytesIO((case/url.rsplit('/',1)[1]).read_bytes())
  receipt=case/'receipt.json'
  with patch.object(m.urllib.request,'urlopen',side_effect=fetch):status=m.cmd_fetch(argparse.Namespace(pin=str(pin_path),dir=str(case),receipt=str(receipt)))
  results[epoch]={'exit':status,'receipt':json.loads(receipt.read_text())}
assert results['before']['exit']==0 and results['after']['exit']!=0
dest.joinpath('ATOMIC_META_BEFORE_AFTER.json').write_text(json.dumps({'evidence_class':'SYNTHETIC','before_source':'2ae9df6f9b1326f61f06b9a22dac5c050f8cd041','observation':'Real fetch/verify/receipt code with synthetic ZIPs and HTTPS response substituted by exact declared bytes. No Rules/card-behavior credit.','results':results},indent=2)+'\n')
print(json.dumps(results,indent=2))
