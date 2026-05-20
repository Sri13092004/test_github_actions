import json
from pathlib import Path

from scripts.ci.validate_oracle_repo import validate_repo


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