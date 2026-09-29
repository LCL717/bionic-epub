"""File discovery and safe output planning for batch commands."""
from pathlib import Path


def discover(inputs: list[str], recursive: bool, exclude: Path | None = None):
    files: dict[Path, Path] = {}
    errors: list[tuple[str, str]] = []
    excluded = exclude.resolve() if exclude else None
    for value in inputs:
        path = Path(value)
        try:
            if path.is_dir():
                if excluded == path.resolve():
                    errors.append((value, "Input and output directories must be different"))
                    continue
                candidates = sorted(path.rglob("*") if recursive else path.iterdir())
                found = []
                for candidate in candidates:
                    resolved = candidate.resolve()
                    if excluded and (resolved == excluded or excluded in resolved.parents):
                        continue
                    if candidate.is_file() and candidate.suffix.lower() == ".epub":
                        found.append(candidate)
                if not found:
                    errors.append((value, "No EPUB files found"))
                for candidate in found:
                    files.setdefault(candidate.resolve(), candidate)
            elif path.is_file() and path.suffix.lower() == ".epub":
                files.setdefault(path.resolve(), path)
            else:
                errors.append((value, "Expected an EPUB file or directory"))
        except OSError as error:
            errors.append((value, str(error)))
    return list(files.values()), errors
