"""Read-only configuration and service health check."""
from __future__ import annotations

import os

import dropbox
from dotenv import load_dotenv
from supabase import create_client

from integrations.rag.config import require_supabase_config


def main() -> None:
    load_dotenv()
    token = os.getenv("DROPBOX_ACCESS_TOKEN", "").strip()
    if not token:
        raise SystemExit("DROPBOX_ACCESS_TOKEN is missing. Add it to Codespaces secrets and restart the Codespace.")

    dbx = dropbox.Dropbox(oauth2_access_token=token)
    account = dbx.users_get_current_account()
    print(f"Dropbox OK: authenticated account {account.name.display_name}")

    url, key = require_supabase_config()
    sb = create_client(url, key)
    status = sb.rpc("rag_connector_health").execute()
    print(f"Supabase OK: {status.data}")


if __name__ == "__main__":
    main()
