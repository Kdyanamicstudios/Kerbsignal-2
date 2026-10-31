"""Verify a test installer in a fresh, explicitly selected directory.

This never runs a normal installation or touches desktop/start-menu shortcuts.
The target must not exist; two /VERIFY installs exercise extraction and repair.
"""
from pathlib import Path
import argparse, hashlib, json, subprocess, zipfile


def verify(installer, target):
    installer, target = Path(installer).resolve(), Path(target).resolve()
    if not installer.is_file():
        raise ValueError('Installer does not exist')
    if target.exists():
        raise ValueError('Choose a fresh verification directory')
    target.mkdir(parents=True)
    previous = target / 'versions/previous-test-runtime'
    previous.mkdir(parents=True)
    (previous / 'keep.txt').write_text('Keep the previous runtime', encoding='utf8')
    (target / 'current.ini').write_text('[App]\nVersion=previous-test-runtime\n', encoding='utf8')

    def install():
        result = subprocess.run([str(installer), '/VERIFY', '/D=' + str(target)], creationflags=0x08000000)
        if result.returncode:
            error = target / 'verification_error.txt'
            raise RuntimeError(error.read_text() if error.exists() else f'Installer exited {result.returncode}')
        version = next(line.split('=', 1)[1] for line in (target / 'current.ini').read_text(encoding='utf-8-sig').splitlines() if line.startswith('Version='))
        runtime = target / 'versions' / version
        if not runtime.resolve().is_relative_to(target):
            raise ValueError('Runtime escaped verification directory')
        subprocess.run([str(target / 'KerbSignal.exe'), '--check'], check=True, creationflags=0x08000000)
        return runtime

    first = install()
    with (first / 'app.py').open('a', encoding='utf8') as stream:
        stream.write('\n# Isolated repair verification marker\n')
    second = install()
    assert first != second and first.is_dir()
    assert (previous / 'keep.txt').read_text(encoding='utf8') == 'Keep the previous runtime'
    project = Path(__file__).resolve().parents[1]
    with zipfile.ZipFile(project / 'KerbSignal_Payload.zip') as archive:
        for item in archive.infolist():
            path = second / item.filename
            assert path.is_file() and path.stat().st_size == item.file_size, item.filename
            with path.open('rb') as actual, archive.open(item) as expected:
                assert hashlib.file_digest(actual, 'sha256').digest() == hashlib.file_digest(expected, 'sha256').digest(), item.filename
        count = len(archive.infolist())
    subprocess.run([str(second / 'python.exe'), str(project / 'windows_build/validate_release.py'), str(second)], check=True)
    record = dict(installer=installer.name, extraction_passed=True, repair_fresh_runtime=True,
        previous_runtime_preserved=True, launcher_check_passed=True, files_sha256_matched=count,
        runtime=str(second), user_installation_modified=False, iracing_tested=False,
        live_driver_speech_tested=False)
    (target / 'verification.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf8')
    print(json.dumps(record), flush=True)
    return record


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--installer', required=True, type=Path)
    parser.add_argument('--target', required=True, type=Path)
    args = parser.parse_args()
    verify(args.installer, args.target)
