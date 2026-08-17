#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, re
from pathlib import Path

PACKAGE_ID="BT2_SEVEN_ROLE_TRAINING"
ROLE="Seven"
CHECKPOINT_SCHEMA="BT2_SEVEN_TRAINING_CHECKPOINT_V1"
H40=re.compile(r"^[0-9a-f]{40}$")
H64=re.compile(r"^[0-9a-f]{64}$")

class TrainingCheckpointError(ValueError): pass

def load_json(path:Path):
    def pairs(items):
        out={}
        for k,v in items:
            if k in out: raise TrainingCheckpointError(f"duplicate JSON key in {path}: {k}")
            out[k]=v
        return out
    def bad(v): raise TrainingCheckpointError(f"non-finite JSON value in {path}: {v}")
    try:
        return json.loads(path.read_text(encoding="utf-8"),object_pairs_hook=pairs,parse_constant=bad)
    except json.JSONDecodeError as e:
        raise TrainingCheckpointError(f"invalid JSON: {path}: {e}") from e

def digest(path:Path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1048576),b""): h.update(b)
    return h.hexdigest()

def relpath(s):
    if not isinstance(s,str) or not s: raise TrainingCheckpointError("path must be a nonempty string")
    p=Path(s)
    if p.is_absolute() or ".." in p.parts: raise TrainingCheckpointError(f"unsafe path: {s}")
    return p

def verify_package(root:Path):
    root=root.resolve(); mp=root/"TRAINING_MANIFEST.json"
    if not mp.is_file(): raise TrainingCheckpointError("TRAINING_MANIFEST.json missing")
    m=load_json(mp)
    if m.get("package_id")!=PACKAGE_ID: raise TrainingCheckpointError("wrong package_id")
    if not isinstance(m.get("role"),dict) or m["role"].get("identity")!=ROLE:
        raise TrainingCheckpointError("wrong role identity")
    version=m.get("training_package_version")
    if not isinstance(version,str) or not version: raise TrainingCheckpointError("training_package_version missing")
    files=m.get("files")
    if not isinstance(files,dict) or not files: raise TrainingCheckpointError("manifest files map missing/empty")
    folded={}; count=0
    for name,meta in files.items():
        rp=relpath(name); cf=name.casefold()
        if cf in folded and folded[cf]!=name:
            raise TrainingCheckpointError(f"case-colliding manifest paths: {folded[cf]} vs {name}")
        folded[cf]=name; p=root/rp
        try: st=p.lstat()
        except FileNotFoundError as e: raise TrainingCheckpointError(f"missing required file: {name}") from e
        if p.is_symlink() or not p.is_file(): raise TrainingCheckpointError(f"not a regular nonsymlink file: {name}")
        if not isinstance(meta,dict): raise TrainingCheckpointError(f"invalid metadata: {name}")
        eh,eb=meta.get("sha256"),meta.get("bytes")
        if not isinstance(eh,str) or not H64.fullmatch(eh): raise TrainingCheckpointError(f"invalid sha256 metadata: {name}")
        if not isinstance(eb,int) or eb<0: raise TrainingCheckpointError(f"invalid byte metadata: {name}")
        if st.st_size!=eb: raise TrainingCheckpointError(f"byte mismatch: {name}")
        if digest(p)!=eh: raise TrainingCheckpointError(f"sha256 mismatch: {name}")
        count+=1
    order=m.get("module_order")
    if not isinstance(order,list) or not order: raise TrainingCheckpointError("module_order missing/empty")
    ids=[]; paths=[]
    for n,e in enumerate(order,1):
        if not isinstance(e,dict) or e.get("order")!=n: raise TrainingCheckpointError("module_order must be contiguous from 1")
        mid,path=e.get("id"),e.get("path")
        if not isinstance(mid,str) or not mid or mid in ids: raise TrainingCheckpointError("module ids must be unique nonempty strings")
        relpath(path)
        if path in paths: raise TrainingCheckpointError("module paths must be unique")
        ids.append(mid); paths.append(path)
    return {"package_id":PACKAGE_ID,"role":ROLE,"version":version,"manifest_sha256":digest(mp),
            "verified_file_count":count,"module_ids":ids,"module_paths":paths}

def make_checkpoint(pkg,repo,commit,path):
    if not H40.fullmatch(commit): raise TrainingCheckpointError("source commit must be exact lowercase 40-hex SHA")
    return {"schema":CHECKPOINT_SCHEMA,
      "package":{"package_id":pkg["package_id"],"training_package_version":pkg["version"],
                 "role_identity":ROLE,"manifest_sha256":pkg["manifest_sha256"]},
      "training_source":{"repository":repo,"commit":commit,"path":path},
      "modules":[{"id":x,"status":"PENDING","evidence_ref":None} for x in pkg["module_ids"][:-1]],
      "qualification":{"module_id":pkg["module_ids"][-1],"response_completed_before_rubric":False,
                       "evaluator_outcome":"PENDING","critical_failures":[],"evaluation_evidence_ref":None},
      "operational_state_loaded_before_freeze":False,"base_status":"NOT_BASE_READY","notes":[]}

