from fastapi.responses import JSONResponse

def format_response(status: int, message: str, data=None, error=None):
    response_body = {
        "status": status,
        "message": message,
        "data": data,
        "error": error
    }
    return JSONResponse(content=response_body, status_code=status)