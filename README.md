# Campus Companion — Student Support Agent (Assignment 2)

## 1. Project Overview

Campus Companion is an AI-powered Student Support Agent developed using Python, Streamlit, and the Groq-hosted Large Language Model (LLM).

Assignment 2 extends the original Student Support Agent by introducing additional privacy controls, authorization checks, human approval workflows, audit logging, and sensitive-memory protection.

The application helps students access academic and administrative information while adding safeguards for sensitive operations and student records.

The bundled student records are fictional sample data intended only for educational and testing purposes.

## 2. Key Features

- **Conversational Student Support:** Allows students to interact with the AI agent through a Streamlit chat interface.
- **Fee and Scholarship Lookup:** Retrieves student fee and scholarship information from sample records.
- **Policy Retrieval:** Provides information from the supplied student policy documents and knowledge base.
- **Student Data Privacy:** Prevents students from accessing another student's restricted records.
- **Role-Based Authorization:** Restricts administrative review actions to authorized reviewers.
- **Course-Change Approval Workflow:** Allows students to submit course-change requests for review.
- **Approval and Rejection:** Supports recording pending, approved, and rejected requests.
- **Audit Logging:** Records important actions, authorization decisions, and denied attempts.
- **Sensitive-Memory Protection:** Refuses targeted attempts to save sensitive information such as passwords and OTPs.
- **Conversation and Preference Memory:** Supports conversation persistence and student preference memory.

## 3. Project Structure

```text
Conversational-Student-Support-Agent-Assignment-2/
│
├── app.py                         # Streamlit interface and session interactions
├── agent.py                       # LLM orchestration, tool calling and authorization
├── approvals.py                   # Course-change approval workflow
├── audit.py                       # Audit logging and action records
├── auth_db.py                     # Authentication and conversation persistence
├── tools.py                       # Student fee and scholarship lookup tools
├── policy.py                      # Institutional policy lookup
├── knowledge_search.py            # Semantic retrieval from local ChromaDB index
├── memory.py                      # Student preference and conversation memory
├── ingest_data.py                 # Knowledge-base data ingestion
├── setup_users.py                 # Local student/admin account setup
├── test_groq.py                   # Groq API connection testing
├── test_tools.py                  # Student-support tool testing
│
├── data/
│   ├── students.json              # Fictional student records
│   └── student_policy.md          # Sample institutional policy
│
├── knowledge_base/
│   ├── documents/
│   │   └── student_handbook.pdf   # Student handbook (if included)
│   │
│   ├── index/                     # Local ChromaDB retrieval index
│   │
│   └── tables/
│       ├── policies.csv           # Policy reference data
│       ├── scholarships.xlsx      # Scholarship information
│       └── student_fees.csv       # Student fee records
│
├── documentation/
│   └── Privacy_and_Approval_Rules.txt  # Privacy and approval rules
│
├── evidence/
│   ├── Required_Scenario_Trace_Summary.csv  # Test scenario results
│   └── Sample_Audit_Records.jsonl           # Representative audit records
│
├── evaluation/
│   └── Assignment_1_vs_Assignment_2_Evaluation.csv  # Evaluation comparison
│
├── Assignment_2_Final_Evaluation_Report.docx  # Final evaluation report
├── requirements.txt               # Required Python libraries
├── .env.example                   # Placeholder for Groq API key
├── .gitignore                     # Excludes sensitive and unnecessary files
└── README.md                      # Project overview and setup instructions
```

## 4. Technology Stack

| Component | Technology |
|---|---|
| Programming Language | Python |
| User Interface | Streamlit |
| Large Language Model | Groq API |
| Agent Orchestration | Python |
| Database | SQLite |
| Knowledge Retrieval | ChromaDB |
| Data Storage | JSON, CSV and Excel |
| Audit Records | JSONL |

## 5. Architecture at a Glance

The application follows a modular architecture:

1. **Streamlit Interface (`app.py`):** Provides the login, student interaction, chat interface, and administrative workspace.
2. **Agent Orchestration (`agent.py`):** Manages LLM interaction, tool calling, and request handling.
3. **Student Support Tools (`tools.py`):** Handles fee and scholarship lookups using sample student records.
4. **Policy Retrieval (`policy.py`):** Supports institutional policy-related queries.
5. **Knowledge Retrieval (`knowledge_search.py`):** Retrieves relevant information from the local ChromaDB index when available.
6. **Authentication (`auth_db.py`):** Handles local authentication and conversation persistence.
7. **Approval Workflow (`approvals.py`):** Records course-change requests and their approval or rejection decisions.
8. **Audit Logging (`audit.py`):** Maintains records of important actions and authorization outcomes.
9. **Memory (`memory.py`):** Supports student preference memory.

## 6. Privacy and Approval Workflow

Assignment 2 introduces additional safeguards for student information and sensitive administrative actions.

### Student Data Privacy

- Students should only access their own restricted fee and scholarship records.
- Cross-student access attempts are denied by the tested tool-level guard.
- Denied attempts are recorded in the audit log.

