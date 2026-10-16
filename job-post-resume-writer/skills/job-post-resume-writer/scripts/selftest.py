#!/usr/bin/env python3
"""Run the whole tool chain on the repository's examples/ folder (fictional persona).

Usage:
    python3 selftest.py [--out DIR] [--keep]

Steps: extract_text (resume.md) → jd_match → cv_check --strict → md_to_cvjson → build-cv.js
(→ PDF when LibreOffice is on PATH). Steps that need a missing dependency are reported as SKIP,
never as failure. Exit 1 if any step FAILs.

Works both inside the cloned repository (examples/ two levels up) and from an installed skill
folder when --examples points at a copy of examples/.
"""
import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_EXAMPLES = HERE.parents[2] / "examples"
PY = sys.executable


def run(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--examples", type=Path, default=DEFAULT_EXAMPLES)
    ap.add_argument("--out", type=Path, help="where to write the generated files (default: a temp folder)")
    ap.add_argument("--keep", action="store_true", help="keep the temp folder")
    a = ap.parse_args()

    ex = a.examples
    needed = ["resume.md", "jd.md", "facts.md", "voice.md", "cv.md"]
    missing = [n for n in needed if not (ex / n).exists()]
    if missing:
        print(f"examples folder {ex} is missing: {', '.join(missing)}")
        return 2
    out = a.out or Path(tempfile.mkdtemp(prefix="jprw-selftest-"))
    out.mkdir(parents=True, exist_ok=True)
    results = []

    def record(name, status, detail=""):
        results.append((name, status, detail))
        print(f"{status:4} {name}" + (f" — {detail}" if detail else ""))

    # 1 extract
    code, log = run([PY, str(HERE / "extract_text.py"), str(ex / "resume.md"), "--out", str(out / "resume.txt")])
    record("extract_text", "PASS" if code == 0 else "FAIL", log.strip().splitlines()[-1] if log.strip() else "")

    # 2 match
    code, log = run([PY, str(HERE / "jd_match.py"), str(ex / "jd.md"), "--facts", str(ex / "facts.md")])
    (out / "match-terms.txt").write_text(log, encoding="utf-8")
    ok = code == 0 and "MAPPED (" in log and "GAPS (" in log
    record("jd_match", "PASS" if ok else "FAIL", "MAPPED/GAPS/UNUSED written to match-terms.txt" if ok else log.strip()[-200:])

    # 3 check
    code, log = run([PY, str(HERE / "cv_check.py"), str(ex / "cv.md"), "--jd", str(ex / "jd.md"),
                     "--facts", str(ex / "facts.md"), "--voice", str(ex / "voice.md"), "--strict"])
    (out / "cv-check.txt").write_text(log, encoding="utf-8")
    summary = next((ln for ln in log.splitlines() if ln.endswith("WARN")), "")
    record("cv_check --strict", "PASS" if code == 0 else "FAIL", summary)

    # 4 json
    code, log = run([PY, str(HERE / "md_to_cvjson.py"), str(ex / "cv.md"), str(out / "cv.json")])
    record("md_to_cvjson", "PASS" if code == 0 else "FAIL", log.strip().splitlines()[-1] if log.strip() else "")

    # 5 docx (+pdf)
    node = shutil.which("node")
    if not node:
        record("build-cv.js", "SKIP", "node not on PATH (docx/pdf output unavailable; Markdown CV still works)")
    else:
        flags = ["--pdf"] if shutil.which("soffice") else []
        code, log = run([node, str(HERE / "build-cv.js"), str(out / "cv.json"), str(out / "cv.docx"), *flags], cwd=str(HERE))
        if code != 0 and "Could not load 'docx'" in log:
            record("build-cv.js", "SKIP", "docx package not installed: run `npm install` in scripts/")
        else:
            last = log.strip().splitlines()[-1] if log.strip() else ""
            record("build-cv.js", "PASS" if code == 0 and (out / "cv.docx").exists() else "FAIL", last)
            if not flags:
                record("pdf", "SKIP", "soffice (LibreOffice) not on PATH")
            elif (out / "cv.pdf").exists():
                record("pdf", "PASS", last)
            else:
                record("pdf", "FAIL", "no cv.pdf produced")

    fails = [r for r in results if r[1] == "FAIL"]
    skips = [r for r in results if r[1] == "SKIP"]
    print(f"\n{len(results) - len(fails) - len(skips)} passed, {len(fails)} failed, {len(skips)} skipped. Output: {out}")
    if not a.out and not a.keep and not fails:
        shutil.rmtree(out, ignore_errors=True)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
