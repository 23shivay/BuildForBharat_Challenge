import streamlit as st
from langgraph.prebuilt import create_react_agent
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from tools import tools, analyze_agricultural_data
from config import *
import json

# ==============================================================================
# STREAMLIT APP CONFIGURATION
# ==============================================================================

st.set_page_config(
    page_title="Project Samarth: Ag-Climate Intelligence",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #2E7D32;
        text-align: center;
        padding: 1rem 0;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #555;
        text-align: center;
        padding-bottom: 2rem;
    }
    .stButton>button {
        background-color: #2E7D32;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# HEADER & INTRODUCTION
# ==============================================================================

st.markdown('<div class="main-header">🌱 Project Samarth</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Intelligent Q&A System for Indian Agricultural & Climate Data</div>', unsafe_allow_html=True)

st.markdown(f"""
**Project Samarth** integrates live data from **data.gov.in** (Ministry of Agriculture & IMD) 
to answer complex queries about India's agricultural economy and climate patterns.

**Data Sources:**
- 🌾 Crop Production: District-wise production data across India  
- 🌧️ Rainfall: IMD subdivision-level monthly/annual rainfall data
""")

# ==============================================================================
# SIDEBAR - SAMPLE QUESTIONS
# ==============================================================================

st.sidebar.title("📋 Sample Questions")
sample_questions = {
    "Q1: Compare Rainfall & Pulses": 
        "Compare the average annual rainfall in Maharashtra and Karnataka for the last 5 years. Also list their top 3 pulse crops.",
    "Q1b: Kerala Alternative": 
        "Compare the average annual rainfall in Kerala and Karnataka for the last 5 years. Also list their top 3 pulse crops.",
    "Q2: Max/Min Districts": 
        "Identify the district in Maharashtra with the highest production of Rice and compare with the district with the lowest production of Rice in Karnataka.",
}

for label, question in sample_questions.items():
    if st.sidebar.button(label, key=label, use_container_width=True):
        st.session_state['selected_question'] = question

st.sidebar.markdown("---")

st.sidebar.title("🔍 API Status")
st.sidebar.markdown("Verify data connectivity and availability:")

if st.sidebar.button("Test API Connection", type="primary", use_container_width=True):
    with st.sidebar:
        with st.spinner("Testing APIs..."):
            try:
                test_q1 = analyze_agricultural_data.run(
                    tool_input={
                        "state_x": DEMO_STATE_X,
                        "state_y": DEMO_STATE_Y,
                        "years": DEMO_YEARS,
                        "metric": "COMPARE_ALL",
                        "crop_type": "Pulses"
                    }
                )
                test_q2 = analyze_agricultural_data.run(
                    tool_input={
                        "state_x": DEMO_STATE_X,
                        "state_y": DEMO_STATE_Y,
                        "years": DEMO_YEARS,
                        "metric": "MAX_MIN_CROP",
                        "crop_z": DEFAULT_CROP_Z
                    }
                )
                try:
                    result_q1 = json.loads(test_q1)
                    result_q2 = json.loads(test_q2)
                except:
                    result_q1 = {"error": "Parse failed"}
                    result_q2 = {"error": "Parse failed"}
                
                if "error" in result_q1 or "error" in result_q2:
                    st.error("⚠️ API Test Failed")
                else:
                    st.success("✅ APIs Operational")
                    st.write(f"**Rainfall Records:** {result_q1.get('rainfall_comparison', {}).get(DEMO_STATE_X, {}).get('data_points', 0)}")
                    st.write(f"**Crop Data (Production):** {result_q2.get(DEMO_STATE_X, {}).get('total_production', 0):.0f}")
                    
            except Exception as e:
                st.error(f"❌ Test Failed: {str(e)}")

st.sidebar.markdown("---")
st.sidebar.markdown("""
**About the Data:**
- Crop production data includes area and production by district  
- Rainfall data includes monthly and annual measurements  
- Data quality depends on government portal availability
""")

# ==============================================================================
# INITIALIZE LLM & AGENT
# ==============================================================================

@st.cache_resource
def initialize_agent():
    """Initialize and cache the LangGraph ReAct agent."""
    try:
        llm = ChatGroq(
            temperature=0.0,
            groq_api_key=GROQ_API_KEY,
            model_name="llama-3.3-70b-versatile"
        )

        system_prompt = """You are Samarth, an intelligent Q&A system for Indian agricultural and climate data.
Use the available tools to answer queries, analyze rainfall and crop production,
and always provide structured, data-backed insights with proper citations."""

        # ✅ Stateless ReAct Agent (No checkpointer)
        agent_executor = create_react_agent(
            model=llm,
            tools=tools,
            prompt=system_prompt
        )
        return agent_executor

    except Exception as e:
        st.error(f"Failed to initialize agent: {str(e)}")
        return None

agent_executor = initialize_agent()

if agent_executor is None:
    st.error("⚠️ Could not initialize the AI agent. Please check your GROQ_API_KEY.")
    st.stop()

# ==============================================================================
# CHAT INTERFACE
# ==============================================================================

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "Hello! I'm **Samarth**, your agricultural data analyst. I can answer complex questions "
                "about Indian agriculture and climate by analyzing live data from data.gov.in.\n\n"
                "**Try asking me:**\n"
                "- Compare rainfall and crop production between states\n"
                "- Find districts with highest/lowest crop production\n"
                "- Analyze production trends and correlations\n"
                "- Get policy recommendations based on climate data\n\n"
                "What would you like to know?"
            ),
        }
    ]

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ==============================================================================
# HANDLE SIDEBAR QUESTION SELECTION
# ==============================================================================

if 'selected_question' in st.session_state:
    prompt = st.session_state['selected_question']
    del st.session_state['selected_question']

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Analyzing data from government APIs..."):
            try:
                enhanced_prompt = f"""
Query: {prompt}

Instructions for tool usage:
- Use 'COMPARE_ALL' for rainfall comparison & crop_type
- Use 'MAX_MIN_CROP' for max/min crop queries
- Use 'POLICY_ADVICE' for policy/trend queries
"""
                response = agent_executor.invoke(
                    {"messages": [{"role": "user", "content": enhanced_prompt}]}
                )

                # ✅ Proper LangGraph response handling
                output = response.content if hasattr(response, "content") else str(response)

                st.markdown(output)
                st.session_state.messages.append({"role": "assistant", "content": output})

            except Exception as e:
                error_msg = f"I encountered an error while processing your request: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})

# ==============================================================================
# HANDLE CHAT INPUT
# ==============================================================================

if user_input := st.chat_input("Ask your agricultural data question..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Analyzing data from government APIs..."):
            try:
                response = agent_executor.invoke(
                    {"messages": [{"role": "user", "content": user_input}]}
                )

                output = response.content if hasattr(response, "content") else str(response)

                st.markdown(output)
                st.session_state.messages.append({"role": "assistant", "content": output})

            except Exception as e:
                error_msg = f"I encountered an error: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})

# ==============================================================================
# FOOTER
# ==============================================================================

st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; font-size: 0.9rem;'>
Built with ❤️ using Streamlit, LangGraph, and Groq API.
</div>
""", unsafe_allow_html=True)
