from contextvars import ContextVar

request_id_context = ContextVar("request_id", default="-")
schema_name_context = ContextVar("schema_name", default="-")
method_context = ContextVar("method", default="-")
path_context = ContextVar("path", default="-")
status_code_context = ContextVar("status_code", default="-")
duration_ms_context = ContextVar("duration_ms", default="-")


def set_request_context(*, request_id="-", schema_name="-", method="-", path="-"):
    return {
        "request_id": request_id_context.set(request_id),
        "schema_name": schema_name_context.set(schema_name),
        "method": method_context.set(method),
        "path": path_context.set(path),
        "status_code": status_code_context.set("-"),
        "duration_ms": duration_ms_context.set("-"),
    }


def set_response_context(*, status_code="-", duration_ms="-"):
    status_code_context.set(status_code)
    duration_ms_context.set(duration_ms)


def reset_request_context(tokens):
    request_id_context.reset(tokens["request_id"])
    schema_name_context.reset(tokens["schema_name"])
    method_context.reset(tokens["method"])
    path_context.reset(tokens["path"])
    status_code_context.reset(tokens["status_code"])
    duration_ms_context.reset(tokens["duration_ms"])


def get_request_context():
    return {
        "request_id": request_id_context.get(),
        "schema_name": schema_name_context.get(),
        "method": method_context.get(),
        "path": path_context.get(),
        "status_code": status_code_context.get(),
        "duration_ms": duration_ms_context.get(),
    }
