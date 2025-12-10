# 🌱 Project Samarth  
### Intelligent Q&A System Over Indian Agricultural & Climate Data  
**Built using Streamlit, LangChain, Groq Llama 3.3, and data.gov.in APIs**

---

## 📌 Overview

**Project Samarth** is an end-to-end prototype that answers complex, data-driven questions about India’s agricultural output and climate patterns.  
It queries **live datasets** from the Government of India (data.gov.in), analyzes crop production and rainfall trends, and synthesizes answers using an LLM — with full **traceability** and **citations**.

This project was built for a challenge requiring:
- Cross-domain insights using **Ministry of Agriculture** + **IMD (Rainfall)** datasets  
- Automatic querying, cleaning, harmonization, and merging of inconsistent government datasets  
- A natural-language chat interface  
- Accurate, cited, data-backed answers  
- Deployability on a **private, secure environment**

Samarth achieves all of this through a combination of **LLM reasoning** + **deterministic data analysis tools**.

---

## 🚀 Key Features

### ✅ 1. **Live data integration from data.gov.in**
- Fetches data via official APIs  
- Handles pagination, filtering, and inconsistent schemas  
- Automatically maps IMD subdivisions to states  

### ✅ 2. **Intelligent Q&A using Groq Llama 3.3**
- LLM decides *what analysis is needed*  
- Calls the analysis tool with precise parameters  
- Synthesizes human-friendly, cited answers  

### ✅ 3. **Robust analysis engine**
- Average rainfall comparisons  
- Top crops by production  
- Max/min district production for a crop  
- Rainfall–crop correlation for policy decision-making  

All done with **Pandas**, using real government data.

### ✅ 4. **Frontend Chat Interface (Streamlit)**
- Chat-style UI for asking natural-language questions  
- Maintains conversation history  
- Displays clean insights with citations  

### ✅ 5. **Traceable, accurate, hallucination-resistant responses**
Tool output → JSON facts → LLM → user response  
Ensures correctness and transparency.

---

## 🧠 Project Architecture

### **High-Level Flow**


### **Core Components**

| Component | Technology | Purpose |
|----------|------------|---------|
| Frontend | Streamlit | Chat UI |
| LLM | Groq Llama 3.3 70B | Reasoning + synthesis |
| Agent | LangChain Tool Calling Agent | Selects correct analysis |
| Analysis Engine | Python, Pandas | Fetch, clean, merge, compute facts |
| Data Sources | data.gov.in APIs | Live crop + rainfall data |

---

## 📂 Repository Structure

project/
│
├── streamlit_app.py # Frontend UI + LLM agent
├── tools.py # Analysis engine + data fetch logic
├── config.py # API keys, resource IDs, mappings
├── requirements.txt # Dependencies
└── README.md


---

## ⚙️ Installation & Setup

### **1. Clone the repo**
```bash
git clone https://github.com/your-username/project-samarth.git
cd project-samarth

pip install -r requirements.txt

CROP_API_KEY = "your_data_gov_api_key"
RAIN_API_KEY = "your_data_gov_api_key"
GROQ_API_KEY = "your_groq_api_key"


streamlit run streamlit_app.py
