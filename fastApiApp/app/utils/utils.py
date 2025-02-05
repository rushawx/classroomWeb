from app.db.postges import session


def get_pg():
    db = session()
    try:
        yield db
    finally:
        db.close()
