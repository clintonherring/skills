#!/usr/bin/env python3
"""Installer for the job-post-resume-writer and my-voice skills.

Python 3.8+ standard library only. Works on macOS, Linux and Windows.

    python3 install.py                 interactive install
    python3 install.py --check         dependency check only
    python3 install.py --upgrade       re-copy skills; never touches the data folder
    python3 install.py --uninstall     remove the skills; keeps the data folder
    python3 install.py --ide cursor --data ~/ResumeData --yes   non-interactive

What it does:
  1. asks which agent you use and copies skills/* to its skills folder
     (or prints manual steps for agents that cannot read local folders)
  2. asks where your private data should live and creates it from templates
  3. checks dependencies and says which are optional
  4. writes ~/.job-post-resume-writer/config.json
"""
import argparse
import datetime as dt
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILLS_SRC = HERE / "skills"
SKILL_NAMES = ["job-post-resume-writer", "my-voice"]
CONFIG_DIR = Path.home() / ".job-post-resume-writer"
CONFIG_PATH = CONFIG_DIR / "config.json"
TEMPLATES = SKILLS_SRC / "job-post-resume-writer" / "templates"
VOICE_TEMPLATE = SKILLS_SRC / "my-voice" / "templates" / "voice.template.md"

IDES = {
    "cursor": ("Cursor", Path.home() / ".cursor" / "skills"),
    "claude-code": ("Claude Code", Path.home() / ".claude" / "skills"),
    "claude-desktop": ("Claude Desktop (manual upload)", None),
    "other": ("Other agent (I will point it at the folder myself)", None),
}


def say(msg=""):
    print(msg)


def ask(prompt, default=None):
    suffix = f" [{default}]" if default else ""
    try:
        val = input(f"{prompt}{suffix}: ").strip()
    except EOFError:
        val = ""
    return val or default


def which(cmd):
    return shutil.which(cmd) is not None


def run_ok(args, cwd=None):
    try:
        subprocess.run(args, cwd=cwd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception:
        return False


def check_deps(install_docx=False, skills_dir=None):
    deps = {}
    deps["python"] = sys.version_info >= (3, 8)
    deps["node"] = which("node") and which("npm")
    deps["soffice"] = which("soffice") or which("libreoffice") or bool(_mac_soffice())
    deps["pdftotext"] = which("pdftotext")
    try:
        import pypdf  # noqa: F401
        deps["pypdf"] = True
    except Exception:
        deps["pypdf"] = False

    # The repository checkout is never written to: the package is installed into the copied skill only.
    if skills_dir is None:
        deps["docx_package"] = False
        return deps
    scripts_dir = skills_dir / "job-post-resume-writer" / "scripts"
    deps["docx_package"] = (scripts_dir / "node_modules" / "docx").exists()
    if install_docx and deps["node"] and not deps["docx_package"]:
        say("  installing the 'docx' package for .docx output (npm install) ...")
        npm = "npm.cmd" if platform.system() == "Windows" else "npm"
        if run_ok([npm, "install", "--silent", "--no-audit", "--no-fund"], cwd=str(scripts_dir)):
            deps["docx_package"] = (scripts_dir / "node_modules" / "docx").exists()
        else:
            say("  npm install failed; you can run it later in " + str(scripts_dir))
    return deps


def _mac_soffice():
    p = Path("/Applications/LibreOffice.app/Contents/MacOS/soffice")
    return str(p) if p.exists() else ""


def report_deps(deps):
    rows = [
        ("Python 3.8+", deps["python"], "required", "install from python.org"),
        ("Node.js + npm", deps["node"], "only for .docx output", "install from nodejs.org, then rerun with --upgrade"),
        ("docx package (npm)", deps["docx_package"], "only for .docx output",
         "run npm install in the installed skill's scripts/ folder; not used without a skills folder"),
        ("LibreOffice (soffice)", deps["soffice"], "only for .pdf output", "install LibreOffice, or export PDF from Word"),
        ("pdftotext (poppler)", deps["pdftotext"], "optional: read a PDF base CV", "or paste the CV text into the chat"),
        ("pypdf (python)", deps["pypdf"], "optional: read a PDF base CV", "pip install pypdf, or paste the text"),
    ]
    say("\nDependencies")
    for name, ok, when, hint in rows:
        mark = "ok  " if ok else "--  "
        line = f"  {mark}{name:<24} {when}"
        if not ok:
            line += f"  ({hint})"
        say(line)
    if not deps["python"]:
        say("\nPython 3.8 or newer is required.")
        return False
    return True


def copy_skills(skills_dir):
    skills_dir.mkdir(parents=True, exist_ok=True)
    for name in SKILL_NAMES:
        src = SKILLS_SRC / name
        dst = skills_dir / name
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst, ignore=shutil.ignore_patterns("node_modules", "__pycache__", "*.pyc"))
        say(f"  copied {name} -> {dst}")


def remove_skills(skills_dir):
    for name in SKILL_NAMES:
        dst = skills_dir / name
        if dst.exists():
            shutil.rmtree(dst)
            say(f"  removed {dst}")


