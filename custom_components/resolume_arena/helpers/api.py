"""Small helpers to build Resolume API endpoints."""
from ..const import API_BASE

def base_url(host, port):
    return f"http://{host}:{port}{API_BASE}"

def composition_url(host, port):
    return f"{base_url(host, port)}/composition"

def layer_by_id_url(host, port, layer_id):
    return f"{base_url(host, port)}/composition/layers/by-id/{layer_id}"

def clip_by_id_url(host, port, clip_id):
    return f"{base_url(host, port)}/composition/clips/by-id/{clip_id}"
