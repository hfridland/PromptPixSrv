import os
import sys
from pathlib import Path
from urllib.parse import urlsplit

from dotenv import dotenv_values
from alembic.config import Config
from alembic import command

ROOT = Path(__file__).resolve().parent
env_file = ROOT / ".env.production"

if not env_file.is_file():
    sys.exit("ERROR: .env.production not found")

database_url = dotenv_values(env_file).get("DATABASE_URL")

if not database_url:
    sys.exit("ERROR: DATABASE_URL is missing")

parsed = urlsplit(database_url)

if (
    parsed.scheme != "postgresql+psycopg"
    or not parsed.hostname
    or not parsed.hostname.endswith(".pooler.supabase.com")
    or parsed.path != "/postgres"
):
    sys.exit("ERROR: Expected a Supabase PostgreSQL pooler URL")

print("Target:", parsed.hostname)
print("Database:", parsed.path.lstrip("/"))
print("WARNING: This will apply Alembic migrations to Supabase.")

if input("Type MIGRATE to continue: ").strip() != "MIGRATE":
    sys.exit("Cancelled")

# Override the local .env configuration for this process.
os.environ["DATABASE_URL"] = database_url

os.chdir(ROOT)

config = Config(str(ROOT / "alembic.ini"))
command.upgrade(config, "head")

print("Supabase migrations completed.")
