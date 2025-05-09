import streamlit as st
import base64
import requests
import tempfile
from datetime import datetime
import nltk
nltk.download('stopwords')
import pyresparser
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import warnings
import spacy
warnings.filterwarnings("ignore", category=UserWarning)


BACKEND_URL = "http://localhost:8000"  # Change to your backend IP if deployed elsewhere

st.set_page_config(page_title="AI Resume Analyzer", layout="centered")
st.title("📄 AI Resume Analyzer")
st.markdown("Upload your resume and paste the job description (JD) to get AI-powered feedback.")


def show_pdf(file_path):
    with open(file_path, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)


def extract_resume_info(file_path, jd_text):
    pyresparser.resume_parser.custom_nlp = spacy.load("en_core_web_sm")

    data = pyresparser.ResumeParser(file_path).get_extracted_data()
    resume_text = " ".join([
        str(data.get("name", "")),
        str(data.get("email", "")),
        str(data.get("skills", "")),
        str(data.get("college_name", "")),
        str(data.get("degree", "")),
        str(data.get("designation", "")),
        str(data.get("company_names", ""))
    ])

    return (
        {
            "name": data.get("name", "N/A"),
            "email_id": data.get("email", "N/A"),
            "mobile_num": data.get("mobile_number"),
        },
        {
            "resume_score": 0,
            "timestamp": datetime.utcnow().timestamp(),
            "no_of_pages": data.get("no_of_pages", 1),
            "user_level": "Fresher" if data.get("no_of_pages", 1) == 1 else "Intermediate",
            "skills": data.get("skills"),
            "total_experience": data.get("total_experience"),
            "job_description": jd_text
        },
    
    )


uploaded_file = st.file_uploader("Upload your Resume (PDF)", type=["pdf"])
jd_text = st.text_area("Paste the Job Description (JD) below:")

if uploaded_file is not None and jd_text.strip():
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(uploaded_file.read())
        tmp_path = tmp_file.name

    st.subheader("📄 Uploaded Resume Preview")
    show_pdf(tmp_path)

    st.subheader("🔍 AI Evaluation")
    with st.spinner("Analyzing resume..."):
        data = extract_resume_info(tmp_path, jd_text)

        print(data[0])

        try:
            upload_user = requests.post(f"{BACKEND_URL}/add_user/", json=data[0])
            upload_user.raise_for_status()

            resume_score = requests.post(f"{BACKEND_URL}/calculate_score/",json=data[1] ,params={"user_id": upload_user.json().get("user_id")})
            resume_score.raise_for_status()

            data[1]["resume_score"] = float(resume_score.json().get("resume_score", 0))

            upload_response = requests.post(f"{BACKEND_URL}/recommend", json=data[1], params={"user_id": upload_user.json().get("user_id")})
            upload_response.raise_for_status()

            recs = upload_response.json().get("recommendations")

            st.success("✅ Resume analyzed successfully!")
            st.markdown(f"### 📊 Resume Score: `{data[1]['resume_score']} / 100`")
            st.markdown(f"### 💡 Recommendations:\n{recs}")
        except Exception as e:
            st.error(f"❌ Error occurred: {e}")