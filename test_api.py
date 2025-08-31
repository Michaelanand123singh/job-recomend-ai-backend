import requests

# Change this to your actual backend URL if different
API_URL = "http://localhost:8000/match-resume"

# Path to a sample resume file (PDF, DOC, or DOCX)
file_path = "1.pdf"

with open(file_path, "rb") as f:
    files = {"file": (file_path, f, "application/pdf")}
    response = requests.post(API_URL, files=files)

print("Status Code:", response.status_code)
print("Response JSON:", response.json())