from flask import current_app


def get_mongo_db():
    client = current_app.extensions["mongo_client"]
    return client[current_app.config["MONGO_DBNAME"]]


def get_report_collections():
    db = get_mongo_db()
    return {
        "daily_sales": db["daily_sales_reports"],
        "daily_profit": db["daily_profit_reports"],
        "top_products": db["top_products_reports"],
        "weekly_sales": db["weekly_sales_reports"],
        "recent_sales": db["recent_sales_reports"],
        "general": db["general_reports"],
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