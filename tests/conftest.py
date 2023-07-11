import pytest
from processingHUPX import app, db

@pytest.fixture(scope="session")
def client():
    app.config['TESTING'] = True
    #app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
    with app.app_context():
        db.create_all()
    with app.test_client() as client:
        yield client
    with app.app_context():
        db.drop_all()


