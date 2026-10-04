#!/usr/bin/env python3
"""Trusted required-test corpus: enumeration, baseline and delta policy.

Trust boundary: trusted default-branch code. Every input is read as Git data
from the trusted object store (``git ls-tree`` / ``git show`` of an exact
commit), never from a working tree that candidate code could have touched.

Why a baseline exists
---------------------
Enumerating the required tests from the candidate tree alone lets the candidate
decide what is required: rename every ``*Test`` class to ``*Check``, move it out
of ``src/test/java`` or delete it, keep one trivially green test, and the
witness faithfully executes the one test that is left. The *required* corpus
must therefore be anchored to something the candidate cannot edit: the baseline
file committed on the default branch, read at the trusted validator commit.

Policy, evaluated in trusted code only
--------------------------------------
* The trusted baseline must be present (else UNKNOWN), well formed (else
  UNKNOWN) and fresh: its entries must equal the trusted enumeration of the
  trusted validator commit, under the same enumeration rule (else UNKNOWN).
  A stale baseline would silently stop protecting tests added since.
* Every baseline entry must still be enumerated in the candidate. A missing
  entry is a FAIL, whatever the reason (deleted, renamed outside the class
  regex, moved outside a test source root, moved to another module), unless the
  trusted baseline lists it under ``approved_removals``. Approvals only count
  when they are on the default branch: an approval the candidate adds to its
  own copy of the baseline grants nothing to that candidate.
* A baseline entry the candidate lacks because it was added to the default
  branch after the candidate's merge base is reported separately
  (``candidate_behind_default_branch``): still a FAIL, but with the honest
  cause, which is fixed by merging the default branch.
* Candidate additions are welcome and are required as well: the required set
  is every pair the candidate enumerates.
* The same holds per test method. A class that stays but loses methods is a
  shrunken corpus, so the baseline also lists every enabled test method of
  every baseline class (``module::Class#method``). A baseline method that the
  candidate deletes, renames, un-annotates or disables (``@Ignore``,
  ``@Disabled*``, ``@Enabled*``, on the method or an enclosing class) is a
  FAIL unless the trusted baseline approves its removal. The static reading is
  only the first gate: every required method must also be reported started by
  the trusted driver (``qualify.py``), so source the parser misreads cannot
  turn a test that never ran into credit.
* The candidate's own baseline file must describe the candidate exactly, so a
  merge can never leave the default branch with a stale baseline. Adding a test
  therefore means adding its entry; removing one means a prior, separately
  reviewed approval plus dropping both the entry and the approval.

The approved update path for a removal or rename is two reviewed changes:
first land the approval (the tests still exist, so that change qualifies),
then land the removal. Nothing here can approve anything by itself.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import PurePosixPath

# Trusted code never resolves tools from the inherited PATH (see sandbox.TOOL_PATH).
GIT = shutil.which("git", path="/usr/sbin:/usr/bin:/sbin:/bin") or "/usr/bin/git"

BASELINE_SCHEMA = "mage.candidate-qualification.test-corpus-baseline/2"
POLICY_SCHEMA = "mage.candidate-qualification.corpus-policy/2"
BASELINE_PATH = ".github/qualification/test_corpus_baseline.json"

# Selection rule for what must run, never an evidence heuristic: a class that
# matches but is missing makes the witness FAIL rather than shrinking the set.
TEST_CLASS_RE = r"(Test|Tests|TestCase|Spec|IT)$"
SOURCE_DIR_MARKERS = ("src/test/java", "src/test/kotlin", "src/test/groovy")
SOURCE_SUFFIX = ".java"
PAIR_SEPARATOR = "::"
METHOD_SEPARATOR = "#"

# What makes a method a required test, read from source. JUnit 4 and Jupiter
# test annotations are matched by simple name; a JUnit 3 ``TestCase`` subclass
# contributes its public no-argument ``test*`` methods.
TEST_METHOD_ANNOTATIONS = ("Test", "ParameterizedTest", "RepeatedTest", "TestFactory", "TestTemplate")
DISABLING_ANNOTATION_RE = r"^(Ignore|Disabled\w*|Enabled\w*)$"
JUNIT3_BASE_RE = r"\bextends\s+(?:junit\.framework\.)?TestCase\b"
JUNIT3_METHOD_RE = r"\bpublic\s+void\s+(test[\w$]*)\s*\(\s*\)"

ENUMERATION_RULE = {
    "class_regex": TEST_CLASS_RE,
    "source_markers": list(SOURCE_DIR_MARKERS),
    "source_suffix": SOURCE_SUFFIX,
    "pair_format": "module" + PAIR_SEPARATOR + "fully.qualified.ClassName",
    "module_rule": "nearest ancestor directory of the test source root that holds a pom.xml",
    "method_format": "module" + PAIR_SEPARATOR + "fully.qualified.ClassName" + METHOD_SEPARATOR + "methodName",
    "method_rule": {
        "test_annotations": list(TEST_METHOD_ANNOTATIONS),
        "disabling_annotation_regex": DISABLING_ANNOTATION_RE,
        "junit3_base_regex": JUNIT3_BASE_RE,
        "junit3_method_regex": JUNIT3_METHOD_RE,
        "scope": "methods declared anywhere in the source file of a baseline class, comments and literals ignored",
        "enabled": "a test method with no disabling annotation on itself or an enclosing type",
    },
}


class CorpusError(RuntimeError):
    pass


def git(repo: str, *args: str) -> str:
    proc = subprocess.run(
        [GIT, "-C", str(repo), *args], capture_output=True, text=True, check=False
    )
    if proc.returncode != 0:
        raise CorpusError("git {} failed: {}".format(" ".join(args), proc.stderr.strip()))
    return proc.stdout


def tree_paths(repo: str, rev: str) -> list[str]:
    out = git(repo, "ls-tree", "-r", "--name-only", "-z", rev)
    return [p for p in out.split("\0") if p]


def read_blob(repo: str, rev: str, path: str) -> bytes | None:
    proc = subprocess.run(
        [GIT, "-C", str(repo), "show", "{}:{}".format(rev, path)],
        capture_output=True,
        check=False,
    )
    return proc.stdout if proc.returncode == 0 else None


def read_blobs(repo: str, rev: str, paths: list[str]) -> dict:
    """Contents of many paths at one commit, through one ``git cat-file --batch``."""
    if any("\n" in path for path in paths):
        raise CorpusError("a tree path contains a newline")
    request = "".join("{}:{}\n".format(rev, path) for path in paths).encode("utf-8")
    proc = subprocess.run(
        [GIT, "-C", str(repo), "cat-file", "--batch"], input=request, capture_output=True, check=False
    )
    if proc.returncode != 0:
        raise CorpusError("git cat-file --batch failed: {}".format(proc.stderr.decode("utf-8", "replace").strip()))
    out, offset, blobs = proc.stdout, 0, {}
    for path in paths:
        end = out.index(b"\n", offset)
        header = out[offset:end].split()
        offset = end + 1
        if len(header) != 3 or header[1] != b"blob":
            raise CorpusError("{}:{} is not a blob".format(rev, path))
        size = int(header[2])
        blobs[path] = out[offset:offset + size]
        offset += size + 1
    return blobs


def pair(module: str, class_name: str) -> str:
    return "{}{}{}".format(module, PAIR_SEPARATOR, class_name)


def split_pair(value: str) -> tuple[str, str]:
    module, _, class_name = value.partition(PAIR_SEPARATOR)
    return module, class_name


def enumerate_paths(paths: list[str], any_class: bool = False) -> list[dict]:
    """Enumerate required (module, class) entries from a list of tree paths.

    With ``any_class`` every source file under a test source root is listed,
    whatever its name (the superclass index of ``inheriting_classes``).
    """
    pattern = re.compile(r".*" if any_class else TEST_CLASS_RE)
    pom_dirs = {str(PurePosixPath(p).parent) for p in paths if PurePosixPath(p).name == "pom.xml"}
    found: dict[str, set] = {}
    for path in paths:
        if not path.endswith(SOURCE_SUFFIX):
            continue
        for marker in SOURCE_DIR_MARKERS:
            token = marker + "/"
            if path.startswith(token):
                prefix, rest = "", path[len(token):]
            elif "/" + token in path:
                prefix, rest = path.split("/" + token, 1)
            else:
                continue
            module = _module_of(prefix, pom_dirs)
            if module is None:
                break
            stem = PurePosixPath(rest).with_suffix("")
            if pattern.search(stem.name):
                found.setdefault(module, {}).setdefault(".".join(stem.parts), path)
            break
    return [
        {"module": module, "class_name": name, "path": found[module][name]}
        for module in sorted(found)
        for name in sorted(found[module])
    ]


def _module_of(source_parent: str, pom_dirs: set) -> str | None:
    current = PurePosixPath(source_parent) if source_parent else PurePosixPath(".")
    while True:
        key = str(current)
        if key in pom_dirs:
            return key
        if key == ".":
            return None
        current = current.parent


def enumerate_rev(repo: str, rev: str) -> list[dict]:
    return enumerate_paths(tree_paths(repo, rev))


_TOKEN = re.compile(r"[A-Za-z_$][\w$]*|\S")
_IDENT = re.compile(r"^[A-Za-z_$][\w$]*$")


def strip_java(text: str) -> str:
    """Java source with comments and string/char/text-block contents removed."""
    out: list[str] = []
    i, n = 0, len(text)
    while i < n:
        if text.startswith("//", i):
            j = text.find("\n", i)
            i = n if j < 0 else j
            out.append(" ")
        elif text.startswith("/*", i):
            j = text.find("*/", i + 2)
            i = n if j < 0 else j + 2
            out.append(" ")
        elif text.startswith('"""', i):
            j = i + 3
            while j < n and not text.startswith('"""', j):
                j += 2 if text[j] == "\\" else 1
            i = j + 3
            out.append('""')
        elif text[i] in "\"'":
            quote, j = text[i], i + 1
            while j < n and text[j] != quote and text[j] != "\n":
                j += 2 if text[j] == "\\" else 1
            i = j + 1
            out.append(quote * 2)
        else:
            out.append(text[i])
            i += 1
    return "".join(out)


