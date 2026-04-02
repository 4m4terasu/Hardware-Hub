import json
from pathlib import Path

from backend.app.db import SessionLocal
from backend.app.models.hardware import Hardware


SEED_FILE_PATH = Path(__file__).resolve().parents[2] / "data" / "seed_hardware.json"


def seed_hardware_if_empty() -> None:
    db = SessionLocal()

    try:
        existing_count = db.query(Hardware).count()
        if existing_count > 0:
            print("Hardware table already contains data. Skipping seed.")
            return

        with SEED_FILE_PATH.open("r", encoding="utf-8") as file:
            seed_rows = json.load(file)

        seen_ids: set[int] = set()
        inserted_count = 0
        skipped_duplicates = 0

        for row in seed_rows:
            hardware_id = row["id"]

            if hardware_id in seen_ids:
                print(f"Skipping duplicate hardware seed row with id={hardware_id}.")
                skipped_duplicates += 1
                continue

            seen_ids.add(hardware_id)

            hardware = Hardware(
                id=hardware_id,
                name=row["name"],
                brand=row.get("brand"),
                purchase_date_raw=row.get("purchaseDate"),
                status_raw=row.get("status"),
                notes=row.get("notes"),
                assigned_to=row.get("assignedTo"),
                history_text=row.get("history"),
            )

            db.add(hardware)
            inserted_count += 1

        db.commit()
        print(
            f"Hardware seed completed. Inserted={inserted_count}, skipped_duplicates={skipped_duplicates}."
        )

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()