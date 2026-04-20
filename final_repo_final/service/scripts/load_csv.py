import argparse
from app.db import SessionLocal
from app.services.loader import load_csv_to_db

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", required=True)
    parser.add_argument("--source", required=True)
    args = parser.parse_args()

    db = SessionLocal()
    try:
        result = load_csv_to_db(db, args.csv, args.source)
        print(result)
    finally:
        db.close()

if __name__ == "__main__":
    main()
