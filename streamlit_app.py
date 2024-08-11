from dotenv import load_dotenv
import streamlit as st
import os
import pyodbc
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Configure the API key for Google Generative AI
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Function to load the Gemini model to provide SQL query as output
def get_gemini_response(question, prompt):
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content([prompt[0], question])
    return response.text.strip()  # Strip any unwanted spaces or newlines

# Function to retrieve data from the SQL database
def read_sql_query(sql):
    # Define the connection string for MS SQL Server
    connection_string = (
        "DRIVER={SQL Server};"
        "SERVER=VIVEK\\SQLEXPRESS;"  # Update this to your server name
        "DATABASE=LLM_app;"  # Update this to your database name
        "Trusted_Connection=yes;"  # Use this if using Windows Authentication
    )
    
    # Connect to the database
    conn = pyodbc.connect(connection_string)
    cur = conn.cursor()
    
    # Execute the SQL query
    cur.execute(sql)
    rows = cur.fetchall()
    
    # Close the connection
    conn.close()
    
    return rows

# Define the prompt with examples including aggregate functions
prompt = [
    """
    You are an expert in converting English questions to SQL queries!
    The SQL database has the name AttendanceData and has the following columns - EmployeeID, EventTime, Pincode, EmployeeName, DeptName, Designation.
    
    For example:
    
    1. "How many entries of records are present?" 
       The SQL command will be: SELECT COUNT(*) FROM AttendanceData;
    
    2. "Tell me all the EmployeeName in DeptName 'HR'?" 
       The SQL command will be: SELECT EmployeeName FROM AttendanceData WHERE DeptName = 'HR';
    
    3. "What is the count of Employees in DeptName 'HR'?"
       The SQL command will be: SELECT DeptName, COUNT(*) AS EmployeeCount FROM AttendanceData WHERE DeptName = 'HR' GROUP BY DeptName;
    
    4. "What is the average time spent by employees in each department?"
       The SQL command will be: SELECT DeptName, AVG(DATEDIFF(minute, MIN(EventTime), MAX(EventTime))) AS AvgTimeSpent FROM AttendanceData GROUP BY DeptName;
    
    5. "List the EmployeeName and their respective ranks within each department based on their EventTime."
       The SQL command will be: 
       SELECT EmployeeName, DeptName, RANK() OVER (PARTITION BY DeptName ORDER BY EventTime) AS RankWithinDept 
       FROM AttendanceData;

    6. "What is the running total of employees checked in by EventTime?"
       The SQL command will be: 
       SELECT EventTime, COUNT(*) OVER (ORDER BY EventTime ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS RunningTotal
       FROM AttendanceData;

    The SQL code should not include `SQL` in the output and should not have any leading or trailing ``` marks.
    """
]

# Streamlit App Configuration
st.set_page_config(page_title="I can Retrieve Any SQL query")
st.header("LLM App To Retrieve SQL Data")

# Input Section
question = st.text_input("Input: ", key="input")

# Submit button
submit = st.button("Ask the question")

# If submit is clicked
if submit:
    # Get the SQL query from the AI model
    response = get_gemini_response(question, prompt)
    st.write(f"Generated SQL Query: {response}")
    
    # Execute the SQL query and retrieve results
    try:
        response_data = read_sql_query(response)
        st.subheader("The Response is:")
        for row in response_data:
            st.write(row)
    except pyodbc.Error as e:
        st.error(f"An error occurred: {e}")