def verify_checkpoint(root:Path,cp_path:Path):
    pkg=verify_package(root); cp=load_json(cp_path)
    if cp.get("schema")!=CHECKPOINT_SCHEMA: raise TrainingCheckpointError("wrong checkpoint schema")
    p=cp.get("package")
    if not isinstance(p,dict): raise TrainingCheckpointError("checkpoint package section missing")
    expected={"package_id":pkg["package_id"],"training_package_version":pkg["version"],
              "role_identity":ROLE,"manifest_sha256":pkg["manifest_sha256"]}
    for k,v in expected.items():
        if p.get(k)!=v: raise TrainingCheckpointError(f"checkpoint package mismatch: {k}")
    src=cp.get("training_source")
    if not isinstance(src,dict) or not isinstance(src.get("repository"),str) or not src["repository"]:
        raise TrainingCheckpointError("training_source repository missing")
    if not isinstance(src.get("commit"),str) or not H40.fullmatch(src["commit"]):
        raise TrainingCheckpointError("training_source commit must be exact lowercase 40-hex SHA")
    if not isinstance(src.get("path"),str) or not src["path"]: raise TrainingCheckpointError("training_source path missing")
    expected_ids=pkg["module_ids"][:-1]; mods=cp.get("modules")
    if not isinstance(mods,list) or len(mods)!=len(expected_ids): raise TrainingCheckpointError("module checkpoint count mismatch")
    passed=[]
    for mid,e in zip(expected_ids,mods):
        if not isinstance(e,dict) or e.get("id")!=mid: raise TrainingCheckpointError(f"module order/id mismatch: {mid}")
        if e.get("status")!="PASS": raise TrainingCheckpointError(f"module not passed: {mid}")
        if not isinstance(e.get("evidence_ref"),str) or not e["evidence_ref"].strip():
            raise TrainingCheckpointError(f"module evidence_ref missing: {mid}")
        passed.append(mid)
    q=cp.get("qualification")
    if not isinstance(q,dict) or q.get("module_id")!=pkg["module_ids"][-1]: raise TrainingCheckpointError("qualification module mismatch")
    if q.get("response_completed_before_rubric") is not True: raise TrainingCheckpointError("qualification response-before-rubric not met")
    if q.get("evaluator_outcome")!="QUALIFICATION_PASS": raise TrainingCheckpointError("qualification is not QUALIFICATION_PASS")
    if not isinstance(q.get("critical_failures"),list) or q["critical_failures"]: raise TrainingCheckpointError("critical_failures must be empty")
    if not isinstance(q.get("evaluation_evidence_ref"),str) or not q["evaluation_evidence_ref"].strip():
        raise TrainingCheckpointError("evaluation_evidence_ref missing")
    if cp.get("operational_state_loaded_before_freeze") is not False: raise TrainingCheckpointError("operational state loaded before freeze")
    if cp.get("base_status")!="BASE_READY": raise TrainingCheckpointError("base_status is not BASE_READY")
    return {"status":"BASE_READY_MECHANICAL_GATE_PASS","package_id":pkg["package_id"],"version":pkg["version"],
            "manifest_sha256":pkg["manifest_sha256"],"source_commit":src["commit"],"modules_passed":passed,
            "qualification":"QUALIFICATION_PASS",
            "semantic_ceiling":"Mechanical integrity/record gate only; this script cannot grade semantic competence or turn self-authored claims into authority."}

def main():
    ap=argparse.ArgumentParser(description="Seven training package/checkpoint mechanical verifier")
    sp=ap.add_subparsers(dest="cmd",required=True)
    p=sp.add_parser("verify-package"); p.add_argument("package_dir")
    p=sp.add_parser("init-checkpoint"); p.add_argument("package_dir"); p.add_argument("output")
    p.add_argument("--source-repo",required=True); p.add_argument("--source-commit",required=True); p.add_argument("--source-path",required=True)
    p=sp.add_parser("verify-checkpoint"); p.add_argument("package_dir"); p.add_argument("checkpoint")
    a=ap.parse_args()
    try:
        if a.cmd=="verify-package": result=verify_package(Path(a.package_dir))
        elif a.cmd=="init-checkpoint":
            result=make_checkpoint(verify_package(Path(a.package_dir)),a.source_repo,a.source_commit,a.source_path)
            Path(a.output).write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
            result={"status":"CHECKPOINT_TEMPLATE_CREATED","output":str(Path(a.output))}
        else: result=verify_checkpoint(Path(a.package_dir),Path(a.checkpoint))
    except (TrainingCheckpointError,OSError) as e:
        print(json.dumps({"status":"FAIL_CLOSED","error":str(e)},sort_keys=True)); return 2
    print(json.dumps(result,sort_keys=True)); return 0

if __name__=="__main__": raise SystemExit(main())
