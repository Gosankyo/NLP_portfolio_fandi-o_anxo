import os
import sys

#FORCE UTF-8 ENVIRONMENT (Fix to the error) 
os.environ["PYTHONUTF8"] = "1"

from crewai import Agent, Task, Crew, LLM
from crewai_tools import FileReadTool

# Ensure terminal output also handles UTF-8
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

# 1. OLLAMA CONFIGURATION 
ollama_llm = LLM(
    model="ollama/llama3:latest",
    base_url="http://localhost:11434"
)

#  2. TOOL INITIALIZATION 
file_tool = FileReadTool()

# 3. AGENT DEFINITION 
researcher = Agent(
    role='Senior Software Analyst',
    goal='Analyze the source code and explain its architecture.',
    backstory='You are a software architect. You use UTF-8 to read files.',
    tools=[file_tool],
    llm=ollama_llm,
    verbose=True,
    allow_delegation=False
)

# 4. TASK DEFINITION 
task1 = Task(
    description='Read the file at "C:/Users/Anxo/Downloads/my_local_Agent.py" and summarize it.',
    expected_output='A technical summary of the code.',
    agent=researcher
)

# 5. CREW ASSEMBLY 
crew = Crew(
    agents=[researcher],
    tasks=[task1],
    verbose=True
)

# --- 6. EXECUTION ---
print("\n" + "="*50)
print(" STARTING LOCAL AGENT ")
print("="*50 + "\n")

try:
    result = crew.kickoff()
    print("\n" + "="*50)
    print(" FINAL ANALYSIS RESULT:")
    print("="*50)
    print(result)
except Exception as e:
    print(f"\n Execution Error: {e}")