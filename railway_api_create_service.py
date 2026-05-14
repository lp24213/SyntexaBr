import requests
import json

url = 'https://backboard.railway.app/graphql/v2'
headers = {
    'Authorization': 'Bearer TgfaptT-UyVCQqImiM_6oWCtRrIQ7xwZhgqYuYLiAdW',
    'Content-Type': 'application/json'
}
query = {
    'query': 'mutation { serviceCreate(input: { projectId: "87a3c18f-921b-46cc-8f19-99604f6d4cd8", environmentId: "27ed0be1-946d-4286-ab34-c9fb2dbbf4f6", name: "syntexa-backend" }) { id name } }'
}
resp = requests.post(url, headers=headers, json=query)
print('Status:', resp.status_code)
print(resp.text)