def create_data_dir(data_dir):
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "applications").mkdir(exist_ok=True)
    facts = data_dir / "facts.md"
    voice = data_dir / "voice.md"
    if not facts.exists():
        shutil.copy(TEMPLATES / "facts.template.md", facts)
        say(f"  created {facts}")
    else:
        say(f"  kept existing {facts}")
    if not voice.exists():
        shutil.copy(VOICE_TEMPLATE, voice)
        say(f"  created {voice}")
    else:
        say(f"  kept existing {voice}")


def load_config():
    if CONFIG_PATH.exists():
        try:
            return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save_config(cfg):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")
    say(f"  wrote {CONFIG_PATH}")


def manual_instructions(ide):
    say("\nManual setup")
    if ide == "claude-desktop":
        say("  Claude Desktop cannot read local skill folders or run scripts.")
        say("  1. Create a Project in Claude Desktop (e.g. 'Resume').")
        say(f"  2. Add these files as project knowledge: {SKILLS_SRC / 'job-post-resume-writer' / 'SKILL.md'}")
        say(f"     and everything under {SKILLS_SRC / 'job-post-resume-writer' / 'references'} and 'templates',")
        say(f"     plus {SKILLS_SRC / 'my-voice' / 'SKILL.md'} and its templates folder.")
        say("  3. In the project instructions write: 'Follow SKILL.md for job-post-resume-writer and my-voice.")
        say("     My facts and voice files are pasted in this project; do not run scripts.'")
        say("  4. Paste your CV text when asked; keep facts.md and voice.md as project files you update by hand.")
    else:
        say(f"  Point your agent at: {SKILLS_SRC / 'job-post-resume-writer' / 'SKILL.md'}")
        say(f"  and:                 {SKILLS_SRC / 'my-voice' / 'SKILL.md'}")
        say("  The scripts expect ~/.job-post-resume-writer/config.json (written below).")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="dependency check only")
    ap.add_argument("--upgrade", action="store_true", help="re-copy skills using the saved config; keep data")
    ap.add_argument("--uninstall", action="store_true", help="remove skills; keep data")
    ap.add_argument("--ide", choices=list(IDES), help="agent to install for")
    ap.add_argument("--data", help="data folder for facts, voice and applications")
    ap.add_argument("--skills-dir", help="override the skills folder")
    ap.add_argument("--yes", action="store_true", help="accept defaults without prompting")
    a = ap.parse_args()

    say("job-post-resume-writer installer")
    say(f"platform: {platform.system()} {platform.release()}  python: {platform.python_version()}")

    if a.check:
        prev_dir = load_config().get("skills_dir")
        deps = check_deps(skills_dir=Path(prev_dir).expanduser() if prev_dir else None)
        return 0 if report_deps(deps) else 1

    cfg = load_config()

    if a.uninstall:
        sd = Path(a.skills_dir or cfg.get("skills_dir", "")).expanduser() if (a.skills_dir or cfg.get("skills_dir")) else None
        if not sd:
            say("No skills_dir in config; nothing to remove.")
            return 0
        remove_skills(sd)
        say(f"Data folder kept: {cfg.get('data_dir', '(unknown)')}")
        return 0

    if a.upgrade and cfg:
        ide = cfg.get("ide", "other")
        skills_dir = Path(cfg["skills_dir"]).expanduser() if cfg.get("skills_dir") else None
        data_dir = Path(cfg["data_dir"]).expanduser()
    else:
        ide = a.ide
        if not ide:
            say("\nWhich agent do you use?")
            keys = list(IDES)
            for i, k in enumerate(keys, 1):
                say(f"  {i}. {IDES[k][0]}")
            choice = ask("Number", "1") if not a.yes else "1"
            try:
                ide = keys[int(choice) - 1]
            except Exception:
                ide = "other"
        default_skills = IDES[ide][1]
        if a.skills_dir:
            skills_dir = Path(a.skills_dir).expanduser()
        elif default_skills is None:
            skills_dir = None
        else:
            skills_dir = Path(ask("Skills folder", str(default_skills)) if not a.yes else default_skills).expanduser()

        default_data = cfg.get("data_dir") or str(Path.home() / "ResumeData")
        data_dir = Path(a.data or (ask("Where should your private data live (facts, voice, CVs)?", default_data) if not a.yes else default_data)).expanduser()

    say("\nSkills")
    if skills_dir is None:
        manual_instructions(ide)
    else:
        copy_skills(skills_dir)

    say("\nData folder")
    create_data_dir(data_dir)

    deps = check_deps(install_docx=True, skills_dir=skills_dir)
    ok = report_deps(deps)

    cfg = {
        "version": 1,
        "ide": ide,
        "skills_dir": str(skills_dir) if skills_dir else None,
        "data_dir": str(data_dir),
        "locale": "eu",
        "deps": deps,
        "installed_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }
    say("\nConfig")
    save_config(cfg)

    say("\nDone." if ok else "\nDone, with missing requirements above.")
    say("Open your agent and say:  set up my resume")
    if ide == "claude-desktop":
        say("(In Claude Desktop, paste the contents of facts.template.md when the skill asks for your facts file.)")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
