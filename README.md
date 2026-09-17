# 🎓 University Admissions Graph RAG

A hands-on **Graph RAG (Retrieval-Augmented Generation)** project that uses university admissions data to demonstrate how messy structured data can be cleaned, transformed into a **Neo4j Knowledge Graph**, retrieved through graph relationships, and used by an LLM to generate grounded answers.

The project also uses **LangChain**, **LangGraph**, and **LangSmith** to demonstrate LLM integration, workflow orchestration, and observability.

---

## Why Graph RAG?

Traditional RAG works well when information can be retrieved from independent text chunks. But some questions depend on **relationships between multiple pieces of information**.

University admissions is a good example.

A student may ask:

> **“I studied Electronics. Which programs am I eligible for that don't require GRE and include AI-related courses?”**

Answering this requires connecting several entities:

```text
Electronics
    ↓ ELIGIBLE_FOR
Program
    ↓ HAS_GRE_POLICY
GRE Not Required

Program
    ↓ HAS_COURSE
Course
    ↓ COVERS
Artificial Intelligence
```

Instead of treating this information as isolated documents, **Graph RAG represents it as connected entities and relationships in a Knowledge Graph**.

This makes it useful for:

* **Multi-hop questions** that require following multiple relationships
* Understanding relationships between entities
* Structured and explainable retrieval
* Querying highly connected domains such as education, healthcare, finance, and enterprise systems
* Providing the LLM with relevant graph context for more grounded answers

For this project, university admissions data is modeled in **Neo4j**, allowing the application to traverse relationships between universities, programs, academic backgrounds, courses, topics, and GRE policies before generating an answer.


---

# Architecture

```text
Messy Admissions CSV
        │
        ▼
┌─────────────────────┐
│    Data Cleaning    │
│  01_clean_data.py   │
└──────────┬──────────┘
           │
           ▼
      Clean CSV
           │
           ▼
┌─────────────────────┐
│ Build Knowledge     │
│ Graph               │
│ 02_load_graph.py    │
└──────────┬──────────┘
           │
           ▼
         Neo4j
    Knowledge Graph
           │
           ▼
┌─────────────────────┐
│     Graph RAG       │
│  03_graph_rag.py    │
└──────────┬──────────┘
           │
           ▼
     LangGraph Flow
           │
           ▼
       LLM Answer
           │
           ▼
   LangSmith Tracing
```

---

# 1. Data Cleaning

The starting dataset intentionally contains inconsistent data to simulate some common data-quality problems.

Examples:

```text
Univ.          → University
AZ             → Arizona
CS             → Computer Science
ECE            → Electronics
No GRE         → GRE Not Required
2 years        → 24 months
$35k           → 35000
Yes / No       → True / False
```

`01_clean_data.py`:

1. Loads the messy CSV
2. Removes unnecessary whitespace
3. Standardizes university names
4. Normalizes states
5. Normalizes program names
6. Standardizes GRE policies
7. Converts duration into a consistent format
8. Standardizes academic backgrounds
9. Normalizes topics
10. Normalizes tuition
11. Converts STEM designation to boolean
12. Removes duplicates
13. Saves a clean dataset

```text
Messy CSV
    ↓
Clean + Normalize
    ↓
university_admissions_clean.csv
```

A clean and consistent dataset is important because different representations of the same entity can otherwise create duplicate or incorrect graph nodes.

---

# 2. Knowledge Graph

The cleaned admissions data is transformed into a Knowledge Graph and stored in **Neo4j**.

## Nodes

The graph contains the following entity types:

```text
University
Program
Background
Course
Topic
GREPolicy
```

Some information is stored as properties rather than separate nodes.

For example, a `Program` can contain properties such as:

```text
name
duration
minimum_gpa
intake
application_deadline
stem_designated
estimated_tuition
```

### Simple rule used in this project

> If we need to traverse or search relationships through something → **Node**
> If it mainly describes an entity → **Property**

---

## Relationships

```text
(University)-[:OFFERS]->(Program)

(Background)-[:ELIGIBLE_FOR]->(Program)

(Program)-[:HAS_COURSE]->(Course)

(Course)-[:COVERS]->(Topic)

(Program)-[:HAS_GRE_POLICY]->(GREPolicy)
```

Example:

```text
                    University
                        │
                      OFFERS
                        ▼
Background ───────► Program ───────► GREPolicy
          ELIGIBLE   │      HAS_GRE_POLICY
                     │
                 HAS_COURSE
                     ▼
                   Course
                     │
                   COVERS
                     ▼
                   Topic
```

This structure allows us to traverse relationships instead of treating admissions information as isolated records.

---

# 3. Graph RAG

`03_graph_rag.py` creates a simple Graph RAG application.

The user can ask a natural-language question such as:

> I studied Electronics. Which programs am I eligible for?

The application follows this workflow:

