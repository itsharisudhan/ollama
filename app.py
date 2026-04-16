import streamlit as st
import requests
import json

# --------------------------------------------------
# Page Configuration
# --------------------------------------------------
st.set_page_config(
    page_title="Indian College Explorer",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

API_URL = "http://127.0.0.1:8000"

# --------------------------------------------------
# Custom CSS — Premium Dark Theme
# --------------------------------------------------
st.markdown("""
<style>
    /* ===== Global Theme ===== */
    .stApp {
        background: linear-gradient(135deg, #0f0c29 0%, #1a1a3e 50%, #24243e 100%);
    }

    /* ===== Hero Section ===== */
    .hero-container {
        text-align: center;
        padding: 2rem 1rem 1rem;
        margin-bottom: 0.5rem;
    }
    .hero-title {
        font-size: 2.6rem;
        font-weight: 800;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.3rem;
        letter-spacing: -1px;
    }
    .hero-subtitle {
        font-size: 1rem;
        color: #a0aec0;
        font-weight: 400;
    }

    /* ===== Stat Cards ===== */
    .stat-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 0.8rem;
        margin: 1rem 0;
    }
    .stat-card {
        background: linear-gradient(145deg, rgba(102, 126, 234, 0.15), rgba(118, 75, 162, 0.1));
        border: 1px solid rgba(102, 126, 234, 0.25);
        border-radius: 14px;
        padding: 1rem;
        text-align: center;
        transition: all 0.3s ease;
        backdrop-filter: blur(10px);
    }
    .stat-card:hover {
        transform: translateY(-3px);
        border-color: rgba(102, 126, 234, 0.5);
        box-shadow: 0 6px 24px rgba(102, 126, 234, 0.2);
    }
    .stat-number {
        font-size: 1.8rem;
        font-weight: 800;
        background: linear-gradient(135deg, #667eea, #764ba2);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .stat-label {
        font-size: 0.78rem;
        color: #a0aec0;
        margin-top: 0.2rem;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    /* ===== College Cards ===== */
    .college-card {
        background: linear-gradient(145deg, rgba(255,255,255,0.06), rgba(255,255,255,0.02));
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 14px;
        padding: 1.2rem 1.4rem;
        margin-bottom: 0.8rem;
        transition: all 0.3s ease;
        backdrop-filter: blur(5px);
    }
    .college-card:hover {
        border-color: rgba(102, 126, 234, 0.5);
        transform: translateX(4px);
        box-shadow: 0 4px 20px rgba(102, 126, 234, 0.15);
    }
    .college-name {
        font-size: 1.05rem;
        font-weight: 700;
        color: #e2e8f0;
        margin-bottom: 0.4rem;
    }
    .college-info {
        font-size: 0.85rem;
        color: #a0aec0;
        line-height: 1.6;
    }
    .college-badge {
        display: inline-block;
        padding: 0.2rem 0.6rem;
        border-radius: 20px;
        font-size: 0.7rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-right: 0.4rem;
    }
    .badge-govt {
        background: linear-gradient(135deg, rgba(72, 187, 120, 0.2), rgba(72, 187, 120, 0.1));
        color: #68d391;
        border: 1px solid rgba(72, 187, 120, 0.3);
    }
    .badge-private {
        background: linear-gradient(135deg, rgba(237, 137, 54, 0.2), rgba(237, 137, 54, 0.1));
        color: #ed8936;
        border: 1px solid rgba(237, 137, 54, 0.3);
    }
    .badge-deemed {
        background: linear-gradient(135deg, rgba(159, 122, 234, 0.2), rgba(159, 122, 234, 0.1));
        color: #b794f4;
        border: 1px solid rgba(159, 122, 234, 0.3);
    }
    .badge-rank {
        background: linear-gradient(135deg, rgba(246, 224, 94, 0.2), rgba(246, 224, 94, 0.1));
        color: #f6e05e;
        border: 1px solid rgba(246, 224, 94, 0.3);
    }
    .badge-placement {
        background: linear-gradient(135deg, rgba(66, 153, 225, 0.2), rgba(66, 153, 225, 0.1));
        color: #63b3ed;
        border: 1px solid rgba(66, 153, 225, 0.3);
    }

    /* ===== Featured Card ===== */
    .featured-card {
        background: linear-gradient(145deg, rgba(102, 126, 234, 0.2), rgba(118, 75, 162, 0.15));
        border: 2px solid rgba(102, 126, 234, 0.4);
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1.2rem;
        position: relative;
        overflow: hidden;
    }
    .featured-card::before {
        content: '⭐ YOUR COLLEGE';
        position: absolute;
        top: 12px;
        right: 12px;
        font-size: 0.6rem;
        font-weight: 700;
        color: #f6e05e;
        letter-spacing: 1px;
        background: rgba(246, 224, 94, 0.1);
        padding: 0.2rem 0.6rem;
        border-radius: 8px;
        border: 1px solid rgba(246, 224, 94, 0.3);
    }
    .featured-title {
        font-size: 1.2rem;
        font-weight: 800;
        background: linear-gradient(135deg, #667eea, #f093fb);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }

    /* ===== Detail Section ===== */
    .detail-section {
        background: linear-gradient(145deg, rgba(255,255,255,0.04), rgba(255,255,255,0.01));
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 12px;
        padding: 1rem 1.2rem;
        margin-bottom: 0.6rem;
    }
    .detail-title {
        font-size: 0.9rem;
        font-weight: 700;
        color: #667eea;
        margin-bottom: 0.5rem;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .detail-content {
        font-size: 0.85rem;
        color: #cbd5e0;
        line-height: 1.7;
    }
    .detail-highlight {
        color: #f6e05e;
        font-weight: 600;
    }

    /* ===== Tabs ===== */
    .stTabs [data-baseweb="tab-list"] {
        gap: 1.5rem;
        background: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        color: #a0aec0;
        font-weight: 600;
        font-size: 0.9rem;
        padding: 0.6rem 0;
    }
    .stTabs [aria-selected="true"] {
        color: #667eea !important;
        border-bottom: 3px solid #667eea !important;
    }

    /* ===== Search Input ===== */
    .stTextInput input {
        background: rgba(255,255,255,0.06) !important;
        border: 1px solid rgba(255,255,255,0.15) !important;
        border-radius: 12px !important;
        color: #e2e8f0 !important;
        padding: 0.7rem 1rem !important;
        font-size: 0.95rem !important;
    }
    .stTextInput input:focus {
        border-color: #667eea !important;
        box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.3) !important;
    }

    /* ===== Chat Messages ===== */
    .stChatMessage {
        background: rgba(255,255,255,0.04) !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
        border-radius: 12px !important;
    }

    /* ===== Sidebar ===== */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1a3e 0%, #0f0c29 100%) !important;
        border-right: 1px solid rgba(255,255,255,0.08);
    }

    hr { border-color: rgba(255,255,255,0.08) !important; }

    .stSelectbox > div > div {
        background: rgba(255,255,255,0.06) !important;
        border: 1px solid rgba(255,255,255,0.15) !important;
        border-radius: 10px !important;
    }

    @media (max-width: 768px) {
        .stat-grid { grid-template-columns: repeat(2, 1fr); }
        .hero-title { font-size: 1.8rem; }
    }
</style>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
</style>
""", unsafe_allow_html=True)


# --------------------------------------------------
# Helper Functions
# --------------------------------------------------
def api_call(endpoint: str, method: str = "GET", data: dict = None):
    """Make API call with error handling."""
    try:
        if method == "POST":
            response = requests.post(f"{API_URL}{endpoint}", json=data, timeout=60)
        else:
            response = requests.get(f"{API_URL}{endpoint}", params=data, timeout=15)

        if response.status_code == 200:
            return response.json()
        else:
            return None
    except requests.exceptions.ConnectionError:
        return None
    except Exception:
        return None


def get_badge_class(inst_type: str) -> str:
    """Get CSS badge class based on institution type."""
    if not inst_type:
        return "badge-private"
    t = inst_type.lower()
    if "government" in t:
        return "badge-govt"
    elif "deemed" in t:
        return "badge-deemed"
    return "badge-private"


def render_college_card(college: dict, featured: bool = False):
    """Render a college card with key details."""
    name = college.get("name", "Unknown")
    short = college.get("short_name", "")
    city = college.get("city", "")
    state = college.get("state", "")
    inst_type = college.get("type", "")
    nirf = college.get("nirf_ranking", "")
    avg_pkg = college.get("placement_avg", "")
    fees = college.get("fees_ug", "")
    badge_class = get_badge_class(inst_type)

    if featured:
        address = college.get("address", "")
        placement_rate = college.get("placement_rate", "")
        highest = college.get("placement_highest", "")
        desc = college.get("description", "")
        st.markdown(f"""
        <div class="featured-card">
            <div class="featured-title">🏛️ {name}</div>
            <div class="college-info">
                📍 {address}<br>
                {f'📊 NIRF: {nirf}' if nirf else ''} {'|' if nirf else ''}
                💰 Avg Package: {avg_pkg if avg_pkg else 'N/A'} |
                🎯 Placement: {placement_rate if placement_rate else 'N/A'}<br>
                💵 UG Fees: {fees if fees else 'N/A'}<br>
                <span class="college-badge {badge_class}">{inst_type}</span>
                {f'<span class="college-badge badge-rank">NIRF {nirf}</span>' if nirf and 'Not' not in str(nirf) else ''}
            </div>
            <div style="margin-top: 0.6rem; font-size: 0.82rem; color: #94a3b8;">{desc}</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="college-card">
            <div class="college-name">🏫 {name} {f'({short})' if short else ''}</div>
            <div class="college-info">
                📍 {city}, {state}
                {f'| 💰 {avg_pkg}' if avg_pkg else ''}
                {f'| 💵 {fees}' if fees else ''}<br>
                <span class="college-badge {badge_class}">{inst_type}</span>
                {f'<span class="college-badge badge-rank">NIRF {nirf}</span>' if nirf and 'Not' not in str(nirf) else ''}
                {f'<span class="college-badge badge-placement">Avg: {avg_pkg}</span>' if avg_pkg else ''}
            </div>
        </div>
        """, unsafe_allow_html=True)


def render_college_detail(college: dict):
    """Render full college detail view."""
    name = college.get("name", "Unknown")
    short = college.get("short_name", "")
    badge_class = get_badge_class(college.get("type", ""))

    st.markdown(f"""
    <div style="margin-bottom: 1rem;">
        <div style="font-size: 1.4rem; font-weight: 800; color: #e2e8f0; margin-bottom: 0.3rem;">
            🏛️ {name}
        </div>
        <div style="font-size: 0.9rem; color: #a0aec0;">
            📍 {college.get('address', '')} |
            Est. {college.get('established', 'N/A')} |
            <span class="college-badge {badge_class}">{college.get('type', '')}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Info grid
    col1, col2 = st.columns(2)

    with col1:
        # Courses
        st.markdown(f"""
        <div class="detail-section">
            <div class="detail-title">📚 Courses Offered</div>
            <div class="detail-content">
                <strong>UG Programs:</strong><br>
                {(college.get('courses_ug', 'N/A') or 'N/A').replace('; ', '<br>• ')}
                <br><br>
                <strong>PG Programs:</strong><br>
                {(college.get('courses_pg', 'N/A') or 'N/A').replace('; ', '<br>• ')}
                <br><br>
                <strong>PhD:</strong> {college.get('courses_phd', 'N/A')}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Admission
        st.markdown(f"""
        <div class="detail-section">
            <div class="detail-title">🎓 Admission Process</div>
            <div class="detail-content">
                <strong>UG:</strong> {college.get('admission_ug', 'N/A')}<br><br>
                <strong>PG:</strong> {college.get('admission_pg', 'N/A')}<br><br>
                <strong>Cutoff:</strong> <span class="detail-highlight">{college.get('admission_cutoff', 'N/A')}</span><br><br>
                <strong>Documents:</strong><br>
                {(college.get('admission_docs', 'N/A') or 'N/A').replace('; ', '<br>• ')}
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        # Fees
        st.markdown(f"""
        <div class="detail-section">
            <div class="detail-title">💰 Fee Structure</div>
            <div class="detail-content">
                <strong>UG Fees:</strong> <span class="detail-highlight">{college.get('fees_ug', 'N/A')}</span><br>
                <strong>PG Fees:</strong> {college.get('fees_pg', 'N/A')}<br>
                <strong>Hostel:</strong> {college.get('fees_hostel', 'N/A')}<br>
                <strong>Total Estimate:</strong> <span class="detail-highlight">{college.get('fees_total_estimate', 'N/A')}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Placements
        st.markdown(f"""
        <div class="detail-section">
            <div class="detail-title">📊 Placement Statistics</div>
            <div class="detail-content">
                <strong>Average Package:</strong> <span class="detail-highlight">{college.get('placement_avg', 'N/A')}</span><br>
                <strong>Highest Package:</strong> <span class="detail-highlight">{college.get('placement_highest', 'N/A')}</span><br>
                <strong>Median Package:</strong> {college.get('placement_median', 'N/A')}<br>
                <strong>Placement Rate:</strong> <span class="detail-highlight">{college.get('placement_rate', 'N/A')}</span><br><br>
                <strong>Top Recruiters:</strong><br>
                {(college.get('placement_recruiters', 'N/A') or 'N/A').replace('; ', ' • ')}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Facilities
        st.markdown(f"""
        <div class="detail-section">
            <div class="detail-title">🏗️ Facilities</div>
            <div class="detail-content">
                {(college.get('facilities', 'N/A') or 'N/A').replace('; ', ' • ')}
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Contact & Highlights (full width)
    st.markdown(f"""
    <div class="detail-section">
        <div class="detail-title">⭐ Key Highlights</div>
        <div class="detail-content">
            {(college.get('highlights', 'N/A') or 'N/A').replace('; ', ' • ')}
        </div>
    </div>
    """, unsafe_allow_html=True)

    contact_parts = []
    if college.get('website'):
        contact_parts.append(f"🌐 <a href='{college['website']}' style='color: #667eea;'>{college['website']}</a>")
    if college.get('phone'):
        contact_parts.append(f"📞 {college['phone']}")
    if college.get('email'):
        contact_parts.append(f"📧 {college['email']}")

    if contact_parts:
        st.markdown(f"""
        <div class="detail-section">
            <div class="detail-title">📞 Contact</div>
            <div class="detail-content">{'  |  '.join(contact_parts)}</div>
        </div>
        """, unsafe_allow_html=True)


# --------------------------------------------------
# Initialize Session State
# --------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "stats" not in st.session_state:
    st.session_state.stats = None

if "selected_college_id" not in st.session_state:
    st.session_state.selected_college_id = None


# --------------------------------------------------
# Hero Section
# --------------------------------------------------
st.markdown("""
<div class="hero-container">
    <div class="hero-title">🎓 Indian College Explorer</div>
    <div class="hero-subtitle">AI-Powered • Detailed Fees, Courses, Admissions & Placements for 45+ Top Colleges</div>
</div>
""", unsafe_allow_html=True)


# --------------------------------------------------
# Load Stats
# --------------------------------------------------
if st.session_state.stats is None:
    stats_data = api_call("/stats")
    if stats_data:
        st.session_state.stats = stats_data

stats = st.session_state.stats

if stats:
    govt_count = stats.get("by_type", {}).get("Government", 0)
    private_count = stats.get("by_type", {}).get("Private", 0)
    deemed_count = stats.get("by_type", {}).get("Deemed University", 0)

    st.markdown(f"""
    <div class="stat-grid">
        <div class="stat-card">
            <div class="stat-number">{stats.get('total_colleges', 0)}</div>
            <div class="stat-label">Curated Colleges</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{stats.get('total_states', 0)}</div>
            <div class="stat-label">States</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{govt_count}</div>
            <div class="stat-label">Government</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{private_count + deemed_count}</div>
            <div class="stat-label">Private / Deemed</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
else:
    st.warning("⚠️ Cannot connect to the API server. Run: `uvicorn api:app --reload`")


# --------------------------------------------------
# Sidebar
# --------------------------------------------------
with st.sidebar:
    st.markdown("### 🔧 Filters")

    # State filter
    states_data = api_call("/states")
    state_list = ["All States"] + (states_data.get("states", []) if states_data else [])
    selected_state = st.selectbox("📍 State", state_list, index=0)

    # Type filter
    type_options = ["All Types", "Government", "Private", "Deemed University"]
    selected_type = st.selectbox("🏷️ Institution Type", type_options, index=0)

    st.divider()

    st.markdown("### 📊 States Coverage")
    if stats:
        top_states = stats.get("top_states", {})
        for state_name, count in list(top_states.items())[:8]:
            st.markdown(f"**{state_name}**: {count} colleges")

    st.divider()
    st.markdown(
        "<div style='color: #667eea; font-size: 0.72rem; text-align: center;'>"
        "45+ Curated Colleges with Full Details<br>"
        "Fees • Courses • Admissions • Placements<br>"
        "Powered by Groq AI"
        "</div>",
        unsafe_allow_html=True
    )


# --------------------------------------------------
# Main Content — Tabs
# --------------------------------------------------
tab_chat, tab_search, tab_directory, tab_browse = st.tabs([
    "💬 AI Chat", "🔍 Search", "📋 College Directory", "🗺️ Browse by State"
])


# --------------------------------------------------
# Tab 1: AI Chat
# --------------------------------------------------
with tab_chat:
    st.markdown("##### Ask anything — fees, admissions, placements, courses, comparisons")

    # Featured college — BIT Campus
    bit_campus = api_call("/search", data={"q": "BIT Campus", "limit": 1})
    if bit_campus and bit_campus.get("colleges"):
        render_college_card(bit_campus["colleges"][0], featured=True)

    # Quick question buttons
    st.markdown("**💡 Try asking:**")
    quick_cols = st.columns(3)
    quick_questions = [
        "Tell me about BIT Campus Trichy",
        "Fees of NIT Tiruchirappalli",
        "Compare IIT Madras vs IIT Bombay"
    ]

    for i, q in enumerate(quick_questions):
        with quick_cols[i]:
            if st.button(f"📌 {q}", key=f"quick_{i}", use_container_width=True):
                st.session_state.messages.append({"role": "user", "content": q})
                response = api_call("/chat", method="POST", data={"question": q})
                if response:
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response["answer"]
                    })
                else:
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": "⚠️ Cannot connect to API server."
                    })
                st.rerun()

    quick_cols2 = st.columns(3)
    quick_questions2 = [
        "Admission process for VIT Vellore",
        "Placements at SRM Chennai",
        "Government colleges in Tamil Nadu"
    ]

    for i, q in enumerate(quick_questions2):
        with quick_cols2[i]:
            if st.button(f"📌 {q}", key=f"quick2_{i}", use_container_width=True):
                st.session_state.messages.append({"role": "user", "content": q})
                response = api_call("/chat", method="POST", data={"question": q})
                if response:
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response["answer"]
                    })
                else:
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": "⚠️ Cannot connect to API server."
                    })
                st.rerun()

    st.divider()

    # Chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    user_input = st.chat_input("Ask about fees, admissions, placements, courses...")

    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})

        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner("🔍 Searching college database..."):
                response = api_call("/chat", method="POST", data={"question": user_input})

                if response:
                    bot_reply = response["answer"]
                else:
                    bot_reply = "⚠️ Cannot connect to API server. Please ensure the backend is running."

                st.markdown(bot_reply)

        st.session_state.messages.append({"role": "assistant", "content": bot_reply})


# --------------------------------------------------
# Tab 2: Search
# --------------------------------------------------
with tab_search:
    st.markdown("##### 🔍 Search Colleges")

    search_query = st.text_input(
        "Type a college name, city, or keyword...",
        placeholder="e.g., BIT Campus, NIT, IIT Madras, Trichy, Coimbatore...",
        key="search_input"
    )

    if search_query and len(search_query) >= 2:
        with st.spinner("Searching..."):
            results = api_call("/search", data={"q": search_query, "limit": 30})

        if results and results.get("colleges"):
            st.markdown(f"**Found {results['count']} results** for \"{search_query}\"")
            st.divider()

            for college in results["colleges"]:
                render_college_card(college)

                # Expandable details
                with st.expander(f"📋 Full Details — {college.get('short_name', college.get('name', ''))}"):
                    detail = api_call(f"/college/{college.get('id', 0)}")
                    if detail and not detail.get("error"):
                        render_college_detail(detail)
                    else:
                        render_college_detail(college)
        elif results:
            st.info(f"No colleges found matching \"{search_query}\". Try a different name.")
        else:
            st.error("⚠️ Cannot connect to API server.")


# --------------------------------------------------
# Tab 3: College Directory
# --------------------------------------------------
with tab_directory:
    st.markdown("##### 📋 All Colleges at a Glance")

    all_colleges = api_call("/colleges")

    if all_colleges and all_colleges.get("colleges"):
        colleges_list = all_colleges["colleges"]

        # Apply filters
        if selected_state != "All States":
            colleges_list = [c for c in colleges_list if c.get("state") == selected_state]

        if selected_type != "All Types":
            colleges_list = [c for c in colleges_list if selected_type.lower() in (c.get("type", "")).lower()]

        st.markdown(f"**Showing {len(colleges_list)} colleges**")
        st.divider()

        for college in colleges_list:
            render_college_card(college)

            with st.expander(f"📋 Full Details — {college.get('short_name', college.get('name', ''))}"):
                detail = api_call(f"/college/{college.get('id', 0)}")
                if detail and not detail.get("error"):
                    render_college_detail(detail)
                else:
                    st.info("Details loading...")

        if len(colleges_list) == 0:
            st.info(f"No colleges found with current filters.")
    else:
        st.info("Loading college directory...")


# --------------------------------------------------
# Tab 4: Browse by State
# --------------------------------------------------
with tab_browse:
    st.markdown("##### 🗺️ Browse Colleges by State")

    browse_state = selected_state if selected_state != "All States" else None

    if browse_state:
        with st.spinner(f"Loading colleges in {browse_state}..."):
            state_colleges = api_call("/colleges/by-state", data={"state": browse_state, "limit": 50})

        if state_colleges and state_colleges.get("colleges"):
            colleges_list = state_colleges["colleges"]
            if selected_type != "All Types":
                colleges_list = [c for c in colleges_list if selected_type.lower() in (c.get("type", "")).lower()]

            st.markdown(f"**Showing {len(colleges_list)} colleges in {browse_state}**")
            st.divider()

            for college in colleges_list:
                render_college_card(college)

                with st.expander(f"📋 Full Details — {college.get('short_name', college.get('name', ''))}"):
                    detail = api_call(f"/college/{college.get('id', 0)}")
                    if detail and not detail.get("error"):
                        render_college_detail(detail)

            if len(colleges_list) == 0:
                st.info(f"No {selected_type} colleges found in {browse_state}.")
        else:
            st.info(f"No data found for {browse_state}.")
    else:
        st.info("👈 Select a state from the sidebar to browse colleges.")

        if stats:
            st.markdown("**🌟 States with Colleges:**")
            top_states = list(stats.get("top_states", {}).keys())[:8]
            cols = st.columns(4)
            for i, state_name in enumerate(top_states):
                with cols[i % 4]:
                    st.markdown(f"""
                    <div class="college-card" style="text-align: center;">
                        <div class="college-name">{state_name}</div>
                        <div class="college-info">{stats['top_states'][state_name]} colleges</div>
                    </div>
                    """, unsafe_allow_html=True)