import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv
import os
import pandas as pd
from datetime import datetime

# Import helper functions from logic module
from logic import (
    extract_amount,
    extract_date,
    load_expense_data,
    save_expense_data,
    add_expense_entry,
    filter_valid_expenses,
    calculate_category_totals,
    format_excel_export,
    prepare_export_dataframe
)

# ---------- SETUP ----------
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

DATA_PATH = "data/voice_expenses.xlsx"
os.makedirs("data", exist_ok=True)

st.set_page_config(page_title="SpendLens - Voice Expense Logger", page_icon="🧾", layout="wide")


# ---------- LOAD DATA ----------
df = load_expense_data(DATA_PATH)

if "df" not in st.session_state:
    st.session_state.df = df

# ---------- SIDEBAR CHAT ----------
st.sidebar.header("💬 Chat with Your Expenses")
st.sidebar.caption("Ask anything about your spending — I’ll analyze your data like an iMessage chat.")

user_query = st.sidebar.text_input("Type your question here:")
if st.sidebar.button("Ask"):
    if user_query.strip() == "":
        st.sidebar.warning("Please enter a question.")
    elif st.session_state.df.empty:
        st.sidebar.info("No data available yet. Log some expenses first.")
    else:
        context = st.session_state.df.to_string(index=False)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a financial assistant analyzing expense data."},
                {"role": "user", "content": f"Here are my expenses:\n{context}\n\nQuestion: {user_query}"}
            ],
        ).choices[0].message.content
        st.sidebar.success(response)

# ---------- MAIN APP ----------
col1, col2 = st.columns([1, 6])
with col1:
    if os.path.exists("spendlens_logo.png"):
        st.image("spendlens_logo.png", width=100)
    else:
        st.warning("⚠️ Logo not found — please add 'spendlens_logo.png' to your project directory.")
with col2:
    st.title("SpendLens")
    st.caption("Know your spending before it knows you.")

st.markdown("---")

st.caption("Log your expenses manually or by voice — all data is saved and visualized automatically.")

# ---------- ADD NEW ENTRY ----------
if st.button("➕ Add New Entry"):
    for key in ["adding_entry", "expense_input", "category_select", "audio_input", "input_mode"]:
        if key in st.session_state:
            del st.session_state[key]
    st.session_state["adding_entry"] = True
    st.rerun()

if st.session_state.get("adding_entry", False):
    st.header("🎙️ Log a New Expense")

    input_mode = st.radio("Choose input mode:", ["🎤 Voice", "⌨️ Text"], horizontal=True, key="input_mode")

    expense_text = ""
    if input_mode == "🎤 Voice":
        st.write("Record your voice (e.g., 'Yesterday I spent $15 at Starbucks')")
        audio_input = st.audio_input("Record your voice", key="audio_input")
        if audio_input:
            transcript = client.audio.transcriptions.create(
                model="gpt-4o-mini-transcribe",
                file=audio_input
            )
            expense_text = transcript.text.strip()
            st.info(f"🗣️ Transcribed text: {expense_text}")
    else:
        expense_text = st.text_input(
            "Type a short description (e.g., 'Lunch at Chipotle for 12 dollars yesterday')",
            key="expense_input"
        )

    detected_amount = extract_amount(expense_text)
    detected_date = extract_date(expense_text)

    # ---------- MANUAL ENTRY FORM ----------
    with st.form("manual_entry_form", clear_on_submit=False):
        st.markdown(f"🧠 **Detected Date:** `{detected_date.strftime('%Y-%m-%d')}`")
        date_input = st.date_input("📅 Date of Expense", detected_date)

        st.markdown("### 🏷️ Select a Category")
        categories = [
            "Food", "Gas", "Shopping", "Entertainment", "Bills",
            "Transportation", "Healthcare", "Errands", "Subscriptions", "Other"
        ]
        selected_category = st.radio("Choose category:", categories, horizontal=True, key="category_select")

        if selected_category == "Other":
            custom_category = st.text_input("✏️ Enter custom category")
            category = custom_category if custom_category else "Uncategorized"
        else:
            category = selected_category

        amount = st.number_input("💵 Amount ($)", value=detected_amount, step=0.01, min_value=0.0)
        note = st.text_area("📝 Notes (optional)", value=expense_text)

        submitted = st.form_submit_button("💾 Save Expense")
        if submitted:
            st.session_state.df = add_expense_entry(
                st.session_state.df,
                date_input,
                category,
                amount,
                note
            )
            save_expense_data(st.session_state.df, DATA_PATH)
            st.success(f"✅ Saved ${amount:.2f} under {category} for {date_input.strftime('%Y-%m-%d')}")
            st.session_state["adding_entry"] = False
            st.rerun()

# ---------- DASHBOARD ----------
st.header("📊 Spending Dashboard")

if not st.session_state.df.empty:
    valid_df = filter_valid_expenses(st.session_state.df)

    st.dataframe(valid_df.reset_index(drop=True), use_container_width=True)

    total_spent = valid_df["Amount ($)"].sum()
    st.metric("💰 Total Spent", f"${total_spent:,.2f}")

    category_totals = calculate_category_totals(valid_df)
    st.bar_chart(category_totals)

# ---------- EXPORT ----------
st.subheader("💾 Export Data")

if not st.session_state.df.empty:
    export_df = prepare_export_dataframe(st.session_state.df)

    if not export_df.empty:
        save_expense_data(export_df, DATA_PATH)
        format_excel_export(DATA_PATH)

    with open(DATA_PATH, "rb") as f:
        st.download_button(
            label="⬇️ Download Formatted Excel File",
            data=f,
            file_name="voice_expenses_formatted.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

# ---------- CLEAR DATA ----------
st.subheader("🧹 Clear All Data")
if "clear_stage" not in st.session_state:
    st.session_state.clear_stage = "idle"

if st.session_state.clear_stage == "idle":
    if st.button("⚠️ Delete All Entries"):
        st.session_state.clear_stage = "confirm"
        st.rerun()
elif st.session_state.clear_stage == "confirm":
    st.warning("Are you sure you want to delete all expense data?")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Yes, clear all data"):
            st.session_state.df = pd.DataFrame(columns=["Date/Time", "Category", "Amount ($)", "Notes"])
            save_expense_data(st.session_state.df, DATA_PATH)
            st.session_state.clear_stage = "idle"
            st.success("✅ All data cleared successfully!")
            st.rerun()
    with col2:
        if st.button("❌ Cancel"):
            st.session_state.clear_stage = "idle"
            st.info("Operation cancelled.")
            st.rerun()
