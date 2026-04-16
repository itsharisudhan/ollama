"""
Data Ingestion Script (v2 - Curated Dataset)
=============================================
Loads 45+ curated colleges with comprehensive details into SQLite + FAISS.
Run this ONCE before starting the app.

Usage: python ingest_data.py
"""

import json
import os
import sqlite3
import sys

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from src.Utility.load_model import load_embeddings
from college_data import COLLEGES


# --------------------------------------------------
# Configuration
# --------------------------------------------------
DB_PATH = "src/data/colleges.db"
FAISS_PATH = "faiss_index"


def create_database():
    """Create SQLite database from curated college data."""

    print(f"--- Loading {len(COLLEGES)} curated colleges...")

    # Create SQLite database
    print(f"\n--- Creating SQLite database at {DB_PATH}...")

    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE colleges (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            short_name TEXT,
            established INTEGER,
            type TEXT,
            affiliation TEXT,
            accreditation TEXT,
            nirf_ranking TEXT,
            city TEXT,
            district TEXT,
            state TEXT,
            pincode TEXT,
            address TEXT,
            courses_ug TEXT,
            courses_pg TEXT,
            courses_phd TEXT,
            fees_ug TEXT,
            fees_pg TEXT,
            fees_hostel TEXT,
            fees_total_estimate TEXT,
            admission_ug TEXT,
            admission_pg TEXT,
            admission_docs TEXT,
            admission_cutoff TEXT,
            placement_avg TEXT,
            placement_highest TEXT,
            placement_median TEXT,
            placement_rate TEXT,
            placement_recruiters TEXT,
            facilities TEXT,
            website TEXT,
            phone TEXT,
            email TEXT,
            highlights TEXT,
            description TEXT,
            search_text TEXT
        )
    """)

    # Create indexes
    cursor.execute("CREATE INDEX idx_name ON colleges(name)")
    cursor.execute("CREATE INDEX idx_short_name ON colleges(short_name)")
    cursor.execute("CREATE INDEX idx_city ON colleges(city)")
    cursor.execute("CREATE INDEX idx_district ON colleges(district)")
    cursor.execute("CREATE INDEX idx_state ON colleges(state)")
    cursor.execute("CREATE INDEX idx_type ON colleges(type)")

    # Insert data
    print("   Inserting records...")
    count = 0
    for c in COLLEGES:
        # Build search text for matching
        search_text = " ".join([
            c.get("name", ""), c.get("short_name", ""),
            c.get("city", ""), c.get("district", ""), c.get("state", ""),
            c.get("type", ""), c.get("affiliation", ""),
            c.get("courses_ug", ""), c.get("courses_pg", ""),
            c.get("description", ""), c.get("highlights", "")
        ]).lower()

        try:
            cursor.execute("""
                INSERT INTO colleges (
                    id, name, short_name, established, type, affiliation,
                    accreditation, nirf_ranking, city, district, state, pincode,
                    address, courses_ug, courses_pg, courses_phd,
                    fees_ug, fees_pg, fees_hostel, fees_total_estimate,
                    admission_ug, admission_pg, admission_docs, admission_cutoff,
                    placement_avg, placement_highest, placement_median,
                    placement_rate, placement_recruiters,
                    facilities, website, phone, email,
                    highlights, description, search_text
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                          ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                c.get("id"), c.get("name"), c.get("short_name"), c.get("established"),
                c.get("type"), c.get("affiliation"), c.get("accreditation"),
                c.get("nirf_ranking"), c.get("city"), c.get("district"),
                c.get("state"), c.get("pincode"), c.get("address"),
                c.get("courses_ug"), c.get("courses_pg"), c.get("courses_phd"),
                c.get("fees_ug"), c.get("fees_pg"), c.get("fees_hostel"),
                c.get("fees_total_estimate"),
                c.get("admission_ug"), c.get("admission_pg"),
                c.get("admission_docs"), c.get("admission_cutoff"),
                c.get("placement_avg"), c.get("placement_highest"),
                c.get("placement_median"), c.get("placement_rate"),
                c.get("placement_recruiters"),
                c.get("facilities"), c.get("website"), c.get("phone"),
                c.get("email"), c.get("highlights"), c.get("description"),
                search_text
            ))
            count += 1
        except sqlite3.IntegrityError as e:
            print(f"  ⚠️ Skipping duplicate: {c.get('name')} - {e}")

    conn.commit()

    # Print stats
    cursor.execute("SELECT COUNT(*) FROM colleges")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(DISTINCT state) FROM colleges")
    states_count = cursor.fetchone()[0]

    print(f"\n   DONE: Inserted {total} colleges")
    print(f"   STATS: {states_count} states covered")

    # Check for BIT Campus
    cursor.execute("SELECT name, city, state FROM colleges WHERE name LIKE '%BIT%Campus%'")
    bit_results = cursor.fetchall()
    if bit_results:
        print(f"\n   FOUND your college:")
        for r in bit_results:
            print(f"      {r[0]} — {r[1]}, {r[2]}")

    conn.close()
    return total


