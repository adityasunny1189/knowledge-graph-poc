import streamlit as st
from neo4j import GraphDatabase

# Neo4j connection details
uri = "bolt://localhost:7687"
user = "neo4j"
password = "sprintoai"

# Connect to Neo4j
driver = GraphDatabase.driver(uri, auth=(user, password))

def get_all_scientists(tx):
    query = "MATCH (s:Scientist) RETURN s.name AS name"
    result = tx.run(query)
    return [record["name"] for record in result]

def find_coauthors_same_university(tx, scientist_name):
    query = """
    MATCH (s:Scientist {name: $scientist_name})-[:COAUTHOR]-(coauthor)
    WHERE s.university IS NOT NULL AND coauthor.university = s.university
    RETURN coauthor.name AS coauthor_name
    """
    result = tx.run(query, scientist_name=scientist_name)
    return [record["coauthor_name"] for record in result]

def did_coauthor(tx, scientist1, scientist2):
    query = """
    MATCH (s1:Scientist {name: $scientist1})-[:COAUTHOR]-(s2:Scientist {name: $scientist2})
    RETURN COUNT(*) > 0 AS coauthored
    """
    result = tx.run(query, scientist1=scientist1, scientist2=scientist2)
    return result.single()["coauthored"]

# Streamlit app
st.title("Neo4j Scientist Coauthorship App")

with driver.session() as session:
    scientists = session.execute_read(get_all_scientists)

    # scientist_name = st.selectbox("Select 1st scientist:", scientists)
    # st.header("Find Coauthors from the Same University")
    # scientist_name = st.selectbox("Select 2nd scientist:", scientists)
    # if st.button("Find Coauthors"):
    #     if scientist_name:
    #         coauthors = session.execute_read(find_coauthors_same_university, scientist_name)
    #         if coauthors:
    #             st.write(f"Coauthors of {scientist_name} from the same university:")
    #             st.write(coauthors)
    #         else:
    #             st.write(f"No coauthors found for {scientist_name} from the same university.")

    st.header("Check if Two Scientists Coauthored")
    scientist1 = st.selectbox("Select first scientist:", scientists)
    scientist2 = st.selectbox("Select second scientist:", scientists)
    if st.button("Check Coauthorship"):
        if scientist1 and scientist2:
            coauthored = session.execute_read(did_coauthor, scientist1, scientist2)
            st.write(f"{scientist1} and {scientist2} coauthored a paper: {coauthored}")
