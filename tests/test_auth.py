from sqlmodel import select

from app.models.user import User, Role


def test_login_success(api, owner_headers):
    # A fixture owner_headers cria o usuário dono@teste.com com a senha "senha1234"
    response = api.post(
        "/auth/login",
        data={"username": "dono@teste.com", "password": "senha1234"},  # formulário, não json
    )

    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


def test_login_wrong_password(api, owner_headers):
    response = api.post(
        "/auth/login",
        data={"username": "dono@teste.com", "password": "senha-errada"},
    )

    assert response.status_code == 401


def test_login_same_error_for_wrong_password_and_unknown_email(api, owner_headers):
    wrong_password = api.post(
        "/auth/login",
        data={"username": "dono@teste.com", "password": "senha-errada"},
    )
    unknown_email = api.post(
        "/auth/login",
        data={"username": "naoexiste@teste.com", "password": "qualquer123"},
    )

    # Mesma resposta nos dois casos: não revela quais e-mails existem
    assert wrong_password.status_code == unknown_email.status_code == 401
    assert wrong_password.json() == unknown_email.json()


def test_protected_route_without_token(api):
    response = api.get("/clientes/")

    assert response.status_code == 401


def test_employee_cannot_access_cash(api, employee_headers):
    response = api.get("/cash/balance", headers=employee_headers)

    assert response.status_code == 403


def test_owner_can_access_cash(api, owner_headers):
    # Controle: prova que o 403 acima vem do papel, e não de outro erro
    response = api.get("/cash/balance", headers=owner_headers)

    assert response.status_code == 200


def test_inactive_user_token_is_rejected(api, session, employee_headers):
    # Controle: antes de desativar, o token funciona
    assert api.get("/sales/", headers=employee_headers).status_code == 200

    # Só existe um funcionário no banco, então busco pelo papel
    user = session.exec(select(User).where(User.role == Role.employee)).first()
    assert user is not None
    user.active = False
    session.add(user)
    session.commit()

    response = api.get("/sales/", headers=employee_headers)

    assert response.status_code == 401