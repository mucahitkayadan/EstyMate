from openai import OpenAI
import psycopg2
from psycopg2 import sql
from api_key import api_key
from prompt import prompt
import logging
import re


# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Set up your OpenAI API key
client = OpenAI(api_key=api_key)

# Database connection details
DB_NAME = "esty_mate"
DB_USER = "postgres"
DB_PASSWORD = "admin"
DB_HOST = "localhost"
DB_PORT = "5432"


# Function to generate estimation questions
def generate_estimation_question():
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a model for creating estimation questions."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=100
    )
    text = response.choices[0].message.content.strip()
    print(text)
    question_text, correct_answer = parse_question_answer(text)
    print(question_text, correct_answer)
    return question_text, correct_answer


def parse_question_answer(output):
    # Regular expression to match the pattern
    pattern = r"Question: \[(.+?)\] Answer: \[(.*?)\]"

    # Find the match
    match = re.search(pattern, output)

    if match:
        question_part = match.group(1)
        correct_answer = match.group(2)

        if correct_answer:  # Ensure there is an answer
            correct_answer = correct_answer.replace(',', '')
            return question_part, correct_answer

    return None, None


# Example usage
output = "Question: [How many hours in a year?] Answer: [8760]"
question, answer = parse_question_answer(output)

if question and answer:
    print(f"Question: {question}, Answer: {answer}")
else:
    print("No valid question and answer found.")


# Function to populate questions in the database
def populate_questions(n):
    try:
        # Attempt to establish a connection
        logging.debug("Connecting to the database...")
        conn = psycopg2.connect(
            dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT
        )
        logging.debug("Database connection established.")
    except Exception as e:
        logging.error("Failed to connect to the database: %s", e)
        return

    try:
        cur = conn.cursor()

        insert_query = sql.SQL(
            "INSERT INTO questions (question_text, correct_answer, category) VALUES (%s, %s, %s)"
        )

        categories = ["science", "math", "general_knowledge", "technology"]  # Example categories

        for _ in range(n):
            question_text, correct_answer = generate_estimation_question()
            if question_text and correct_answer is not None:
                category = categories[_ % len(categories)]  # Rotate through categories
                cur.execute(insert_query, (question_text, correct_answer, category))
                logging.debug("Inserted question: %s", question_text)
            else:
                logging.warning("Generated question is invalid: %s, %s", question_text, correct_answer)

        conn.commit()
        logging.debug("Transaction committed.")
    except Exception as e:
        logging.error("An error occurred while inserting data: %s", e)
    finally:
        cur.close()
        conn.close()
        logging.debug("Database connection closed.")


# Generate and populate 2000 questions
populate_questions(20)
