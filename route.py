from fastapi import FastAPI, Request
import json
from main import get_movie_urls_not_in_db  # Import your scraping function from the main file
from schemas import ScrapeRequest
from controller import main as run_all_scripts
from fastapi.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn  
import os 
app = FastAPI()

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/scrape-movies")
async def scrape_movies(request: ScrapeRequest):
    alphabet = request.alphabet
    num_pages = request.num_pages

    # Run the scraping process
    missing_urls = get_movie_urls_not_in_db(alphabet, num_pages)  # Function call
    with open("missing_url.json", "w") as f:
        json.dump(missing_urls, f)
    script_outputs = run_all_scripts()

    # Return both missing URLs and script outputs
    return {
        "missing_urls": missing_urls,
        "script_outputs": script_outputs
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8070)
