from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from src.routers import receipt_radar_router, total_messages_router , get_attachments

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["DELETE", "GET", "POST", "PUT"],
    allow_headers=["*"],
)

app.include_router(receipt_radar_router.router)
app.include_router(total_messages_router.router)
app.include_router(get_attachments.router)
@app.get("/")
async def test():
    return {"Message":"Application is Working!"}
