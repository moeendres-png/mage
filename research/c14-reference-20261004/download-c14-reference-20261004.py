from pathlib import Path
import urllib.request,json,hashlib,re,zipfile
root=Path('/home/moeen/work/c14-reference-20261004');root.mkdir(exist_ok=True)
records={}
for name in ('AllPrintings.json.zip','AtomicCards.json.zip'):
 url='https://mtgjson.com/api/v5/'+name
 def request(address):return urllib.request.urlopen(urllib.request.Request(address,headers={'User-Agent':'xmage-verify-reference-refresh'}),timeout=300)
 with request(url+'.sha256') as response:expected=response.read().decode().strip()
 assert re.fullmatch('[0-9a-f]{64}',expected)
 path=root/name
 if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=expected:
  with request(url) as response,path.open('wb') as out:
   while block:=response.read(1<<20):out.write(block)
 actual=hashlib.sha256(path.read_bytes()).hexdigest();assert actual==expected,(name,actual,expected)
 with zipfile.ZipFile(path) as archive:
  assert archive.namelist()==[name.removesuffix('.zip')]
  with archive.open(archive.namelist()[0]) as member:head=member.read(65536).decode()
  meta=json.loads(re.search(r'"meta"\s*:\s*(\{[^{}]*\})',head).group(1))
 records[name]={'sha256':actual,'bytes':path.stat().st_size,'meta':meta,'url':url,'upstream_checksum_url':url+'.sha256'}
 print(name,json.dumps(records[name]),flush=True)
(root/'DOWNLOAD.json').write_text(json.dumps({'source':'MTGJSON official HTTPS and published SHA256','files':records},indent=2)+'\n')
