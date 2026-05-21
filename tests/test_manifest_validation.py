import json
from pathlib import Path
import re

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

def should_skip(path: Path) -> bool:
    ignored = {".git", ".venv", "venv", "__pycache__", ".pytest_cache"}
    return any(part in ignored for part in path.parts)

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


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def test_valid_oic_project_manifest(tmp_path):
    (tmp_path / "oic" / "projects").mkdir(parents=True)
    (tmp_path / "oic" / "projects" / "CUSTOMER_APP.car").write_text("dummy", encoding="utf-8")

    write_json(
        tmp_path / "manifest.json",
        {
            "components": {
                "oic": {
                    "projects": [
                        {"id": "CUSTOMER_APP", "filename": "CUSTOMER_APP.car"}
                    ]
                }
            }
        },
    )

    assert validate_repo(tmp_path) == []


def test_oic_project_requires_car_file(tmp_path):
    write_json(
        tmp_path / "manifest.json",
        {
            "components": {
                "oic": {
                    "projects": [
                        {"id": "CUSTOMER_APP", "filename": "CUSTOMER_APP.zip"}
                    ]
                }
            }
        },
    )

    errors = validate_repo(tmp_path)
    assert any("filename must end with .car" in error for error in errors)


def test_oic_project_referenced_car_must_exist(tmp_path):
    write_json(
        tmp_path / "manifest.json",
        {
            "components": {
                "oic": {
                    "projects": [
                        {"id": "CUSTOMER_APP", "filename": "MISSING.car"}
                    ]
                }
            }
        },
    )

    errors = validate_repo(tmp_path)
    assert any("referenced CAR file not found: MISSING.car" in error for error in errors)


def test_oic_integration_requires_id_and_version(tmp_path):
    write_json(
        tmp_path / "manifest.json",
        {
            "components": {
                "oic": {
                    "integrations": [
                        {"id": "", "version": ""}
                    ]
                }
            }
        },
    )

    errors = validate_repo(tmp_path)
    assert any("OIC integration missing id" in error for error in errors)
    assert any("OIC integration missing version" in error for error in errors)


def test_db_script_requires_existing_sql_and_schema(tmp_path):
    write_json(
        tmp_path / "manifest.json",
        {
            "components": {
                "db": {
                    "scripts": [
                        {"script": "create_customer.sql", "schema": ""}
                    ]
                }
            }
        },
    )

    errors = validate_repo(tmp_path)
    assert any("referenced SQL file not found: create_customer.sql" in error for error in errors)
    assert any("DB script missing schema" in error for error in errors)