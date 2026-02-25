import streamlit as st
import pandas as pd
import sqlite3
from datetime import date, datetime
def init_db():
    conn = sqlite3.connect("crm_data.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            demo_req INTEGER,
            registration INTEGER,
            whatsapp_enquiry INTEGER,
            pricing_check INTEGER,
            source TEXT,
            enquiry_date TEXT,
            status TEXT DEFAULT 'New'
        )
    """)
    conn.commit()
    conn.close()
def calculate_metrics(row):
    score = 0
    reasons = []
    if row["demo_req"]:
        score += 40
        reasons.append("Requested Demo")
    if row["registration"]:
        score += 10
        reasons.append("Registered")
    if row["whatsapp_enquiry"]:
        score += 15
        reasons.append("WhatsApp/Call Enquiry")
    if row["pricing_check"]:
        score += 20
        reasons.append("Checked Pricing")
    if row["source"] == "Referral":
        score += 15
        reasons.append("Referral Source")
    elif row["source"] == "Event":
        score += 5
        reasons.append("Event Lead")
    days_old = (date.today() - datetime.strptime(row["enquiry_date"], "%Y-%m-%d").date()).days
    decay = (days_old // 7) * 2
    score = max(0, min(100, score - decay))
    if score >= 70:
        nba = "CALL IMMEDIATELY"
    elif score >= 40:
        nba = "Send Case Study"
    else:
        nba = "Add to Monthly Newsletter"

    return pd.Series([score, ", ".join(reasons), nba])
st.set_page_config(page_title="AI CRM Assistant", layout="wide")
init_db()
st.title("AI Lead Scoring CRM")
with st.sidebar:
    st.header("Add New Lead")
    with st.form("lead_form", clear_on_submit=True):
        name = st.text_input("Lead Name")
        source = st.selectbox("Source", ["Referral", "Event", "Call", "WhatsApp", "Ad"])
        enq_date = st.date_input("Enquiry Date", value=date.today())
        st.write("---")
        demo = st.checkbox("Requested Demo")
        reg = st.checkbox("Registered")
        wa = st.checkbox("WhatsApp/Call Enquiry")
        price = st.checkbox("Pricing Comparison Check")
        submit = st.form_submit_button("Add to CRM")
        if submit and name:
            conn = sqlite3.connect("crm_data.db")
            c = conn.cursor()
            c.execute(
                """
                INSERT INTO leads
                (name, demo_req, registration, whatsapp_enquiry, pricing_check, source, enquiry_date)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (name, int(demo), int(reg), int(wa), int(price), source, str(enq_date)),
            )
            conn.commit()
            conn.close()
            st.success("Lead Added!")
conn = sqlite3.connect("crm_data.db")
df = pd.read_sql_query("SELECT * FROM leads", conn)
conn.close()
if not df.empty:
    df[["Score", "Why", "Next Action"]] = df.apply(calculate_metrics, axis=1)
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Active Leads", len(df))
    m2.metric("High Priority (70+)", len(df[df["Score"] >= 70]))
    m3.metric("Avg Quality Score", f"{int(df['Score'].mean())}%")
    st.subheader("Lead Priority Queue")
    def color_cells(val):
        if val >= 70:
            return "background-color: green; color: white"
        elif val >= 40:
            return "background-color: orange; color: white"
        else:
            return "background-color: gray; color: white"
    display_df = df[
        ["name", "Score", "Next Action", "Why", "source", "enquiry_date"]
    ]
    st.dataframe(
        display_df.sort_values(by="Score", ascending=False)
        .style.applymap(color_cells, subset=["Score"]),
        use_container_width=True,
        hide_index=True,
    )
    st.write("---")
    c1, c2 = st.columns(2)
    with c1:
        st.write("### Score Distribution")
        st.bar_chart(df["Score"])
    with c2:
        st.write("### Sources Performance")
        st.line_chart(df.groupby("source")["Score"].mean())
else:
    st.info("No leads in the database yet. Use the sidebar to add your first lead!")
