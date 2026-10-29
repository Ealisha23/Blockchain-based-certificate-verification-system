"""API tests. Need a database (BCV_test_db or BCV_DATABASE_URL) and a Hardhat
node with the contract deployed (see README)."""
import uuid

BASE = "/api/v1"


def _email():
    return "{}@example.com".format(uuid.uuid4().hex[:10])


def _auth(token):
    return {"Authorization": "Bearer " + token}


def _signup_login(client, path, body):
    r = client.post(BASE + path, json=body)
    assert r.status_code == 201, r.get_data(as_text=True)
    obj = r.get_json()
    t = client.post(BASE + "/login", json={"userMail": body["email"],
                                           "password": body["password"]})
    return obj, t.get_json()["token"]


def _admin_token(client):
    from app.models.admin import Admin
    email = _email()
    Admin(email=email, username="root", password="adminpass123",
          is_superadmin=True).save()
    r = client.post(BASE + "/login-admin",
                    json={"userMail": email, "password": "adminpass123"})
    assert r.status_code == 200
    return r.get_json()["token"]


def test_status(client):
    assert client.get(BASE + "/status").get_json() == {"status": "OK"}


def test_unknown_route_404_json(client):
    r = client.get(BASE + "/nope")
    assert r.status_code == 404 and "error" in r.get_json()


def test_protected_routes_need_token(client):
    for method, path in [("get", "/users"), ("get", "/schools"),
                         ("get", "/stats"), ("get", "/admins"),
                         ("get", "/certificate"), ("post", "/admins"),
                         ("post", "/pdf-data")]:
        assert getattr(client, method)(BASE + path).status_code == 401, path


def test_signup_validation_and_duplicates(client):
    assert client.post(BASE + "/users", json={"password": "x"}).status_code == 400
    assert client.post(BASE + "/users", json={"email": _email()}).status_code == 400
    email = _email()
    assert client.post(BASE + "/users", json={"email": email, "password": "pw12345678"}).status_code == 201
    assert client.post(BASE + "/users", json={"email": email, "password": "pw12345678"}).status_code == 409
    # same email may not be re-used as a school
    assert client.post(BASE + "/schools", json={"email": email, "password": "pw12345678"}).status_code == 409


def test_login(client):
    email = _email()
    client.post(BASE + "/users", json={"email": email, "password": "S3cret!pw", "first_name": "Ada"})
    ok = client.post(BASE + "/login", json={"userMail": email, "password": "S3cret!pw"})
    assert ok.status_code == 200 and "token" in ok.get_json()
    assert client.post(BASE + "/login", json={"userMail": email, "password": "bad"}).status_code == 401
    assert client.post(BASE + "/login", json={"userMail": email}).status_code == 400
    assert client.post(BASE + "/login", data="nonsense").status_code == 400


def test_no_privilege_escalation(client):
    user, token = _signup_login(client, "/users", {"email": _email(), "password": "pw12345678", "role": "admin"})
    assert user["role"] == "user"
    r = client.put(BASE + "/users/" + user["id"], json={"role": "admin"}, headers=_auth(token))
    assert r.status_code == 200 and r.get_json()["role"] == "user"
    assert client.post(BASE + "/admins", json={"email": _email(), "password": "pw12345678"},
                       headers=_auth(token)).status_code == 403


def test_users_cannot_touch_each_other(client):
    a, ta = _signup_login(client, "/users", {"email": _email(), "password": "pw12345678"})
    b, tb = _signup_login(client, "/users", {"email": _email(), "password": "pw12345678"})
    assert client.get(BASE + "/users/" + b["id"], headers=_auth(ta)).status_code == 403
    assert client.delete(BASE + "/users/" + b["id"], headers=_auth(ta)).status_code == 403
    assert client.put(BASE + "/users/" + b["id"], json={"first_name": "x"}, headers=_auth(ta)).status_code == 403
    assert client.get(BASE + "/users", headers=_auth(ta)).status_code == 403


def test_admin_flow(client):
    token = _admin_token(client)
    assert client.get(BASE + "/stats", headers=_auth(token)).status_code == 200
    r = client.post(BASE + "/admins", json={"email": _email(), "password": "pw12345678", "username": "n"},
                    headers=_auth(token))
    assert r.status_code == 201 and "password" not in r.get_json()


def test_pdf_data_blocks_ssrf(client):
    _, token = _signup_login(client, "/users", {"email": _email(), "password": "pw12345678"})
    for url in ["http://169.254.169.254/latest", "https://localhost/x.pdf", "file:///etc/passwd", None]:
        r = client.post(BASE + "/pdf-data", json={"pdfURL": url}, headers=_auth(token))
        assert r.status_code == 400, url


def test_full_certificate_flow(client):
    user, utoken = _signup_login(client, "/users", {"email": _email(), "password": "pw12345678"})
    school, stoken = _signup_login(client, "/schools", {"email": _email(), "password": "pw12345678",
                                                        "school_name": "Hardhat University",
                                                        "school_location": "Localhost"})
    body = {"student_name": "Ada Lovelace", "student_email": "ada@example.com",
            "school_id": school["id"], "school_name": "Hardhat University",
            "school_major": "Mathematics", "school_department": "Science",
            "school_location": "Localhost", "completion_data": "2023-05-01"}
    r = client.post("{}/users/{}/certificates".format(BASE, user["id"]), json=body, headers=_auth(utoken))
    assert r.status_code == 201, r.get_data(as_text=True)
    cert = r.get_json()
    assert cert["certificate_status"] == "unverified"

    # student asks for verification
    r = client.post("{}/certificate/{}/request/verify".format(BASE, cert["id"]), json={}, headers=_auth(utoken))
    assert r.status_code == 201 and r.get_json()["certificate_status"] == "pending"

    # the student cannot write to the chain, the school can
    assert client.post(BASE + "/add-certificate/" + cert["id"], json={}, headers=_auth(utoken)).status_code == 403
    r = client.post(BASE + "/add-certificate/" + cert["id"], json={}, headers=_auth(stoken))
    assert r.status_code == 200, r.get_data(as_text=True)
    h = r.get_json()["certificate_data"]["certificate_hash"]
    assert len(h) == 64
    # cannot add twice
    assert client.post(BASE + "/add-certificate/" + cert["id"], json={}, headers=_auth(stoken)).status_code == 409

    # public verification lookup (no token)
    r = client.get("{}/get-certificate/{}".format(BASE, h))
    assert r.get_json()["certificate_data"]["student_name"] == "Ada Lovelace"
    assert r.get_json()["certificate_data"]["certificate_verify"] is False
    assert client.get(BASE + "/get-certificate/" + "00" * 32).status_code == 404

    # another school may not verify it
    _, other = _signup_login(client, "/schools", {"email": _email(), "password": "pw12345678"})
    assert client.put("{}/verify-certificate/{}".format(BASE, h), json={}, headers=_auth(other)).status_code == 403

    r = client.put("{}/verify-certificate/{}".format(BASE, h), json={}, headers=_auth(stoken))
    assert r.status_code == 200, r.get_data(as_text=True)
    assert client.get("{}/get-certificate/{}".format(BASE, h)).get_json()["certificate_data"]["certificate_verify"] is True
    assert client.put("{}/verify-certificate/{}".format(BASE, h), json={}, headers=_auth(stoken)).status_code == 400

    r = client.get("{}/users/{}/certificate".format(BASE, user["id"]), headers=_auth(utoken))
    assert r.get_json()[0]["certificate_status"] == "verified"
    assert client.delete("{}/users/{}/certificates/{}".format(BASE, user["id"], cert["id"]),
                         headers=_auth(utoken)).status_code == 200
