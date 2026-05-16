import re
import pandas as pd
import streamlit as st

from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle


def find_evidence_sentences(policy_text, matched_keywords, limit=2):
    sentences = re.split(r'(?<=[.!?])\s+', policy_text)

    evidence = []

    for sentence in sentences:
        sentence_lower = sentence.lower()

        for keyword in matched_keywords:
            if keyword in sentence_lower:
                clean_sentence = sentence.strip()

                if clean_sentence not in evidence:
                    evidence.append(clean_sentence)

                break

        if len(evidence) >= limit:
            break

    return evidence


def analyze_privacy_policy(policy_text):
    policy = policy_text.lower()

    checks = {
        "Data Controller": {
            "keywords": [
                "data controller", "controller", "responsible for processing",
                "who we are", "contact us", "registered office", "imprint"
            ],
            "strong_threshold": 2
        },
        "Legal Basis": {
            "keywords": [
                "legal basis", "lawful basis", "consent", "contract",
                "legitimate interest", "legal obligation", "vital interests",
                "public interest"
            ],
            "strong_threshold": 2
        },
        "Purpose of Processing": {
            "keywords": [
                "purpose", "purposes", "we use your data", "we process your data",
                "used to", "in order to", "to provide", "to improve"
            ],
            "strong_threshold": 2
        },
        "Data Retention": {
            "keywords": [
                "retention", "retain", "stored for", "keep your data",
                "storage period", "deleted after", "as long as necessary",
                "erased", "deleted"
            ],
            "strong_threshold": 2
        },
        "User Rights": {
            "keywords": [
                "right of access", "right to access", "access your data",
                "right to erasure", "delete your data", "right to rectification",
                "correct your data", "right to object", "data portability",
                "withdraw consent", "restriction of processing",
                "right to restriction", "right to complain"
            ],
            "strong_threshold": 3
        },
        "Third-Party Sharing": {
            "keywords": [
                "third party", "third parties", "service providers",
                "partners", "share your data", "recipients", "processors"
            ],
            "strong_threshold": 2
        },
        "International Transfers": {
            "keywords": [
                "international transfer", "outside the eu", "outside the eea",
                "outside the european union", "third country",
                "adequacy decision", "standard contractual clauses",
                "sccs"
            ],
            "strong_threshold": 2
        },
        "Cookies or Tracking": {
            "keywords": [
                "cookies", "tracking", "analytics", "pixel",
                "preferences", "cookie banner", "tracking technologies"
            ],
            "strong_threshold": 2
        },
        "Automated Decision-Making": {
            "keywords": [
                "automated decision", "profiling", "automated processing",
                "algorithmic decision", "solely automated",
                "no automated decision"
            ],
            "strong_threshold": 1
        },
        "Complaint to Authority": {
            "keywords": [
                "supervisory authority", "data protection authority",
                "complaint", "lodge a complaint", "right to complain"
            ],
            "strong_threshold": 1
        }
    }

    results = {}

    for category, data in checks.items():
        keywords = data["keywords"]
        threshold = data["strong_threshold"]

        found_keywords = [word for word in keywords if word in policy]

        if len(found_keywords) >= threshold:
            strength = "Strong"
        elif len(found_keywords) >= 1:
            strength = "Weak"
        else:
            strength = "Missing"

        evidence = find_evidence_sentences(policy_text, found_keywords)

        results[category] = {
            "strength": strength,
            "matched_keywords": found_keywords,
            "evidence": evidence
        }

    total_checks = len(checks)
    score = 0

    for item in results.values():
        if item["strength"] == "Strong":
            score += 1
        elif item["strength"] == "Weak":
            score += 0.5

    final_score = round((score / total_checks) * 100, 2)

    if final_score >= 80:
        risk_level = "Low Risk"
    elif final_score >= 50:
        risk_level = "Medium Risk"
    else:
        risk_level = "High Risk"

    return {
        "score": final_score,
        "risk_level": risk_level,
        "results": results
    }


def convert_report_to_dataframe(report):
    rows = []

    for category, result in report["results"].items():
        rows.append({
            "Category": category,
            "Strength": result["strength"],
            "Matched Keywords": ", ".join(result["matched_keywords"]) if result["matched_keywords"] else "None",
            "Evidence": " | ".join(result["evidence"]) if result["evidence"] else "None"
        })

    return pd.DataFrame(rows)


