"""Build a single Nitii 3.0.0 distribution from the two published, pinned inputs."""
import argparse
import ast
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

ROOT = "nitii-logic-suite/"
PLUGIN = "plugins/nitii-logic-suite/"
SKILLS = PLUGIN + "skills/"
VERSION = "3.0.0"
BASE_DIGEST = "c8f50428e0e5794ce82ec3ed073d285581cf137034963d89f333fcec714bff10"
PATCH_DIGEST = "be340122b5af8b5828c2a49eafaf515d06090b877c05a698b01be591829e8233"
SOURCE = Path(__file__).resolve().parent


def digest(data):
    return sha256(data).hexdigest()


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode()


def read_archive(content, prefix=""):
    with ZipFile(BytesIO(content)) as archive:
        files = {}
        for info in archive.infolist():
            if info.is_dir():
                continue
            if not info.filename.startswith(prefix):
                raise ValueError("Unexpected ZIP layout: " + info.filename)
            name = info.filename[len(prefix):]
            if name in files:
                raise ValueError("Duplicate ZIP entry: " + name)
            files[name] = archive.read(info)
        return files


def verified_archive(path, expected, prefix=""):
    data = path.read_bytes()
    if digest(data) != expected:
        raise ValueError("Release checksum differs for " + path.name)
    return read_archive(data, prefix)


