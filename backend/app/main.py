from fastapi import FastAPI

app = FastAPI(title="Hardware Hub API")


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Hardware Hub backend is running"}


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}