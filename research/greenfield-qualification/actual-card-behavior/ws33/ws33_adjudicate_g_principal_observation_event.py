#!/usr/bin/env python3
"""Event-v21 adapter for the generic WS33 G principal-observation adjudicator."""
from __future__ import annotations
import base64
import ws33_adjudicate_g_principal_observation as base
import ws33_adjudicate_g_principal_observation_v5 as v5

def dec(x): return base64.b64decode(x,validate=True).decode('utf-8')
def load_cases_v21(path):
    out={}
    for n,line in enumerate(path.read_text().splitlines(),1):
        if not line: continue
        f=line.split('\t')
        if len(f)!=21: raise SystemExit(f"WS33_G_PRINCIPAL_OBSERVATION=FAIL event case ABI line {n}: columns={len(f)}")
        pid=f[1]; api=f[7]; script=dec(f[19]); hidden=f[15]=='1'; decision=f[18]=='1'
        profile,reason=v5.positive_profile_v5(api,script,hidden,decision)
        row={'ordinal':int(f[0]),'oracle_id':f[4],'api':api,'implementation':f[8],'hidden':hidden,'rng':f[16]=='1','replay':f[17]=='1','decision':decision,'profile':profile,'profile_reason':reason,'script':script,'case_abi':'G_SVAR_EVENT_V21'}
        if pid in out:
            prior=out[pid]; keys=('api','implementation','hidden','rng','replay','decision','profile','script')
            if any(prior[k]!=row[k] for k in keys): raise SystemExit(f"WS33_G_PRINCIPAL_OBSERVATION=FAIL duplicate event parents disagree for {pid}")
        else: out[pid]=row
    if not out: raise SystemExit('WS33_G_PRINCIPAL_OBSERVATION=FAIL empty event cases')
    return out

def load_summary_event(path):
    rows=[x.split('\t') for x in path.read_text().splitlines() if x]
    out={}
    for r in rows:
        if len(r)<20: raise SystemExit(f"WS33_G_PRINCIPAL_OBSERVATION=FAIL event summary columns={len(r)}")
        pid=r[0]
        if pid in out: raise SystemExit(f"WS33_G_PRINCIPAL_OBSERVATION=FAIL duplicate event summary path {pid}")
        # Generic adjudicator expects path at index 1; retain all event metrics at their native indexes.
        rr=list(r); rr[1]=pid; out[pid]=rr
    return out

def main():
    v5.regression_contract(); base.positive_profile=v5.positive_profile_v5; base.load_cases=load_cases_v21; base.load_summary=load_summary_event; base.main()
if __name__=='__main__': main()
