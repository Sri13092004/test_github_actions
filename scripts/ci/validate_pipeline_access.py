import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
USERS_FILE = ROOT / "config" / "users.json"
REQUESTS_DIR = ROOT / "pipeline_requests"


def load_users():
    data = json.loads(USERS_FILE.read_text(encoding="utf-8"))
    return {user["username"]: user for user in data["users"]}


def validate_request(path: Path, users: dict) -> list[str]:
    errors = []
    request = json.loads(path.read_text(encoding="utf-8"))

    requested_by = request.get("requested_by")
    action = request.get("action")
    environment = request.get("environment")

    if not requested_by:
        errors.append(f"{path}: requested_by is required")
        return errors

    user = users.get(requested_by)
    if not user:
        errors.append(f"{path}: unknown user '{requested_by}'")
        return errors

    if action not in user.get("allowed_actions", []):
        errors.append(
            f"{path}: user '{requested_by}' is not allowed to run action '{action}'"
        )

    if environment not in user.get("allowed_environments", []):
        errors.append(
            f"{path}: user '{requested_by}' is not allowed to deploy to '{environment}'"
        )

    if environment == "prod" and user.get("role") != "release_manager":
        errors.append(
            f"{path}: only release_manager can submit prod deployments"
        )

    return errors


def main():
    errors = []

    if not USERS_FILE.exists():
        errors.append("config/users.json is missing")
    else:
        users = load_users()

        if REQUESTS_DIR.exists():
            for request_file in REQUESTS_DIR.glob("*.json"):
                errors.extend(validate_request(request_file, users))

    if errors:
        print("Access validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Access validation passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())