"""Web server for the Interview Bot application."""
import asyncio
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from typing import Dict, Any

# Initialize FastAPI app
app = FastAPI(
    title="Interview Bot API",
    description="API for Interview Bot application",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root() -> Dict[str, str]:
    """
    Root endpoint that returns a simple status message.
    
    Returns:
        Dict[str, str]: A dictionary with a status message.
    """
    return {"status": "I am alive"}

@app.get("/health")
async def health_check() -> Dict[str, str]:
    """
    Health check endpoint for monitoring.
    
    Returns:
        Dict[str, str]: A dictionary with the health status.
    """
    return {"status": "healthy"}

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Global exception handler for the application.
    
    Args:
        request: The request that caused the exception.
        exc: The exception that was raised.
        
    Returns:
        JSONResponse: A JSON response with error details.
    """
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": f"An error occurred: {str(exc)}"},
    )

def run_web_server(host: str = "0.0.0.0", port: int = 8080) -> None:
    """
    Run the FastAPI web server.
    
    Args:
        host: The host to bind the server to.
        port: The port to bind the server to.
    """
    config = uvicorn.Config(
        app=app,
        host=host,
        port=port,
        log_level="info",
        workers=1,
    )
    server = uvicorn.Server(config)
    
    try:
        asyncio.run(server.serve())
    except asyncio.CancelledError:
        pass  # Server was stopped
    except Exception as e:
        print(f"Error running web server: {e}")

if __name__ == "__main__":
    run_web_server()