def _skip_parens(tokens: list[str], start: int) -> int:
    depth = 0
    for index in range(start, len(tokens)):
        if tokens[index] == "(":
            depth += 1
        elif tokens[index] == ")":
            depth -= 1
            if depth == 0:
                return index + 1
    return len(tokens)


def java_test_methods(source: str) -> tuple[set, set]:
    """(enabled, disabled) test method names declared in one Java source file."""
    code = strip_java(source)
    tokens = _TOKEN.findall(code)
    disabling = re.compile(DISABLING_ANNOTATION_RE)
    enabled: set = set()
    disabled: set = set()
    scopes = [False]  # per brace scope: is an enclosing type disabled?
    pending: list[str] = []  # simple names of annotations awaiting their declaration
    type_disabled = None  # a type declaration waiting for its body
    prev = None
    i, n = 0, len(tokens)
    while i < n:
        tok = tokens[i]
        if tok == "@" and i + 1 < n and tokens[i + 1] != "interface":
            j, name = i + 1, None
            while j < n and _IDENT.match(tokens[j]):
                name = tokens[j]
                if j + 2 < n and tokens[j + 1] == "." and _IDENT.match(tokens[j + 2]):
                    j += 2
                else:
                    j += 1
                    break
            if j < n and tokens[j] == "(":
                j = _skip_parens(tokens, j)
            if name:
                pending.append(name)
            i, prev = max(j, i + 1), None
            continue
        if tok in ("class", "interface", "enum") and prev != ".":
            type_disabled = scopes[-1] or any(disabling.match(a) for a in pending)
            pending = []
        elif tok == "{":
            scopes.append(scopes[-1] if type_disabled is None else type_disabled)
            type_disabled, pending = None, []
        elif tok == "}":
            if len(scopes) > 1:
                scopes.pop()
            pending = []
        elif tok == ";":
            pending = []
        elif tok == "(":
            if prev and _IDENT.match(prev) and any(a in TEST_METHOD_ANNOTATIONS for a in pending):
                off = scopes[-1] or any(disabling.match(a) for a in pending)
                (disabled if off else enabled).add(prev)
            pending = []
            i, prev = _skip_parens(tokens, i), ")"
            continue
        prev = tok
        i += 1
    if re.search(JUNIT3_BASE_RE, code):
        enabled.update(re.findall(JUNIT3_METHOD_RE, code))
    return enabled, disabled - enabled


