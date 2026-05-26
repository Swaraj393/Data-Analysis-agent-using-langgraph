# 📊 Autonomous AI Data Analyst Agent

An intelligent, self-correcting data analysis platform built with **LangGraph**, **Llama-3.3 (via Groq)**, and **Streamlit**. This application allows users to upload any custom CSV dataset, state an analytical goal in plain English, and watch an AI agent automatically write code, execute it in a safe sandbox environment, inspect output logs, and sequentially self-correct its own code bugs until the analysis is fully finalized.

---

## 🛠️ System Architecture

The application splits responsibilities into a decoupled multi-file design for scalability:
* **`DAA_Backend.py`**: Orchestrates the core LangGraph state machine. It manages a persistent state containing the user query, dataframe schemas, executed code blocks, terminal outputs, and error tracking variables.
* **`DAA_Frontend.py`**: Serves an interactive, responsive Streamlit interface that handles direct user file streams and isolates background calculation loops from the user.

### The Self-Correction Loop
If the LLM generates Python code that throws a `NameError`, `TypeError`, or any structural execution exception, the **Executor Node** captures the traceback data and routes it back to the **Programmer Node**. The agent reviews its own error log, rewrites the code, and attempts execution again (up to 3 times) before delivering the final clean results.

---

## 🚀 Key Features

* **Autonomous Bug Fixing Loops:** Uses iterative LangGraph node relationships to catch, review, and fix raw terminal traceback execution errors dynamically.
* **Persistent Session Workspace:** Implements active multi-chat history tab navigation using Streamlit session states, making conversation contexts entirely secure across accidental page reloads.
* **Silent API Management:** Seamlessly reads access credentials locally via an `.env` configuration template, abstracting token setup screens away from the end-user.
* **Dynamic Media Generation:** Auto-saves, tracks, and renders clean tabular terminal printouts alongside targeted visualization line/bar charts directly onto frontend split-panel view containers.

---