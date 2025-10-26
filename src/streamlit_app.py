"""
SpendLens - AI-Powered Expense Tracker
Streamlit UI layer using SOLID architecture with dependency injection.
"""

import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv
import os
import pandas as pd
from datetime import datetime
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from logic import (
    ExpenseController,
    ExcelStorage,
    ExpenseParser,
    ExpenseAnalyzer,
    ExcelFormatter,
    OpenAIService
)
from models import Expense

# ---------- SETUP ----------
load_dotenv()

# Dependency Injection - SOLID Principle
DATA_PATH = "data/voice_expenses.xlsx"
os.makedirs("data", exist_ok=True)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Initialize dependencies
storage = ExcelStorage(DATA_PATH)
parser = ExpenseParser()
analyzer = ExpenseAnalyzer()
formatter = ExcelFormatter()
ai_service = OpenAIService(client)

# Create controller with dependency injection
controller = ExpenseController(storage, parser, analyzer, formatter, ai_service)

st.set_page_config(
    page_title="SpendLens - Voice Expense Logger",
    page_icon="🧾",
    layout="wide"
)

# ---------- SESSION STATE ----------
if "expenses_loaded" not in st.session_state:
    st.session_state.expenses_loaded = False
    st.session_state.dashboard_data = None

# Load expenses on first run
if not st.session_state.expenses_loaded:
    try:
        st.session_state.dashboard_data = controller.get_dashboard_data()
        st.session_state.expenses_loaded = True
    except Exception as e:
        st.error(f"Failed to load expenses: {e}")

# ---------- SIDEBAR CHAT ----------
st.sidebar.header("💬 Chat with Your Expenses")
st.sidebar.caption("Ask anything about your spending — powered by AI.")

user_query = st.sidebar.text_input("Type your question here:", key="user_query")
if st.sidebar.button("🔍 Ask", use_container_width=True):
    if user_query.strip() == "":
        st.sidebar.warning("⚠️ Please enter a question.")
    elif not st.session_state.dashboard_data or st.session_state.dashboard_data["expense_count"] == 0:
        st.sidebar.info("ℹ️ No data available yet. Log some expenses first.")
    else:
        try:
            with st.spinner("Analyzing..."):
                expenses = st.session_state.dashboard_data["expenses"]
                response = ai_service.analyze_expenses(expenses, user_query)
                st.sidebar.success(response)
        except Exception as e:
            st.sidebar.error(f"❌ Analysis failed: {e}")

# ---------- MAIN APP ----------
col1, col2 = st.columns([1, 6])
with col1:
    if os.path.exists("spendlens_logo.png"):
        st.image("spendlens_logo.png", width=100)
    else:
        st.write("🧾")
with col2:
    st.title("SpendLens")
    st.caption("Know your spending before it knows you.")

st.markdown("---")
st.caption("💡 Log your expenses manually or by voice — all data is saved and visualized automatically.")

# ---------- ADD NEW ENTRY ----------
if st.button("➕ Add New Entry", use_container_width=True, type="primary"):
    for key in ["adding_entry", "expense_input", "category_select", "audio_input", "input_mode"]:
        if key in st.session_state:
            del st.session_state[key]
    st.session_state["adding_entry"] = True
    st.rerun()

