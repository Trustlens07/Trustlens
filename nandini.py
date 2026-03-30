# HOMESCREEN

import streamlit as st

# --------------- PAGE CONFIG ----------------
st.set_page_config(page_title="AI Resume Screener", layout="wide")

# --------------- SESSION STATE ----------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "user_type" not in st.session_state:
    st.session_state.user_type = None

if "show_company_login" not in st.session_state:
    st.session_state.show_company_login = False

if "show_candidate_status" not in st.session_state:
    st.session_state.show_candidate_status = False

if "show_status_page" not in st.session_state:
    st.session_state.show_status_page = False

if "selected_candidate" not in st.session_state:
    st.session_state.selected_candidate = None


# --------------- SAMPLE CANDIDATE DATABASE ----------------
candidate_records = {
    "APP001": {
        "email": "user@gmail.com",
        "name": "Alice Johnson",
        "skills": "Python, Machine Learning, SQL",
        "status": "Accepted",
        "criteria": "Skill match, ML project experience, problem solving",
        "reason": "Strong ML portfolio and relevant internship experience",
        "improvement": "Improve system design knowledge"
    },
    "APP002": {
        "email": "test@gmail.com",
        "name": "Bob Smith",
        "skills": "Java, Spring Boot",
        "status": "Rejected",
        "criteria": "Backend development skills, project relevance",
        "reason": "Limited project experience related to job role",
        "improvement": "Work on real backend projects and improve API design skills"
    },
    "APP003": {
        "email": "candidate@gmail.com",
        "name": "Charlie Brown",
        "skills": "React, JavaScript, UI Design",
        "status": "Pending",
        "criteria": "Frontend development, UI/UX portfolio",
        "reason": "Application under review by HR team",
        "improvement": "Add more real-world UI projects"
    }
}


# --------------- SIMPLE COMPANY AUTH SYSTEM ----------------
users = {
    "company": {"admin@company.com": "1234"}
}

def login(email, password):
    if email in users["company"] and users["company"][email] == password:
        st.session_state.logged_in = True
        st.session_state.user_type = "company"
        return True
    return False


# --------------- HEADER ----------------
col1, col2, col3 = st.columns([2,6,2])

with col1:
    st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=80)

with col2:
    st.markdown(
        "<h1 style='text-align:center;'>AI Resume Screening Platform</h1>",
        unsafe_allow_html=True
    )

with col3:

    if not st.session_state.logged_in:

        if st.button("Company Login"):
            st.session_state.show_company_login = True

        if st.button("Candidate Status Check"):
            st.session_state.show_candidate_status = True

    else:
        st.success("Logged in as Company")

        if st.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.user_type = None

st.markdown("---")


# --------------- COMPANY LOGIN ----------------
if st.session_state.show_company_login:

    st.subheader("Company Login")

    email = st.text_input("Company Email")
    password = st.text_input("Password", type="password")

    if st.button("Login as Company"):

        if login(email, password):
            st.success("Login Successful!")
            st.session_state.show_company_login = False
        else:
            st.error("Invalid credentials")


# --------------- CANDIDATE STATUS CHECK ----------------
if st.session_state.show_candidate_status:

    st.subheader("Candidate Application Status Check")

    email = st.text_input("Candidate Email")
    app_id = st.text_input("Application ID")

    if st.button("Check Status"):

        if app_id in candidate_records:

            record = candidate_records[app_id]

            if record["email"] == email:
                st.session_state.selected_candidate = record
                st.session_state.show_status_page = True
            else:
                st.error("Email does not match the Application ID")

        else:
            st.error("Invalid Application ID")


# --------------- STATUS PAGE ----------------
if st.session_state.show_status_page:

    data = st.session_state.selected_candidate

    st.title("Application Status")

    st.success(f"Current Status: {data['status']}")

    st.markdown("### Candidate Details")

    st.table({
        "Field": [
            "Candidate Name",
            "Skills Identified",
            "Selection Criteria Considered",
            "Reason for Decision",
            "Suggested Improvements"
        ],
        "Details": [
            data["name"],
            data["skills"],
            data["criteria"],
            data["reason"],
            data["improvement"]
        ]
    })

    if st.button("Back"):
        st.session_state.show_status_page = False


st.markdown("---")


# --------------- HERO SECTION ----------------
st.markdown("## 🚀 Hire Smarter with AI-Powered Resume Screening")
st.write("Quickly filter and shortlist the best candidates using intelligent automation.")

col1, col2 = st.columns(2)

with col1:
    st.button("Start Screening")
    st.button("Request Demo")

with col2:
    st.image(
        "https://images.unsplash.com/photo-1551288049-bebda4e38f71",
        caption="AI Dashboard Preview"
    )

st.markdown("---")


# --------------- PROMOTIONAL ----------------
st.markdown("## 🌟 Why Choose Us?")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Resumes Screened", "10,000+")

with col2:
    st.metric("Companies Onboarded", "500+")

with col3:
    st.metric("Time Saved", "70%")


st.markdown("---")


# --------------- ABOUT ----------------
st.markdown("## ℹ️ About Our Platform")

st.write("""
Our AI-powered platform helps companies streamline hiring
by automatically screening and ranking resumes.
""")


st.markdown("---")


# --------------- FEATURES ----------------
st.markdown("## ⚙️ Core Features")

features = [
    "Resume Parsing (PDF, DOCX)",
    "AI-Based Ranking",
    "Skill Matching",
    "Bulk Upload",
    "Analytics Dashboard",
    "Export Candidates"
]

for f in features:
    st.write(f"✔️ {f}")


st.markdown("---")


# --------------- TESTIMONIALS ----------------
st.markdown("## ⭐ Testimonials")

col1, col2 = st.columns(2)

with col1:
    st.info("“Reduced hiring time drastically.” – HR Manager")

with col2:
    st.info("“Very efficient tool.” – Recruiter")


st.markdown("---")


# --------------- DEMO ----------------
st.markdown("## 🎥 Demo")

st.video("https://www.youtube.com/watch?v=dQw4w9WgXcQ")


st.markdown("---")


# --------------- CONTACT ----------------
st.markdown("## 📧 Contact Us")

with st.form("contact"):

    name = st.text_input("Name")
    email = st.text_input("Email")
    msg = st.text_area("Message")

    submit = st.form_submit_button("Send")

    if submit:
        st.success("Message sent!")


st.markdown("---")


# --------------- FAQ ----------------
st.markdown("## ❓ FAQ")

with st.expander("How does AI screening work?"):
    st.write("AI evaluates resumes using skills and keywords.")

with st.expander("Is data secure?"):
    st.write("Yes, we use encryption and secure storage.")


st.markdown("---")


# --------------- FOOTER ----------------
st.markdown("""
© 2026 AI Resume Screening Platform  

Privacy Policy | Terms | Copyright
""")