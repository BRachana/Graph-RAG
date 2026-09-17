import os
import pandas as pd

from pathlib import Path
from dotenv import load_dotenv
from neo4j import GraphDatabase


# ============================================================
# 1. LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")


# ============================================================
# 2. LOAD CLEAN DATA
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

df = pd.read_csv(
    BASE_DIR / "data" / "university_admissions_clean.csv"
)

print(f"Loaded {len(df)} clean rows")


# ============================================================
# 3. CONNECT TO NEO4J
# ============================================================

driver = GraphDatabase.driver(
    NEO4J_URI,
    auth=(NEO4J_USER, NEO4J_PASSWORD)
)

driver.verify_connectivity()

print("Connected to Neo4j!")


# ============================================================
# 4. CREATE UNIVERSITY NODES
# ============================================================

def create_universities(driver, df):

    with driver.session() as session:

        for _, row in df.iterrows():

            session.run(
                """
                MERGE (u:University {name: $name})
                SET u.city = $city,
                    u.state = $state
                """,
                name=row["university_name"],
                city=row["city"],
                state=row["state"]
            )

    print("University nodes created!")


# ============================================================
# 5. CREATE PROGRAM NODES
# ============================================================

def create_programs(driver, df):

    with driver.session() as session:

        for _, row in df.iterrows():

            session.run(
                """
                MERGE (p:Program {
                    name: $program_name,
                    university: $university_name
                })

                SET p.duration = $duration,
                    p.minimum_gpa = $minimum_gpa,
                    p.intake = $intake,
                    p.application_deadline = $application_deadline,
                    p.stem_designated = $stem_designated,
                    p.estimated_tuition = $estimated_tuition
                """,
                program_name=row["program_name"],
                university_name=row["university_name"],
                duration=row["duration"],
                minimum_gpa=row["minimum_gpa"],
                intake=row["intake"],
                application_deadline=row["application_deadline"],
                stem_designated=row["stem_designated"],
                estimated_tuition=row["estimated_tuition"]
            )

    print("Program nodes created!")


# ============================================================
# 6. UNIVERSITY -> PROGRAM
# ============================================================

def create_university_program_relationships(driver, df):

    with driver.session() as session:

        for _, row in df.iterrows():

            session.run(
                """
                MATCH (u:University {name: $university_name})

                MATCH (p:Program {
                    name: $program_name,
                    university: $university_name
                })

                MERGE (u)-[:OFFERS]->(p)
                """,
                university_name=row["university_name"],
                program_name=row["program_name"]
            )

    print("University -> Program relationships created!")


# ============================================================
# 7. CREATE BACKGROUND NODES + ELIGIBILITY
# ============================================================

def create_backgrounds(driver, df):

    with driver.session() as session:

        for _, row in df.iterrows():

            backgrounds = row["eligible_backgrounds"].split("|")

            for background in backgrounds:

                background = background.strip()

                session.run(
                    """
                    MERGE (b:Background {name: $background})

                    WITH b

                    MATCH (p:Program {
                        name: $program_name,
                        university: $university_name
                    })

                    MERGE (b)-[:ELIGIBLE_FOR]->(p)
                    """,
                    background=background,
                    program_name=row["program_name"],
                    university_name=row["university_name"]
                )

    print("Background nodes and eligibility relationships created!")


# ============================================================
# 8. CREATE COURSE NODES + PROGRAM -> COURSE
# ============================================================

def create_courses(driver, df):

    with driver.session() as session:

        for _, row in df.iterrows():

            courses = row["courses"].split("|")

            for course in courses:

                course = course.strip()

                session.run(
                    """
                    MERGE (c:Course {name: $course})

                    WITH c

                    MATCH (p:Program {
                        name: $program_name,
                        university: $university_name
                    })

                    MERGE (p)-[:HAS_COURSE]->(c)
                    """,
                    course=course,
                    program_name=row["program_name"],
                    university_name=row["university_name"]
                )

    print("Course nodes and relationships created!")


# ============================================================
# 9. CREATE TOPIC NODES + COURSE -> TOPIC
# ============================================================

def create_topics(driver, df):

    with driver.session() as session:

        for _, row in df.iterrows():

            courses = [
                course.strip()
                for course in row["courses"].split("|")
            ]

            topics = [
                topic.strip()
                for topic in row["topics"].split("|")
            ]

            for course in courses:

                for topic in topics:

                    session.run(
                        """
                        MERGE (t:Topic {name: $topic})

                        WITH t

                        MATCH (c:Course {name: $course})

                        MERGE (c)-[:COVERS]->(t)
                        """,
                        course=course,
                        topic=topic
                    )

    print("Topic nodes and relationships created!")


# ============================================================
# 10. CREATE GRE POLICY NODES
# ============================================================

def create_gre_policies(driver, df):

    with driver.session() as session:

        for _, row in df.iterrows():

            session.run(
                """
                MERGE (g:GREPolicy {name: $gre_policy})

                WITH g

                MATCH (p:Program {
                    name: $program_name,
                    university: $university_name
                })

                MERGE (p)-[:HAS_GRE_POLICY]->(g)
                """,
                gre_policy=row["gre_policy"],
                program_name=row["program_name"],
                university_name=row["university_name"]
            )

    print("GRE Policy nodes and relationships created!")


# ============================================================
# 11. BUILD COMPLETE GRAPH
# ============================================================

def build_graph():

    print("\nBuilding Knowledge Graph...\n")

    create_universities(driver, df)

    create_programs(driver, df)

    create_university_program_relationships(driver, df)

    create_backgrounds(driver, df)

    create_courses(driver, df)

    create_topics(driver, df)

    create_gre_policies(driver, df)

    print("\nKnowledge Graph created successfully!")


# ============================================================
# 12. RUN
# ============================================================

if __name__ == "__main__":

    try:
        build_graph()

    finally:
        driver.close()

        print("Neo4j connection closed.")