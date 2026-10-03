#!/usr/bin/env python3
"""Run candidate code under a separate OS identity that cannot write trusted state.

Trust boundary: trusted default-branch code. This is the answer to "candidate
Maven and candidate tests run as the same user that owns the validator": they no
longer do.

Every candidate execution (the Maven build, per-module classpath resolution and
the JVM that executes candidate test bytecode) runs as the dedicated
unprivileged account ``CANDIDATE_USER``:

* through ``sudo -n -u CANDIDATE_USER -- env -i ...`` with an allowlisted
  environment, so no ``GITHUB_ENV`` / ``GITHUB_PATH`` / ``GITHUB_OUTPUT`` /
  ``ACTIONS_*`` handle or runner variable reaches candidate code;
* in a sandbox directory owned by that account, holding a ``git archive`` export
  of the exact locked candidate commit (never a working tree another step
  touched);
* with every candidate process killed after each execution and the kill
  verified, so no daemon survives into a later trusted step;
* only after a probe, run AS the candidate account, has shown that none of the
  trusted paths (validator checkout, evidence, workflow command files, the
  trusted bundle, the runner's Maven cache) nor any of their ancestors can be
  written by it. A writable trusted path fails closed.

The account must be separate: not root, not the invoking user, and not a member
of a group that implies root (sudo, admin, wheel, docker, adm, lxd).

Integrity is then verified, not assumed: ``verify`` re-derives every trusted
qualification file from the trusted commit's Git blobs (``git hash-object``
against ``git ls-tree``), rejects untracked files in that directory (a planted
module would shadow an import), re-checks every sealed evidence digest, and
re-checks that no candidate process is alive. Any mismatch is a
``trusted_state_integrity_violation``, which ``qualify.py`` turns into FAIL.
"""

from __future__ import annotations

import argparse
import grp
import hashlib
import json
import os
import pwd
import shutil
import stat
import subprocess
import sys
import tempfile
import time
from pathlib import Path

SCHEMA_PREPARE = "mage.candidate-qualification.sandbox-prepare/1"
SCHEMA_RUN = "mage.candidate-qualification.sandbox-run/1"
SCHEMA_INTEGRITY = "mage.candidate-qualification.integrity/1"
SCHEMA_SEAL = "mage.candidate-qualification.evidence-seal/1"

CANDIDATE_USER = "c12cand"
PRIVILEGED_GROUPS = ("sudo", "admin", "wheel", "docker", "adm", "lxd", "root")
# Variables a candidate process may see. Nothing else crosses the boundary.
ENV_ALLOWLIST = ("LANG", "LC_ALL", "TZ", "MAVEN_OPTS", "JAVA_HOME")
REAP_TIMEOUT_SECONDS = 15


class SandboxError(RuntimeError):
    pass


def _priv(cmd: list[str]) -> list[str]:
    return list(cmd) if os.geteuid() == 0 else ["sudo", "-n", *cmd]


def _run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, check=False, **kwargs)


def _must(cmd: list[str], what: str, **kwargs) -> subprocess.CompletedProcess:
    proc = _run(cmd, **kwargs)
    if proc.returncode != 0:
        raise SandboxError("{} failed ({}): {}".format(what, proc.returncode, (proc.stderr or proc.stdout).strip()[:600]))
    return proc


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


# ---------------------------------------------------------------------------
# identity


def ensure_user(user: str, home: Path) -> pwd.struct_passwd:
    try:
        entry = pwd.getpwnam(user)
    except KeyError:
        _must(_priv(["mkdir", "-p", str(home.parent)]), "create sandbox parent")
        _must(
            _priv(["useradd", "--create-home", "--home-dir", str(home), "--shell", "/bin/sh", "--user-group", user]),
            "create candidate account",
        )
        entry = pwd.getpwnam(user)
    assert_separate_identity(entry)
    return entry


