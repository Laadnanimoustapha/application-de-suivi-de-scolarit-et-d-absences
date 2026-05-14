"""
Supabase Storage utility module.

Handles file uploads to the 'justifications' bucket in Supabase Storage.
Files are stored with a unique path based on student ID and timestamp.
The public URL is returned for storage in the MySQL database.
"""

import os
import uuid
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

BUCKET_NAME = "justifications"

# Allowed file extensions for medical documents
ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg", "webp"}
MAX_FILE_SIZE_MB = 5


def _get_supabase_client():
    """Lazy initialization of the Supabase client to avoid import-time failures."""
    from supabase import create_client
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables.")
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def _is_allowed_file(filename):
    """Validates the file extension against the whitelist."""
    if "." not in filename:
        return False
    extension = filename.rsplit(".", 1)[1].lower()
    return extension in ALLOWED_EXTENSIONS


def _generate_storage_path(eleve_id, filename):
    """
    Generates a unique, organized path for the file inside the bucket.
    Format: eleve_{id}/{year}/{uuid}.{ext}
    """
    extension = filename.rsplit(".", 1)[1].lower()
    year = datetime.now().strftime("%Y")
    unique_name = f"{uuid.uuid4().hex}.{extension}"
    return f"eleve_{eleve_id}/{year}/{unique_name}"


def upload_justification(eleve_id, file_data, filename):
    """
    Uploads a justification file to Supabase Storage.

    Args:
        eleve_id: The student's database ID.
        file_data: The raw file bytes.
        filename: The original filename (used for extension detection).

    Returns:
        dict: {"success": True, "url": "https://..."} on success.
              {"success": False, "error": "..."} on failure.
    """
    # Validate extension
    if not _is_allowed_file(filename):
        return {
            "success": False,
            "error": f"Type de fichier non autorise. Formats acceptes: {', '.join(ALLOWED_EXTENSIONS)}"
        }

    # Validate size
    size_mb = len(file_data) / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        return {
            "success": False,
            "error": f"Fichier trop volumineux ({size_mb:.1f} MB). Maximum: {MAX_FILE_SIZE_MB} MB."
        }

    try:
        client = _get_supabase_client()
        storage_path = _generate_storage_path(eleve_id, filename)

        # Determine content type
        extension = filename.rsplit(".", 1)[1].lower()
        content_types = {
            "pdf": "application/pdf",
            "png": "image/png",
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "webp": "image/webp",
        }
        content_type = content_types.get(extension, "application/octet-stream")

        # Upload to Supabase Storage
        client.storage.from_(BUCKET_NAME).upload(
            path=storage_path,
            file=file_data,
            file_options={"content-type": content_type}
        )

        # Build the public URL
        public_url = f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET_NAME}/{storage_path}"

        return {"success": True, "url": public_url}

    except Exception as e:
        print(f"Erreur upload Supabase : {e}")
        return {"success": False, "error": str(e)}
