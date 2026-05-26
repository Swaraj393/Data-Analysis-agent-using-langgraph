import streamlit as st
import os
import io
import pandas as pd
import datetime

# Import backend agent workflow
from DAA_Backend import analyst_agent

st.set_page_config(page_title="Autonomous AI Data Analyst", page_icon="📊", layout="wide")

# =====================================================================
# SYSTEM STATE MANAGEMENT (Keeps memory alive across refreshes)
# =====================================================================
if "chats" not in st.session_state:
    # Dictionary structure to hold multiple conversations
    st.session_state.chats = {
        "Chat 1": {
            "query": "",
            "output": "",
            "has_chart": False,
            "chart_data": None,
            "uploaded_file_name": None,
            "df_preview": None,
            "schema_info": None
        }
    }

if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = "Chat 1"

# Shortcut reference pointing to the active chat scope
current_chat = st.session_state.chats[st.session_state.current_chat_id]
TEMP_CSV_PATH = f"data_sandbox_{st.session_state.current_chat_id}.csv"

# =====================================================================
# SIDEBAR NAVIGATION INTERFACE
# =====================================================================
st.sidebar.title("💬 Conversation Hub")

# Button: Create New Chat
if st.sidebar.button("➕ Start New Chat", use_container_width=True):
    new_id = f"Chat {len(st.session_state.chats) + 1} ({datetime.datetime.now().strftime('%H:%M:%S')})"
    st.session_state.chats[new_id] = {
        "query": "",
        "output": "",
        "has_chart": False,
        "chart_data": None,
        "uploaded_file_name": None,
        "df_preview": None,
        "schema_info": None
    }
    st.session_state.current_chat_id = new_id
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.subheader("History Logs")

# Radio selection list to jump between saved chats instantly
selected_chat = st.sidebar.radio(
    "Select a workspace session:",
    options=list(st.session_state.chats.keys()),
    index=list(st.session_state.chats.keys()).index(st.session_state.current_chat_id)
)

# If user clicks a different chat in history, swap the active pointer and reload the UI
if selected_chat != st.session_state.current_chat_id:
    st.session_state.current_chat_id = selected_chat
    st.rerun()

# =====================================================================
# MAIN APPLICATION INTERFACE
# =====================================================================
st.title(f"📊 Workspace Context: {st.session_state.current_chat_id}")
st.markdown("Upload a CSV file and run autonomous deep data analytical code loops seamlessly.")

# Core File Loader
uploaded_file = st.file_uploader("📂 Upload your target CSV dataset", type=["csv"])

# If a file is uploaded right now, save it into the active chat session memory state
if uploaded_file is not None:
    user_df = pd.read_csv(uploaded_file)
    user_df.to_csv(TEMP_CSV_PATH, index=False)
    
    current_chat["uploaded_file_name"] = uploaded_file.name
    current_chat["df_preview"] = user_df.head(5)
    
    schema_buffer = io.StringIO()
    user_df.info(buf=schema_buffer)
    current_chat["schema_info"] = schema_buffer.getvalue() + f"\n\nFirst 3 rows:\n{user_df.head(3).to_string()}"

# Display active dataset files if they exist inside this specific conversation
if current_chat["uploaded_file_name"] is not None:
    metric_col, preview_col = st.columns([1, 2])
    with metric_col:
        st.success(f"Active file: {current_chat['uploaded_file_name']}")
    with preview_col:
        st.write("👀 **Data Frame Preview Sample:**")
        st.dataframe(current_chat["df_preview"], use_container_width=True)
        
    st.markdown("---")
    
    # Text input area mapping into session memory layout
    user_query = st.text_area(
        "💡 Define analysis objectives for this workspace:",
        value=current_chat["query"],
        placeholder="Example: Compute total column summaries and render statistical layouts..."
    )
    current_chat["query"] = user_query
    
    if st.button("🚀 Execute Background Analytical Agent Loop", type="primary"):
        if not user_query.strip():
            st.warning("Please outline an instruction objective parameter first.")
        else:
            # Drop old disk-saved chart flags
            chart_filename = "analysis_chart.png"
            if os.path.exists(chart_filename):
                os.remove(chart_filename)
                
            initial_payload = {
                "query": user_query + " Make sure to explicitly call print() to display your text findings or tables.",
                "csv_path": TEMP_CSV_PATH,
                "schema_info": current_chat["schema_info"],
                "error": "",
                "output": "",
                "iteration": 0
            }
            
            with st.status("🕵️ Invoking autonomous Llama-3.3 execution pipelines...", expanded=True) as status:
                final_state = analyst_agent.invoke(initial_payload)
                status.update(label="Analysis Completed Successfully!", state="complete", expanded=False)
            
            # Save the execution results straight into this specific chat's session memory data pack
            current_chat["output"] = final_state["output"] if not final_state["error"] else f"Execution Error:\n{final_state['error']}"
            
            if os.path.exists(chart_filename):
                current_chat["has_chart"] = True
                with open(chart_filename, "rb") as file:
                    current_chat["chart_data"] = file.read()
            else:
                current_chat["has_chart"] = False
                current_chat["chart_data"] = None
                
            st.rerun()

    # =====================================================================
    # RENDER HISTORICAL SESSION PACK OUTPUT DATA
    # =====================================================================
    if current_chat["output"]:
        st.subheader("📈 Final Generated Session Reports")
        text_panel, image_panel = st.columns([1, 1])
        
        with text_panel:
            st.markdown("### 📋 Captured Metrics & Output")
            st.code(current_chat["output"], language="text")
            
        with image_panel:
            st.markdown("### 🎨 Rendered Visualizations")
            if current_chat["has_chart"] and current_chat["chart_data"] is not None:
                st.image(current_chat["chart_data"], use_container_width=True)
            else:
                st.info("No visualization artifact remains registered for this session context.")
else:
    st.info("💡 Drop a new CSV file above to spin up data calculation loops within this chat instance.")