def method_id(class_pair: str, method: str) -> str:
    return "{}{}{}".format(class_pair, METHOD_SEPARATOR, method)


def class_of_method(value: str) -> str:
    return value.rpartition(METHOD_SEPARATOR)[0]


def enumerate_methods(entries: list[dict], read) -> tuple[list[str], list[str]]:
    """Enabled and disabled test method identities of enumerated classes.

    ``read(path)`` returns the file's bytes; a class whose source cannot be read
    fails closed rather than contributing no methods.
    """
    enabled: set = set()
    disabled: set = set()
    for entry in entries:
        blob = read(entry["path"])
        if blob is None:
            raise CorpusError("source of {} is unreadable".format(entry["path"]))
        on, off = java_test_methods(blob.decode("utf-8", errors="replace"))
        base = pair(entry["module"], entry["class_name"])
        enabled.update(method_id(base, name) for name in on)
        disabled.update(method_id(base, name) for name in off)
    return sorted(enabled), sorted(disabled - enabled)


def java_type_header(source: str) -> dict:
    """Package, imports and the first top-level class declaration of one Java file.

    ``abstract`` and ``disabled`` describe that class; ``extends`` is the
    superclass name as written (simple or qualified), or None.
    """
    tokens = _TOKEN.findall(strip_java(source))
    disabling = re.compile(DISABLING_ANNOTATION_RE)
    header = {"package": "", "imports": [], "abstract": False, "disabled": False, "extends": None, "found": False}
    depth, pending, i, n = 0, [], 0, len(tokens)

    def qualified(start: int) -> tuple[str, int]:
        parts, j = [], start
        while j < n and _IDENT.match(tokens[j]):
            parts.append(tokens[j])
            if j + 2 < n and tokens[j + 1] == "." and (_IDENT.match(tokens[j + 2]) or tokens[j + 2] == "*"):
                if tokens[j + 2] == "*":
                    parts.append("*")
                    return ".".join(parts), j + 3
                j += 2
            else:
                j += 1
                break
        return ".".join(parts), j

    while i < n:
        tok = tokens[i]
        if tok == "{":
            depth += 1
        elif tok == "}":
            depth -= 1
            pending = []
        elif depth == 0 and tok == "@" and i + 1 < n and tokens[i + 1] != "interface":
            name, j = qualified(i + 1)
            if j < n and tokens[j] == "(":
                j = _skip_parens(tokens, j)
            pending.append(name.rpartition(".")[2])
            i = max(j, i + 1)
            continue
        elif depth == 0 and tok == ";":
            pending = []
        elif depth == 0 and tok == "package":
            header["package"], i = qualified(i + 1)
            continue
        elif depth == 0 and tok == "import":
            j = i + 1
            if j < n and tokens[j] == "static":
                header["imports"].append(None)
                _, i = qualified(j + 1)
                continue
            name, i = qualified(j)
            header["imports"].append(name)
            continue
        elif depth == 0 and tok in ("class", "interface", "enum", "record"):
            if tok == "class":
                header["found"] = True
                header["abstract"] = "abstract" in pending
                header["disabled"] = any(disabling.match(a) for a in pending)
                j = i + 2
                if j < n and tokens[j] == "<":
                    angle = 0
                    while j < n:
                        angle += {"<": 1, ">": -1}.get(tokens[j], 0)
                        j += 1
                        if angle == 0:
                            break
                if j < n and tokens[j] == "extends":
                    header["extends"], _ = qualified(j + 1)
            header["imports"] = [m for m in header["imports"] if m]
            return header
        elif depth == 0:
            pending.append(tok)
        i += 1
    header["imports"] = [m for m in header["imports"] if m]
    return header