if st.session_state.get("adding_entry", False):
    st.header("🎙️ Log a New Expense")

    input_mode = st.radio(
        "Choose input mode:",
        ["🎤 Voice", "⌨️ Text"],
        horizontal=True,
        key="input_mode",
        help="Use voice for hands-free logging or text for manual entry"
    )

    expense_text = ""
    
    if input_mode == "🎤 Voice":
        st.write("🎤 Record your voice (e.g., 'Yesterday I spent $15 at Starbucks')")
        audio_input = st.audio_input("Record your voice", key="audio_input")
        
        if audio_input:
            try:
                with st.spinner("Transcribing audio..."):
                    expense_text = ai_service.transcribe_audio(audio_input)
                    st.info(f"🗣️ Transcribed: **{expense_text}**")
            except Exception as e:
                st.error(f"❌ Transcription failed: {e}")
                expense_text = ""
    else:
        expense_text = st.text_input(
            "Type a short description",
            placeholder="e.g., 'Lunch at Chipotle for 12 dollars yesterday'",
            key="expense_input",
            help="Describe your expense in natural language"
        )

    # Parse expense if text provided
    detected_amount = 0.0
    detected_date = datetime.now()
    
    if expense_text:
        try:
            parsed = parser.parse_expense(expense_text)
            detected_amount = parsed.detected_amount
            detected_date = parsed.detected_date
        except Exception as e:
            st.warning(f"⚠️ Parsing issue: {e}")

    # ---------- MANUAL ENTRY FORM ----------
    with st.form("manual_entry_form", clear_on_submit=False):
        st.markdown(f"🧠 **Detected Date:** `{detected_date.strftime('%Y-%m-%d')}`")
        date_input = st.date_input(
            "📅 Date of Expense",
            detected_date,
            help="Adjust if auto-detection was incorrect"
        )

        st.markdown("### 🏷️ Select a Category")
        categories = [
            "Food", "Gas", "Shopping", "Entertainment", "Bills",
            "Transportation", "Healthcare", "Errands", "Subscriptions", "Other"
        ]
        selected_category = st.radio(
            "Choose category:",
            categories,
            horizontal=True,
            key="category_select"
        )

        if selected_category == "Other":
            custom_category = st.text_input("✏️ Enter custom category")
            category = custom_category if custom_category else "Uncategorized"
        else:
            category = selected_category

        amount = st.number_input(
            "💵 Amount ($)",
            value=float(detected_amount),
            step=0.01,
            min_value=0.0,
            help="Enter the dollar amount spent"
        )
        
        note = st.text_area(
            "📝 Notes (optional)",
            value=expense_text,
            help="Additional details about this expense"
        )

        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button("💾 Save Expense", use_container_width=True, type="primary")
        with col2:
            cancelled = st.form_submit_button("❌ Cancel", use_container_width=True)
        
        if submitted:
            if amount <= 0:
                st.error("❌ Amount must be greater than 0")
            else:
                try:
                    expense = controller.add_expense(
                        text=note,
                        category=category,
                        manual_amount=amount,
                        manual_date=datetime.combine(date_input, datetime.min.time())
                    )
                    
                    st.success(f"✅ Saved **${amount:.2f}** under **{category}** for **{date_input.strftime('%Y-%m-%d')}**")
                    st.toast(f"✅ Expense added: ${amount:.2f}", icon="✅")
                    
                    st.session_state.dashboard_data = controller.get_dashboard_data()
                    st.session_state["adding_entry"] = False
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Failed to save expense: {e}")
        
        if cancelled:
            st.session_state["adding_entry"] = False
            st.info("ℹ️ Operation cancelled")
            st.rerun()

# ---------- DASHBOARD ----------
st.header("📊 Spending Dashboard")

if st.session_state.dashboard_data and st.session_state.dashboard_data["expense_count"] > 0:
    data = st.session_state.dashboard_data
    
    expense_dicts = [exp.to_dict() for exp in data["expenses"]]
    df_display = pd.DataFrame(expense_dicts)
    
    st.dataframe(df_display.reset_index(drop=True), use_container_width=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("💰 Total Spent", f"${data['total_spending']:,.2f}")
    with col2:
        st.metric("📝 Total Entries", data['expense_count'])
    with col3:
        if data['category_totals']:
            top_category = data['category_totals'][0]
            st.metric("🔝 Top Category", f"{top_category.category} (${top_category.total:.2f})")

    if data['category_totals']:
        st.subheader("📈 Spending by Category")
        chart_data = {ct.category: ct.total for ct in data['category_totals']}
        st.bar_chart(chart_data)
else:
    st.info("ℹ️ No expenses logged yet. Click **Add New Entry** to get started!")

# ---------- EXPORT ----------
st.subheader("💾 Export Data")

if st.session_state.dashboard_data and st.session_state.dashboard_data["expense_count"] > 0:
    if st.button("📥 Generate Excel Export", use_container_width=True):
        try:
            with st.spinner("Generating formatted Excel file..."):
                controller.export_to_excel(DATA_PATH)
                st.success("✅ Excel file generated successfully!")
                st.toast("✅ Export complete", icon="📁")
        except Exception as e:
            st.error(f"❌ Export failed: {e}")
    
    if os.path.exists(DATA_PATH):
        with open(DATA_PATH, "rb") as f:
            st.download_button(
                label="⬇️ Download Formatted Excel File",
                data=f,
                file_name="voice_expenses_formatted.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
else:
    st.info("ℹ️ No data to export yet.")

# ---------- CLEAR DATA ----------
st.subheader("🧹 Clear All Data")

if "clear_stage" not in st.session_state:
    st.session_state.clear_stage = "idle"

if st.session_state.clear_stage == "idle":
    if st.button("⚠️ Delete All Entries", use_container_width=True):
        st.session_state.clear_stage = "confirm"
        st.rerun()
        
elif st.session_state.clear_stage == "confirm":
    st.warning("⚠️ **Are you sure you want to delete all expense data?** This action cannot be undone.")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("✅ Yes, clear all data", use_container_width=True, type="primary"):
            try:
                controller.clear_all_expenses()
                st.session_state.dashboard_data = controller.get_dashboard_data()
                st.session_state.clear_stage = "idle"
                st.success("✅ All data cleared successfully!")
                st.toast("✅ Data cleared", icon="🧹")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Failed to clear data: {e}")
                
    with col2:
        if st.button("❌ Cancel", use_container_width=True):
            st.session_state.clear_stage = "idle"
            st.info("ℹ️ Operation cancelled")
            st.rerun()

# ---------- FOOTER ----------
st.markdown("---")
st.caption("🧾 SpendLens v1.0 | Built with SOLID principles | Powered by OpenAI & Streamlit")
