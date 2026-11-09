"""Build the small one-time migration ZIP; no network or credentials."""
from pathlib import Path
import argparse
import hashlib
import zipfile
import enable_auto_update as patch


def build(output):
    root = Path(__file__).resolve().parent
    patch.payload()  # Verify the installer's pinned payload digest before delivery.
    output.mkdir(parents=True, exist_ok=True)
    destination = output / 'Nitii_Auto_Update_Patch_1.2.1.zip'
    names = ('enable_auto_update.py', 'update_knowledge.py', 'AUTO_UPDATE_PATCH_TH.md')
    checksums = '\n'.join(hashlib.sha256((root / name).read_bytes()).hexdigest() + '  ' + name for name in names) + '\n'
    with zipfile.ZipFile(destination, 'w', zipfile.ZIP_DEFLATED) as archive:
        for name in names:
            archive.writestr(name, (root / name).read_bytes())
        archive.writestr('SHA256SUMS.txt', checksums.encode('utf-8'))
    digest = hashlib.sha256(destination.read_bytes()).hexdigest()
    (output / 'SHA256SUMS.txt').write_text(digest + '  ' + destination.name + '\n', encoding='utf-8')
    return destination


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(build(args.output).resolve())
