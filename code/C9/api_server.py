"""
Flask API for the Chapter 9 Graph RAG cooking assistant.

The original console application remains available in main.py. This server
wraps the same AdvancedGraphRAGSystem with JSON endpoints for a Vue dashboard.
"""

import os
import sys
import threading
import time
import traceback
import mimetypes
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, Optional

from flask import Flask, jsonify, request, send_from_directory

CURRENT_DIR = Path(__file__).resolve().parent
FRONTEND_DIST = CURRENT_DIR / "frontend" / "dist"
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from config import DEFAULT_CONFIG, GraphRAGConfig

mimetypes.add_type("application/javascript", ".js")
mimetypes.add_type("text/css", ".css")


class GraphRAGWebService:
    """Thread-safe facade around the long-lived RAG system instance."""

    def __init__(self):
        self._lock = threading.RLock()
        self._system: Optional[AdvancedGraphRAGSystem] = None
        self._config = DEFAULT_CONFIG
        self._operation = {
            "running": False,
            "name": None,
            "started_at": None,
            "finished_at": None,
            "status": "idle",
            "message": "系统尚未启动",
            "error": None,
        }
        self._last_error = None

    def _create_system(self):
        # Import lazily so the dashboard and health endpoints can start even
        # before optional RAG dependencies such as neo4j/pymilvus are installed.
        from main import AdvancedGraphRAGSystem

        return AdvancedGraphRAGSystem(config=self._config)

    def get_config(self) -> Dict[str, Any]:
        return self._config.to_dict()

    def update_config(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        allowed = set(self._config.to_dict().keys())
        clean_payload = {key: value for key, value in payload.items() if key in allowed}
        config_data = {**self._config.to_dict(), **clean_payload}

        int_fields = {"milvus_port", "milvus_dimension", "top_k", "max_tokens", "chunk_size", "chunk_overlap", "max_graph_depth"}
        float_fields = {"temperature"}
        for key in int_fields:
            if key in config_data:
                config_data[key] = int(config_data[key])
        for key in float_fields:
            if key in config_data:
                config_data[key] = float(config_data[key])

        with self._lock:
            if self._system and self._system.system_ready:
                raise RuntimeError("系统已就绪，修改配置前请重启 Flask 服务")
            self._config = GraphRAGConfig.from_dict(config_data)
            return self.get_config()

    def status(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "ready": bool(self._system and self._system.system_ready),
                "initialized": bool(self._system),
                "operation": dict(self._operation),
                "last_error": self._last_error,
                "config": self.get_config(),
                "runtime": {
                    "python_executable": sys.executable,
                    "python_version": sys.version,
                    "working_directory": os.getcwd(),
                },
            }

    def _set_operation(self, name: str, status: str, message: str, error: Optional[str] = None):
        self._operation.update({
            "running": status == "running",
            "name": name,
            "status": status,
            "message": message,
            "error": error,
        })
        if status == "running":
            self._operation["started_at"] = time.time()
            self._operation["finished_at"] = None
        else:
            self._operation["finished_at"] = time.time()

    def _run_operation(self, name: str, fn, success_message: str):
        with self._lock:
            if self._operation["running"]:
                raise RuntimeError(f"当前正在执行：{self._operation['name']}")
            self._set_operation(name, "running", f"{name} 进行中")

        def worker():
            try:
                fn()
                with self._lock:
                    self._last_error = None
                    self._set_operation(name, "success", success_message)
            except Exception as exc:
                error = f"{exc}"
                with self._lock:
                    self._last_error = traceback.format_exc()
                    self._set_operation(name, "error", f"{name} 失败", error)

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()
        return self.status()

    def initialize(self):
        def task():
            with self._lock:
                if self._system is not None:
                    return
                self._system = self._create_system()
            self._system.initialize_system()

        return self._run_operation("初始化系统", task, "系统初始化完成")

    def build_knowledge_base(self):
        def task():
            with self._lock:
                if self._system is None:
                    self._system = self._create_system()
            if not self._system.data_module:
                self._system.initialize_system()
            self._system.build_knowledge_base()

        return self._run_operation("构建知识库", task, "知识库已加载或构建完成")

    def rebuild_knowledge_base(self):
        def task():
            with self._lock:
                if self._system is None:
                    self._system = self._create_system()
            if not self._system.data_module:
                self._system.initialize_system()
            if self._system.index_module:
                self._system.index_module.delete_collection()
            self._system.build_knowledge_base()

        return self._run_operation("重建知识库", task, "知识库重建完成")

    def ask(self, question: str, explain_routing: bool = False) -> Dict[str, Any]:
        with self._lock:
            if not self._system or not self._system.system_ready:
                raise RuntimeError("系统未就绪，请先初始化并构建知识库")
            start_time = time.time()
            answer, analysis = self._system.ask_question_with_routing(
                question,
                stream=False,
                explain_routing=explain_routing,
            )
            elapsed = time.time() - start_time
            return {
                "question": question,
                "answer": answer,
                "elapsed_seconds": round(elapsed, 3),
                "analysis": serialize_analysis(analysis),
                "stats": self.stats(),
            }

    def explain_routing(self, question: str) -> Dict[str, Any]:
        with self._lock:
            if not self._system or not self._system.query_router:
                raise RuntimeError("系统未初始化，无法分析路由")
            analysis = self._system.query_router.analyze_query(question)
            return {
                "question": question,
                "analysis": serialize_analysis(analysis),
            }

    def stats(self) -> Dict[str, Any]:
        with self._lock:
            if not self._system:
                return empty_stats()

            data_stats = {}
            milvus_stats = {}
            route_stats = {}
            graph_index_stats = {}

            if self._system.data_module:
                data_stats = self._system.data_module.get_statistics()
            if self._system.index_module:
                milvus_stats = self._system.index_module.get_collection_stats()
            if self._system.query_router:
                route_stats = self._system.query_router.get_route_statistics()
            if self._system.traditional_retrieval and self._system.traditional_retrieval.graph_indexing:
                graph_index_stats = self._system.traditional_retrieval.graph_indexing.get_statistics()

            return {
                "system_ready": self._system.system_ready,
                "knowledge": data_stats,
                "milvus": milvus_stats,
                "routes": route_stats,
                "graph_index": graph_index_stats,
            }


def serialize_analysis(analysis) -> Optional[Dict[str, Any]]:
    if analysis is None:
        return None
    data = asdict(analysis)
    strategy = data.get("recommended_strategy")
    if hasattr(strategy, "value"):
        data["recommended_strategy"] = strategy.value
    return data


def empty_stats() -> Dict[str, Any]:
    return {
        "system_ready": False,
        "knowledge": {
            "total_recipes": 0,
            "total_ingredients": 0,
            "total_cooking_steps": 0,
            "total_documents": 0,
            "total_chunks": 0,
        },
        "milvus": {},
        "routes": {
            "traditional_count": 0,
            "graph_rag_count": 0,
            "combined_count": 0,
            "total_queries": 0,
        },
        "graph_index": {},
    }


service = GraphRAGWebService()
app = Flask(__name__, static_folder=str(FRONTEND_DIST), static_url_path="")


def json_error(message: str, status_code: int = 400):
    response = jsonify({"ok": False, "error": message})
    response.status_code = status_code
    return response


@app.get("/api/health")
def health():
    return jsonify({"ok": True, **service.status()})


@app.get("/api/config")
def get_config():
    return jsonify({"ok": True, "config": service.get_config()})


@app.put("/api/config")
def update_config():
    try:
        return jsonify({"ok": True, "config": service.update_config(request.get_json(force=True) or {})})
    except Exception as exc:
        return json_error(str(exc))


@app.post("/api/system/initialize")
def initialize_system():
    try:
        return jsonify({"ok": True, **service.initialize()})
    except Exception as exc:
        return json_error(str(exc), 409)


@app.post("/api/knowledge/build")
def build_knowledge_base():
    try:
        return jsonify({"ok": True, **service.build_knowledge_base()})
    except Exception as exc:
        return json_error(str(exc), 409)


@app.post("/api/knowledge/rebuild")
def rebuild_knowledge_base():
    payload = request.get_json(silent=True) or {}
    if payload.get("confirm") != "REBUILD":
        return json_error("请传入 confirm=REBUILD 以确认重建知识库")
    try:
        return jsonify({"ok": True, **service.rebuild_knowledge_base()})
    except Exception as exc:
        return json_error(str(exc), 409)


@app.get("/api/stats")
def get_stats():
    return jsonify({"ok": True, "stats": service.stats(), "status": service.status()})


@app.post("/api/chat")
def chat():
    payload = request.get_json(force=True) or {}
    question = (payload.get("question") or "").strip()
    if not question:
        return json_error("问题不能为空")
    try:
        result = service.ask(question, bool(payload.get("explain_routing")))
        return jsonify({"ok": True, **result})
    except Exception as exc:
        return json_error(str(exc))


@app.post("/api/routing/explain")
def explain_routing():
    payload = request.get_json(force=True) or {}
    question = (payload.get("question") or "").strip()
    if not question:
        return json_error("问题不能为空")
    try:
        return jsonify({"ok": True, **service.explain_routing(question)})
    except Exception as exc:
        return json_error(str(exc))


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_frontend(path: str):
    if FRONTEND_DIST.exists():
        target = FRONTEND_DIST / path
        if path and target.exists():
            return send_from_directory(FRONTEND_DIST, path)
        return send_from_directory(FRONTEND_DIST, "index.html")
    return jsonify({
        "ok": True,
        "message": "API 已启动。前端开发模式请运行：cd code/C9/frontend && npm run dev",
    })


if __name__ == "__main__":
    port = int(os.environ.get("C9_WEB_PORT", "5000"))
    debug = os.environ.get("C9_WEB_DEBUG", "").lower() in {"1", "true", "yes"}
    app.run(host="127.0.0.1", port=port, debug=debug, use_reloader=debug)
