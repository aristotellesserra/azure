import json
import os
from urllib.parse import quote

import requests

TENANT_ID = os.environ.get("TENANT_ID")
CLIENT_ID = os.environ.get("CLIENT_ID")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET")
DEFAULT_USER_ID = os.environ.get("USER_ID")


def get_access_token(tenant_id: str, client_id: str, client_secret: str) -> str:
    token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
        "scope": "https://graph.microsoft.com/.default",
    }

    resp = requests.post(token_url, data=data)
    if resp.status_code != 200:
        raise RuntimeError(f"Token request failed: {resp.status_code} {resp.text}")
    return resp.json()["access_token"]


def get_user_groups(access_token: str, user_id: str) -> dict:
    encoded_user_id = quote(user_id, safe="")
    graph_url = f"https://graph.microsoft.com/v1.0/users/{encoded_user_id}/memberOf"
    headers = {"Authorization": f"Bearer {access_token}"}
    resp = requests.get(graph_url, headers=headers)
    if resp.status_code != 200:
        raise RuntimeError(f"Graph request failed: {resp.status_code} {resp.text}")
    return resp.json()


def handler(ctx, data=None, headers=None):
    if isinstance(data, bytes):
        data = data.decode("utf-8")

    user_id = DEFAULT_USER_ID
    if data:
        try:
            payload = json.loads(data)
            user_id = payload.get("user_id", user_id)
        except ValueError:
            user_id = data or user_id

    if not TENANT_ID or not CLIENT_ID or not CLIENT_SECRET:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Missing TENANT_ID, CLIENT_ID, or CLIENT_SECRET environment variable."}),
        }

    if not user_id:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Missing user_id. Set USER_ID environment variable or provide user_id in the request body."}),
        }

    try:
        token = get_access_token(TENANT_ID, CLIENT_ID, CLIENT_SECRET)
        groups = get_user_groups(token, user_id)
        return {"statusCode": 200, "body": json.dumps(groups)}
    except Exception as exc:
        return {"statusCode": 500, "body": json.dumps({"error": str(exc)})}
