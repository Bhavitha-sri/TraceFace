import os
import json
import hashlib
import uuid
from datetime import datetime, timezone


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

EVIDENCE_FILE = os.path.join(
    BASE_DIR,
    "data",
    "evidence_records.json"
)


def load_evidence_records():
    """
    Load previously saved evidence records.
    """

    if not os.path.exists(EVIDENCE_FILE):
        return []

    with open(
        EVIDENCE_FILE,
        "r",
        encoding="utf-8"
    ) as file:
        return json.load(file)


def save_evidence_record(record):
    """
    Save a new evidence record.
    """

    records = load_evidence_records()

    records.append(record)

    with open(
        EVIDENCE_FILE,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            records,
            file,
            indent=4,
            ensure_ascii=False
        )


def calculate_sha256(data):
    """
    Convert structured data into a canonical string
    and calculate its SHA-256 fingerprint.
    """

    canonical_data = json.dumps(
        data,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False
    )

    return hashlib.sha256(
        canonical_data.encode("utf-8")
    ).hexdigest()


def create_evidence(best_match, uploaded_filename):
    """
    Create a unique evidence record for the matched content.
    """

    evidence_id = (
        "TF-"
        + datetime.now(timezone.utc).strftime("%Y%m%d")
        + "-"
        + uuid.uuid4().hex[:8].upper()
    )

    timestamp = datetime.now(
        timezone.utc
    ).isoformat()

    # This is the exact information we want
    # to protect with the hash.
    evidence_payload = {

        "evidence_id": evidence_id,

        "uploaded_file": uploaded_filename,

        "matched_post_id": best_match["id"],

        "title": best_match["title"],

        "source": best_match["source"],

        "source_url": best_match["url"],

        "face_similarity":
            round(
                best_match["similarity"],
                6
            ),

        "created_at": timestamp
    }

    # Generate cryptographic fingerprint
    evidence_hash = calculate_sha256(
        evidence_payload
    )

    # Complete record
    record = {

        "evidence": evidence_payload,

        "sha256": evidence_hash,

        "blockchain": {

            "status": "NOT_RECORDED",

            "transaction_hash": None
        }
    }

    save_evidence_record(record)

    return record