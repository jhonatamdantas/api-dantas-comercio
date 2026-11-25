from decimal import Decimal

import pytest
from sqlmodel import select

from app.models.cash import CashEntry, EntryType   # ajuste aos seus nomes
from app.models.sale import Sale, SaleStatus
from tests.helpers import money, sale_payload


def test_sale_with_client_updates_total_and_stock(api, session, employee_headers, product_a, maria):
    response = api.post(
        "/sales/",
        json=sale_payload((product_a.id, 3), client_id=maria.id),
        headers=employee_headers,
    )

    assert response.status_code == 201
    body = response.json()
    assert money(body["total"]) == Decimal("15.00")
    assert body["client_id"] == maria.id

    session.expire_all()  # força a sessão do teste a reler o banco
    assert product_a.stock == 7


def test_sale_with_two_products(api, session, employee_headers, product_a, product_b):
    response = api.post(
        "/sales/",
        json=sale_payload((product_a.id, 1), (product_b.id, 1)),
        headers=employee_headers,
    )

    assert response.status_code == 201
    assert money(response.json()["total"]) == Decimal("25.00")

    session.expire_all()
    assert product_a.stock == 9
    assert product_b.stock == 1


def test_sale_without_stock_keeps_everything_unchanged(api, session, employee_headers, product_a, product_b):
    # O produto A tem estoque, o B não: a venda inteira deve ser recusada
    response = api.post(
        "/sales/",
        json=sale_payload((product_a.id, 1), (product_b.id, 5)),
        headers=employee_headers,
    )

    assert response.status_code == 400

    session.expire_all()
    # Nenhum estoque mudou, nem o do A, que foi validado antes do erro
    assert product_a.stock == 10
    assert product_b.stock == 2
    # Nada foi gravado: nem venda, nem lançamento no caixa
    assert session.exec(select(Sale)).all() == []
    assert session.exec(select(CashEntry)).all() == []


def test_repeated_product_quantities_are_summed(api, session, employee_headers, product_a):
    response = api.post(
        "/sales/",
        json=sale_payload((product_a.id, 1), (product_a.id, 1)),
        headers=employee_headers,
    )

    assert response.status_code == 201
    body = response.json()
    assert len(body["items"]) == 1          # um único item, não dois
    assert body["items"][0]["quantity"] == 2
    assert money(body["total"]) == Decimal("10.00")

    session.expire_all()
    assert product_a.stock == 8


def test_sale_without_client_is_allowed(api, session, employee_headers, product_a):
    # Venda de balcão: sem client_id
    response = api.post(
        "/sales/",
        json=sale_payload((product_a.id, 1)),
        headers=employee_headers,
    )

    assert response.status_code == 201
    assert response.json()["client_id"] is None


def test_sale_with_unknown_client_returns_404(api, session, employee_headers, product_a):
    response = api.post(
        "/sales/",
        json=sale_payload((product_a.id, 1), client_id=999),
        headers=employee_headers,
    )

    assert response.status_code == 404
    session.expire_all()
    assert product_a.stock == 10


def test_sale_with_inactive_client_returns_400(api, session, employee_headers, product_a, maria):
    maria.active = False
    session.add(maria)
    session.commit()

    response = api.post(
        "/sales/",
        json=sale_payload((product_a.id, 1), client_id=maria.id),
        headers=employee_headers,
    )

    assert response.status_code == 400
    session.expire_all()
    assert product_a.stock == 10


@pytest.mark.parametrize(
    "items",
    [
        [],
        [{"product_id": 1, "quantity": 0}],
        [{"product_id": 1, "quantity": -2}],
    ],
    ids=["empty_items", "zero_quantity", "negative_quantity"],
)
def test_sale_validation_errors_return_422(api, employee_headers, items):
    response = api.post(
        "/sales/",
        json={"payment_method": "pix", "items": items},
        headers=employee_headers,
    )

    assert response.status_code == 422


def test_sale_with_unknown_product_returns_404(api, employee_headers):
    response = api.post(
        "/sales/",
        json=sale_payload((999, 1)),
        headers=employee_headers,
    )

    assert response.status_code == 404


def test_sale_with_inactive_product_returns_400(api, session, employee_headers, product_a):
    product_a.active = False
    session.add(product_a)
    session.commit()

    response = api.post(
        "/sales/",
        json=sale_payload((product_a.id, 1)),
        headers=employee_headers,
    )

    assert response.status_code == 400


def test_unit_price_is_frozen_after_price_change(api, session, employee_headers, product_a):
    created = api.post(
        "/sales/",
        json=sale_payload((product_a.id, 3)),
        headers=employee_headers,
    )
    sale_id = created.json()["id"]

    # Reajusta o preço do produto depois da venda
    patch = api.patch(f"/produtos/{product_a.id}", json={"price": 8.00}, headers=employee_headers)
    assert patch.status_code == 200

    # A venda antiga continua com o preço da época
    old_sale = api.get(f"/sales/{sale_id}", headers=employee_headers).json()
    assert money(old_sale["total"]) == Decimal("15.00")
    assert money(old_sale["items"][0]["unit_price"]) == Decimal("5.00")

    # Uma venda nova já usa o preço novo
    new_sale = api.post(
        "/sales/",
        json=sale_payload((product_a.id, 1)),
        headers=employee_headers,
    ).json()
    assert money(new_sale["items"][0]["unit_price"]) == Decimal("8.00")


def test_sale_creates_one_cash_inflow(api, session, employee_headers, product_a):
    api.post(
        "/sales/",
        json=sale_payload((product_a.id, 2)),
        headers=employee_headers,
    )

    entries = session.exec(select(CashEntry)).all()
    assert len(entries) == 1
    assert entries[0].type == EntryType.inflow
    assert money(entries[0].amount) == Decimal("10.00")
    assert entries[0].source == "venda"


def test_cancel_sale_returns_stock_and_creates_refund(api, session, employee_headers, product_a):
    created = api.post(
        "/sales/",
        json=sale_payload((product_a.id, 3)),
        headers=employee_headers,
    )
    sale_id = created.json()["id"]

    response = api.post(f"/sales/{sale_id}/cancel", headers=employee_headers)

    assert response.status_code == 200
    assert response.json()["status"] == SaleStatus.canceled.value

    session.expire_all()
    assert product_a.stock == 10  # o estoque voltou

    # O caixa tem a entrada original e uma saída que a compensa: nada foi apagado
    entries = session.exec(select(CashEntry).order_by(CashEntry.id)).all() #type:ignore
    assert [entry.type for entry in entries] == [EntryType.inflow, EntryType.outflow]
    assert money(entries[0].amount) == money(entries[1].amount) == Decimal("15.00")
    assert entries[1].source == "estorno_venda"


def test_cancel_sale_twice_returns_400(api, session, employee_headers, product_a):
    created = api.post(
        "/sales/",
        json=sale_payload((product_a.id, 3)),
        headers=employee_headers,
    )
    sale_id = created.json()["id"]

    api.post(f"/sales/{sale_id}/cancel", headers=employee_headers)
    second = api.post(f"/sales/{sale_id}/cancel", headers=employee_headers)

    assert second.status_code == 400
    session.expire_all()
    assert product_a.stock == 10  # não devolveu o estoque duas vezes


def test_cancel_unknown_sale_returns_404(api, employee_headers):
    response = api.post("/sales/999/cancel", headers=employee_headers)

    assert response.status_code == 404


def test_get_unknown_sale_returns_404(api, employee_headers):
    response = api.get("/sales/999", headers=employee_headers)

    assert response.status_code == 404