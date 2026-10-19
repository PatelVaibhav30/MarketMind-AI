from datetime import datetime, timedelta, timezone



def create_test_stock(client):
    response = client.post(
        "/stocks",
        json={
            "symbol": "RELIANCE",
            "company_name": "Reliance Industries Limited",
            "exchange": "NSE",
        },
    )
    assert response.status_code == 201
    return response.json()


def price_payload(stock_id, timestamp=None, close="1423.80"):
    if timestamp is None:
        timestamp = datetime(
            2026, 10, 1, 9, 15, tzinfo=timezone.utc
        )
    elif isinstance(timestamp, str):
        timestamp = datetime.fromisoformat(timestamp)

    return {
        "stock_id": stock_id,
        "timestamp": timestamp.isoformat(),
        "open": "1420.50",
        "high": "1425.75",
        "low": "1418.25",
        "close": close,
        "volume": 1250000,
    }


def test_create_market_price(client):
    stock = create_test_stock(client)

    response = client.post(
        "/market-prices",
        json=price_payload(stock["id"]),
    )

    assert response.status_code == 201
    assert response.json()["stock_id"] == stock["id"]
    assert response.json()["close"] == "1423.800000"


def test_create_market_price_for_missing_stock(client):
    response = client.post(
        "/market-prices",
        json=price_payload(999999),
    )

    assert response.status_code == 409


def test_create_duplicate_market_price(client):
    stock = create_test_stock(client)
    payload = price_payload(stock["id"])

    first_response = client.post("/market-prices", json=payload)
    second_response = client.post("/market-prices", json=payload)

    assert first_response.status_code == 201
    assert second_response.status_code == 409


def test_create_market_price_rejects_invalid_ohlc(client):
    stock = create_test_stock(client)
    payload = price_payload(stock["id"])
    payload["close"] = "1500"

    response = client.post("/market-prices", json=payload)

    assert response.status_code == 422


def test_create_market_prices_bulk(client):
    stock = create_test_stock(client)
    timestamp = datetime(2026, 10, 1, 9, 15, tzinfo=timezone.utc)

    second_price = price_payload(
        stock["id"],
        timestamp + timedelta(minutes=1),
        close="1426.00",
    )
    second_price["high"] = "1427.00"

    payload = [
        price_payload(stock["id"], timestamp),
        second_price,
    ]

    response = client.post("/market-prices/bulk", json=payload)

    print("BULK STATUS:", response.status_code)
    print("BULK BODY:", response.text)

    assert response.status_code == 201
    assert len(response.json()) == 2


def test_get_market_prices(client):
    stock = create_test_stock(client)
    client.post("/market-prices", json=price_payload(stock["id"]))

    response = client.get(f"/market-prices/{stock['id']}")

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_get_latest_market_price(client):
    stock = create_test_stock(client)
    timestamp = datetime(2026, 10, 1, 9, 15, tzinfo=timezone.utc)

    first_response = client.post(
        "/market-prices",
        json=price_payload(stock["id"], timestamp),
    )
    print("FIRST POST:", first_response.status_code, first_response.text)

    second_payload = price_payload(
        stock["id"],
        timestamp + timedelta(minutes=1),
        close="1426.00",
    )
    second_payload["high"] = "1427.00"

    second_response = client.post(
        "/market-prices",
        json=second_payload,
    )
    print("SECOND POST:", second_response.status_code, second_response.text)

    response = client.get(f"/market-prices/{stock['id']}/latest")
    print("LATEST RESPONSE:", response.status_code, response.text)

    assert response.status_code == 200
    assert response.json()["close"] == "1426.000000"


def test_get_latest_market_price_when_empty(client):
    stock = create_test_stock(client)

    response = client.get(f"/market-prices/{stock['id']}/latest")

    assert response.status_code == 404


def test_get_market_prices_in_range(client):
    stock = create_test_stock(client)
    timestamp = datetime(2026, 10, 1, 9, 15, tzinfo=timezone.utc)

    client.post(
        "/market-prices",
        json=price_payload(stock["id"], timestamp),
    )
    client.post(
        "/market-prices",
        json=price_payload(
            stock["id"],
            timestamp + timedelta(minutes=1),
        ),
    )

    start_time = timestamp.isoformat()
    end_time = (timestamp + timedelta(minutes=1)).isoformat()

    response = client.get(
        f"/market-prices/{stock['id']}/range",
        params={
            "start_time": start_time,
            "end_time": end_time,
        },
    )

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_get_market_prices_in_range_rejects_naive_datetime(client):
    stock = create_test_stock(client)

    response = client.get(
        f"/market-prices/{stock['id']}/range",
        params={
            "start_time": "2026-10-01T09:15:00",
            "end_time": "2026-10-01T10:15:00+00:00",
        },
    )

    assert response.status_code == 422

def test_get_market_prices_returns_404_for_nonexistent_stock(client):
    response = client.get("/market-prices/999999")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_get_latest_price_returns_404_for_nonexistent_stock(client):
    response = client.get("/market-prices/999999/latest")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_get_market_prices_range_returns_404_for_nonexistent_stock(client):
    response = client.get(
        "/market-prices/999999/range",
        params={
            "start_time": "2026-10-01T09:15:00+00:00",
            "end_time": "2026-10-01T15:30:00+00:00",
        },
    )

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_bulk_market_price_insert_rolls_back_on_duplicate_timestamp(client):
    stock = create_test_stock(client)

    first_price = price_payload(
        stock["id"],
        timestamp="2026-10-01T09:15:00+00:00",
    )

    duplicate_price = price_payload(
        stock["id"],
        timestamp="2026-10-01T09:15:00+00:00",
        close="1424.00",
    )

    response = client.post(
        "/market-prices/bulk",
        json=[first_price, duplicate_price],
    )
    print("STATUS:", response.status_code)
    print("BODY:", response.text)
    assert response.status_code == 409

    prices_response = client.get(
        f"/market-prices/{stock['id']}"
    )

    assert prices_response.status_code == 200
    assert prices_response.json() == []