import base64, hashlib, json, tempfile, unittest, uuid
from pathlib import Path
from materialize_card_manifest import materialize

A="00000000-0000-0000-0000-000000000001"
B="00000000-0000-0000-0000-000000000002"

class T(unittest.TestCase):
 def setUp(s):
  s.t=tempfile.TemporaryDirectory(); s.r=Path(s.t.name)
  s.i=s.r/'index.json'; s.i.write_text(json.dumps({'source_head':'h','source_tree':'t','oracle_identity_count':2,'cards':[{'oracle_id':A,'name':'Alpha'},{'oracle_id':B,'name':'Beta'}]}))
 def tearDown(s): s.t.cleanup()
 def w(s,p,v):
  q=s.r/p; q.parent.mkdir(parents=True,exist_ok=True); q.write_text(json.dumps(v)); return q
 def union_chunk(s, rows):
  raw=b''.join(uuid.UUID(oid).bytes+bytes([mask]) for oid,mask in rows)
  p=s.r/'f/union.b64'; p.parent.mkdir(parents=True,exist_ok=True); p.write_text(base64.b64encode(raw).decode()+'\n')
  return {'path':'f/union.b64','encoding':'uuid16-mask8-base64-v1','count':len(rows),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
 def frag(s,sc,oid,name):
  return {'status':'PASS','source_class':sc,'provenance':{'x':1},'record_count':1,'expected_record_count':1,'distinct_oracle_ids':1,'resolution_policy':{'fuzzy_matching':False,'synthetic_promotion':False},'records':[{'oracle_id':oid,'oracle_name':name,'quantity':1}]}
 def compact(s,sc):
  return {'status':'PASS','source_class':sc,'provenance':{'x':1},'record_count':1,'expected_record_count':1,'distinct_oracle_ids':1,'slot_count':1,'expected_slot_count':1,'resolution_policy':{'fuzzy_matching':False,'synthetic_promotion':False},'resolution_evidence':{'resolved_records':1,'missing':0,'ambiguous':0},'membership_authority':'ACTUAL_CARD_REQUIREMENT_UNION.source_class_mask'}
 def unk(s):
  return {'status':'PASS','source_class':'unknown_real_opponents','provenance':{'x':1},'synthetic_promotion':False,'oracle_id_promotion_performed':False,'slot_count':1,'slots':[{'slot_id':'u1','resolution_status':'UNKNOWN','oracle_id':None}]}
 def setup(s,target=2):
  chunk=s.union_chunk([(A,1),(B,2)])
  s.w('m.json',{'oracle_union':{'target_count':target,'source_classes':['operational_own','rogshai','unknown_real_opponents'],'known_source_files':['f/o.json','f/r.json'],'unknown_source_files':['f/u.json'],'official_precon_reconciliation':'f/x.json','canonical_union_chunks':[chunk]}})
  s.w('f/o.json',s.compact('operational_own')); s.w('f/r.json',s.frag('rogshai',B,'Beta')); s.w('f/u.json',s.unk()); s.w('f/x.json',{'status':'PASS','deck_count':11,'all_100_slots':True})
 def runm(s): return materialize(s.r/'m.json',s.i,'h','t','forge')
 def test_canonical_union_masks_drive_compact_membership(s):
  s.setup(); r=s.runm(); s.assertEqual(('PASS',2,1),(r['status'],r['computed_oracle_id_count'],r['unknown_real_opponent_slots']))
 def test_union_chunk_hash_tamper_fails(s):
  s.setup(); (s.r/'f/union.b64').write_text('bad\n'); s.assertEqual('FAIL',s.runm()['status'])
 def test_record_membership_must_match_union_mask(s):
  s.setup(); s.w('f/r.json',s.frag('rogshai',A,'Alpha')); s.assertEqual('FAIL',s.runm()['status'])
 def test_union_id_not_in_pin_fails(s):
  s.setup(); C='00000000-0000-0000-0000-000000000003'; chunk=s.union_chunk([(A,1),(C,2)]); m=json.loads((s.r/'m.json').read_text()); m['oracle_union']['canonical_union_chunks']=[chunk]; s.w('m.json',m); r=s.runm(); s.assertEqual('FAIL',r['status']); s.assertFalse(r['gate']['all_ids_in_pinned_index'])
 def test_unknown_promotion_fails(s):
  s.setup(); u=s.unk(); u['slots'][0]['oracle_id']=A; s.w('f/u.json',u); s.assertEqual('FAIL',s.runm()['status'])
 def test_target_fails(s):
  s.setup(3); s.assertFalse(s.runm()['gate']['target_count_equal'])
 def test_missing_source_not_run(s):
  s.setup(); (s.r/'f/r.json').unlink(); s.assertEqual('NOT_RUN',s.runm()['status'])

if __name__=='__main__': unittest.main()