def generate_legal_conclusion(report):
    strong = []
    weak = []
    missing = []

    for category, result in report["results"].items():
        if result["strength"] == "Strong":
            strong.append(category)
        elif result["strength"] == "Weak":
            weak.append(category)
        else:
            missing.append(category)

    if report["score"] >= 80:
        conclusion = (
            "Based on this keyword-based screening, the privacy policy appears to cover many of the main GDPR transparency areas. "
            "However, a full legal review should still assess whether the wording is accurate, complete, and compliant in context."
        )
    elif report["score"] >= 50:
        conclusion = (
            "Based on this keyword-based screening, the privacy policy covers some important GDPR transparency areas, "
            "but several sections may need improvement. The policy should be reviewed carefully to ensure that users receive clear, complete, and accessible information."
        )
    else:
        conclusion = (
            "Based on this keyword-based screening, the privacy policy appears incomplete in several important GDPR transparency areas. "
            "The most urgent gaps should be reviewed and improved before relying on the policy as a compliance document."
        )

    return conclusion, strong, weak, missing


def get_recommendation(category):
    recommendation_texts = {
        "Data Controller": "The policy should clearly identify the data controller and provide contact details.",
        "Legal Basis": "The policy should explain the lawful basis for processing personal data, such as consent, contract, legal obligation, or legitimate interest.",
        "Purpose of Processing": "The policy should clearly explain the specific purposes for which personal data is processed.",
        "Data Retention": "The policy should state how long personal data is stored or explain the criteria used to decide the storage period.",
        "User Rights": "The policy should clearly explain GDPR rights such as access, rectification, erasure, objection, restriction, portability, and withdrawal of consent.",
        "Third-Party Sharing": "The policy should explain whether data is shared with third parties, service providers, processors, or other recipients.",
        "International Transfers": "The policy should state whether personal data is transferred outside the EU/EEA and explain the safeguards used.",
        "Cookies or Tracking": "The policy should explain the use of cookies, analytics, tracking tools, and user choices.",
        "Automated Decision-Making": "The policy should explain whether automated decision-making or profiling is used, or clearly state that it is not used.",
        "Complaint to Authority": "The policy should inform users that they can complain to a data protection supervisory authority."
    }

    return recommendation_texts.get(category, "This section may need further legal review.")

def generate_pdf_report(report, df_report, conclusion):
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()
    story = []

    title = Paragraph("GDPR Privacy Policy Analyzer Report", styles["Title"])
    story.append(title)
    story.append(Spacer(1, 16))

    summary = Paragraph(
        f"<b>Overall Score:</b> {report['score']}%<br/>"
        f"<b>Risk Level:</b> {report['risk_level']}",
        styles["Normal"]
    )
    story.append(summary)
    story.append(Spacer(1, 16))

    story.append(Paragraph("<b>Legal Screening Conclusion</b>", styles["Heading2"]))
    story.append(Paragraph(conclusion, styles["Normal"]))
    story.append(Spacer(1, 16))

    story.append(Paragraph("<b>Detailed Analysis</b>", styles["Heading2"]))

    table_data = [["Category", "Strength", "Matched Keywords"]]

    for _, row in df_report.iterrows():
        table_data.append([
            row["Category"],
            row["Strength"],
            row["Matched Keywords"]
        ])

    table = Table(table_data, colWidths=[150, 80, 250])

    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))

    story.append(table)
    story.append(Spacer(1, 16))

    story.append(Paragraph("<b>Recommendations</b>", styles["Heading2"]))

    for category, result in report["results"].items():
        if result["strength"] in ["Weak", "Missing"]:
            story.append(
                Paragraph(
                    f"<b>{result['strength']}: {category}</b>",
                    styles["Normal"]
                )
            )
            story.append(Paragraph(get_recommendation(category), styles["Normal"]))
            story.append(Spacer(1, 8))

    story.append(Spacer(1, 16))

    note = Paragraph(
        "<b>Legal Note:</b> This report is generated through keyword-based screening. "
        "It does not replace professional legal advice or a full GDPR compliance audit.",
        styles["Normal"]
    )
    story.append(note)

    doc.build(story)

    buffer.seek(0)
    return buffer
st.set_page_config(
    page_title="GDPR Privacy Policy Analyzer",
    page_icon="⚖️",
    layout="wide"
)
st.markdown("""
<style>
    .main {
        background-color: #f8fafc;
    }

    h1, h2, h3 {
        color: #1f2937;
    }

    .stAlert {
        border-radius: 12px;
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    .project-card {
        background-color: white;
        padding: 1.2rem;
        border-radius: 14px;
        border: 1px solid #e5e7eb;
        box-shadow: 0 4px 12px rgba(0,0,0,0.04);
        margin-bottom: 1rem;
    }

    .small-muted {
        color: #6b7280;
        font-size: 0.95rem;
    }
</style>
""", unsafe_allow_html=True)