def assert_separate_identity(entry: pwd.struct_passwd) -> None:
    if entry.pw_uid == 0:
        raise SandboxError("candidate account is root")
    if entry.pw_uid == os.geteuid():
        raise SandboxError("candidate account is the trusted invoking user")
    memberships = {g.gr_name for g in grp.getgrall() if entry.pw_name in g.gr_mem}
    try:
        memberships.add(grp.getgrgid(entry.pw_gid).gr_name)
    except KeyError:
        pass
    privileged = sorted(memberships & set(PRIVILEGED_GROUPS))
    if privileged:
        raise SandboxError("candidate account is in privileged group(s) {}".format(",".join(privileged)))
    sudo = _run(_priv(["sudo", "-n", "-l", "-U", entry.pw_name]))
    if sudo.returncode == 0 and "may run the following" in sudo.stdout:
        raise SandboxError("candidate account has sudo rights")


def candidate_environment(home: Path, extra: dict | None = None) -> list[str]:
    java = shutil.which("java")
    mvn = shutil.which("mvn")
    path_parts = []
    for tool in (java, mvn):
        if tool:
            parent = str(Path(tool).resolve().parent)
            if parent not in path_parts:
                path_parts.append(parent)
    path_parts += ["/usr/local/bin", "/usr/bin", "/bin"]
    env = {"HOME": str(home), "PATH": ":".join(path_parts), "LANG": "C.UTF-8"}
    for key in ENV_ALLOWLIST:
        if os.environ.get(key):
            env[key] = os.environ[key]
    # Java takes user.home from the passwd entry, not $HOME; pin it so Maven's
    # local repository is the sandbox's, whatever the account's home says.
    env["MAVEN_OPTS"] = " ".join(filter(None, [env.get("MAVEN_OPTS", ""), "-Duser.home={}".format(home)]))
    env.update(extra or {})
    return ["{}={}".format(k, v) for k, v in sorted(env.items())]


def candidate_command(user: str, home: Path, cwd: Path, cmd: list[str], extra_env: dict | None = None) -> list[str]:
    # env -i: the candidate starts from an empty environment. sh only changes
    # directory; the candidate command is exec'd with its own argv.
    return [
        "sudo", "-n", "-u", user, "--",
        "/usr/bin/env", "-i", *candidate_environment(home, extra_env),
        "/bin/sh", "-c", 'cd -- "$1" && shift && exec "$@"', "c12-sandbox", str(cwd), *cmd,
    ]


def alive(user: str) -> list[str]:
    proc = _run(["pgrep", "-u", user, "-a"])
    return [line for line in proc.stdout.splitlines() if line.strip()]


def reap(user: str) -> None:
    deadline = time.monotonic() + REAP_TIMEOUT_SECONDS
    while True:
        _run(_priv(["pkill", "-KILL", "-u", user]))
        survivors = alive(user)
        if not survivors:
            return
        if time.monotonic() > deadline:
            raise SandboxError("candidate processes survived the kill: {}".format("; ".join(survivors[:5])))
        time.sleep(0.2)


def run_candidate(user: str, home: Path, cwd: Path, cmd: list[str], timeout: int | None = None,
                  extra_env: dict | None = None, stdin_bytes: bytes | None = None) -> subprocess.CompletedProcess:
    reap(user)
    # Output goes to trusted-owned files, not pipes: a candidate daemon that
    # inherits a pipe would otherwise hold the trusted runner open until it
    # chose to exit. Only the direct child is waited for; everything else the
    # candidate started is killed by reap().
    with tempfile.TemporaryFile() as out, tempfile.TemporaryFile() as err, tempfile.TemporaryFile() as feed:
        # stdin is an unlinked trusted-owned file: readable only through the
        # inherited descriptor, never by path.
        feed.write(stdin_bytes or b"")
        feed.seek(0)
        child = subprocess.Popen(candidate_command(user, home, cwd, cmd, extra_env),
                                 cwd="/", stdin=feed, stdout=out, stderr=err)
        try:
            returncode = child.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            reap(user)
            child.kill()
            child.wait()
            raise SandboxError("candidate execution timed out after {}s".format(timeout))
        reap(user)
        out.seek(0)
        err.seek(0)
        stdout = out.read().decode("utf-8", errors="replace")
        stderr = err.read().decode("utf-8", errors="replace")
    return subprocess.CompletedProcess(child.args, returncode, stdout, stderr)


