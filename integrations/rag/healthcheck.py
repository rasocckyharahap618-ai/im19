"""Read-only configuration and service health check."""
from __future__ import annotations

import os
from dotenv import load_dotenv
from supabase import create_client
import dropbox


def main() -> None:
    load_dotenv()
    required = ["DROPBOX_ACCESS_TOKEN", "SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY"]
    missing = [key for key in required if not os.getenv(key, "").strip()]
    if missing:
        raise SystemExit("Missing environment variables: " + ", ".join(missing))
    dbx = dropbox.Dropbox(oauth2_access_token=os.environ["DROPBOX_ACCESS_TOKEN"])
    account = dbx.users_get_current_account()
    print(f"Dropbox OK: authenticated account {account.name.display_name}")
    sb = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_ROLE_KEY"])
    docs = sb.table("rag_documents").select("id", count="exact").limit(1).execute()
    chunks = sb.table("rag_chunks").select("id", count="exact").limit(1).execute()
    print(f"Supabase OK: rag_documents={docs.count}, rag_chunks={chunks.count}")


if __name__ == "__main__":
    main()
