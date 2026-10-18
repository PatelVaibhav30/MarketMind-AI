def create_test_stock(client):
    return client.post(
        "/stocks",
        json={
            "symbol": "RELIANCE",
            "company_name": "Reliance Industries Limited",
            "exchange": "NSE",
        },
    )


def test_create_stock(client):
    response = create_test_stock(client)

    assert response.status_code == 201

    data = response.json()

    assert data["symbol"] == "RELIANCE"
    assert data["company_name"] == "Reliance Industries Limited"
    assert data["exchange"] == "NSE"
    assert data["is_active"] is True


def test_get_stocks(client):
    create_test_stock(client)

    response = client.get("/stocks")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["symbol"] == "RELIANCE"


def test_get_existing_stock(client):
    create_test_stock(client)

    response = client.get("/stocks/RELIANCE")

    assert response.status_code == 200

    data = response.json()

    assert data["symbol"] == "RELIANCE"


def test_get_missing_stock(client):
    response = client.get("/stocks/INVALID")

    assert response.status_code == 404


def test_duplicate_stock(client):
    create_test_stock(client)

    response = create_test_stock(client)

    assert response.status_code == 409


def test_invalid_stock(client):
    response = client.post(
        "/stocks",
        json={
            "symbol": "",
            "company_name": "",
            "exchange": "",
        },
    )

    assert response.status_code == 422