# ---------------------------------------------------------------------------
# staging


def stage_readonly(src: Path, dest: Path) -> None:
    """Copy trusted material to a root-owned location the candidate can only read."""
    _must(_priv(["rm", "-rf", str(dest)]), "clear trusted bundle")
    _must(_priv(["mkdir", "-p", str(dest.parent)]), "create trusted bundle parent")
    _must(_priv(["chown", "root:root", str(dest.parent)]), "own trusted bundle parent")
    _must(_priv(["chmod", "0755", str(dest.parent)]), "mode trusted bundle parent")
    _must(_priv(["cp", "-a", str(src), str(dest)]), "copy trusted bundle")
    _must(_priv(["chown", "-R", "root:root", str(dest)]), "own trusted bundle")
    _must(_priv(["chmod", "-R", "u=rwX,go=rX", str(dest)]), "mode trusted bundle")


def stage_candidate(user: str, src: Path, dest: Path) -> None:
    """Hand the exact-SHA export to the candidate account."""
    _must(_priv(["rm", "-rf", str(dest)]), "clear candidate tree")
    _must(_priv(["mkdir", "-p", str(dest.parent)]), "create candidate parent")
    _must(_priv(["cp", "-a", str(src), str(dest)]), "copy candidate tree")
    _must(_priv(["chown", "-R", "{}:".format(user), str(dest)]), "own candidate tree")
    _must(_priv(["chmod", "-R", "a+rX", str(dest)]), "mode candidate tree")


def export_commit(repo: Path, sha: str, dest: Path) -> None:
    """Materialise an exact commit from the trusted object store."""
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    archive = subprocess.run(["git", "-C", str(repo), "archive", "--format=tar", sha], capture_output=True, check=False)
    if archive.returncode != 0:
        raise SandboxError("git archive {} failed: {}".format(sha, archive.stderr.decode(errors="replace")[:400]))
    untar = subprocess.run(["tar", "-x", "-C", str(dest)], input=archive.stdout, capture_output=True, check=False)
    if untar.returncode != 0:
        raise SandboxError("untar failed: {}".format(untar.stderr.decode(errors="replace")[:400]))


def sandbox_home(sandbox: Path) -> Path:
    # HOME always lives inside the sandbox, whatever the account's passwd entry
    # says, so the candidate's Maven repository and dotfiles stay on its side.
    return sandbox / "home"


def prepare_sandbox(user: str, sandbox: Path) -> Path:
    home = sandbox_home(sandbox)
    ensure_user(user, home)
    reap(user)
    for path in (sandbox, home):
        _must(_priv(["mkdir", "-p", str(path)]), "create sandbox")
        _must(_priv(["chown", "{}:".format(user), str(path)]), "own sandbox")
        _must(_priv(["chmod", "0755", str(path)]), "mode sandbox")
    return home


def seed_maven_repository(user: str, home: Path, source: Path) -> bool:
    if not source.is_dir():
        return False
    dest = home / ".m2" / "repository"
    if dest.is_dir():
        return True
    _must(_priv(["mkdir", "-p", str(dest.parent)]), "create candidate maven dir")
    _must(_priv(["cp", "-a", str(source) + "/.", str(dest)]), "seed candidate maven repository")
    _must(_priv(["chown", "-R", "{}:".format(user), str(home / ".m2")]), "own candidate maven repository")
    return True


# ---------------------------------------------------------------------------
# probes and integrity


