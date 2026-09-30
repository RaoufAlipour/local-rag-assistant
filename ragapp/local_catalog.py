"""SDK 2.0.1 catalog_urls için cihaz içi, salt okunur metadata kataloğu.

Gerçek model metadata'sı çevrimiçi snapshot komutuyla kaydedilir. Bu servis
model çalıştırmaz, ağırlık indirmez ve dış adreslere istek göndermez.
"""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import secrets
import threading

from ragapp.evaluation import digest


def validate_snapshot(snapshot, device):
    if snapshot.get("schema_version") != 1 or snapshot.get("sdk_version") != "2.0.1":
        raise ValueError("Yerel katalog sürümü uyumsuz; çevrimiçi snapshot çalıştırın.")
    if snapshot.get("device") != device:
        raise ValueError("Yerel katalog farklı cihaz için hazırlanmış.")
    models = snapshot.get("models")
    if not isinstance(models, list) or not models or snapshot.get("digest") != digest(models):
        raise ValueError("Yerel katalog boş veya değiştirilmiş; snapshot komutunu yeniden çalıştırın.")
    ids = set()
    provider = {"cpu": "CPUExecutionProvider", "cuda": "CUDAExecutionProvider"}[device]
    for model in models:
        if (not model.get("name") or model.get("id") != f"{model['name']}:{model.get('version')}"
                or not model.get("alias") or not model.get("uri")
                or model.get("task") not in {"embeddings", "chat-completion", "vision-language-chat"}
                or (model.get("runtime") or {}).get("execution_provider") != provider
                or model["id"] in ids):
            raise ValueError("Yerel katalogda eksik/uyumsuz model bilgisi var.")
        ids.add(model["id"])
    return models


def catalog_entry(info):
    """Python ModelInfo alanlarını SDK'nın katalog yanıt biçimine çevirir."""
    tags = {"alias": info["alias"], "task": info["task"], "foundryLocal": "true"}
    for source, target in (("license", "license"), ("license_description", "licenseDescription"),
                           ("max_output_tokens", "maxOutputTokens")):
        if info.get(source) is not None:
            tags[target] = str(info[source])
    if info.get("supports_tool_calling") is not None:
        tags["supportsToolCalling"] = str(info["supports_tool_calling"]).lower()
    if info.get("prompt_template"):
        tags["promptTemplate"] = json.dumps(info["prompt_template"])
    backend = info["runtime"]
    variant = {"modelType": info.get("model_type") or "ONNX",
               "device": backend["device_type"], "executionProvider": backend["execution_provider"]}
    if info.get("file_size_mb") is not None:
        variant["fileSizeBytes"] = info["file_size_mb"] * 1024 * 1024
    return {"assetId": info["uri"], "entityId": info["id"],
            "annotations": {"tags": tags, "systemCatalogData": {
                k: info[v] for k, v in (("publisher", "publisher"), ("displayName", "display_name"),
                                        ("maxOutputTokens", "max_output_tokens")) if info.get(v) is not None}},
            "properties": {"id": info["id"], "name": info["name"], "version": info["version"],
                           "variantInfo": {"variantMetadata": variant},
                           **({"minFLVersion": info["min_fl_version"]} if info.get("min_fl_version") else {})}}


def filter_entries(entries, request):
    fields = {"properties/id": lambda e: e["properties"]["id"],
              "properties/name": lambda e: e["properties"]["name"],
              "annotations/tags/alias": lambda e: e["annotations"]["tags"]["alias"],
              "properties/variantInfo/variantMetadata/device": lambda e: e["properties"]["variantInfo"]["variantMetadata"]["device"],
              "properties/variantInfo/variantMetadata/executionProvider": lambda e: e["properties"]["variantInfo"]["variantMetadata"]["executionProvider"]}
    result = list(entries)
    for rule in request.get("indexEntitiesRequest", {}).get("filters", []):
        field = rule.get("field")
        if field in fields:
            values = {str(v).casefold() for v in rule.get("values", [])}
            result = [entry for entry in result if str(fields[field](entry)).casefold() in values]
    return result


class LocalCatalog:
    def __init__(self, models):
        entries = [catalog_entry(info) for info in models]
        token = secrets.token_urlsafe(24)
        endpoint = f"/{token}/entities/crossRegion"
        self.requests = 0
        owner = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_):
                pass

            def do_POST(self):
                if self.path != endpoint:
                    self.send_error(404)
                    return
                try:
                    length = int(self.headers.get("Content-Length", "0"))
                    if not 0 < length <= 65536:
                        raise ValueError("request size")
                    request = json.loads(self.rfile.read(length))
                    selected = filter_entries(entries, request)
                except (ValueError, TypeError, AttributeError):
                    self.send_error(400)
                    return
                owner.requests += 1
                body = json.dumps({"indexEntitiesResponse": {"totalCount": len(selected), "value": selected}}).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self.server.server_port}/{token}"
        self.thread = threading.Thread(target=self.server.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True)
        self.thread.start()

    def close(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()
