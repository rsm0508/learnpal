from fastapi import FastAPI

app = FastAPI(title="LearnPal API")

@app.get("/health")
def health():
    return {"status": "ok"}
