"""Install or upgrade the Nitii 3.0 project skills from the extracted release ZIP."""
import argparse
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import sys
import uuid


VERSION = "3.0.0"
SKILLS = {"nitii-" + name for name in (
    "logic", "knowledge", "solution", "qa", "sa", "po", "pm", "uxui",
    "backend", "frontend", "explain")}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def filesystem_path(path):
    absolute = os.path.abspath(path.expanduser())
    if os.name == "nt" and not absolute.startswith("\\\\?\\"):
        if absolute.startswith("\\\\"):
            absolute = "\\\\?\\UNC\\" + absolute[2:]
        else:
            absolute = "\\\\?\\" + absolute
    return Path(absolute)


def reject_links(path):
    for item in (path, *path.parents):
        try:
            entry = item.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(entry.st_mode) or getattr(entry, "st_file_attributes", 0) & 0x400:
            raise ValueError(f"Linked installation path: {item}")


@contextmanager
def install_lock(directory):
    path = directory / ".nitii-install.lock"
    reject_links(path)
    with path.open("a+b") as handle:
        if os.name == "nt":
            import msvcrt
            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield


def install(project, skills_dir=None):
    package = filesystem_path(Path(__file__).parent)
    source = package / "plugins" / "nitii-logic-suite" / "skills"
    if {p.name for p in source.iterdir() if p.is_dir()} != SKILLS:
        raise ValueError("Extract the complete Nitii 3.0 release ZIP before installing")
    baseline = json.loads((package / "install-baseline.json").read_bytes())
    if skills_dir is None:
        project = filesystem_path(project)
        if not project.is_dir() or project.resolve() == package.resolve():
            raise ValueError("Select the existing project where you use Nitii")
        target = project / ".agents" / "skills"
    else:
        target = filesystem_path(skills_dir)
    reject_links(target)
    if source.resolve() == target.resolve() or source.resolve() in target.resolve().parents:
        raise ValueError("The installation directory must be outside the packaged skills")
    target.mkdir(parents=True, exist_ok=True)
    with install_lock(target):
        fresh = sorted(name for name in SKILLS if not (target / name).exists())
        changes, kept, conflicts = [], [], []
        for src in sorted(source.rglob("*")):
            rel = src.relative_to(source)
            dst = target / rel
            reject_links(dst)
            if src.is_dir():
                if dst.exists() and not dst.is_dir():
                    raise ValueError(f"Expected a directory at {dst}")
                continue
            if rel.parts[0] in fresh:
                continue
            if not dst.exists():
                changes.append((rel, None))
                continue
            prior = digest(dst)
            if prior == digest(src):
                continue
            if prior in baseline.get(rel.as_posix(), []):
                changes.append((rel, prior))
            elif rel.parts[0] == "nitii-knowledge" and (
                    rel.parts[1] == "scripts" or rel.as_posix() == "nitii-knowledge/SKILL.md"):
                conflicts.append(rel.as_posix())
            else:
                kept.append(rel.as_posix())
        if conflicts:
            raise ValueError("Custom knowledge files require review. Installation stopped: " +
                             ", ".join(conflicts))
        status = "current"
        if fresh or changes:
            apply_changes(source, target, fresh, changes)
            status = "installed" if len(fresh) == len(SKILLS) else "upgraded"
        return {"status": status, "version": VERSION, "skills": len(SKILLS),
                "target": str(target), "preservedCustomFiles": kept}


def apply_changes(source, target, fresh, changes):
    stage = target / (".nitii-stage-" + uuid.uuid4().hex)
    stage.mkdir()
    new = stage / "new"
    old = stage / "original"
    written, added = [], []
    clean_stage = True
    try:
        for name in fresh:
            shutil.copytree(source / name, new / name)
        for rel, prior in changes:
            (new / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source / rel, new / rel)
            if prior is not None:
                (old / rel).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(target / rel, old / rel)
        for rel, prior in changes:
            dst = target / rel
            reject_links(dst)
            if (digest(dst) if dst.exists() else None) != prior:
                raise ValueError(f"File changed during installation: {rel}")
            dst.parent.mkdir(parents=True, exist_ok=True)
            os.replace(new / rel, dst)
            written.append((rel, prior))
        for name in fresh:
            if (target / name).exists():
                raise ValueError(f"Skill appeared during installation: {name}")
            (new / name).rename(target / name)
            added.append(name)
    except BaseException:
        clean_stage = False
        for name in reversed(added):
            (target / name).rename(new / name)
        for rel, prior in reversed(written):
            if prior is None:
                (target / rel).unlink()
            else:
                os.replace(old / rel, target / rel)
        clean_stage = True
        raise
    finally:
        if clean_stage and stage.resolve().parent == target.resolve():
            shutil.rmtree(stage)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--project", "--install-root", type=Path,
                       help="Existing Codex project; installs into its .agents/skills")
    group.add_argument("--skills-dir", type=Path, help="Explicit destination for the 11 skills")
    args = parser.parse_args()
    try:
        project = args.project
        if project is None and args.skills_dir is None:
            value = input("Project folder where you use Nitii: ").strip().strip('"')
            if not value:
                raise ValueError("A project folder is required")
            project = Path(value)
        print(json.dumps(install(project, args.skills_dir), ensure_ascii=True))
        return 0
    except (OSError, ValueError, EOFError) as error:
        print(json.dumps({"status": "error", "error": str(error)}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
