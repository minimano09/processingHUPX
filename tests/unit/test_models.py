import pytest
from processingHUPX.models import User, Request
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from processingHUPX import db

def test_new_user(client):
    user = User(username='teszt_model', email="teszt@model.hu", password="tesztuser", db_name="database_teszt_model")
    db.session.add(user)
    db.session.commit()
    assert user.id is not None

    saved = User.query.filter_by(username="teszt_model").first()
    assert saved.email == "teszt@model.hu"
    assert saved.is_admin == 2
    assert len(user.requests) == 0

def test_new_admin(client):
    admin = User(username="admin", email="admin@vagyok.hu", password="admin_vagyok", db_name="database_admin", is_admin=1)
    db.session.add(admin)
    db.session.commit()
    assert admin.is_admin == 1


def test_user_model(client):
   assert User.query.count() > 0

   admin = User.query.filter_by(username="admin").first()
   assert admin.email == "admin@vagyok.hu"
   assert admin.is_admin == 1
   assert admin.id == 2

def test_add_request(client):
    admin = User.query.filter_by(username="admin").first()
    req = Request(title="teszt_lekerdezes", img_name="teszt_img", owner=admin, table_name="admin_table", boxes="-1-2-3-", div_file="teszt_div", js_file="teszt_js")
    db.session.add(req)
    db.session.commit()

    assert req.id is not None
    assert req.date_requested.date() == datetime.utcnow().date()

def test_req_model(client):
    assert Request.query.count() > 0
    req = Request.query.filter_by(id=1).first()
    assert req.title == "teszt_lekerdezes"

def test_user_has_req(client):
    admin = User.query.filter_by(username="admin").first()
    assert admin.requests[0].title == "teszt_lekerdezes"

def test_missing_username(client):
    user = User(email="hianyzo@felhasznalonev.hu", password="hianyzo", db_name="database_hianyzo")
    with pytest.raises(IntegrityError):
        db.session.add(user)
        db.session.commit()

def test_missing_title(client):
    db.session.rollback()
    admin = User.query.filter_by(username="admin").first()
    req = Request(img_name="teszt_img", owner=admin, table_name="admin_table",
                  boxes="-1-2-3-", div_file="teszt_div", js_file="teszt_js")
    with pytest.raises(IntegrityError):
        db.session.add(req)
        db.session.commit()

def test_unique_username(client):
    db.session.rollback()
    with pytest.raises(IntegrityError):
        user_not_unique = User(username='teszt_model', email="not@unique.hu", password="tesztuser", db_name="database_teszt_model")
        db.session.add(user_not_unique)
        db.session.commit()