def _superclass_candidates(header: dict) -> list[str]:
    """Fully qualified names the declared superclass may resolve to."""
    name = header.get("extends")
    if not name:
        return []
    if "." in name:
        return [name]
    out = []
    for imported in header["imports"]:
        if imported.rpartition(".")[2] == name:
            return [imported]
        if imported.endswith(".*"):
            out.append(imported[:-1] + name)
    package = header["package"]
    return [(package + "." + name) if package else name] + out


def inheriting_classes(entries: list[dict], sources: list[dict], read, enabled_methods: list[str]) -> list[str]:
    """Required classes that own no test method but inherit enabled tests.

    ``entries`` are the required (module, class) entries; ``sources`` every Java
    file under a test source root (superclasses need not match the class
    regex). A class qualifies when it is concrete, not disabled at class level,
    owns no enabled test method, and its superclass chain (resolved by package,
    single-type or on-demand imports) reaches a class that declares an enabled
    test method. Such a class must be run and entered: tests it only inherits
    are otherwise never executed for it.
    """
    by_name: dict = {}
    headers: dict = {}
    for source in sources:
        blob = read(source["path"])
        if blob is None:
            raise CorpusError("source of {} is unreadable".format(source["path"]))
        key = pair(source["module"], source["class_name"])
        text = blob.decode("utf-8", errors="replace")
        headers[key] = java_type_header(text)
        on, _ = java_test_methods(text)
        headers[key]["declares_tests"] = bool(on)
        by_name.setdefault(source["class_name"], []).append(key)
    owning = {class_of_method(m) for m in enabled_methods}

    memo: dict = {}

    def declares_or_inherits(key: str, seen: frozenset) -> bool:
        if key in memo:
            return memo[key]
        header = headers.get(key)
        if header is None or key in seen:
            return False
        result = header["declares_tests"] or key in owning
        if not result:
            module = split_pair(key)[0]
            for fqcn in _superclass_candidates(header):
                supers = by_name.get(fqcn, [])
                ordered = sorted(supers, key=lambda k: split_pair(k)[0] != module)
                if any(declares_or_inherits(s, seen | {key}) for s in ordered):
                    result = True
                    break
        memo[key] = result
        return result

    out = []
    for entry in entries:
        key = pair(entry["module"], entry["class_name"])
        header = headers.get(key)
        if header is None:
            raise CorpusError("required class {} has no indexed source".format(key))
        if key in owning or not header["found"] or header["abstract"] or header["disabled"]:
            continue
        module = entry["module"]
        for fqcn in _superclass_candidates(header):
            supers = sorted(by_name.get(fqcn, []), key=lambda k: split_pair(k)[0] != module)
            if any(declares_or_inherits(s, frozenset({key})) for s in supers):
                out.append(key)
                break
    return sorted(out)


