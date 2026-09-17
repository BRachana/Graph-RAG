"""
load_dataset()

clean_dataset()

create_nodes()

create_relationships()

save_to_neo4j()
"""

import pandas as pd
import re


# --------------------------------------------------
# 1. LOAD DATA
# --------------------------------------------------

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

df = pd.read_csv(
    BASE_DIR / "data" / "university_admissions_messy_large.csv"
)

print("BEFORE CLEANING")
print(df.head())


# --------------------------------------------------
# 2. CLEAN WHITESPACE
# --------------------------------------------------

def clean_whitespace(value):
    if isinstance(value, str):
        return value.strip()
    return value


df = df.map(clean_whitespace)


# --------------------------------------------------
# 3. CLEAN UNIVERSITY NAME
# --------------------------------------------------

def clean_university_name(name):
    if not isinstance(name, str):
        return name

    name = name.strip()
    name = name.replace("Univ.", "University")
    name = name.title()

    return name


df["university_name"] = df["university_name"].apply(
    clean_university_name
)


# --------------------------------------------------
# 4. CLEAN STATE
# --------------------------------------------------

def clean_state(state):

    state_mapping = {
        "AZ": "Arizona",
        "TX": "Texas",
        "CA": "California",
        "MA": "Massachusetts",
        "IL": "Illinois",
        "WA": "Washington",
        "NC": "North Carolina",
        "CO": "Colorado"
    }

    return state_mapping.get(state, state)


df["state"] = df["state"].apply(clean_state)


# --------------------------------------------------
# 5. CLEAN PROGRAM NAME
# --------------------------------------------------

def clean_program_name(name):

    if not isinstance(name, str):
        return name

    replacements = {
        "M.S. ": "MS ",
        "Masters in ": "MS "
    }

    for old, new in replacements.items():
        name = name.replace(old, new)

    return name.strip()


df["program_name"] = df["program_name"].apply(
    clean_program_name
)


# --------------------------------------------------
# 6. CLEAN GRE POLICY
# --------------------------------------------------

def clean_gre_policy(value):

    if not isinstance(value, str):
        return value

    value = value.lower().strip()

    if value in ["no gre", "gre not required"]:
        return "GRE Not Required"

    if value in ["optional", "gre optional"]:
        return "GRE Optional"

    if value in ["required", "gre required"]:
        return "GRE Required"

    return value


df["gre_policy"] = df["gre_policy"].apply(
    clean_gre_policy
)


# --------------------------------------------------
# 7. CLEAN DURATION
# --------------------------------------------------

def clean_duration(value):

    if not isinstance(value, str):
        return value

    value = value.lower().strip()

    if value == "2 years":
        return 24

    match = re.search(r"\d+", value)

    if match:
        return int(match.group())

    return None


df["duration"] = df["duration"].apply(
    clean_duration
)


# --------------------------------------------------
# 8. CLEAN BACKGROUNDS
# --------------------------------------------------

def clean_backgrounds(value):

    if not isinstance(value, str):
        return value

    mapping = {
        "CS": "Computer Science",
        "IT": "Information Technology",
        "ECE": "Electronics",
        "Maths": "Mathematics",
        "Stats": "Statistics"
    }

    backgrounds = value.split("|")

    cleaned = []

    for background in backgrounds:

        background = background.strip()

        background = mapping.get(
            background,
            background
        )

        cleaned.append(background)

    return " | ".join(cleaned)


df["eligible_backgrounds"] = df["eligible_backgrounds"].apply(
    clean_backgrounds
)


# --------------------------------------------------
# 9. CLEAN TOPICS
# --------------------------------------------------

def clean_topics(value):

    if not isinstance(value, str):
        return value

    mapping = {
        "AI": "Artificial Intelligence",
        "ML": "Machine Learning",
        "NLP": "Natural Language Processing"
    }

    topics = value.split("|")

    cleaned = []

    for topic in topics:

        topic = topic.strip()

        topic = mapping.get(
            topic,
            topic
        )

        cleaned.append(topic)

    return " | ".join(cleaned)


df["topics"] = df["topics"].apply(
    clean_topics
)


# --------------------------------------------------
# 10. CLEAN TUITION
# --------------------------------------------------

def clean_tuition(value):

    if not isinstance(value, str):
        return value

    value = value.lower().strip()

    # Example: $35k → 35000
    if "k" in value:

        number = re.findall(
            r"\d+",
            value
        )

        if number:
            return int(number[0]) * 1000

    # Example:
    # "$28,000" → 28000
    # "32000 USD" → 32000

    numbers = re.sub(
        r"[^\d]",
        "",
        value
    )

    if numbers:
        return int(numbers)

    return None


df["estimated_tuition"] = df["estimated_tuition"].apply(
    clean_tuition
)


# --------------------------------------------------
# 11. CLEAN STEM DESIGNATION
# --------------------------------------------------

def clean_stem(value):

    if not isinstance(value, str):
        return value

    value = value.lower().strip()

    if value == "yes":
        return True

    if value == "no":
        return False

    return None


df["stem_designated"] = df["stem_designated"].apply(
    clean_stem
)


# --------------------------------------------------
# 12. REMOVE EXACT DUPLICATES
# --------------------------------------------------

df = df.drop_duplicates()


# --------------------------------------------------
# 13. RESET INDEX
# --------------------------------------------------

df = df.reset_index(drop=True)


# --------------------------------------------------
# 14. CHECK CLEAN DATA
# --------------------------------------------------

print("\nAFTER CLEANING")
print(df.head())

print("\nUNIVERSITIES")
print(df["university_name"].unique())

print("\nPROGRAMS")
print(df["program_name"].unique())

print("\nGRE POLICIES")
print(df["gre_policy"].unique())

print("\nSTATES")
print(df["state"].unique())


# --------------------------------------------------
# 15. SAVE CLEAN DATA
# --------------------------------------------------

df.to_csv(
    BASE_DIR / "data" / "university_admissions_clean.csv",
    index=False
)


print("\nClean dataset saved!")