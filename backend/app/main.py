from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.data_fetch import get_stock_data, get_company_info, get_stock_news, search_ticker
from app.features import add_features
from app.models.baseline import train_baseline

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"status": "stock terminal backend running"}

@app.get("/stock/{ticker}")
def stock_data(ticker: str):
    df = get_stock_data(ticker)
    return df.reset_index().to_dict(orient="records")

@app.get("/stock/{ticker}/features")
def stock_features(ticker: str):
    df = get_stock_data(ticker, period="6mo")
    df = add_features(df)
    df = df.dropna()
    return df.reset_index().to_dict(orient="records")

@app.get("/stock/{ticker}/predict")
def stock_predict(ticker: str):
    df = get_stock_data(ticker, period="6mo")
    df = add_features(df)
    df = df.dropna()
    result = train_baseline(df)
    return result

@app.get("/stock/{ticker}/info")
def stock_info(ticker: str):
    return get_company_info(ticker)

@app.get("/stock/{ticker}/news")
def stock_news(ticker: str):
    return get_stock_news(ticker)
@app.get("/search/{query}")
def search(query: str):
    return search_ticker(query)