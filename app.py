import streamlit as st
import os
from dotenv import load_dotenv
import cohere
import csv
from datetime import datetime

def save_to_csv(candidate_data, tech_questions, tech_answers):
    file_exists = os.path.isfile("interview_results.csv")

    with open("interview_results.csv", "a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)

        # Write header only once
        if not file_exists:
            header = ["timestamp"] + list(candidate_data.keys())
            for i in range(len(tech_questions)):
                header.append(f"Q{i+1}")
                header.append(f"A{i+1}")
            writer.writerow(header)

        # Write row
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        row = [timestamp] + list(candidate_data.values())

        for i in range(len(tech_questions)):
            row.append(tech_questions[i])
            row.append(tech_answers.get(i, ""))

        writer.writerow(row)


# --------------------------------
# Setup
# --------------------------------
load_dotenv()
co = cohere.Client(os.getenv("COHERE_API_KEY"))

st.set_page_config(page_title="AI Hiring Assistant", layout="centered")
st.title("🤖 AI Hiring Assistant")

# --------------------------------
# Session state
# --------------------------------
if "question_index" not in st.session_state:
    st.session_state.question_index = 0

if "candidate_data" not in st.session_state:
    st.session_state.candidate_data = {}

if "tech_questions" not in st.session_state:
    st.session_state.tech_questions = []

if "tech_answers" not in st.session_state:
    st.session_state.tech_answers = {}

if "interview_started" not in st.session_state:
    st.session_state.interview_started = False

if "interview_submitted" not in st.session_state:
    st.session_state.interview_submitted = False


# --------------------------------
# Candidate questions (PDF)
# --------------------------------
CANDIDATE_QUESTIONS = [
    ("full_name", "What is your full name?"),
    ("email", "What is your email address?"),
    ("phone", "What is your phone number?"),
    ("experience", "How many years of experience do you have?"),
    ("position", "What position(s) are you applying for?"),
    ("location", "What is your current location?"),
    ("tech_stack", "Please list your tech stack (languages, frameworks, tools).")
]

# --------------------------------
# Phase 1: Candidate details (one by one)
# --------------------------------
if st.session_state.question_index < len(CANDIDATE_QUESTIONS):

    key, question = CANDIDATE_QUESTIONS[st.session_state.question_index]

    st.subheader(question)

    answer = st.text_input(
        "Your answer:",
        key=f"candidate_{st.session_state.question_index}"
    )

    if st.button("Next"):
        if answer.strip() == "":
            st.warning("Please enter an answer.")
        else:
            st.session_state.candidate_data[key] = answer
            st.session_state.question_index += 1
            st.rerun()
    # --------------------------------
# Transition screen: Ready for interview
# --------------------------------
elif (
    st.session_state.question_index >= len(CANDIDATE_QUESTIONS)
    and not st.session_state.interview_started
):

    st.success("✅ Candidate details submitted successfully!")

    st.markdown("""
### 🧠 Technical Interview

You are now about to start the technical interview.

When you are ready, click the **Start Interview** button below.
""")

    if st.button("Start Interview"):
        st.session_state.interview_started = True
        st.rerun()


# --------------------------------
# Phase 2: Generate technical questions
# --------------------------------
elif (
    st.session_state.interview_started
    and not st.session_state.tech_questions
):
    tech_stack = st.session_state.candidate_data["tech_stack"]

    prompt = f"""
You are a technical interviewer.

Based on the candidate's tech stack below:
{tech_stack}

Generate 3 to 5 CLEAR, DIRECT technical interview QUESTIONS.

Rules:
- Each item MUST be a question
- Each question MUST end with a question mark (?)
- Do NOT return topics or headings
- Do NOT include explanations
- Return ONLY a numbered list of questions

Example:
1. What is the difference between stack and queue?
2. Explain encapsulation in OOP with an example.
"""


    response = co.chat(
        model="command-a-03-2025",
        message=prompt
    )

    # Split questions into list
    questions = [
    q.strip()
    for q in response.text.split("\n")
    if q.strip().startswith(tuple(str(i) for i in range(1, 10)))
    and q.strip().endswith("?")
]


    st.session_state.tech_questions = questions
    st.rerun()

# --------------------------------
# Phase 3: Technical interview (WRITE ANSWERS)
# --------------------------------
elif st.session_state.tech_questions and not st.session_state.interview_submitted:

    st.subheader("🧠 Technical Interview")

    for i, q in enumerate(st.session_state.tech_questions):
        st.markdown(f"**{q}**")

        st.session_state.tech_answers[i] = st.text_area(
            "Your answer:",
            key=f"tech_answer_{i}"
        )

    if st.button("Submit Interview"):
        save_to_csv(
            st.session_state.candidate_data,
            st.session_state.tech_questions,
            st.session_state.tech_answers
        )
        st.session_state.interview_submitted = True
        st.rerun()



# --------------------------------
# Phase 4: Completion screen
# --------------------------------
elif st.session_state.interview_submitted:
    st.success("✅ Interview completed successfully!")
    st.info("Thank you for your time. Our team will contact you soon.")

    if os.path.exists("interview_results.csv"):
        with open("interview_results.csv", "rb") as f:
            st.download_button(
                "⬇ Download Interview Results (CSV)",
                f,
                file_name="interview_results.csv",
                mime="text/csv"
            )