```text
User Question
      │
      ▼
Extract Entities
     (LLM)
      │
      ▼
Retrieve Graph Context
     (Neo4j)
      │
      ▼
Check Context
    ┌───────┴────────┐
    │                │
 Context          No Context
 Found
    │                │
    ▼                ▼
Generate          Return
 Answer          Safe Response
    │
    ▼
Final Answer
```

The LLM is instructed to answer using the retrieved Knowledge Graph context rather than inventing missing university information.

---

# LangGraph Workflow

The Graph RAG pipeline is orchestrated using **LangGraph**.

```text
START
  │
  ▼
extract_entities
  │
  ▼
retrieve_graph
  │
  ▼
check_context
  │
  ├── context found ──► generate_answer ──► END
  │
  └── no context ─────► no_context ───────► END
```

An important distinction:

```text
Neo4j       → Knowledge / Data Graph

LangGraph   → Application Execution Graph

LangChain   → Prompt + LLM Integration

LangSmith   → Tracing / Observability
```

---

# LangSmith Observability

Every Graph RAG query can be traced using **LangSmith**.

This makes it possible to inspect:

```text
User Question
      ↓
Extracted Entities
      ↓
Retrieved Graph Context
      ↓
LLM Prompt
      ↓
LLM Response
```

It also helps with:

* Debugging
* Latency analysis
* Token usage
* Cost tracking
* Error investigation
* Understanding model behavior

---

# Example Questions

Start with simple graph questions:

```text
What programs are related to Electronics?

Which programs do not require GRE?

Which programs require GRE?

What courses are available for MS Data Science?

Which universities offer MS Computer Science?
```

Then try relationship-based questions:

```text
I studied Electronics. Which programs am I eligible for?

Which programs are available for Computer Science graduates?

Which courses cover Artificial Intelligence?

Which programs have Machine Learning related courses?
```

And more complex questions:

```text
I studied Electronics. Which programs am I eligible for that do not require GRE?

Which programs don't require GRE and contain Machine Learning related courses?

I have a Computer Science background. Find programs with AI-related courses that don't require GRE.
```

You can also test hallucination handling:

```text
Which universities offer a Master's in Quantum Computing?
```

If that information doesn't exist in the graph, the application should not invent it.

---

# Tech Stack

| Technology    | Purpose                                 |
| ------------- | --------------------------------------- |
| Python        | Application development                 |
| Pandas        | Data cleaning and transformation        |
| Neo4j         | Knowledge Graph database                |
| Cypher        | Graph querying                          |
| LangChain     | LLM and prompt integration              |
| LangGraph     | Graph RAG workflow orchestration        |
| OpenAI        | Entity extraction and answer generation |
| LangSmith     | Tracing and observability               |
| python-dotenv | Environment variable management         |

---

# Project Structure

```text
Graph-RAG/
│
├── data/
│   ├── university_admissions_messy_large.csv
│   └── university_admissions_clean.csv
│
├── 01_clean_data.py
├── 02_load_graph.py
├── 03_graph_rag.py
├── README.md
├── .gitignore
└── .env              # Local only — DO NOT commit
```

---

# Setup

### 1. Clone the repository

```bash
git clone <repository-url>

cd Graph-RAG
```

### 2. Install dependencies

Install the required Python packages:

```bash
pip install pandas neo4j python-dotenv langchain langchain-openai langgraph langsmith
```

### 3. Configure environment variables

Create a `.env` file:

```env
NEO4J_URI=your_neo4j_uri
NEO4J_USER=your_neo4j_username
NEO4J_PASSWORD=your_neo4j_password

OPENAI_API_KEY=your_openai_api_key

LANGSMITH_TRACING=true
LANGSMITH_API_KEY=your_langsmith_api_key
LANGSMITH_PROJECT=university-graph-rag
```
---

# Running the Project

### Step 1 — Clean the data

```bash
python 01_clean_data.py
```

This generates:

```text
data/university_admissions_clean.csv
```

### Step 2 — Build the Neo4j Knowledge Graph

```bash
python 02_load_graph.py
```

This creates the nodes and relationships in Neo4j.

### Step 3 — Run Graph RAG

```bash
python 03_graph_rag.py
```

Then ask questions directly from the terminal.

---

# What This Project Demonstrates

This small project covers the complete learning flow:

```text
Raw Data
   ↓
Data Cleaning
   ↓
Entity Identification
   ↓
Node / Property Design
   ↓
Relationship Modeling
   ↓
Neo4j Knowledge Graph
   ↓
Cypher Retrieval
   ↓
LLM Entity Extraction
   ↓
Graph RAG
   ↓
LangGraph Orchestration
   ↓
Grounded Answer
   ↓
LangSmith Observability
```

The main takeaway is that **Graph RAG becomes especially useful when information is connected and answering a question requires traversing relationships between multiple entities.**

