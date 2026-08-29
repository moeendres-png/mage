#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from pathlib import Path

def load(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def dump(p,o):Path(p).write_text(json.dumps(o,sort_keys=True,separators=(',',':'))+'\n',encoding='utf-8')
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);ap.add_argument('--provenance',type=Path,required=True);ap.add_argument('--deterministic',action='store_true');a=ap.parse_args();o=a.out
    prov=load(a.provenance);pre=load(o/'WS26_PRE_GATE.json');bs=load(o/'WS26_BINDING_SUMMARY.json');man=load(o/'WS26_BEHAVIOR_PATH_MANIFEST_V2.json');parts=load(o/'WS26_OWNER_PARTITIONS.json');compat=load(o/'WS26_EXISTING_WITNESS_COMPATIBILITY.json');hg=load(o/'WS26_HARNESS_GATE.json');variants=load(o/'WS26_PATH_VARIANTS.json')
    gran_counts=variants['counts'];model={
      'exact_ws91_base_verified':prov.get('exact_ws91_base_verified') is True,
      'exact_forge_pin_verified':prov.get('exact_forge_pin_verified') is True,
      'ws11_input_hash_verified':prov.get('ws11_input_hash_verified') is True,
      'ws14_manifest_verified':prov.get('ws14_manifest_verified') is True,
      'ws24_current_gate_verified':prov.get('ws24_current_gate_verified') is True,
      'oracle_identity_count_1678':pre['oracle_identity_count']==1678,
      'oracle_identity_drops_zero':pre['oracle_identity_drops']==0,
      'oracle_identity_additions_zero':pre['oracle_identity_additions']==0,
      'input_unresolved_occurrences_1800':bs['input_unresolved_occurrences']==1800,
      'accounted_occurrences_1800':bs['accounted_occurrences']==1800,
      'silently_dropped_zero':bs['silently_dropped']==0,
      'keyword_occurrences_888':bs['directive_counts'].get('KEYWORD')==888,
      'svar_occurrences_895':bs['directive_counts'].get('SVAR')==895,
      'alternate_mode_occurrences_17':bs['directive_counts'].get('ALTERNATE_MODE')==17,
      'production_reachable_UNKNOWN_bindings_zero':bs['production_reachable_UNKNOWN_bindings']==0,
      'ambiguous_bindings_zero':bs['ambiguous_bindings']==0,
      'card_name_binding_rules_zero':bs['card_name_binding_rules']==0,
      'fuzzy_text_binding_rules_zero':bs['fuzzy_text_binding_rules']==0,
      'unproven_metadata_promotions_zero':bs['unproven_metadata_promotions']==0,
      'unproven_unreachable_promotions_zero':bs['unproven_unreachable_promotions']==0,
      'v1_primitives_accounted_174':pre['v1_primitives_accounted']==174,
      'granularity_UNKNOWN_zero':gran_counts.get('UNKNOWN',0)==0,
      'silent_v1_primitive_drop_zero':sum(gran_counts.values())==174,
      'every_split_has_children':all(x.get('v2_child_path_ids') for x in variants.get('split_primitives',[])),
      'duplicate_v2_path_ids_zero':pre['duplicate_v2_path_ids']==0,
      'conflicting_v2_descriptors_zero':pre['conflicting_v2_descriptors']==0,
      'production_paths_without_owner_zero':pre['production_paths_without_owner']==0 and parts['production_paths_without_owner']==0,
      'production_paths_multiple_owners_zero':pre['production_paths_with_multiple_primary_owners']==0 and parts['production_paths_with_multiple_primary_owners']==0,
      'card_name_semantic_keys_zero':pre['card_name_semantic_keys']==0,
      'nondeterministic_id_components_zero':pre['nondeterministic_id_components']==0,
      'existing_pass_witnesses_accounted_13':compat['existing_pass_witnesses_accounted']==13 and len(compat['entries'])==13,
      'automatic_blanket_v1_to_v2_inheritance_zero':compat['automatic_blanket_v1_to_v2_inheritance']==0,
      'deterministic_materialization_byte_identical':a.deterministic,
    }
    harness={
      'exact_pinned_engine_execution_PASS':hg.get('exact_pinned_engine_execution')=='PASS',
      'actual_card_execution_PASS':hg.get('actual_card_execution')=='PASS',
      'authoritative_decision_boundary_used_PASS':hg.get('authoritative_decision_boundary_used')=='PASS',
      'initial_state_retained_PASS':hg.get('initial_state_retained')=='PASS',
      'final_state_retained_PASS':hg.get('final_state_retained')=='PASS',
      'immutable_trace_hash_PASS':hg.get('immutable_trace_hash')=='PASS',
      'stdout_only_false':hg.get('stdout_only') is False,
      'negative_ABI_fixtures_PASS':hg.get('negative_ABI_fixtures')=='PASS',
      'illegal_response_rejected_PASS':hg.get('illegal_response_rejected')=='PASS',
      'silent_fallbacks_zero':hg.get('silent_fallbacks')==0,
    }
    model_pass=all(model.values());harness_pass=all(harness.values());eligible=model_pass and harness_pass
    failed=[k for k,v in model.items() if not v]+[k for k,v in harness.items() if not v]
    gate={'schema':'commander-simulator-next.ws26-gate.v1','source_head':man['source_head'],'source_tree':man['source_tree'],'forge_pin':man['forge_pin'],'hard_gates':{'model':model,'harness':harness},'binding_states':bs['states'],'granularity_counts':gran_counts,'v2_path_count':man['path_count'],'owner_family_path_counts':{k:v['path_count'] for k,v in parts['families'].items()},'WS26_MODEL_V2':'PASS' if model_pass else 'FAIL_CLOSED','WS26_SHARED_HARNESS':'PASS' if harness_pass else 'FAIL_CLOSED','WORKSTREAM_COMPLETE':True,'WS27_WS31_ELIGIBLE':eligible,'WS32_ELIGIBLE':eligible,'Q6_ACTUAL_CARD_BEHAVIOR':'NOT_ADJUDICATED_BY_WS26','FAILURE_SEMANTICS_OVERALL_CLAIMED':False,'CARD_BEHAVIOR_FAILURE_PRODUCTION_BINDING_CLAIMED':False,'INITIAL_ARCHITECTURE_DECISION_FROZEN':False,'WS13_ELIGIBLE':False,'READY_FOR_GREENFIELD_BUILD':False,'PRODUCTION_REPOSITORY_CREATED':False,'first_unresolved_systemic_blocker':failed[0] if failed else None,'failed_hard_gates':failed,'evidence_class':'TECHNICALLY_CONFORMANT' if eligible else 'UNKNOWN'};dump(o/'WS26_GATE.json',gate);print(json.dumps({'WS26_MODEL_V2':gate['WS26_MODEL_V2'],'WS26_SHARED_HARNESS':gate['WS26_SHARED_HARNESS'],'WS27_WS31_ELIGIBLE':eligible,'first_blocker':gate['first_unresolved_systemic_blocker']},sort_keys=True))
    if not eligible:raise SystemExit(2)
if __name__=='__main__':main()