def pack(files, prefix=ROOT):
    buffer = BytesIO()
    with ZipFile(buffer, "w") as archive:
        for name, data in sorted(files.items()):
            info = ZipInfo(prefix + name, date_time=(1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data, compress_type=ZIP_DEFLATED, compresslevel=9)
    return buffer.getvalue()


def replace_once(data, old, new):
    old_bytes = old.encode()
    if data.count(old_bytes) != 1:
        raise ValueError("Expected one copy of: " + old[:100])
    return data.replace(old_bytes, new.encode())


def template(name):
    # A Git checkout with autocrlf and one with LF must produce identical bytes.
    return (SOURCE / name).read_text(encoding="utf-8").encode()


def prepare_skills(files, patch):
    knowledge = "nitii-knowledge/SKILL.md"
    previous = {k[len(SKILLS):]: v for k, v in files.items() if k.startswith(SKILLS)}
    skills = previous.copy()
    # Read the published patch's literal replacements without executing its installer.
    tree = ast.parse(patch["enable_auto_update.py"])
    paragraphs = {
        stmt.targets[0].id: ast.literal_eval(stmt.value)
        for stmt in tree.body
        if isinstance(stmt, ast.Assign) and isinstance(stmt.targets[0], ast.Name)
        and stmt.targets[0].id in {"OLD_PARAGRAPH", "NEW_PARAGRAPH"}
    }
    patched_skill = replace_once(previous[knowledge], paragraphs["OLD_PARAGRAPH"],
                                 paragraphs["NEW_PARAGRAPH"])
    skills[knowledge] = replace_once(patched_skill, "Before-use automatic refresh (1.2.1)",
                                     "Before-use automatic refresh")
    skills[knowledge] = replace_once(
        skills[knowledge], "Read only `references/knowledge/snapshot.json` for snapshot scope/date/limits.",
        "Identify the active dataset from the helper's knowledge_update output. "
        "Use `references/knowledge/snapshot.json` for the bundled offline fallback only.")
    skills["nitii-knowledge/scripts/update_knowledge.py"] = patch["update_knowledge.py"]
    router = "nitii-logic/SKILL.md"
    skills[router] = replace_once(
        previous[router],
        "For setup without a work request, read only `../nitii-knowledge/references/knowledge/snapshot.json`; report package version, scope/date and observed host capabilities with one example task.",
        "For setup, report package version 3.0.0, observed host capabilities and one example task. "
        "For the date of the active data, use the nitii-knowledge search/read helper's "
        "knowledge_update output. The packaged snapshot.json describes the offline fallback.")
    deep = "nitii-logic/references/deep-review.md"
    skills[deep] = replace_once(previous[deep], "Current onboarding reads snapshot.json only.",
                                 "Use the current nitii-logic and nitii-knowledge entrypoints for data freshness.")
    baseline = {k: [digest(previous[k])] for k in skills if skills[k] != previous[k]}
    baseline[knowledge].append(digest(patched_skill))
    # The patch's updater is already the distributed file and passes the installer's
    # direct equality check, so its digest needs no separate upgrade exception.
    files.update({SKILLS + k: v for k, v in skills.items()})
    return skills, baseline


def prepare_guides(files):
    files["README_TH.md"] = template("README_3.0_TH.md")
    files["AUTO_UPDATE_TH.md"] = template("AUTO_UPDATE_3.0_TH.md")
    install = files["INSTALL_TH.md"].decode()
    install = install[install.index("# คู่มือติดตั้ง"):].replace("-1.1.0.zip", "-3.0.0.zip")
    start = install.index("อีกทางสำหรับ Codex ที่ใช้ local skills:")
    end = install.index("\n", start)
    install = (install[:start] + "สำหรับโปรเจกต์ Codex ที่ใช้ local skills "
               "ให้รัน `python install_nitii.py --project \"C:/path/to/project\"` จาก ZIP ที่แตกแล้ว "
               "แล้วเริ่มแชทใหม่ในโปรเจกต์ปลายทาง ดู [คู่มือชุดเต็ม](README_TH.md)" + install[end:])
    install = install.replace("## การอัปเดตและนำออก", "## การอัปเดตชุดสกิลและนำออก")
    files["INSTALL_TH.md"] = (install + "\nดู [การอัปเดตข้อมูล Wiki อัตโนมัติก่อนค้น](AUTO_UPDATE_TH.md)\n").encode()
    scope = files["KNOWLEDGE_SCOPE.md"].decode()
    scope = scope.replace("# ขอบเขตฐานความรู้", "# ขอบเขตสำเนาสำรองที่บรรจุใน ZIP", 1)
    scope = scope.replace(" ไม่มีการเผยแพร่ขึ้น repository หรือส่งไปบัญชีอื่นในรอบนี้", "")
    files["KNOWLEDGE_SCOPE.md"] = scope.encode()
    files["TOKEN_USAGE_TH.md"] = replace_once(
        files["TOKEN_USAGE_TH.md"],
        "อ่าน snapshot.json สำหรับขอบเขตสำเนา",
        "ใช้ผล knowledge_update จากตัวค้นและตัวอ่านสำหรับวันที่ของข้อมูลที่ใช้งาน และใช้ snapshot.json สำหรับขอบเขตสำเนาสำรอง")
    web = "web-assistants/INSTRUCTIONS_TH.txt"
    files[web] = replace_once(files[web],
                             "Use the immutable manifestPath and relevant pages under its snapshot folder;",
                             "Read the published archive at archivePath where the host supports it. Otherwise use the uploaded snapshot and report its date;")
    gemini = PLUGIN + "GEMINI.md"
    files[gemini] = replace_once(files[gemini], "snapshot summary → compact search → bounded passages",
                                 "run the nitii-knowledge search helper → inspect knowledge_update → read bounded passages")


def build(base, patch_path, out):
    files = verified_archive(base, BASE_DIGEST, ROOT)
    patch = verified_archive(patch_path, PATCH_DIGEST)
    standalone = read_archive(files.pop("packages/nitii-logic-suite-skill-1.2.0.zip"), ROOT)
    del files["packages/nitii-logic-suite-plugin-1.2.0.zip"]
    skills, baseline = prepare_skills(files, patch)
    prepare_guides(files)
    files["VERSION"] = (VERSION + "\n").encode()
    files["install_nitii.py"] = template("install_nitii.py")
    files["install-baseline.json"] = json_bytes(baseline)
    for name in ["plugin.json", ".claude-plugin/plugin.json", "gemini-extension.json"]:
        path = PLUGIN + name
        metadata = json.loads(files[path])
        metadata["version"] = VERSION
        files[path] = json_bytes(metadata)
    plugin = {k[len(PLUGIN):]: v for k, v in files.items() if k.startswith(PLUGIN)}
    standalone.update({"modules/" + k: v for k, v in skills.items()})
    standalone["SCOPE.md"] = files["KNOWLEDGE_SCOPE.md"]
    standalone["AUTO_UPDATE_TH.md"] = files["AUTO_UPDATE_TH.md"]
    standalone["SKILL.md"] = replace_once(
        standalone["SKILL.md"],
        "Setup needs only `modules/nitii-knowledge/references/knowledge/snapshot.json`.",
        "For data freshness, use the helper's knowledge_update output and report the checkedAtUtc of a successful check or the snapshotCapturedAtUtc of a stale fallback.")
    for role, package in [("skill", standalone), ("plugin", plugin)]:
        files[f"packages/nitii-logic-suite-{role}-{VERSION}.zip"] = pack(package)
    full = pack(files)
    out.mkdir(parents=True, exist_ok=True)
    release = out / f"Nitii_Logic_Suite_{VERSION}.zip"
    release.write_bytes(full)
    (out / "SHA256SUMS.txt").write_bytes((digest(full) + "  " + release.name + "\n").encode())
    print(f"{release}  {len(full)} bytes  {digest(full)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path, required=True, help="Full public v1.2.0 ZIP")
    parser.add_argument("--patch", type=Path, required=True, help="Public v1.2.1 patch ZIP")
    parser.add_argument("--out", type=Path, required=True, help="Directory for release files")
    args = parser.parse_args()
    build(args.base, args.patch, args.out)