def corpus_rev(repo: str, rev: str) -> dict:
    """Classes and test methods of one exact commit, from Git objects only."""
    paths = tree_paths(repo, rev)
    entries = enumerate_paths(paths)
    sources = enumerate_paths(paths, any_class=True)
    blobs = read_blobs(repo, rev, sorted({e["path"] for e in entries} | {s["path"] for s in sources}))
    enabled, disabled = enumerate_methods(entries, blobs.get)
    return {
        "pairs": pairs_of(entries),
        "methods": enabled,
        "disabled_methods": disabled,
        "inheriting": inheriting_classes(entries, sources, blobs.get, enabled),
    }


def pairs_of(entries: list[dict]) -> list[str]:
    return sorted({pair(e["module"], e["class_name"]) for e in entries})


def entries_digest(entries: list[str]) -> str:
    return hashlib.sha256(("\n".join(entries) + "\n").encode("utf-8")).hexdigest()


def build_baseline(entries: list[str], approved_removals: list[dict] | None = None,
                   methods: list[str] | None = None) -> dict:
    entries = sorted(set(entries))
    methods = sorted(set(methods or []))
    return {
        "schema": BASELINE_SCHEMA,
        "enumeration_rule": ENUMERATION_RULE,
        "entries": entries,
        "entries_count": len(entries),
        "entries_sha256": entries_digest(entries),
        "methods": methods,
        "methods_count": len(methods),
        "methods_sha256": entries_digest(methods),
        "approved_removals": sorted(approved_removals or [], key=lambda r: r.get("entry", "")),
    }