st.title("⚖️ GDPR Privacy Policy Analyzer")

st.markdown("""
<div class="project-card">
    <p>
        This tool performs a basic GDPR transparency screening of privacy policies.
        It checks for key areas such as legal basis, data retention, user rights,
        international transfers, cookies, automated decision-making, and complaint rights.
    </p>
    <p class="small-muted">
        Built as a LegalTech and data science project combining legal analysis, text processing,
        keyword matching, evidence extraction, and automated reporting.
    </p>
</div>
""", unsafe_allow_html=True)

st.warning(
    "This is a keyword-based screening tool. It does not replace professional legal advice or a full GDPR compliance audit."
)
st.sidebar.title("About this project")

st.sidebar.write(
    "This GDPR Privacy Policy Analyzer is a beginner LegalTech/data science project."
)

st.sidebar.markdown("""
**Main features:**
- GDPR checklist analysis
- Strong / Weak / Missing classification
- Matched keyword detection
- Evidence sentence extraction
- Legal-style recommendations
- CSV report download
- PDF report download
""")

st.sidebar.markdown("""
**Built with:**
- Python
- Streamlit
- pandas
- ReportLab
""")

st.sidebar.info(
    "Designed for legal screening and learning purposes, not as a substitute for full legal advice."
)
sample_text = """
We collect your personal data to provide our services.
We process your data based on your consent and our legitimate interest.
You have the right to access, correct, and delete your personal data.
We may share your data with service providers.
We use cookies and analytics tools.
"""

policy_text = st.text_area(
    "Paste privacy policy text here:",
    value=sample_text,
    height=300
)

analyze_button = st.button("Analyze Privacy Policy")

if analyze_button:
    if not policy_text.strip():
        st.error("Please paste a privacy policy before running the analysis.")
    else:
        report = analyze_privacy_policy(policy_text)
        df_report = convert_report_to_dataframe(report)
        conclusion, strong, weak, missing = generate_legal_conclusion(report)

        st.subheader("Overall Result")

        col1, col2 = st.columns(2)

        with col1:
            st.metric("GDPR Screening Score", f"{report['score']}%")

        with col2:
            st.metric("Risk Level", report["risk_level"])

        if report["risk_level"] == "Low Risk":
            st.success("The policy appears to cover many key GDPR transparency areas.")
        elif report["risk_level"] == "Medium Risk":
            st.warning("The policy covers some areas but may need improvement.")
        else:
            st.error("The policy appears incomplete in several important GDPR transparency areas.")

        st.subheader("Legal Screening Conclusion")
        st.write(conclusion)

        st.subheader("Detailed Analysis Table")
        st.dataframe(df_report, use_container_width=True)

        st.subheader("Strong Areas")
        if strong:
            for item in strong:
                result = report["results"][item]

                with st.expander(item):
                    st.write("**Matched keywords:**")
                    st.write(", ".join(result["matched_keywords"]) if result["matched_keywords"] else "None")

                    st.write("**Evidence:**")
                    if result["evidence"]:
                        for sentence in result["evidence"]:
                            st.write(f"- {sentence}")
                    else:
                        st.write("None")
        else:
            st.write("No strong areas detected.")

        st.subheader("Weak Areas")
        if weak:
            for item in weak:
                result = report["results"][item]

                with st.expander(item):
                    st.write("**Matched keywords:**")
                    st.write(", ".join(result["matched_keywords"]) if result["matched_keywords"] else "None")

                    st.write("**Evidence:**")
                    if result["evidence"]:
                        for sentence in result["evidence"]:
                            st.write(f"- {sentence}")
                    else:
                        st.write("None")

                    st.write("**Recommendation:**")
                    st.write(get_recommendation(item))
        else:
            st.write("No weak areas detected.")

        st.subheader("Missing Areas")
        if missing:
            for item in missing:
                with st.expander(item):
                    st.write("**Matched keywords:** None")
                    st.write("**Evidence:** None")
                    st.write("**Recommendation:**")
                    st.write(get_recommendation(item))
        else:
            st.write("No missing areas detected.")

        st.subheader("Download Report")

        csv_data = df_report.to_csv(index=False).encode("utf-8")

        st.download_button(
            label="Download CSV Report",
            data=csv_data,
            file_name="gdpr_policy_analysis_report.csv",
            mime="text/csv"
        )

        pdf_data = generate_pdf_report(report, df_report, conclusion)

        st.download_button(
            label="Download PDF Report",
            data=pdf_data,
            file_name="gdpr_policy_analysis_report.pdf",
            mime="application/pdf"
        )