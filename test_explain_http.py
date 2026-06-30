import requests

url = "http://127.0.0.1:8000/explain"
data = {"topic": "Gravity"}

print("Sending POST request to /explain...")
try:
    response = requests.post(url, json=data)
    print("Status Code:", response.status_code)
    print("Headers:", response.headers)
    print("Response Content:")
    # print safely with replace to avoid encoding errors on windows console
    print(response.text.encode('utf-8', errors='replace').decode('utf-8'))
except Exception as e:
    print("Request failed:", e)
