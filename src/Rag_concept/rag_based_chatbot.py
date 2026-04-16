"""
Hybrid College Chatbot (v2 - Rich Details)
==========================================
Combines SQLite (structured queries) + FAISS (semantic search) + Groq LLM.
Now supports detailed queries about fees, courses, admissions, placements, etc.
"""

import os
import sqlite3

from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from src.Utility.load_model import load_embeddings, load_llm_model
from config import Settings


# --------------------------------------------------
# Database Helper
# --------------------------------------------------
class CollegeDB:
    """SQLite interface for structured college queries."""

    def __init__(self, db_path: str):
        self.db_path = db_path

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _row_to_dict(self, row):
        """Convert sqlite3.Row to dict."""
        return dict(row) if row else None

    def search_by_name(self, query: str, limit: int = 10):
        """Search colleges by name (fuzzy LIKE match)."""
        conn = self._connect()
        cursor = conn.cursor()

        words = query.strip().split()
        conditions = " AND ".join([f"search_text LIKE ?" for _ in words])
        params = [f"%{w.lower()}%" for w in words]

        cursor.execute(f"""
            SELECT * FROM colleges
            WHERE {conditions}
            ORDER BY name
            LIMIT ?
        """, params + [limit])

        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results

    def get_college_by_id(self, college_id: int):
        """Get full college details by ID."""
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM colleges WHERE id = ?", (college_id,))
        result = self._row_to_dict(cursor.fetchone())
        conn.close()
        return result

    def get_college_detail(self, name: str):
        """Get full details of a specific college by name match."""
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM colleges
            WHERE name LIKE ? OR short_name LIKE ?
            ORDER BY name LIMIT 1
        """, (f"%{name}%", f"%{name}%"))
        result = self._row_to_dict(cursor.fetchone())
        conn.close()
        return result

    def get_all_colleges(self):
        """Get all colleges (basic info)."""
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, name, short_name, city, state, type,
                   nirf_ranking, placement_avg, fees_ug
            FROM colleges ORDER BY name
        """)
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results

    def get_by_state(self, state: str, limit: int = 50):
        """Get colleges by state."""
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM colleges
            WHERE state LIKE ?
            ORDER BY name LIMIT ?
        """, (f"%{state}%", limit))
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results

    def get_by_city(self, city: str, limit: int = 50):
        """Get colleges by city."""
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM colleges
            WHERE city LIKE ? OR district LIKE ?
            ORDER BY name LIMIT ?
        """, (f"%{city}%", f"%{city}%", limit))
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results

    def get_by_type(self, inst_type: str, state: str = None, limit: int = 30):
        """Get colleges by type, optionally filtered by state."""
        conn = self._connect()
        cursor = conn.cursor()
        if state:
            cursor.execute("""
                SELECT * FROM colleges
                WHERE type LIKE ? AND state LIKE ?
                ORDER BY name LIMIT ?
            """, (f"%{inst_type}%", f"%{state}%", limit))
        else:
            cursor.execute("""
                SELECT * FROM colleges
                WHERE type LIKE ?
                ORDER BY name LIMIT ?
            """, (f"%{inst_type}%", limit))
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results

    def search_by_course(self, course: str, limit: int = 20):
        """Search colleges offering a specific course."""
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM colleges
            WHERE courses_ug LIKE ? OR courses_pg LIKE ? OR courses_phd LIKE ?
            ORDER BY name LIMIT ?
        """, (f"%{course}%", f"%{course}%", f"%{course}%", limit))
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results

    def get_stats(self):
        """Get overall database statistics."""
        conn = self._connect()
        cursor = conn.cursor()

        stats = {}
        cursor.execute("SELECT COUNT(*) FROM colleges")
        stats["total_colleges"] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(DISTINCT state) FROM colleges")
        stats["total_states"] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(DISTINCT city) FROM colleges")
        stats["total_cities"] = cursor.fetchone()[0]

        cursor.execute("""
            SELECT state, COUNT(*) as count
            FROM colleges
            GROUP BY state
            ORDER BY count DESC
            LIMIT 10
        """)
        stats["top_states"] = {row["state"]: row["count"] for row in cursor.fetchall()}

        # Count by type
        cursor.execute("""
            SELECT
                SUM(CASE WHEN type LIKE '%Government%' THEN 1 ELSE 0 END) as govt,
                SUM(CASE WHEN type LIKE '%Private%' THEN 1 ELSE 0 END) as private,
                SUM(CASE WHEN type LIKE '%Deemed%' THEN 1 ELSE 0 END) as deemed
            FROM colleges
        """)
        row = cursor.fetchone()
        stats["by_type"] = {
            "Government": row["govt"] or 0,
            "Private": row["private"] or 0,
            "Deemed University": row["deemed"] or 0
        }

        conn.close()
        return stats

    def get_all_states(self):
        """Get list of all states."""
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT state FROM colleges ORDER BY state")
        states = [row["state"] for row in cursor.fetchall()]
        conn.close()
        return states

    def get_colleges_by_district(self, district: str, limit: int = 50):
        """Get colleges filtered by district."""
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM colleges
            WHERE district LIKE ?
            ORDER BY name LIMIT ?
        """, (f"%{district}%", limit))
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results


