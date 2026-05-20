import json
import re
import sys
from pathlib import Path


def should_skip(path: Path) -> bool:
    ignored = {".git", ".venv", "venv", "__pycache__", ".pytest_cache"}
    return any(part in ignored for part in path.parts)


def find_file(root: Path, name: str) -> bool:
    return any(p.name == name for p in root.rglob(name) if not should_skip(p))


def validate_manifest(root: Path, manifest_path: Path) -> list[str]:
    errors = []

    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return [f"{manifest_path}: invalid JSON: {exc}"]

    components = data.get("components")
    if not isinstance(components, dict):
        return [f"{manifest_path}: missing object field components"]

    oic = components.get("oic", {})
    for project in oic.get("projects", []):
        project_id = project.get("id")
        filename = project.get("filename")

        if not project_id:
            errors.append(f"{manifest_path}: OIC project missing id")
        if not filename or not filename.endswith(".car"):
            errors.append(f"{manifest_path}: OIC project filename must end with .car")
        elif not find_file(root, filename):
            errors.append(f"{manifest_path}: referenced CAR file not found: {filename}")

    for integration in oic.get("integrations", []):
        if not integration.get("id"):
            errors.append(f"{manifest_path}: OIC integration missing id")
        if not integration.get("version"):
            errors.append(f"{manifest_path}: OIC integration missing version")

    db = components.get("db", {})
    for script in db.get("scripts", []):
        script_name = script.get("script")
        schema = script.get("schema")

        if not script_name or not script_name.endswith(".sql"):
            errors.append(f"{manifest_path}: DB script must end with .sql")
        elif not find_file(root, script_name):
            errors.append(f"{manifest_path}: referenced SQL file not found: {script_name}")

        if not schema:
            errors.append(f"{manifest_path}: DB script missing schema")

    return errors


def scan_for_secrets(root: Path) -> list[str]:
    errors = []
    pattern = re.compile(r"(api[_-]?key|token|password|secret)\s*=\s*['\"][^'\"]{12,}['\"]", re.I)

    for path in root.rglob("*"):
        if should_skip(path) or not path.is_file():
            continue
        if path.suffix.lower() not in {".py", ".json", ".txt", ".yml", ".yaml"}:
            continue

        text = path.read_text(encoding="utf-8", errors="ignore")
        if pattern.search(text):
            errors.append(f"{path}: possible hardcoded secret found")

    return errors


def validate_repo(root: Path) -> list[str]:
    errors = []

    manifests = [p for p in root.rglob("manifest.json") if not should_skip(p)]
    if not manifests:
        errors.append("manifest.json not found")

    for manifest in manifests:
        errors.extend(validate_manifest(root, manifest))

    errors.extend(scan_for_secrets(root))
    return errors


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    errors = validate_repo(root)

    if errors:
        print("Validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Oracle repository validation passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())