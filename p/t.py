from fastapi import FastAPI
from wtma import WTMA

app = FastAPI()

@app.get("/")
def root():
    return {
        "message": "Hello, world!"
    }

# Wrap the app at the end
app = WTMA(app, log_path="log.json", file_format="JSON", log_to_console=True)
