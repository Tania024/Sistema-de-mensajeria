from functools import wraps
from flask import request, jsonify

def validate_token(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        token = request.headers.get("Authorization")
        user = request.headers.get("X-User")
        if not token or token != "Bearer 12345" or not user:
            return jsonify({"error": "Acceso denegado"}), 403
        return func(*args, **kwargs)
    return wrapper
