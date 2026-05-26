import os
import sys
import io
import traceback
from typing import TypedDict, Dict, Any
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, START, END

from dotenv import load_dotenv
load_dotenv()


class AnalystState(TypedDict):
    query: str
    csv_path: str
    schema_info: str
    code: str
    error: str
    output: str
    iteration: int

# 2. Define Node Logics
def programmer_node(state: AnalystState) -> Dict[str, Any]:
    query = state["query"]
    schema = state["schema_info"]
    csv_path = state["csv_path"]
    previous_error = state.get("error", "")
    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
    
    system_prompt = (
        "You are an expert Data Analyst and Senior Python Developer. Your objective is to write pure, "
        f"executable Python code to analyze a dataset located exactly at: '{csv_path}'.\n\n"
        f"Here is the verified dataset metadata/schema info:\n{schema}\n\n"
        "CRITICAL EXECUTION RULES:\n"
        "1. Respond ONLY with valid, raw Python code enclosed within standard markdown blocks: ```python ... ```\n"
        "2. Do not include any greeting, explanation, or conversational commentary outside the code block.\n"
        "3. You MUST use print() statements to display your textual findings, tables, or final calculations.\n"
        "4. If the user asks for a chart, visualization, or plot, save it locally to disk as 'analysis_chart.png' "
        "using matplotlib or seaborn. Do not call plt.show() as this environment is non-interactive."
    )
    
    user_prompt = f"User Goal: {query}\n"
    if previous_error:
        user_prompt += f"\n Your previous code failed with this error:\n{previous_error}\nFix the bug and return the full corrected script."

    response = llm.invoke([("system", system_prompt), ("user", user_prompt)])
    
    raw_text = response.content
    extracted_code = raw_text.split("```python")[1].split("```")[0].strip() if "```python" in raw_text else raw_text.strip()
    return {"code": extracted_code, "iteration": state.get("iteration", 0) + 1}


def executor_node(state: AnalystState) -> Dict[str, Any]:
    code = state["code"]
    old_stdout = sys.stdout
    redirected_output = sys.stdout = io.StringIO()
    error_msg = ""
    
    try:
        local_scope = {}
        exec(code, {}, local_scope)
    except Exception as e:
        error_msg = traceback.format_exc()
    finally:
        sys.stdout = old_stdout
        
    captured_stdout = redirected_output.getvalue()
    return {"error": error_msg, "output": captured_stdout if not error_msg else ""}


def should_continue(state: AnalystState):
    if state["error"] == "":
        return "end"
    elif state["iteration"] >= 3:
        return "end"
    else:
        return "programmer"

# 3. Assemble and Compile Workflow
workflow = StateGraph(AnalystState)
workflow.add_node("programmer", programmer_node)
workflow.add_node("executor", executor_node)

workflow.add_edge(START, "programmer")
workflow.add_edge("programmer", "executor")
workflow.add_conditional_edges("executor", should_continue, {"programmer": "programmer", "end": END})

# This is the compiled graph variable we will import into our frontend
analyst_agent = workflow.compile()