def validate_baseline(doc) -> list[str]:
    """Structural problems of a baseline document; empty means well formed."""
    problems: list[str] = []
    if not isinstance(doc, dict):
        return ["baseline is not a JSON object"]
    if doc.get("schema") != BASELINE_SCHEMA:
        problems.append("unexpected schema {!r}".format(doc.get("schema")))
    entries = doc.get("entries")
    if not isinstance(entries, list) or not all(isinstance(e, str) for e in entries):
        problems.append("entries must be a list of strings")
        return problems
    if entries != sorted(set(entries)):
        problems.append("entries must be sorted and unique")
    for entry in entries:
        module, class_name = split_pair(entry)
        if not module or not class_name or PAIR_SEPARATOR in class_name:
            problems.append("malformed entry {!r}".format(entry))
            break
    if doc.get("entries_count") != len(entries):
        problems.append("entries_count does not match entries")
    if doc.get("entries_sha256") != entries_digest(entries):
        problems.append("entries_sha256 does not match entries")
    methods = doc.get("methods")
    if not isinstance(methods, list) or not all(isinstance(m, str) for m in methods):
        problems.append("methods must be a list of strings")
        return problems
    if methods != sorted(set(methods)):
        problems.append("methods must be sorted and unique")
    known = set(entries)
    known_methods = set(methods)
    for method in methods:
        owner, _, name = method.rpartition(METHOD_SEPARATOR)
        if owner not in known or not _IDENT.match(name):
            problems.append("malformed method {!r}".format(method))
            break
    if doc.get("methods_count") != len(methods):
        problems.append("methods_count does not match methods")
    if doc.get("methods_sha256") != entries_digest(methods):
        problems.append("methods_sha256 does not match methods")
    removals = doc.get("approved_removals")
    if not isinstance(removals, list):
        problems.append("approved_removals must be a list")
        return problems
    seen = set()
    for removal in removals:
        if not isinstance(removal, dict):
            problems.append("approved removal is not an object")
            continue
        entry = removal.get("entry")
        if not isinstance(entry, str) or (entry not in known and entry not in known_methods):
            # An approval for a test the baseline no longer lists is stale: it
            # would otherwise linger as a blanket licence for a future removal.
            problems.append("approved removal {!r} is not a baseline entry".format(entry))
        if not str(removal.get("reason") or "").strip():
            problems.append("approved removal {!r} has no reason".format(entry))
        if not str(removal.get("reference") or "").strip():
            problems.append("approved removal {!r} has no review reference".format(entry))
        if entry in seen:
            problems.append("approved removal {!r} is duplicated".format(entry))
        seen.add(entry)
    return problems


