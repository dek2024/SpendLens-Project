"""import streamlit as st

SpendLens - AI-Powered Expense Trackerfrom openai import OpenAI

Streamlit UI layer using SOLID architecture with dependency injection.from dotenv import load_dotenv

"""import os

import pandas as pd

import streamlit as stfrom datetime import datetime

from openai import OpenAI

from dotenv import load_dotenv# Import helper functions from logic module

import osfrom logic import (

import pandas as pd    extract_amount,

from datetime import datetime    extract_date,

import sys    load_expense_data,

    save_expense_data,

# Add src to path    add_expense_entry,

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))    filter_valid_expenses,

    calculate_category_totals,

from logic import (    format_excel_export,

    ExpenseController,    prepare_export_dataframe

    ExcelStorage,)

    ExpenseParser,

    ExpenseAnalyzer,# ---------- SETUP ----------

    ExcelFormatter,load_dotenv()

    OpenAIServiceclient = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

)

from models import ExpenseDATA_PATH = "data/voice_expenses.xlsx"

os.makedirs("data", exist_ok=True)

# ---------- SETUP ----------

load_dotenv()st.set_page_config(page_title="SpendLens - Voice Expense Logger", page_icon="🧾", layout="wide")



# Dependency Injection - SOLID Principle

DATA_PATH = "data/voice_expenses.xlsx"# ---------- LOAD DATA ----------

os.makedirs("data", exist_ok=True)df = load_expense_data(DATA_PATH)



# Initialize OpenAI clientif "df" not in st.session_state:

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))    st.session_state.df = df



# Initialize dependencies# ---------- SIDEBAR CHAT ----------

storage = ExcelStorage(DATA_PATH)st.sidebar.header("💬 Chat with Your Expenses")

parser = ExpenseParser()st.sidebar.caption("Ask anything about your spending — I’ll analyze your data like an iMessage chat.")

analyzer = ExpenseAnalyzer()

formatter = ExcelFormatter()user_query = st.sidebar.text_input("Type your question here:")

ai_service = OpenAIService(client)if st.sidebar.button("Ask"):

    if user_query.strip() == "":

# Create controller with dependency injection        st.sidebar.warning("Please enter a question.")

controller = ExpenseController(storage, parser, analyzer, formatter, ai_service)    elif st.session_state.df.empty:

        st.sidebar.info("No data available yet. Log some expenses first.")

st.set_page_config(    else:

    page_title="SpendLens - Voice Expense Logger",        context = st.session_state.df.to_string(index=False)

    page_icon="🧾",        response = client.chat.completions.create(

    layout="wide"            model="gpt-4o-mini",

)            messages=[

                {"role": "system", "content": "You are a financial assistant analyzing expense data."},

# ---------- SESSION STATE ----------                {"role": "user", "content": f"Here are my expenses:\n{context}\n\nQuestion: {user_query}"}

if "expenses_loaded" not in st.session_state:            ],

    st.session_state.expenses_loaded = False        ).choices[0].message.content

    st.session_state.dashboard_data = None        st.sidebar.success(response)



# Load expenses on first run# ---------- MAIN APP ----------

if not st.session_state.expenses_loaded:col1, col2 = st.columns([1, 6])

    try:with col1:

        st.session_state.dashboard_data = controller.get_dashboard_data()    if os.path.exists("spendlens_logo.png"):

        st.session_state.expenses_loaded = True        st.image("spendlens_logo.png", width=100)

    except Exception as e:    else:

        st.error(f"Failed to load expenses: {e}")        st.warning("⚠️ Logo not found — please add 'spendlens_logo.png' to your project directory.")

with col2:

# ---------- SIDEBAR CHAT ----------    st.title("SpendLens")

st.sidebar.header("💬 Chat with Your Expenses")    st.caption("Know your spending before it knows you.")

st.sidebar.caption("Ask anything about your spending — powered by AI.")

st.markdown("---")

user_query = st.sidebar.text_input("Type your question here:", key="user_query")

if st.sidebar.button("🔍 Ask", use_container_width=True):st.caption("Log your expenses manually or by voice — all data is saved and visualized automatically.")

    if user_query.strip() == "":

        st.sidebar.warning("⚠️ Please enter a question.")# ---------- ADD NEW ENTRY ----------

    elif not st.session_state.dashboard_data or st.session_state.dashboard_data["expense_count"] == 0:if st.button("➕ Add New Entry"):

        st.sidebar.info("ℹ️ No data available yet. Log some expenses first.")    for key in ["adding_entry", "expense_input", "category_select", "audio_input", "input_mode"]:

    else:        if key in st.session_state:

        try:            del st.session_state[key]

            with st.sidebar.spinner("Analyzing..."):    st.session_state["adding_entry"] = True

                expenses = st.session_state.dashboard_data["expenses"]    st.rerun()

                response = ai_service.analyze_expenses(expenses, user_query)

                st.sidebar.success(response)if st.session_state.get("adding_entry", False):

        except Exception as e:    st.header("🎙️ Log a New Expense")

            st.sidebar.error(f"❌ Analysis failed: {e}")

    input_mode = st.radio("Choose input mode:", ["🎤 Voice", "⌨️ Text"], horizontal=True, key="input_mode")