def writable_by(user: str, paths: list[Path]) -> list[dict]:
    """Every trusted path the candidate account could write, itself or via an ancestor."""
    findings: list[dict] = []
    checked_ancestors: set = set()
    for path in paths:
        if not path.exists():
            continue
        probe = _run(_priv(["sudo", "-n", "-u", user, "--", "/usr/bin/env", "-i", "PATH=/usr/bin:/bin",
                            "find", str(path), "-writable", "-print", "-quit"]))
        hit = probe.stdout.strip()
        if hit:
            findings.append({"path": str(path), "writable": hit})
        for ancestor in [path] + list(path.parents):
            if str(ancestor) in checked_ancestors:
                continue
            checked_ancestors.add(str(ancestor))
            test = _run(_priv(["sudo", "-n", "-u", user, "--", "/usr/bin/test", "-w", str(ancestor)]))
            if test.returncode != 0:
                continue
            info = ancestor.stat()
            sticky = bool(info.st_mode & stat.S_ISVTX)
            if sticky and ancestor != path:
                # A sticky directory (e.g. /tmp) lets the candidate write next to,
                # but not rename or replace, an entry it does not own.
                continue
            findings.append({"path": str(path), "writable_ancestor": str(ancestor)})
    return findings


def git_tracked_digests(repo: Path, sha: str, rel_dir: str) -> dict:
    out = _must(["git", "-C", str(repo), "ls-tree", "-r", "-z", sha, "--", rel_dir], "git ls-tree").stdout
    tracked = {}
    for record in out.split("\0"):
        if not record:
            continue
        meta, path = record.split("\t", 1)
        mode, kind, blob = meta.split()
        if kind == "blob":
            tracked[path] = blob
    return tracked


def verify_trusted_tree(repo: Path, sha: str, rel_dir: str) -> dict:
    """Every trusted qualification file must hash to the trusted commit's blob."""
    head = _must(["git", "-C", str(repo), "rev-parse", "HEAD"], "git rev-parse").stdout.strip()
    tracked = git_tracked_digests(repo, sha, rel_dir)
    mismatched, missing = [], []
    for path, blob in sorted(tracked.items()):
        full = repo / path
        if not full.is_file() or full.is_symlink():
            missing.append(path)
            continue
        actual = _must(["git", "-C", str(repo), "hash-object", "--no-filters", "--", path], "git hash-object").stdout.strip()
        if actual != blob:
            mismatched.append(path)
    present = {
        str(p.relative_to(repo)) for p in (repo / rel_dir).rglob("*") if p.is_file() or p.is_symlink()
    }
    untracked = sorted(present - set(tracked))
    return {
        "head": head,
        "head_matches_trusted_sha": head == sha,
        "files_checked": len(tracked),
        "mismatched": mismatched,
        "missing": missing,
        "untracked": untracked,
        "ok": head == sha and not mismatched and not missing and not untracked and bool(tracked),
    }


def seal(files: list[Path]) -> dict:
    return {
        "schema": SCHEMA_SEAL,
        "files": {str(p.resolve()): sha256_file(p) for p in files},
    }


def verify_seal(document: dict) -> list[dict]:
    problems = []
    for path, digest in sorted((document.get("files") or {}).items()):
        p = Path(path)
        if not p.is_file() or p.is_symlink():
            problems.append({"path": path, "problem": "missing"})
        elif sha256_file(p) != digest:
            problems.append({"path": path, "problem": "digest_changed"})
    return problems