def build_faiss_index():
    """Build FAISS vector index from curated college data."""

    print("\n--- Building FAISS vector index...")
    print("   Loading embedding model...")
    embeddings = load_embeddings()

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM colleges")
    rows = cursor.fetchall()
    conn.close()

    print(f"   Creating rich documents for {len(rows)} colleges...")

    documents = []
    for row in rows:
        # Create comprehensive text for semantic search
        text = f"""
College: {row['name']} (also known as {row['short_name']}).
Established in {row['established']}.
Location: {row['address']}, {row['city']}, {row['district']}, {row['state']} - {row['pincode']}.
Type: {row['type']}. Affiliation: {row['affiliation']}.
Accreditation: {row['accreditation']}. NIRF Ranking: {row['nirf_ranking']}.

Courses Offered:
UG Programs: {row['courses_ug']}
PG Programs: {row['courses_pg']}
PhD Programs: {row['courses_phd']}

Fee Structure:
UG Fees: {row['fees_ug']}
PG Fees: {row['fees_pg']}
Hostel Fees: {row['fees_hostel']}
Total Estimate: {row['fees_total_estimate']}

Admission Process:
UG Admission: {row['admission_ug']}
PG Admission: {row['admission_pg']}
Documents Required: {row['admission_docs']}
Cutoff Info: {row['admission_cutoff']}

Placement Statistics:
Average Package: {row['placement_avg']}
Highest Package: {row['placement_highest']}
Median Package: {row['placement_median']}
Placement Rate: {row['placement_rate']}
Top Recruiters: {row['placement_recruiters']}

Facilities: {row['facilities']}
Website: {row['website']}
Phone: {row['phone']}
Email: {row['email']}
Key Highlights: {row['highlights']}
Description: {row['description']}
""".strip()

        doc = Document(
            page_content=text,
            metadata={
                "college_id": row['id'],
                "name": row['name'],
                "short_name": row['short_name'],
                "city": row['city'],
                "state": row['state'],
                "type": row['type']
            }
        )
        documents.append(doc)

    print(f"   Embedding {len(documents)} documents...")

    # Build FAISS
    db = FAISS.from_documents(documents, embeddings)

    # Save index
    if os.path.exists(FAISS_PATH):
        import shutil
        shutil.rmtree(FAISS_PATH)

    db.save_local(FAISS_PATH)
    print(f"   DONE: FAISS index saved to {FAISS_PATH}/")

    return len(documents)


# --------------------------------------------------
# Main
# --------------------------------------------------
if __name__ == "__main__":
    print("=" * 60)
    print("College Chatbot - Data Ingestion (v2 Curated)")
    print("=" * 60)

    total = create_database()
    faiss_count = build_faiss_index()

    print("\n" + "=" * 60)
    print(f"DONE! {total} colleges in SQLite, {faiss_count} in FAISS")
    print("=" * 60)
    print("\nYou can now start the app:")
    print("  1. uvicorn api:app --reload")
    print("  2. streamlit run app.py")
