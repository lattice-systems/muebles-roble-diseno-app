from flask import current_app
from pymongo import MongoClient


def get_mongo_client():
    client = current_app.extensions.get("mongo_client")
    if client is None:
        mongo_uri = current_app.config.get("MONGO_URI")
        if not mongo_uri:
            raise RuntimeError("MONGO_URI is not configured")

        client = MongoClient(mongo_uri)
        current_app.extensions["mongo_client"] = client

    return client


def get_mongo_db():
    db_name = current_app.config.get("MONGO_DBNAME")
    if not db_name:
        raise RuntimeError("MONGO_DBNAME is not configured")

    client = get_mongo_client()
    return client[db_name]


def get_report_collections():
    db = get_mongo_db()
    return {
        "daily_sales": db["daily_sales_reports"],
        "daily_profit": db["daily_profit_reports"],
        "top_products": db["top_products_reports"],
        "weekly_sales": db["weekly_sales_reports"],
        "recent_sales": db["recent_sales_reports"],
        "general": db["general_reports"],
        "cost_snapshots": db["cost_snapshots"],
    }


def ensure_report_indexes():
    collections = get_report_collections()

    collections["daily_sales"].create_index("report_date", unique=True)
    collections["daily_profit"].create_index("report_date", unique=True)
    collections["weekly_sales"].create_index("report_date", unique=True)
    collections["recent_sales"].create_index("report_date", unique=True)
    collections["top_products"].create_index(
        [("date_from", 1), ("date_to", 1)],
        unique=True,
    )
    collections["general"].create_index("report_date", unique=True)
