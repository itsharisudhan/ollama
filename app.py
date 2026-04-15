import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000/chat"

st.set_page_config(
    page_title="Trichy College Admission Chatbot",
    page_icon="🎓",
    layout="wide"
)

st.title("🎓 Trichy Engineering College Assistant")

st.markdown(
    "Select a college or ask a question about admissions, courses, placements and campus details."
)

# ----------------------------
# Initialize Chat Memory
# ----------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# ----------------------------
# College List
# ----------------------------
colleges = [
    "University College of Engineering BIT Campus",
    "Government College of Engineering, Srirangam",
    "Cauvery College of Engineering & Technology",
    "Indra Ganesan College of Engineering",
    "J.J College of Engineering and Technology",
    "M.A.M College of Engineering",
    "NIT Trichy",
    "Saranathan College of Engineering",
    "MIET Engineering College",
    "SRM Institute of Science and Technology",
    "Trichy Engineering College"
]

st.subheader("🏫 Trichy Engineering Colleges")

cols = st.columns(3)

# ----------------------------
# College Buttons
# ----------------------------
for i, college in enumerate(colleges):

    with cols[i % 3]:

        if st.button(f"🏫 {college}", use_container_width=True):

            question = f"Tell me about {college}"

            st.session_state.messages.append({
                "role": "user",
                "content": question
            })

            try:

                response = requests.post(
                    API_URL,
                    json={"question": question}
                )

                if response.status_code == 200:
                    answer = response.json()["answer"]
                else:
                    answer = "⚠️ API Error"

            except:
                answer = "⚠️ Cannot connect to chatbot server"

            st.session_state.messages.append({
                "role": "assistant",
                "content": answer
            })

# ----------------------------
# Chat Section
# ----------------------------
st.divider()

st.subheader("💬 Chat with Admission Assistant")

# Display previous messages
for message in st.session_state.messages:

    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ----------------------------
# Chat Input
# ----------------------------
user_input = st.chat_input("Ask about courses, placements, admissions...")

if user_input:

    # Show user message
    st.session_state.messages.append({
        "role": "user",
        "content": user_input
    })

    with st.chat_message("user"):
        st.markdown(user_input)

    try:

        response = requests.post(
            API_URL,
            json={"question": user_input}
        )

        if response.status_code == 200:
            bot_reply = response.json()["answer"]
        else:
            bot_reply = "⚠️ Error from API"

    except:
        bot_reply = "⚠️ Cannot connect to FastAPI server"

    # Save bot message
    st.session_state.messages.append({
        "role": "assistant",
        "content": bot_reply
    })

    # Show bot response
    with st.chat_message("assistant"):
        st.markdown(bot_reply)