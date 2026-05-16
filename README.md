\# GDPR Privacy Policy Analyzer



A beginner LegalTech and data science project that performs a basic GDPR transparency screening of privacy policies.



\## Overview



This app allows users to paste a privacy policy and receive a keyword-based GDPR screening report. It checks whether the policy mentions important transparency areas such as legal basis, data retention, user rights, cookies, international transfers, automated decision-making, and complaint rights.



\## Features



\- GDPR checklist analysis

\- Strong / Weak / Missing classification

\- Matched keyword detection

\- Evidence sentence extraction

\- Legal-style recommendations

\- CSV report download

\- PDF report download

\- Streamlit web interface



\## Tech Stack



\- Python

\- Streamlit

\- pandas

\- ReportLab



\## How It Works



The app uses keyword-based text analysis to detect whether a privacy policy includes certain GDPR-related transparency elements. It then assigns a score, classifies the risk level, and generates a report.



\## Disclaimer



This tool is for learning and preliminary legal screening only. It does not replace professional legal advice or a full GDPR compliance audit.



\## How to Run Locally



```bash

pip install -r requirements.txt

streamlit run app.py
## Live Demo

Try the app here: https://gdpr-privacy-policy-analyzer-fh4ynkvxkk2v62xhd3nevs.streamlit.app/

Author



Built by Testimony as a LegalTech and data science portfolio project.