def integrity(repo: Path, sha: str, rel_dir: str, seals: list[Path], user: str, probe_paths: list[Path]) -> dict:
    doc = {
        "schema": SCHEMA_INTEGRITY,
        "status": "UNKNOWN",
        "trusted_sha": sha,
        "trusted_tree": None,
        "seals": [],
        "surviving_candidate_processes": [],
        "candidate_writable_trusted_paths": [],
        "violations": [],
    }
    try:
        tree = verify_trusted_tree(repo, sha, rel_dir)
        doc["trusted_tree"] = tree
        if not tree["ok"]:
            doc["violations"].append("trusted_validator_changed: {}".format(
                json.dumps({k: tree[k] for k in ("head_matches_trusted_sha", "mismatched", "missing", "untracked")})[:600]))
        for seal_path in seals:
            if not seal_path.is_file():
                doc["violations"].append("evidence_seal_missing: {}".format(seal_path))
                continue
            problems = verify_seal(json.loads(seal_path.read_text()))
            doc["seals"].append({"seal": str(seal_path), "problems": problems})
            if problems:
                doc["violations"].append("sealed_evidence_changed: {}".format(problems[:5]))
        survivors = alive(user)
        doc["surviving_candidate_processes"] = survivors
        if survivors:
            doc["violations"].append("candidate_process_survived: {}".format(survivors[:5]))
        writable = writable_by(user, probe_paths)
        doc["candidate_writable_trusted_paths"] = writable
        if writable:
            doc["violations"].append("trusted_path_writable_by_candidate: {}".format(writable[:5]))
    except (SandboxError, OSError, ValueError, json.JSONDecodeError) as exc:
        doc["violations"].append("integrity_unverifiable: {}".format(exc))
        doc["status"] = "UNKNOWN"
        return doc
    doc["status"] = "VIOLATION" if doc["violations"] else "OK"
    return doc


# ---------------------------------------------------------------------------
# CLI


def _write(path: str, document: dict) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n")


def cmd_prepare(args) -> int:
    doc = {"schema": SCHEMA_PREPARE, "status": "UNKNOWN", "user": args.user, "candidate_sha": args.candidate_sha}
    try:
        sandbox = Path(args.sandbox_dir)
        home = prepare_sandbox(args.user, sandbox)
        doc["candidate_home"] = str(home)
        with tempfile.TemporaryDirectory(dir=args.work_dir) as tmp:
            export = Path(tmp) / "candidate"
            export_commit(Path(args.repo), args.candidate_sha, export)
            stage_candidate(args.user, export, sandbox / "candidate")
        doc["candidate_root"] = str(sandbox / "candidate")
        doc["maven_repository_seeded"] = seed_maven_repository(args.user, home, Path(args.seed_maven_repo)) if args.seed_maven_repo else False
        bundle = Path(args.bundle_dir)
        with tempfile.TemporaryDirectory(dir=args.work_dir) as tmp:
            staging = Path(tmp) / "bundle"
            staging.mkdir()
            for item in args.bundle_file:
                shutil.copy2(item, staging / Path(item).name)
            stage_readonly(staging, bundle)
        doc["bundle_dir"] = str(bundle)
        probes = [Path(p) for p in args.probe] + [bundle]
        if args.stage_jdk:
            # The toolchain the trusted steps use AFTER candidate code has run must
            # not sit under a candidate-writable ancestor (on hosted runners /opt,
            # home of the tool cache, is world-writable): stage a root-owned,
            # read-only copy before any candidate code runs and use only that.
            jdk = Path(args.jdk_dest)
            stage_readonly(Path(args.stage_jdk).resolve(), jdk)
            if not (jdk / "bin" / "javac").is_file() or not (jdk / "bin" / "java").is_file():
                raise SandboxError("staged JDK at {} has no java/javac".format(jdk))
            doc["trusted_jdk"] = str(jdk)
            probes.append(jdk)
        writable = writable_by(args.user, probes)
        doc["probed_paths"] = [str(p) for p in probes]
        doc["candidate_writable_trusted_paths"] = writable
        if writable:
            raise SandboxError("trusted path writable by the candidate account: {}".format(writable[:5]))
        doc["status"] = "READY"
    except (SandboxError, OSError) as exc:
        doc["error"] = str(exc)
        _write(args.out, doc)
        print("SANDBOX = UNKNOWN ({})".format(exc), file=sys.stderr)
        return 2
    _write(args.out, doc)
    print("SANDBOX = READY user={} candidate={}".format(args.user, args.candidate_sha))
    return 0


