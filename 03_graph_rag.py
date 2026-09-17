import os

from typing import TypedDict

from dotenv import load_dotenv
from neo4j import GraphDatabase

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from langgraph.graph import StateGraph, START, END
from langsmith import traceable

# ============================================================
# 1. LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


# ============================================================
# 2. CONNECT TO NEO4J
# ============================================================

driver = GraphDatabase.driver(
    NEO4J_URI,
    auth=(NEO4J_USER, NEO4J_PASSWORD)
)

driver.verify_connectivity()

print("Connected to Neo4j!")


# ============================================================
# 3. CREATE LLM
# ============================================================

llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0
)


# ============================================================
# 4. DEFINE LANGGRAPH STATE
# ============================================================

class GraphRAGState(TypedDict):

    question: str

    entities: list[str]

    context: str

    answer: str


# ============================================================
# 5. EXTRACT ENTITIES FROM QUESTION
# ============================================================

def extract_entities(state: GraphRAGState):

    question = state["question"]

    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            """
            You extract important entities from university
            admission questions.

            Entities can include:

            - university
            - program
            - academic background
            - course
            - topic
            - GRE policy
            - state
            - city

            Return only comma-separated entities.

            Example:

            Question:
            I studied Electronics and want an AI program
            without GRE.

            Output:
            Electronics, Artificial Intelligence, GRE Not Required
            """
        ),
        (
            "human",
            "{question}"
        )
    ])

    chain = prompt | llm

    response = chain.invoke({
        "question": question
    })

    entities = [
        entity.strip()
        for entity in response.content.split(",")
        if entity.strip()
    ]

    print("\nExtracted entities:")
    print(entities)

    return {
        "entities": entities
    }


# ============================================================
# 6. SEARCH NEO4J GRAPH
# ============================================================

def retrieve_graph(state: GraphRAGState):

    entities = state["entities"]

    results = []

    with driver.session() as session:

        for entity in entities:

            result = session.run(
                """
                MATCH (n)
                WHERE toLower(n.name) CONTAINS toLower($entity)

                OPTIONAL MATCH (n)-[r]-(connected)

                RETURN
                    labels(n) AS source_type,
                    n.name AS source,
                    type(r) AS relationship,
                    labels(connected) AS target_type,
                    connected.name AS target
                """,
                entity=entity
            )

            for record in result:

                results.append({
                    "source_type": record["source_type"],
                    "source": record["source"],
                    "relationship": record["relationship"],
                    "target_type": record["target_type"],
                    "target": record["target"]
                })

    context_lines = []

    for item in results:

        line = (
            f"{item['source']} "
            f"--{item['relationship']}--> "
            f"{item['target']}"
        )

        context_lines.append(line)

    context = "\n".join(context_lines)

    print("\nRetrieved Graph Context:")
    print(context)

    return {
        "context": context
    }


# ============================================================
# 7. CHECK IF CONTEXT WAS FOUND
# ============================================================

def check_context(state: GraphRAGState):

    context = state["context"]

    if context and context.strip():
        return "generate"

    return "no_context"


# ============================================================
# 8. GENERATE ANSWER USING GRAPH CONTEXT
# ============================================================

def generate_answer(state: GraphRAGState):

    question = state["question"]
    context = state["context"]

    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            """
            You are a university admissions assistant.

            Answer the user's question using ONLY the
            knowledge graph context provided.

            Do not invent universities, programs,
            eligibility rules, GRE requirements,
            courses or other information.

            If the graph context does not contain enough
            information, clearly say that the available
            graph data is insufficient.
            """
        ),
        (
            "human",
            """
            Question:

            {question}


            Knowledge Graph Context:

            {context}


            Answer the question clearly and concisely.
            """
        )
    ])

    chain = prompt | llm

    response = chain.invoke({
        "question": question,
        "context": context
    })

    return {
        "answer": response.content
    }


# ============================================================
# 9. HANDLE NO CONTEXT
# ============================================================

def no_context_answer(state: GraphRAGState):

    return {
        "answer": (
            "I couldn't find relevant information "
            "in the university knowledge graph."
        )
    }


# ============================================================
# 10. BUILD LANGGRAPH
# ============================================================

workflow = StateGraph(GraphRAGState)


# Add nodes

workflow.add_node(
    "extract_entities",
    extract_entities
)

workflow.add_node(
    "retrieve_graph",
    retrieve_graph
)

workflow.add_node(
    "generate_answer",
    generate_answer
)

workflow.add_node(
    "no_context",
    no_context_answer
)


# ============================================================
# 11. CONNECT LANGGRAPH NODES
# ============================================================

workflow.add_edge(
    START,
    "extract_entities"
)

workflow.add_edge(
    "extract_entities",
    "retrieve_graph"
)


workflow.add_conditional_edges(
    "retrieve_graph",
    check_context,
    {
        "generate": "generate_answer",
        "no_context": "no_context"
    }
)


workflow.add_edge(
    "generate_answer",
    END
)

workflow.add_edge(
    "no_context",
    END
)


# ============================================================
# 12. COMPILE GRAPH
# ============================================================

app = workflow.compile()


# ============================================================
# 13. ASK QUESTION
# ============================================================

@traceable(name="University Graph RAG Query")
def ask_question(question):

    result = app.invoke({
        "question": question,
        "entities": [],
        "context": "",
        "answer": ""
    })

    return result["answer"]


# ============================================================
# 14. RUN APPLICATION
# ============================================================

if __name__ == "__main__":

    try:

        print("\nUniversity Graph RAG")
        print("--------------------")

        while True:

            question = input(
                "\nAsk a question (or type 'exit'): "
            )

            if question.lower() == "exit":
                break

            answer = ask_question(question)

            print("\nAnswer:")
            print(answer)

    finally:

        driver.close()

        print("\nNeo4j connection closed.")