### Course-Change Approval

The application supports a request-based approval workflow:

1. A student submits a course-change request.
2. The request is recorded with a pending status.
3. An authorized reviewer can approve or reject the request.
4. The decision is recorded in the approval and audit records.
5. Rejected requests are not executed.

Approval records indicate authorized processing only. They do not automatically update actual course enrollment.

### Sensitive-Memory Protection

The application includes targeted checks to prevent sensitive information, such as passwords and OTPs, from being saved through the preference-memory functionality.

### Audit Logging

The audit module records important actions, including authorization decisions and denied attempts. Representative audit records are provided in the `evidence/` folder.

## 7. Requirements

- Windows, macOS, or Linux
- Python 3.10 or newer
- Groq API key
- Internet connection

## 8. Setup and Run (Windows PowerShell)

### Step 1: Clone the Repository

```powershell
git clone YOUR_GITHUB_REPOSITORY_URL
cd Conversational-Student-Support-Agent-Assignment-2
```

### Step 2: Create a Virtual Environment

```powershell
python -m venv .venv
```

### Step 3: Activate the Environment

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Then activate the environment again.

### Step 4: Install Dependencies

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### Step 5: Configure the Groq API Key

Copy `.env.example` to `.env`:

```powershell
Copy-Item .env.example .env
```

Open `.env` and add your own API key:

```text
GROQ_API_KEY=your_actual_key_here
```

Never upload the actual `.env` file or API key to GitHub.

### Step 6: Create a Local Account

Run:

```powershell
python setup_users.py
```

Follow the prompts to create a local student or administrator account supported by the application.

Use fictional demo credentials only.

### Step 7: Start the Application

```powershell
python -m streamlit run app.py
```

Open the local URL displayed in the terminal, usually:

`http://localhost:8501`

## 9. Demonstration and Test Scenarios

The following scenarios can be used to demonstrate Assignment 2:

| Test Scenario | Expected Behaviour |
|---|---|
| Own fee status lookup | Retrieves the logged-in student's fee information |
| Scholarship lookup | Retrieves scholarship information |
| Cross-student fee lookup | Denies access to another student's restricted information |
| Course-change request | Creates a pending approval request |
| Course-change rejection | Records rejection without executing the change |
| Course-change approval | Records approval without automatically changing enrollment |
| Unauthorized student review | Denies administrative review and records the attempt |
| Sensitive-memory request | Refuses to save the tested dummy password or OTP |

The scenario summary and representative audit records are available in the `evidence/` folder.

## 10. Evaluation and Assignment 1 Comparison

The project was evaluated using recorded interaction traces from both assignments.

### Evaluation Metrics

| Measurement | Assignment 1 | Assignment 2 | Observed Change |
|---|---:|---:|---:|
| Number of Traces | 14 | 33 | Different sample sizes |
| Average Latency | 1.811 s | 2.032 s | +12.2% |
| Average Input Tokens per Trace | 1,106.7 | 1,456.0 | +31.6% |
| Average Output Tokens per Trace | 74.9 | 139.8 | +86.6% |

### Key Observations

- Assignment 2 introduced stronger tested enforcement against cross-student fee access.
- Course-change requests can be recorded as pending, approved, or rejected.
- Unauthorized student review attempts were denied and audited in the tested scenario.
- Targeted dummy password and OTP memory tests were refused.
- Additional authorization and audit features increased the recorded average latency and token usage in the supplied samples.

These are descriptive measurements from different trace samples, not a controlled benchmark. A formal accuracy percentage is not claimed because the supplied evidence uses qualitative scenario outcomes rather than a validated common accuracy test set.

The detailed comparison is available in:

`evaluation/Assignment_1_vs_Assignment_2_Evaluation.csv`

The combined evaluation report is available in:

`Assignment_2_Final_Evaluation_Report.docx`

## 11. Known Limitations

- The LLM requires a valid Groq API key and internet connection.
- Approval records do not update actual course enrollment.
- Reviewer authorization should derive identity and role from a trusted authenticated session. A caller-supplied role is not production-grade authorization.
- The trace summary represents scenario-level results, not the complete raw 33-trace runtime log.
- The audit evidence contains representative records from tested scenarios.
- Sensitive-memory protection was tested with dummy password and OTP examples; this does not establish exhaustive detection of every possible secret format.
- The previous bundle contained an empty handbook PDF and an incomplete cached index artifact. These were omitted from the cleaned package. The supplied Markdown policy and CSV/XLSX knowledge tables are included.
- If semantic retrieval requires a populated local index, rebuild and validate it before relying on that functionality.
- The application requires additional security, authorization, and deployment review before real-world use.

## 12. Conclusion

Campus Companion Assignment 2 extends the original Student Support Agent by introducing privacy protection, authorization checks, human approval workflows, audit logging, and sensitive-memory safeguards.

The project demonstrates how Agentic AI applications can combine conversational intelligence with controlled tool execution and accountability mechanisms for student-support activities.

