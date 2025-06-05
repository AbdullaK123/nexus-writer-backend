from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.controllers.auth import user_controller


app = FastAPI(
    title="Nexus Writer API",
    description="The backend API for Nexus Writer",
    version="1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


app.include_router(user_controller)


@app.get('/health')
async def get_health() -> dict:
    return {
        'message': 'Everything is healthy!'
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host='localhost', port=8000)