def cmd_run(args) -> int:
    command = list(args.command)
    if command and command[0] == "--":
        command = command[1:]
    doc = {"schema": SCHEMA_RUN, "label": args.label, "user": args.user, "command": command,
           "exit_code": None, "status": "UNKNOWN"}
    try:
        home = sandbox_home(Path(args.sandbox_dir))
        assert_separate_identity(pwd.getpwnam(args.user))
        proc = run_candidate(args.user, home, Path(args.cwd), command, timeout=args.timeout)
        doc["exit_code"] = proc.returncode
        doc["stdout_tail"] = proc.stdout[-4000:]
        doc["stderr_tail"] = proc.stderr[-4000:]
        doc["reaped"] = True
        doc["status"] = "RECORDED"
        sys.stdout.write(proc.stdout[-20000:])
        sys.stderr.write(proc.stderr[-20000:])
    except (SandboxError, KeyError, OSError) as exc:
        doc["error"] = str(exc)
        _write(args.out, doc)
        print("SANDBOX_RUN {} = UNKNOWN ({})".format(args.label, exc), file=sys.stderr)
        return 2
    _write(args.out, doc)
    print("SANDBOX_RUN {} exit={} (recorded by trusted code)".format(args.label, doc["exit_code"]))
    return 0


def cmd_seal(args) -> int:
    document = seal([Path(p) for p in args.file])
    _write(args.out, document)
    print("SEALED {} file(s)".format(len(document["files"])))
    return 0


def cmd_verify(args) -> int:
    doc = integrity(Path(args.repo), args.trusted_sha, args.rel_dir, [Path(s) for s in args.seal],
                    args.user, [Path(p) for p in args.probe])
    _write(args.out, doc)
    print("INTEGRITY = {}{}".format(doc["status"], " ({})".format("; ".join(doc["violations"])[:400]) if doc["violations"] else ""))
    return {"OK": 0, "VIOLATION": 1}.get(doc["status"], 2)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command_name", required=True)

    p = sub.add_parser("prepare")
    p.add_argument("--user", default=CANDIDATE_USER)
    p.add_argument("--repo", required=True)
    p.add_argument("--candidate-sha", required=True)
    p.add_argument("--sandbox-dir", required=True)
    p.add_argument("--bundle-dir", required=True)
    p.add_argument("--bundle-file", action="append", default=[])
    p.add_argument("--seed-maven-repo", default="")
    p.add_argument("--work-dir", required=True)
    p.add_argument("--probe", action="append", default=[])
    p.add_argument("--stage-jdk", default="", help="JAVA_HOME to copy into a root-owned read-only location")
    p.add_argument("--jdk-dest", default="/var/lib/c12-trusted/jdk")
    p.add_argument("--out", required=True)

    r = sub.add_parser("run")
    r.add_argument("--user", default=CANDIDATE_USER)
    r.add_argument("--label", required=True)
    r.add_argument("--sandbox-dir", required=True)
    r.add_argument("--cwd", required=True)
    r.add_argument("--timeout", type=int, default=None)
    r.add_argument("--out", required=True)
    r.add_argument("command", nargs=argparse.REMAINDER)

    s = sub.add_parser("seal")
    s.add_argument("--out", required=True)
    s.add_argument("file", nargs="+")

    v = sub.add_parser("verify")
    v.add_argument("--user", default=CANDIDATE_USER)
    v.add_argument("--repo", required=True)
    v.add_argument("--trusted-sha", required=True)
    v.add_argument("--rel-dir", default=".github/qualification")
    v.add_argument("--seal", action="append", default=[])
    v.add_argument("--probe", action="append", default=[])
    v.add_argument("--out", required=True)

    args = parser.parse_args()
    return {"prepare": cmd_prepare, "run": cmd_run, "seal": cmd_seal, "verify": cmd_verify}[args.command_name](args)


if __name__ == "__main__":
    sys.exit(main())