# ---------- MAIN APP ----------

col1, col2 = st.columns([1, 6])    expense_text = ""

with col1:    if input_mode == "🎤 Voice":

    if os.path.exists("spendlens_logo.png"):        st.write("Record your voice (e.g., 'Yesterday I spent $15 at Starbucks')")

        st.image("spendlens_logo.png", width=100)        audio_input = st.audio_input("Record your voice", key="audio_input")

    else:        if audio_input:

        st.write("🧾")            transcript = client.audio.transcriptions.create(

with col2:                model="gpt-4o-mini-transcribe",

    st.title("SpendLens")                file=audio_input

    st.caption("Know your spending before it knows you.")            )

            expense_text = transcript.text.strip()

st.markdown("---")            st.info(f"🗣️ Transcribed text: {expense_text}")

    else:

st.caption("💡 Log your expenses manually or by voice — all data is saved and visualized automatically.")        expense_text = st.text_input(

            "Type a short description (e.g., 'Lunch at Chipotle for 12 dollars yesterday')",

# ---------- ADD NEW ENTRY ----------            key="expense_input"

if st.button("➕ Add New Entry", use_container_width=True, type="primary"):        )

    for key in ["adding_entry", "expense_input", "category_select", "audio_input", "input_mode"]:

        if key in st.session_state:    detected_amount = extract_amount(expense_text)

            del st.session_state[key]    detected_date = extract_date(expense_text)

    st.session_state["adding_entry"] = True

    st.rerun()    # ---------- MANUAL ENTRY FORM ----------

    with st.form("manual_entry_form", clear_on_submit=False):

if st.session_state.get("adding_entry", False):        st.markdown(f"🧠 **Detected Date:** `{detected_date.strftime('%Y-%m-%d')}`")

    st.header("🎙️ Log a New Expense")        date_input = st.date_input("📅 Date of Expense", detected_date)



    input_mode = st.radio(        st.markdown("### 🏷️ Select a Category")

        "Choose input mode:",        categories = [

        ["🎤 Voice", "⌨️ Text"],            "Food", "Gas", "Shopping", "Entertainment", "Bills",

        horizontal=True,            "Transportation", "Healthcare", "Errands", "Subscriptions", "Other"

        key="input_mode",        ]

        help="Use voice for hands-free logging or text for manual entry"        selected_category = st.radio("Choose category:", categories, horizontal=True, key="category_select")

    )

        if selected_category == "Other":

    expense_text = ""            custom_category = st.text_input("✏️ Enter custom category")

                category = custom_category if custom_category else "Uncategorized"

    if input_mode == "🎤 Voice":        else:

        st.write("🎤 Record your voice (e.g., 'Yesterday I spent $15 at Starbucks')")            category = selected_category

        audio_input = st.audio_input("Record your voice", key="audio_input")

                amount = st.number_input("💵 Amount ($)", value=detected_amount, step=0.01, min_value=0.0)

        if audio_input:        note = st.text_area("📝 Notes (optional)", value=expense_text)

            try:

                with st.spinner("Transcribing audio..."):        submitted = st.form_submit_button("💾 Save Expense")

                    expense_text = ai_service.transcribe_audio(audio_input)        if submitted:

                    st.info(f"🗣️ Transcribed: **{expense_text}**")            st.session_state.df = add_expense_entry(

            except Exception as e:                st.session_state.df,

                st.error(f"❌ Transcription failed: {e}")                date_input,

                expense_text = ""                category,

    else:                amount,

        expense_text = st.text_input(                note

            "Type a short description",            )

            placeholder="e.g., 'Lunch at Chipotle for 12 dollars yesterday'",            save_expense_data(st.session_state.df, DATA_PATH)

            key="expense_input",            st.success(f"✅ Saved ${amount:.2f} under {category} for {date_input.strftime('%Y-%m-%d')}")

            help="Describe your expense in natural language"            st.session_state["adding_entry"] = False

        )            st.rerun()



    # Parse expense if text provided# ---------- DASHBOARD ----------

    detected_amount = 0.0st.header("📊 Spending Dashboard")

    detected_date = datetime.now()

    if not st.session_state.df.empty:

    if expense_text:    valid_df = filter_valid_expenses(st.session_state.df)

        try:

            parsed = parser.parse_expense(expense_text)    st.dataframe(valid_df.reset_index(drop=True), use_container_width=True)

            detected_amount = parsed.detected_amount

            detected_date = parsed.detected_date    total_spent = valid_df["Amount ($)"].sum()

        except Exception as e:    st.metric("💰 Total Spent", f"${total_spent:,.2f}")

            st.warning(f"⚠️ Parsing issue: {e}")

    category_totals = calculate_category_totals(valid_df)

    # ---------- MANUAL ENTRY FORM ----------    st.bar_chart(category_totals)

    with st.form("manual_entry_form", clear_on_submit=False):

        st.markdown(f"🧠 **Detected Date:** `{detected_date.strftime('%Y-%m-%d')}`")# ---------- EXPORT ----------

        date_input = st.date_input(st.subheader("💾 Export Data")

            "📅 Date of Expense",

            detected_date,if not st.session_state.df.empty:

            help="Adjust if auto-detection was incorrect"    export_df = prepare_export_dataframe(st.session_state.df)

        )

    if not export_df.empty:

        st.markdown("### 🏷️ Select a Category")        save_expense_data(export_df, DATA_PATH)

        categories = [        format_excel_export(DATA_PATH)

            "Food", "Gas", "Shopping", "Entertainment", "Bills",

            "Transportation", "Healthcare", "Errands", "Subscriptions", "Other"    with open(DATA_PATH, "rb") as f:

        ]        st.download_button(

        selected_category = st.radio(            label="⬇️ Download Formatted Excel File",

            "Choose category:",            data=f,

            categories,            file_name="voice_expenses_formatted.xlsx",

            horizontal=True,            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

            key="category_select"        )

        )