# --------------------------------------------------
# Prompt Templates
# --------------------------------------------------
CHAT_PROMPT = ChatPromptTemplate.from_template("""
You are an expert Indian College Information Assistant with detailed knowledge of {total_colleges} carefully curated colleges.

Your job is to provide COMPREHENSIVE, DETAILED answers about Indian colleges including:
- Full course listings (UG, PG, PhD programs)
- Fee structure (tuition, hostel, total estimates)
- Admission process (entrance exams, counselling, documents required, cutoffs)
- Placement statistics (average, highest, median packages, placement rate, top recruiters)
- Facilities and infrastructure
- Key highlights and what makes each college unique
- Rankings and accreditation
- Contact information

RULES:
1. Use ONLY the context provided below to answer.
2. Present information in a clear, well-organized format with sections and bullet points.
3. When listing fees, show all available fee details.
4. When discussing admissions, mention the entrance exam, counselling process, and required documents.
5. For placements, always include average package, highest package, and placement rate.
6. Be helpful, thorough, and accurate.
7. If asked to compare colleges, create a clear comparison table or side-by-side format.
8. If the information is not in the context, say "I don't have that specific information in my database."

Context:
{context}

Question: {question}

Detailed Answer:
""")


# --------------------------------------------------
# Hybrid RAG Chain
# --------------------------------------------------
class HybridCollegeChatbot:
    """Combines SQLite + FAISS + LLM for intelligent college queries."""

    def __init__(self):
        settings = Settings()
        self.db = CollegeDB(settings.DATABASE_PATH)
        self.llm = load_llm_model()
        self.parser = StrOutputParser()

        # Get total count for prompt
        try:
            stats = self.db.get_stats()
            self.total_colleges = stats.get("total_colleges", 45)
        except Exception:
            self.total_colleges = 45

        self.chain = CHAT_PROMPT | self.llm | self.parser

        # Load FAISS index
        if os.path.exists(settings.FAISS_INDEX_PATH):
            print("Loading FAISS index...")
            embeddings = load_embeddings()
            self.vector_store = FAISS.load_local(
                settings.FAISS_INDEX_PATH,
                embeddings,
                allow_dangerous_deserialization=True
            )
            self.retriever = self.vector_store.as_retriever(
                search_type="mmr",
                search_kwargs={"k": 5, "fetch_k": 10}
            )
        else:
            print("⚠️ FAISS index not found. Run ingest_data.py first.")
            self.vector_store = None
            self.retriever = None

    def _format_college_full(self, college: dict) -> str:
        """Format a college with ALL details for context."""
        if not college:
            return ""

        return f"""
=== {college.get('name', 'Unknown')} ({college.get('short_name', '')}) ===
Established: {college.get('established', 'N/A')}
Type: {college.get('type', 'N/A')}
Affiliation: {college.get('affiliation', 'N/A')}
Accreditation: {college.get('accreditation', 'N/A')}
NIRF Ranking: {college.get('nirf_ranking', 'N/A')}
Location: {college.get('address', 'N/A')}, {college.get('city', '')}, {college.get('state', '')} - {college.get('pincode', '')}

📚 COURSES:
  UG: {college.get('courses_ug', 'N/A')}
  PG: {college.get('courses_pg', 'N/A')}
  PhD: {college.get('courses_phd', 'N/A')}

💰 FEE STRUCTURE:
  UG Fees: {college.get('fees_ug', 'N/A')}
  PG Fees: {college.get('fees_pg', 'N/A')}
  Hostel: {college.get('fees_hostel', 'N/A')}
  Total Estimate: {college.get('fees_total_estimate', 'N/A')}

🎓 ADMISSION:
  UG: {college.get('admission_ug', 'N/A')}
  PG: {college.get('admission_pg', 'N/A')}
  Documents: {college.get('admission_docs', 'N/A')}
  Cutoff: {college.get('admission_cutoff', 'N/A')}

📊 PLACEMENTS:
  Average Package: {college.get('placement_avg', 'N/A')}
  Highest Package: {college.get('placement_highest', 'N/A')}
  Median Package: {college.get('placement_median', 'N/A')}
  Placement Rate: {college.get('placement_rate', 'N/A')}
  Top Recruiters: {college.get('placement_recruiters', 'N/A')}

🏗️ FACILITIES: {college.get('facilities', 'N/A')}

🌐 CONTACT:
  Website: {college.get('website', 'N/A')}
  Phone: {college.get('phone', 'N/A')}
  Email: {college.get('email', 'N/A')}

⭐ HIGHLIGHTS: {college.get('highlights', 'N/A')}
📝 DESCRIPTION: {college.get('description', 'N/A')}
"""

    def _format_colleges_summary(self, colleges: list) -> str:
        """Format multiple colleges with key details."""
        if not colleges:
            return "No matching colleges found."

        lines = []
        for c in colleges:
            lines.append(f"""
- {c.get('name', 'Unknown')} ({c.get('short_name', '')})
  Location: {c.get('city', '')}, {c.get('state', '')} | Type: {c.get('type', '')}
  NIRF: {c.get('nirf_ranking', 'N/A')} | Fees: {c.get('fees_ug', 'N/A')}
  Avg Package: {c.get('placement_avg', 'N/A')} | Rate: {c.get('placement_rate', 'N/A')}
  Courses UG: {c.get('courses_ug', 'N/A')}
""")
        return "\n".join(lines)

    def _classify_query(self, question: str) -> str:
        """Classify the type of query for optimal handling."""
        q = question.lower()

        # Specific college detail query
        detail_keywords = ["about", "tell me", "details", "information", "info",
                           "everything about", "describe"]
        if any(k in q for k in detail_keywords):
            return "detail"

        # Fee queries
        if any(w in q for w in ["fee", "fees", "cost", "tuition", "hostel fee",
                                 "expensive", "affordable", "cheap", "price"]):
            return "fees"

        # Admission queries
        if any(w in q for w in ["admission", "admit", "entrance", "apply",
                                 "application", "cutoff", "eligibility", "counselling",
                                 "tnea", "jee", "gate", "how to get"]):
            return "admission"

        # Placement queries
        if any(w in q for w in ["placement", "salary", "package", "recruiter",
                                 "company", "hire", "job", "lpa", "crore"]):
            return "placement"

        # Course queries
        if any(w in q for w in ["course", "program", "branch", "department",
                                 "btech", "b.tech", "b.e", "mtech", "m.tech",
                                 "mba", "mca", "phd", "computer science", "cse",
                                 "mechanical", "civil", "ece", "eee", "ai", "data science"]):
            return "course"

        # Comparison queries
        if any(w in q for w in ["compare", "vs", "versus", "difference",
                                 "better", "which is"]):
            return "comparison"

        # Ranking queries
        if any(w in q for w in ["rank", "ranking", "nirf", "top", "best"]):
            return "ranking"

        # State/city queries
        state_keywords = [
            "tamil nadu", "karnataka", "maharashtra", "delhi", "kerala",
            "andhra pradesh", "telangana", "uttar pradesh", "rajasthan",
            "gujarat", "west bengal", "madhya pradesh", "punjab", "odisha",
            "assam", "uttarakhand"
        ]
        city_keywords = [
            "trichy", "tiruchirappalli", "chennai", "bangalore", "mumbai",
            "delhi", "hyderabad", "pune", "coimbatore", "madurai",
            "vellore", "thanjavur", "warangal", "roorkee", "kanpur",
            "kharagpur", "guwahati", "indore", "mangalore", "kozhikode",
            "erode", "varanasi"
        ]
        for kw in state_keywords + city_keywords:
            if kw in q:
                return "location"

        # Type queries
        if any(w in q for w in ["government", "govt", "private", "deemed",
                                 "autonomous", "aided"]):
            return "type"

        # Stats queries
        if any(w in q for w in ["how many", "total", "count", "statistics"]):
            return "stats"

        # List queries
        if any(w in q for w in ["list", "show all", "all colleges"]):
            return "list"

        return "semantic"

    def _extract_college_name(self, question: str) -> str:
        """Try to extract a college name from the question."""
        q = question.lower()

        # Common college name patterns
        college_names = {
            "bit campus": "BIT Campus",
            "bit trichy": "BIT Campus",
            "nit trichy": "NIT Tiruchirappalli",
            "nit tiruchirappalli": "NIT Tiruchirappalli",
            "iit madras": "IIT Madras",
            "iit bombay": "IIT Bombay",
            "iit delhi": "IIT Delhi",
            "iit kanpur": "IIT Kanpur",
            "iit kharagpur": "IIT Kharagpur",
            "iit roorkee": "IIT Roorkee",
            "iit guwahati": "IIT Guwahati",
            "iit hyderabad": "IIT Hyderabad",
            "iit bhu": "IIT BHU",
            "iit indore": "IIT Indore",
            "iit ropar": "IIT Ropar",
            "nit surathkal": "NIT Surathkal",
            "nit warangal": "NIT Warangal",
            "nit calicut": "NIT Calicut",
            "nit rourkela": "NIT Rourkela",
            "anna university": "Anna University",
            "ceg": "CEG Anna University",
            "psg tech": "PSG Tech",
            "psg college": "PSG Tech",
            "vit": "VIT Vellore",
            "vit vellore": "VIT Vellore",
            "srm": "SRM",
            "srm chennai": "SRM Chennai",
            "srm trichy": "SRM TRP",
            "saranathan": "Saranathan",
            "jjcet": "JJCET",
            "jj college": "JJCET",
            "mamce": "MAMCE",
            "miet": "MIET",
            "ssn": "SSN",
            "sastra": "SASTRA",
            "amrita": "Amrita",
            "tce madurai": "TCE Madurai",
            "thiagarajar": "TCE Madurai",
            "kongu": "Kongu",
            "kct": "KCT",
            "kumaraguru": "KCT",
            "cit coimbatore": "CIT Coimbatore",
            "gct": "GCT Coimbatore",
            "mit chennai": "MIT Anna University",
            "vel tech": "Vel Tech",
            "bits pilani": "BITS Pilani",
        }

        for key, value in college_names.items():
            if key in q:
                return value
        return None

    def __call__(self, question: str) -> str:
        """Process a user question and return a detailed answer."""
        query_type = self._classify_query(question)
        context = ""

        if query_type == "stats":
            stats = self.db.get_stats()
            context = f"""
Database Statistics:
- Total curated colleges: {stats['total_colleges']}
- States covered: {stats['total_states']}
- Cities covered: {stats['total_cities']}

By Type: Government: {stats['by_type'].get('Government', 0)}, Private: {stats['by_type'].get('Private', 0)}, Deemed: {stats['by_type'].get('Deemed University', 0)}

Colleges by State:
{chr(10).join(f'  - {k}: {v} colleges' for k, v in stats['top_states'].items())}
"""

        elif query_type == "detail":
            college_name = self._extract_college_name(question)
            if college_name:
                college = self.db.get_college_detail(college_name)
                if college:
                    context = self._format_college_full(college)
                else:
                    # Try FAISS
                    if self.retriever:
                        docs = self.retriever.invoke(question)
                        context = "\n\n".join(doc.page_content for doc in docs)
            else:
                # Try search
                colleges = self.db.search_by_name(question, limit=3)
                if colleges:
                    context = "\n".join(self._format_college_full(c) for c in colleges)
                elif self.retriever:
                    docs = self.retriever.invoke(question)
                    context = "\n\n".join(doc.page_content for doc in docs)

        elif query_type in ["fees", "admission", "placement", "course"]:
            college_name = self._extract_college_name(question)
            if college_name:
                college = self.db.get_college_detail(college_name)
                if college:
                    context = self._format_college_full(college)

            if not context:
                # Search by name keywords
                colleges = self.db.search_by_name(question, limit=5)
                if colleges:
                    context = "\n".join(self._format_college_full(c) for c in colleges[:3])
                elif self.retriever:
                    docs = self.retriever.invoke(question)
                    context = "\n\n".join(doc.page_content for doc in docs)

        elif query_type == "comparison":
            # Try to find two colleges to compare
            if self.retriever:
                docs = self.retriever.invoke(question)
                # Get unique colleges
                seen = set()
                unique_docs = []
                for doc in docs:
                    name = doc.metadata.get("name", "")
                    if name not in seen:
                        seen.add(name)
                        unique_docs.append(doc)
                context = "\n\n".join(doc.page_content for doc in unique_docs[:3])
            else:
                colleges = self.db.search_by_name(question, limit=5)
                context = "\n".join(self._format_college_full(c) for c in colleges[:3])

        elif query_type == "location":
            q = question.lower()
            # City search
            city_map = {
                "trichy": "Tiruchirappalli", "tiruchirappalli": "Tiruchirappalli",
                "chennai": "Chennai", "coimbatore": "Coimbatore",
                "madurai": "Madurai", "vellore": "Vellore",
                "thanjavur": "Thanjavur", "erode": "Erode",
                "mumbai": "Mumbai", "bangalore": "Mangalore",
                "warangal": "Warangal", "roorkee": "Roorkee",
                "kanpur": "Kanpur", "kharagpur": "Kharagpur",
                "guwahati": "Guwahati", "hyderabad": "Hyderabad",
                "indore": "Indore", "mangalore": "Mangalore",
                "kozhikode": "Kozhikode", "varanasi": "Varanasi",
                "delhi": "Delhi", "new delhi": "New Delhi",
            }
            # State search
            state_map = {
                "tamil nadu": "Tamil Nadu", "karnataka": "Karnataka",
                "maharashtra": "Maharashtra", "delhi": "Delhi",
                "kerala": "Kerala", "telangana": "Telangana",
                "uttar pradesh": "Uttar Pradesh", "west bengal": "West Bengal",
                "madhya pradesh": "Madhya Pradesh", "rajasthan": "Rajasthan",
                "punjab": "Punjab", "odisha": "Odisha",
                "assam": "Assam", "uttarakhand": "Uttarakhand",
            }

            colleges = []
            for key, value in city_map.items():
                if key in q:
                    colleges = self.db.get_by_city(value, limit=20)
                    break

            if not colleges:
                for key, value in state_map.items():
                    if key in q:
                        colleges = self.db.get_by_state(value, limit=20)
                        break

            if colleges:
                context = self._format_colleges_summary(colleges)
            elif self.retriever:
                docs = self.retriever.invoke(question)
                context = "\n\n".join(doc.page_content for doc in docs)

        elif query_type == "type":
            q = question.lower()
            if "government" in q or "govt" in q:
                colleges = self.db.get_by_type("Government")
            elif "deemed" in q:
                colleges = self.db.get_by_type("Deemed")
            elif "private" in q:
                colleges = self.db.get_by_type("Private")
            else:
                colleges = self.db.get_all_colleges()

            if colleges:
                context = self._format_colleges_summary(colleges)

        elif query_type == "ranking":
            # Return all colleges sorted by relevance
            colleges = self.db.get_all_colleges()
            context = self._format_colleges_summary(colleges)

        elif query_type == "list":
            colleges = self.db.get_all_colleges()
            context = self._format_colleges_summary(colleges)

        else:
            # Semantic search fallback
            college_name = self._extract_college_name(question)
            if college_name:
                college = self.db.get_college_detail(college_name)
                if college:
                    context = self._format_college_full(college)

            if not context:
                colleges = self.db.search_by_name(question, limit=5)
                if colleges:
                    context = "\n".join(self._format_college_full(c) for c in colleges[:3])
                elif self.retriever:
                    docs = self.retriever.invoke(question)
                    context = "\n\n".join(doc.page_content for doc in docs)
                else:
                    context = "No matching colleges found."

        # Generate response with LLM
        try:
            answer = self.chain.invoke({
                "context": context,
                "question": question,
                "total_colleges": self.total_colleges
            })
            return answer
        except Exception as e:
            return f"⚠️ Error generating response: {str(e)}"

    # ---- API helper methods ----

    def search(self, query: str, limit: int = 20) -> list:
        """Direct search returning structured results."""
        return self.db.search_by_name(query, limit)

    def get_college_detail_api(self, college_id: int) -> dict:
        """Get full college details by ID."""
        return self.db.get_college_by_id(college_id)

    def get_all_colleges_api(self) -> list:
        """Get all colleges."""
        return self.db.get_all_colleges()

    def get_stats(self) -> dict:
        """Get database statistics."""
        return self.db.get_stats()

    def get_states(self) -> list:
        """Get all states."""
        return self.db.get_all_states()

    def get_colleges_by_state(self, state: str, limit: int = 50) -> list:
        """Get colleges filtered by state."""
        return self.db.get_by_state(state, limit)

    def get_colleges_by_district(self, district: str, limit: int = 50) -> list:
        """Get colleges filtered by district."""
        return self.db.get_colleges_by_district(district, limit)


# --------------------------------------------------
# Factory Function
# --------------------------------------------------
def main():
    """Initialize and return the chatbot instance."""
    print("--- Initializing Hybrid College Chatbot (v2)...")
    chatbot = HybridCollegeChatbot()
    print("--- Chatbot ready!")
    return chatbot