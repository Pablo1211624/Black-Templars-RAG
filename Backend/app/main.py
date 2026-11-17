from fastapi import FastAPI

app = FastAPI(title="Black Templars RAG")


@app.get("/health")
def health_check():
    return {"status": "ok"}
