"""Build and smoke-test a portable Windows CLI. Run through build.cmd."""
from pathlib import Path
import hashlib
import os
import runpy
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def run(*args, cwd=ROOT, **kwargs):
    subprocess.run([str(arg) for arg in args], cwd=cwd, check=True, **kwargs)


def main():
    if sys.platform != "win32":
        raise SystemExit("Build this Windows executable on Windows.")
    python = ROOT / ".venv/Scripts/python.exe"
    if not python.exists():
        run(sys.executable, "-m", "venv", ROOT / ".venv")
    if Path(sys.executable).resolve() != python.resolve():
        run(python, Path(__file__).resolve())
        return
    run(python, "-m", "pip", "install", "-e", ".[test,build]")
    run(python, "-m", "pytest", "-q")
    run(python, "-m", "PyInstaller", "--noconfirm", "--clean", "--onefile",
        "--console", "--noupx", "--name", "bionic-epub",
        "--paths", ROOT / "src", "--distpath", ROOT / "dist",
        "--workpath", ROOT / "build/pyinstaller", "--specpath", ROOT / "build",
        ROOT / "scripts/cli_entry.py")
    exe = ROOT / "dist/bionic-epub.exe"
    # Exercise the frozen executable outside the source tree without Python paths.
    env = dict(os.environ)
    for key in ("PYTHONPATH", "PYTHONHOME", "VIRTUAL_ENV"):
        env.pop(key, None)
    with tempfile.TemporaryDirectory(prefix="bionic-smoke-") as folder:
        temp = Path(folder)
        source = temp / "sample book.epub"
        output = temp / "sample bionic.epub"
        runpy.run_path(str(ROOT / "tests/test_epub_io.py"))["_create_epub"](source)
        before = source.read_bytes()
        run(exe, "--help", cwd=temp, env=env, stdout=subprocess.DEVNULL)
        run(exe, "preview", "The quick brown fox", cwd=temp, env=env)
        run(exe, "convert", source, "-o", output, cwd=temp, env=env)
        run(exe, "validate", output, cwd=temp, env=env)
        batch_out = temp / "batch output"
        run(exe, "batch-convert", source, "-o", batch_out, cwd=temp, env=env)
        run(exe, "batch-validate", batch_out, cwd=temp, env=env)
        assert (batch_out / "sample book-bionic.epub").exists()
        with zipfile.ZipFile(output) as archive:
            assert b"<strong>The</strong>" in archive.read("OEBPS/chapter.xhtml")
        assert source.read_bytes() == before
        refused = subprocess.run([str(exe), "convert", str(source), "-o", str(output)],
                                 cwd=temp, env=env, capture_output=True)
        assert refused.returncode != 0, "Existing output must not be overwritten"
    bundle = ROOT / "dist/bionic-epub-windows-portable.zip"
    with zipfile.ZipFile(bundle, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.write(exe, exe.name)
        archive.write(ROOT / "README.md", "README.md")
    sums = [hashlib.sha256(p.read_bytes()).hexdigest() + "  " + p.name for p in (exe, bundle)]
    (ROOT / "dist/SHA256SUMS.txt").write_text("\n".join(sums) + "\n", encoding="utf-8")
    print(f"Build and smoke tests passed: {exe}")
    print(f"Portable ZIP: {bundle}")


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as error:
        raise SystemExit(error.returncode)
