import streamlit as st
# from langchain.agents import AgentExecutor, create_tool_calling_agent
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from tools import tools, analyze_agricultural_data
from config import *
import json


# STREAMLIT APP CONFIGURATION

st.set_page_config(
    page_title="Project Samarth: Ag-Climate Intelligence",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
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
    .sample-question {
        background-color: #f0f8f0;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #2E7D32;
        margin: 0.5rem 0;
    }
    .stButton>button {
        background-color: #2E7D32;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

# HEADER & INTRODUCTION

st.markdown('<div class="main-header">🌱 Project Samarth</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Intelligent Q&A System for Indian Agricultural & Climate Data</div>', unsafe_allow_html=True)

st.markdown(f"""
**Project Samarth** integrates live data from **data.gov.in** (Ministry of Agriculture & IMD) to answer complex queries 
about India's agricultural economy and climate patterns.


**Data Sources:**
- 🌾 Crop Production: District-wise production data across India
- 🌧️ Rainfall: IMD subdivision-level monthly/annual rainfall data
""")

# ==============================================================================
# SIDEBAR - SAMPLE QUESTIONS
# ==============================================================================

st.sidebar.title("📋 Sample Questions")
st.sidebar.markdown("Click any question to try it:")

# sample_questions = {
#     "Q1: Rainfall & Top Crops Comparison": f"Compare the average annual rainfall in {DEMO_STATE_X} and {DEMO_STATE_Y} for the last {DEMO_YEARS} years. Also list their top 3 pulse crops by production volume.",
    
#     "Q2: Max/Min District Production": f"Identify the district in {DEMO_STATE_X} with the highest production of {DEFAULT_CROP_Z} and compare that with the district with the lowest production of {DEFAULT_CROP_Z} in {DEMO_STATE_Y} for the last {DEMO_YEARS} years.",
    
#     "Q3: Production Trend Analysis": f"Analyze the production trend of Rice in {DEMO_STATE_X} over the last {DEMO_YEARS} years and correlate it with rainfall data.",
    
#     "Q4: Policy Recommendation": f"A policy advisor suggests promoting drought-resistant crops over water-intensive crops in {DEMO_STATE_X} and {DEMO_STATE_Y}. What are the three most compelling data-backed arguments to support this policy based on the last {DEMO_YEARS} years?",
    
#     "Custom: State Comparison": "Compare agricultural output between Punjab and Haryana for cereals in the last 5 years.",
# }
sample_questions = {
    "Q1: Compare Rainfall & Pulses": 
        "Compare the average annual rainfall in Maharashtra and Karnataka for the last 5 years. Also list their top 3 pulse crops.",
    
    "Q1b: Kerala Alternative": 
        "Compare the average annual rainfall in Kerala and Karnataka for the last 5 years. Also list their top 3 pulse crops.",
    
    "Q2: Max/Min Districts": 
        "Identify the district in Maharashtra with the highest production of Rice and compare with the district with the lowest production of Rice in Karnataka.",
    
    # "Q4: Policy Recommendation": 
    #     "A policy advisor suggests promoting drought-resistant crops in Maharashtra and Karnataka. What are data-backed arguments to support this?",
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
                # Test Q1 - Rainfall & Crops
                test_q1 = analyze_agricultural_data.run(
                    tool_input={
                        "state_x": DEMO_STATE_X,
                        "state_y": DEMO_STATE_Y,
                        "years": DEMO_YEARS,
                        "metric": "COMPARE_ALL",
                        "crop_type": "Pulses"
                    }
                )
                
                # Test Q2 - Max/Min
                test_q2 = analyze_agricultural_data.run(
                    tool_input={
                        "state_x": DEMO_STATE_X,
                        "state_y": DEMO_STATE_Y,
                        "years": DEMO_YEARS,
                        "metric": "MAX_MIN_CROP",
                        "crop_z": DEFAULT_CROP_Z
                    }
                )
                
                # Parse results
                try:
                    result_q1 = json.loads(test_q1)
                    result_q2 = json.loads(test_q2)
                except:
                    result_q1 = {"error": "Parse failed"}
                    result_q2 = {"error": "Parse failed"}
                
                # Display status
                if "error" in result_q1 or "error" in result_q2:
                    st.error("⚠️ API Test Failed")
                    if "error" in result_q1:
                        st.write("**Q1 Error:**", result_q1.get("error"))
                    if "error" in result_q2:
                        st.write("**Q2 Error:**", result_q2.get("error"))
                else:
                    st.success("✅ APIs Operational")
                    st.write(f"**Rainfall Data:** {result_q1.get('rainfall_comparison', {}).get(DEMO_STATE_X, {}).get('data_points', 0)} records")
                    st.write(f"**Crop Data:** {result_q2.get(DEMO_STATE_X, {}).get('total_production', 0):.0f} units")
                
                with st.expander("View Full Test Results"):
                    st.json({"Q1_Result": result_q1, "Q2_Result": result_q2})
                    
            except Exception as e:
                st.error(f"❌ Test Failed: {str(e)}")

st.sidebar.markdown("---")
st.sidebar.markdown("""
**About the Data:**
- Crop production data includes area and production by district
- Rainfall data includes monthly and annual measurements
- Data quality depends on government portal availability
""")


# INITIALIZE LLM & AGENT

@st.cache_resource
# def initialize_agent():
#     """Initialize and cache the LangChain agent."""
#     try:
#         llm = ChatGroq(
#             temperature=0.0,
#             groq_api_key=GROQ_API_KEY,
#             model_name="llama-3.3-70b-versatile"
#         )
        
#         system_prompt = """You are Samarth, an intelligent Q&A system for Indian agricultural and climate data.

# Your capabilities:
# 1. Answer questions by calling the 'analyze_agricultural_data' tool
# 2. Synthesize data into clear, comprehensive responses
# 3. Always cite data sources from the 'citations' field in tool output

# Guidelines:
# - Use the tool for ALL data analysis - never calculate manually
# - For rainfall comparisons: use metric='COMPARE_ALL' with crop_type
# - For max/min queries: use metric='MAX_MIN_CROP' with crop_z
# - For policy/correlation: use metric='POLICY_ADVICE'
# - Always include source citations in your response
# - If data is unavailable, explain what's missing and why

# Response format:
# 1. Direct answer to the query
# 2. Key insights from the data
# 3. Source citations at the end
# """
        
#         prompt = ChatPromptTemplate.from_messages([
#             ("system", system_prompt),
#             ("human", "{input}"),
#             ("placeholder", "{agent_scratchpad}"),
#         ])
        
#         agent = create_tool_calling_agent(llm, tools, prompt)
#         agent_executor = AgentExecutor(
#             agent=agent,
#             tools=tools,
#             verbose=True,
#             handle_parsing_errors=True,
#             max_iterations=5
#         )
        
#         return agent_executor
    

        
    
#     except Exception as e:
#         st.error(f"Failed to initialize agent: {str(e)}")
#         return None



@st.cache_resource
def initialize_agent():
    """Initialize and cache the LangGraph ReAct agent."""
    try:
        from langchain_groq import ChatGroq

        llm = ChatGroq(
            temperature=0.0,
            groq_api_key=GROQ_API_KEY,
            model_name="llama-3.3-70b-versatile"
        )

        system_prompt = """You are Samarth, an intelligent Q&A system for Indian agricultural and climate data.

Use the available tools to answer queries, analyze rainfall and crop production,
and always provide structured, data-backed insights with proper citations."""

        # 🧠 Memory for conversation context
        memory = MemorySaver()

        # ✅ Create new-style ReAct agent (replacement for AgentExecutor + create_tool_calling_agent)
        agent_executor = create_react_agent(
            model=llm,
            tools=tools,
            checkpoint=memory,
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

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": f"Hello! I'm **Samarth**, your agricultural data analyst. I can answer complex questions about Indian agriculture and climate by analyzing live data from data.gov.in.\n\n**Try asking me:**\n- Compare rainfall and crop production between states\n- Find districts with highest/lowest crop production\n- Analyze production trends and correlations\n- Get policy recommendations based on climate data\n\nWhat would you like to know?"
        }
    ]

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Handle selected question from sidebar
if 'selected_question' in st.session_state:
    prompt = st.session_state['selected_question']
    del st.session_state['selected_question']
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Generate response
    with st.chat_message("assistant"):
        with st.spinner("Analyzing data from government APIs..."):
            try:
                # Enhanced prompt with explicit instructions
                enhanced_prompt = f"""
Query: {prompt}

Instructions for tool usage:
1. Identify the query type:
   - Rainfall comparison + top crops → metric='COMPARE_ALL', specify crop_type
   - Max/min district production → metric='MAX_MIN_CROP', specify crop_z
   - Trend/correlation/policy → metric='POLICY_ADVICE'

2. Extract parameters:
   - States mentioned → state_x and state_y
   - Time period (e.g., "last 5 years") → years parameter
   - Crop category (Pulses, Cereals) → crop_type
   - Specific crop (Rice, Wheat) → crop_z

3. Call the tool and present results with citations.
"""
                
                # response = agent_executor.invoke({"input": enhanced_prompt})
                # output = response['output']
                response = agent_executor.invoke({"messages": [{"role": "user", "content": enhanced_prompt}]})
                output = response["messages"][-1]["content"]

                
                st.markdown(output)
                st.session_state.messages.append({"role": "assistant", "content": output})
                
            except Exception as e:
                error_msg = f"I encountered an error while processing your request: {str(e)}\n\nPlease try rephrasing your question or check the API status in the sidebar."
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})

# Chat input
if prompt := st.chat_input("Ask your agricultural data question..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        with st.spinner("Analyzing data from government APIs..."):
            try:
                enhanced_prompt = f"""
Query: {prompt}

Instructions for tool usage:
1. Identify the query type:
   - Rainfall comparison + top crops → metric='COMPARE_ALL', specify crop_type
   - Max/min district production → metric='MAX_MIN_CROP', specify crop_z
   - Trend/correlation/policy → metric='POLICY_ADVICE'

2. Extract parameters:
   - States mentioned → state_x and state_y
   - Time period (e.g., "last 5 years") → years parameter
   - Crop category (Pulses, Cereals) → crop_type
   - Specific crop (Rice, Wheat) → crop_z

3. Call the tool and present results with citations.
"""
                
                response = agent_executor.invoke({"input": enhanced_prompt})
                output = response['output']
                
                st.markdown(output)
                st.session_state.messages.append({"role": "assistant", "content": output})
                
            except Exception as e:
                error_msg = f"I encountered an error: {str(e)}\n\nPlease try a different question or check the API status."
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})

# ==============================================================================
# FOOTER
# ==============================================================================

st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; font-size: 0.9rem;'>
   
</div>
""", unsafe_allow_html=True)