# ---------- CLEAR DATA ----------

        if selected_category == "Other":st.subheader("🧹 Clear All Data")

            custom_category = st.text_input("✏️ Enter custom category")if "clear_stage" not in st.session_state:

            category = custom_category if custom_category else "Uncategorized"    st.session_state.clear_stage = "idle"

        else:

            category = selected_categoryif st.session_state.clear_stage == "idle":

    if st.button("⚠️ Delete All Entries"):

        amount = st.number_input(        st.session_state.clear_stage = "confirm"

            "💵 Amount ($)",        st.rerun()

            value=float(detected_amount),elif st.session_state.clear_stage == "confirm":

            step=0.01,    st.warning("Are you sure you want to delete all expense data?")

            min_value=0.0,    col1, col2 = st.columns(2)

            help="Enter the dollar amount spent"    with col1:

        )        if st.button("✅ Yes, clear all data"):

                    st.session_state.df = pd.DataFrame(columns=["Date/Time", "Category", "Amount ($)", "Notes"])

        note = st.text_area(            save_expense_data(st.session_state.df, DATA_PATH)

            "📝 Notes (optional)",            st.session_state.clear_stage = "idle"

            value=expense_text,            st.success("✅ All data cleared successfully!")

            help="Additional details about this expense"            st.rerun()

        )    with col2:

        if st.button("❌ Cancel"):

        col1, col2 = st.columns(2)            st.session_state.clear_stage = "idle"

        with col1:            st.info("Operation cancelled.")

            submitted = st.form_submit_button("💾 Save Expense", use_container_width=True, type="primary")            st.rerun()

        with col2:
            cancelled = st.form_submit_button("❌ Cancel", use_container_width=True)
        
        if submitted:
            if amount <= 0:
                st.error("❌ Amount must be greater than 0")
            else:
                try:
                    # Use controller to add expense
                    expense = controller.add_expense(
                        text=note,
                        category=category,
                        manual_amount=amount,
                        manual_date=datetime.combine(date_input, datetime.min.time())
                    )
                    
                    st.success(f"✅ Saved **${amount:.2f}** under **{category}** for **{date_input.strftime('%Y-%m-%d')}**")
                    st.toast(f"✅ Expense added: ${amount:.2f}", icon="✅")
                    
                    # Reload dashboard data
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
    
    # Convert expenses to DataFrame for display
    expense_dicts = [exp.to_dict() for exp in data["expenses"]]
    df_display = pd.DataFrame(expense_dicts)
    
    st.dataframe(
        df_display.reset_index(drop=True),
        width=None,
        height=None,
        use_container_width=True
    )

    # Metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("💰 Total Spent", f"${data['total_spending']:,.2f}")
    with col2:
        st.metric("📝 Total Entries", data['expense_count'])
    with col3:
        if data['category_totals']:
            top_category = data['category_totals'][0]
            st.metric("🔝 Top Category", f"{top_category.category} (${top_category.total:.2f})")

    # Category chart
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
                st.toast("✅ Export complete", icon="📥")
        except Exception as e:
            st.error(f"❌ Export failed: {e}")
    
    # Download button
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
                st.toast("✅ Data cleared", icon="🗑️")
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
