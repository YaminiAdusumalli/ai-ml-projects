import streamlit as st
import requests

# Backend URL (FastAPI server)
BACKEND_URL = "http://127.0.0.1:8000"

# Page setup
st.set_page_config(page_title="Resume Matcher v2", layout="wide")
st.title("🧠 Resume Matcher v2")
st.write("Upload up to 3 resumes and paste a job description to find the best fit candidate.")

# File uploader
uploaded_files = st.file_uploader(
    "Upload Resumes (PDF or DOCX)",
    type=["pdf", "docx"],
    accept_multiple_files=True
)

# Job description input
job_description = st.text_area("Paste Job Description", height=200)

# Button for processing
if st.button("Match Candidates"):
    if not uploaded_files or not job_description.strip():
        st.warning("⚠️ Please upload resumes and enter a job description.")
    else:
        try:
            # Step 1 — Upload resumes
            with st.spinner("📤 Uploading resumes..."):
                resume_ids = []
                for file in uploaded_files:
                    # ✅ Field name must match backend
                    files = {"files": (file.name, file, file.type)}
                    res = requests.post(f"{BACKEND_URL}/upload", files=files)
                    if res.ok:
                        data = res.json()
                        resume_ids.extend(data.get("resume_ids", []))
                    else:
                        st.error(f"❌ Failed to upload {file.name}")
                        st.stop()

                st.write("Uploaded Resume IDs:", resume_ids)

            # Step 2 — Learn from resumes
            with st.spinner("🧠 Learning from resumes..."):
                learn_res = requests.post(
                    f"{BACKEND_URL}/learn",
                    json={"resume_ids": resume_ids}
                )
                if not learn_res.ok:
                    st.error("❌ Learning step failed.")
                    st.stop()

            # Step 3 — Match candidates
            with st.spinner("🔍 Matching candidates to the job description..."):
                match_res = requests.post(
                    f"{BACKEND_URL}/match",
                    json={
                        "resume_ids": resume_ids,
                        "job_description": job_description.strip(),
                    },
                )

            # Step 4 — Handle results
            if not match_res.ok:
                st.error("❌ Matching step failed.")
            else:
                results = match_res.json().get("results", [])
                if not results:
                    st.warning("No matches found.")
                else:
                    st.success("✅ Matching complete! Here are the results:")

                    # 🔁 Loop through each candidate result
                    for r in results:
                        filename = r.get("filename", f"Resume_{r['resume_id']}")
                        score = r.get("score", 0)

                        # Header with better formatting
                        st.markdown(
                            f"""
                            <div style="padding:10px; border-radius:10px; background-color:#202830; margin-bottom:10px;">
                                <h4 style="color:#4FC3F7;">👤 <b>{filename}</b> — 
                                <span style="color:#FFD54F;">Score: {score:.2f}</span></h4>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                        # Section scores
                        if r.get("section_scores"):
                            st.write("**📊 Section-wise Scores:**")
                            for section, value in r["section_scores"].items():
                                st.progress(min(value, 1.0))  # progress bar
                                st.caption(f"{section.capitalize()}: {value:.2f}")

                        # Why this resume is a good match
                        if r.get("highlights"):
                            highlights = [h.capitalize() for h in r["highlights"][:6]]
                            skills_list = ", ".join(highlights[:-1]) + f", and {highlights[-1]}" if len(highlights) > 1 else highlights[0]

                            st.markdown("**💡 Why this candidate fits the role:**")
                            
                            st.markdown(
                                   f"""
                                   <p style='color:#A5D6A7; font-size:15px;'>
                                   This resume appears to be a strong fit for this role because the candidate demonstrates
                                   solid experience and technical proficiency in <b>{skills_list}</b>, aligning well with the job’s skill requirements.
                                   </p>
              """,
                                
                                unsafe_allow_html=True
                            )

                        st.divider()

        except Exception as e:
            st.error(f"Unexpected error: {e}")