def load_baseline_blob(blob: bytes | None) -> tuple[dict | None, list[str]]:
    if blob is None:
        return None, ["missing"]
    try:
        doc = json.loads(blob.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        return None, ["unparseable: {}".format(exc)]
    return doc, validate_baseline(doc)


def evaluate(repo: str, trusted_rev: str, base_rev: str, candidate_rev: str) -> dict:
    """Evaluate the candidate corpus against the trusted baseline. Git data only."""
    result = {
        "schema": POLICY_SCHEMA,
        "status": "UNKNOWN",
        "baseline_path": BASELINE_PATH,
        "trusted_rev": trusted_rev,
        "comparison_base_rev": base_rev,
        "candidate_rev": candidate_rev,
        "enumeration_rule": ENUMERATION_RULE,
        "trusted_baseline": None,
        "unknowns": [],
        "violations": [],
        "required_pairs": [],
        "required_methods": [],
        "required_inheriting_classes": [],
        "additions": [],
        "removed_without_approval": [],
        "behind_default_branch": [],
        "approved_removals_applied": [],
        "method_additions": [],
        "methods_removed_without_approval": [],
        "methods_disabled_without_approval": [],
        "methods_behind_default_branch": [],
        "candidate_baseline": None,
    }

    candidate = corpus_rev(repo, candidate_rev)
    candidate_pairs = candidate["pairs"]
    result["required_pairs"] = candidate_pairs
    result["required_methods"] = candidate["methods"]
    result["required_inheriting_classes"] = candidate["inheriting"]

    doc, problems = load_baseline_blob(read_blob(repo, trusted_rev, BASELINE_PATH))
    trusted = corpus_rev(repo, trusted_rev)
    trusted_pairs = trusted["pairs"]
    summary = {"present": doc is not None, "problems": problems}
    result["trusted_baseline"] = summary
    if problems == ["missing"]:
        result["unknowns"].append("corpus_baseline_missing: {} absent at trusted {}".format(BASELINE_PATH, trusted_rev))
        return result
    if problems:
        result["unknowns"].append("corpus_baseline_malformed: {}".format("; ".join(problems[:5])))
        return result

    entries = doc["entries"]
    methods = doc["methods"]
    summary["entries_count"] = len(entries)
    summary["entries_sha256"] = doc["entries_sha256"]
    summary["methods_count"] = len(methods)
    summary["methods_sha256"] = doc["methods_sha256"]
    if doc.get("enumeration_rule") != ENUMERATION_RULE:
        result["unknowns"].append("corpus_baseline_stale: enumeration rule differs from the trusted validator")
        return result
    if entries != trusted_pairs or methods != trusted["methods"]:
        missing = sorted(set(trusted_pairs) - set(entries))
        extra = sorted(set(entries) - set(trusted_pairs))
        missing_methods = sorted(set(trusted["methods"]) - set(methods))
        extra_methods = sorted(set(methods) - set(trusted["methods"]))
        summary["unlisted_trusted_tests"] = missing[:50]
        summary["listed_but_absent"] = extra[:50]
        summary["unlisted_trusted_methods"] = missing_methods[:50]
        summary["listed_methods_absent"] = extra_methods[:50]
        result["unknowns"].append(
            "corpus_baseline_stale: baseline differs from the trusted enumeration "
            "({} unlisted, {} absent; {} unlisted methods, {} absent methods)".format(
                len(missing), len(extra), len(missing_methods), len(extra_methods)
            )
        )
        return result

    approved = {r["entry"]: r for r in doc["approved_removals"]}
    base = corpus_rev(repo, base_rev)
    base_pairs = set(base["pairs"])
    candidate_set = set(candidate_pairs)
    for entry in entries:
        if entry in candidate_set:
            continue
        if entry in approved:
            result["approved_removals_applied"].append(approved[entry])
        elif entry not in base_pairs:
            result["behind_default_branch"].append(entry)
        else:
            result["removed_without_approval"].append(entry)
    result["additions"] = sorted(candidate_set - set(entries))

    # Methods of a class that is gone are reported with the class, once.
    base_methods = set(base["methods"])
    candidate_methods = set(candidate["methods"])
    candidate_disabled = set(candidate["disabled_methods"])
    retained: set = set()
    for method in methods:
        if class_of_method(method) not in candidate_set:
            continue
        if method in candidate_methods:
            retained.add(method)
        elif method in approved:
            result["approved_removals_applied"].append(approved[method])
        elif method not in base_methods:
            result["methods_behind_default_branch"].append(method)
            retained.add(method)
        elif method in candidate_disabled:
            result["methods_disabled_without_approval"].append(method)
            retained.add(method)
        else:
            result["methods_removed_without_approval"].append(method)
            retained.add(method)
    result["method_additions"] = sorted(candidate_methods - set(methods))
    # Every baseline method still owed, whatever the static reading of the
    # candidate says, must also be seen started by the trusted driver.
    result["required_methods"] = sorted(candidate_methods | retained)
    # A trusted class that runs only inherited tests stays owed while it exists:
    # making it abstract or dropping its superclass in the candidate must not
    # silently stop it from running (it then never enters, which fails).
    result["required_inheriting_classes"] = sorted(
        set(candidate["inheriting"]) | (set(trusted["inheriting"]) & candidate_set)
    )

    if result["removed_without_approval"]:
        result["violations"].append(
            "baseline_test_removed: {} required test class(es) no longer enumerated without a "
            "default-branch approval: {}".format(
                len(result["removed_without_approval"]),
                ",".join(result["removed_without_approval"][:10]),
            )
        )
    shrunk = result["methods_removed_without_approval"] + result["methods_disabled_without_approval"]
    if shrunk:
        result["violations"].append(
            "baseline_test_method_removed: {} required test method(s) deleted, renamed, "
            "un-annotated or disabled without a default-branch approval: {}".format(
                len(shrunk), ",".join(sorted(shrunk)[:10]),
            )
        )
    behind = result["behind_default_branch"] + result["methods_behind_default_branch"]
    if behind:
        result["violations"].append(
            "candidate_behind_default_branch: {} baseline test class(es) or method(s) were added "
            "after the merge base; merge the default branch: {}".format(len(behind), ",".join(behind[:10]))
        )

    candidate_doc, candidate_problems = load_baseline_blob(read_blob(repo, candidate_rev, BASELINE_PATH))
    candidate_summary = {"present": candidate_doc is not None, "problems": candidate_problems}
    result["candidate_baseline"] = candidate_summary
    if candidate_problems:
        result["violations"].append(
            "candidate_corpus_baseline_invalid: {}".format("; ".join(candidate_problems[:5]))
        )
    else:
        unlisted = sorted(candidate_set - set(candidate_doc["entries"]))
        listed_absent = sorted(set(candidate_doc["entries"]) - candidate_set)
        unlisted_methods = sorted(candidate_methods - set(candidate_doc["methods"]))
        listed_methods_absent = sorted(set(candidate_doc["methods"]) - candidate_methods)
        candidate_summary["unlisted"] = unlisted[:50]
        candidate_summary["listed_but_absent"] = listed_absent[:50]
        candidate_summary["unlisted_methods"] = unlisted_methods[:50]
        candidate_summary["listed_methods_absent"] = listed_methods_absent[:50]
        candidate_summary["consistent"] = not (
            unlisted or listed_absent or unlisted_methods or listed_methods_absent
        ) and candidate_doc.get("enumeration_rule") == ENUMERATION_RULE
        if not candidate_summary["consistent"]:
            result["violations"].append(
                "candidate_corpus_baseline_not_updated: the candidate's {} does not describe the "
                "candidate ({} unlisted, {} listed but absent; {} unlisted methods, {} listed "
                "methods absent)".format(
                    BASELINE_PATH, len(unlisted), len(listed_absent),
                    len(unlisted_methods), len(listed_methods_absent),
                )
            )

    result["status"] = "VIOLATION" if result["violations"] else "OK"
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    gen = sub.add_parser("generate", help="write the baseline for an exact commit")
    gen.add_argument("--repo", required=True)
    gen.add_argument("--rev", required=True)
    gen.add_argument("--keep-approvals-from", default="", help="existing baseline whose still-valid approvals are kept")
    gen.add_argument("--out", required=True)

    ev = sub.add_parser("evaluate", help="evaluate a candidate against the trusted baseline")
    ev.add_argument("--repo", required=True)
    ev.add_argument("--trusted", required=True)
    ev.add_argument("--base", required=True)
    ev.add_argument("--candidate", required=True)
    ev.add_argument("--out", required=True)

    args = parser.parse_args()
    if args.command == "generate":
        corpus = corpus_rev(args.repo, args.rev)
        entries, methods = corpus["pairs"], corpus["methods"]
        approvals = []
        if args.keep_approvals_from:
            with open(args.keep_approvals_from, "rb") as handle:
                previous, _ = load_baseline_blob(handle.read())
            known = set(entries) | set(methods)
            approvals = [
                r for r in (previous or {}).get("approved_removals") or [] if r.get("entry") in known
            ]
        doc = build_baseline(entries, approvals, methods)
        with open(args.out, "w", encoding="utf-8") as handle:
            handle.write(json.dumps(doc, indent=1, sort_keys=True) + "\n")
        print("CORPUS_BASELINE entries={} methods={} sha256={} methods_sha256={}".format(
            len(entries), len(methods), doc["entries_sha256"], doc["methods_sha256"]))
        return 0

    try:
        result = evaluate(args.repo, args.trusted, args.base, args.candidate)
    except CorpusError as exc:
        result = {"schema": POLICY_SCHEMA, "status": "UNKNOWN", "unknowns": ["corpus_policy_error: {}".format(exc)]}
    with open(args.out, "w", encoding="utf-8") as handle:
        handle.write(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print("CORPUS_POLICY = {}".format(result["status"]))
    return {"OK": 0, "VIOLATION": 1}.get(result["status"], 2)


if __name__ == "__main__":
    sys.exit(main())
