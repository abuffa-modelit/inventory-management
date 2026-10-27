"""
Tests for restocking API endpoints.
"""
from datetime import datetime, timedelta

import pytest

import main


@pytest.fixture(autouse=True)
def clear_submitted_orders():
    """Submitted orders are module-level state, so reset them around each test."""
    main.submitted_orders.clear()
    yield
    main.submitted_orders.clear()


class TestRestockRecommendations:
    """Test suite for restocking recommendation endpoint."""

    def test_get_recommendations_structure(self, client):
        """Test that recommendations have the expected structure."""
        response = client.get("/api/restocking/recommendations?budget=5000")
        assert response.status_code == 200

        data = response.json()
        for field in ["budget", "total_cost", "remaining", "max_useful_budget", "items"]:
            assert field in data
        assert isinstance(data["items"], list)
        assert len(data["items"]) > 0

        for item in data["items"]:
            for field in ["sku", "name", "quantity", "unit_cost", "line_total",
                          "lead_time_days", "trend", "priority_rank"]:
                assert field in item
            assert isinstance(item["quantity"], int)
            assert item["quantity"] >= 1
            assert abs(item["line_total"] - item["quantity"] * item["unit_cost"]) < 0.01

    def test_zero_budget_returns_no_items(self, client):
        """Test that a zero budget recommends nothing."""
        response = client.get("/api/restocking/recommendations?budget=0")
        assert response.status_code == 200

        data = response.json()
        assert data["items"] == []
        assert data["total_cost"] == 0

    def test_negative_budget_rejected(self, client):
        """Test that a negative budget fails validation."""
        response = client.get("/api/restocking/recommendations?budget=-100")
        assert response.status_code == 422

    @pytest.mark.parametrize("budget", [1, 100, 2500, 10000, 30000, 52000])
    def test_total_never_exceeds_budget(self, client, budget):
        """Test that recommended totals stay within the budget."""
        data = client.get(f"/api/restocking/recommendations?budget={budget}").json()

        assert data["total_cost"] <= budget
        assert abs(data["total_cost"] + data["remaining"] - budget) < 0.01
        assert abs(sum(i["line_total"] for i in data["items"]) - data["total_cost"]) < 0.01

    def test_large_budget_includes_all_non_decreasing_items(self, client):
        """Test that an unlimited budget recommends every non-decreasing item at full quantity."""
        demand = client.get("/api/demand").json()
        expected = {f["item_sku"]: f["forecasted_demand"] for f in demand if f["trend"] != "decreasing"}

        data = client.get("/api/restocking/recommendations?budget=1000000").json()
        recommended = {i["sku"]: i["quantity"] for i in data["items"]}

        assert recommended == expected
        assert abs(data["total_cost"] - data["max_useful_budget"]) < 0.01

    def test_decreasing_items_never_recommended(self, client):
        """Test that items with decreasing demand are excluded."""
        data = client.get("/api/restocking/recommendations?budget=1000000").json()

        for item in data["items"]:
            assert item["trend"] != "decreasing"

    def test_increasing_items_prioritized_over_stable(self, client):
        """Test that increasing-demand items rank ahead of stable ones."""
        data = client.get("/api/restocking/recommendations?budget=1000000").json()
        trends = [i["trend"] for i in sorted(data["items"], key=lambda i: i["priority_rank"])]

        last_increasing = max(idx for idx, t in enumerate(trends) if t == "increasing")
        first_stable = min(idx for idx, t in enumerate(trends) if t == "stable")
        assert last_increasing < first_stable

    def test_partial_fill_when_budget_runs_out(self, client):
        """Test that the top item is partially filled when it doesn't fully fit."""
        full = client.get("/api/restocking/recommendations?budget=1000000").json()
        top = min(full["items"], key=lambda i: i["priority_rank"])
        top_full_cost = top["quantity"] * top["unit_cost"]

        budget = top_full_cost / 2
        data = client.get(f"/api/restocking/recommendations?budget={budget}").json()
        top_partial = next(i for i in data["items"] if i["sku"] == top["sku"])

        assert 0 < top_partial["quantity"] < top["quantity"]
        assert top_partial["quantity"] == int(budget // top["unit_cost"])


class TestRestockOrders:
    """Test suite for restocking order endpoints."""

    def test_get_orders_initially_empty(self, client):
        """Test that no restock orders exist before any are submitted."""
        response = client.get("/api/restocking/orders")
        assert response.status_code == 200
        assert response.json() == []

    def test_create_order(self, client):
        """Test submitting a restock order."""
        payload = {
            "budget": 5000,
            "items": [{"sku": "FLT-405", "quantity": 100}, {"sku": "VLV-506", "quantity": 2}]
        }
        response = client.post("/api/restocking/orders", json=payload)
        assert response.status_code == 201

        order = response.json()
        assert order["order_number"] == "RST-0001"
        assert order["status"] == "Submitted"
        assert len(order["items"]) == 2
        assert abs(order["total_value"] - (100 * 8.95 + 2 * 67.40)) < 0.01

    def test_order_lead_time_is_slowest_item(self, client):
        """Test that order lead time is the max item lead time and drives expected delivery."""
        demand = {f["item_sku"]: f for f in client.get("/api/demand").json()}
        skus = ["FLT-405", "VLV-506", "WDG-001"]
        payload = {"budget": 100000, "items": [{"sku": s, "quantity": 1} for s in skus]}

        order = client.post("/api/restocking/orders", json=payload).json()

        expected_lead = max(demand[s]["lead_time_days"] for s in skus)
        assert order["lead_time_days"] == expected_lead

        submitted = datetime.fromisoformat(order["submitted_date"])
        expected_delivery = datetime.fromisoformat(order["expected_delivery"])
        assert expected_delivery - submitted == timedelta(days=expected_lead)

    def test_order_uses_server_prices(self, client):
        """Test that line prices come from forecast data."""
        demand = {f["item_sku"]: f for f in client.get("/api/demand").json()}
        payload = {"budget": 100000, "items": [{"sku": "MTR-304", "quantity": 3}]}

        order = client.post("/api/restocking/orders", json=payload).json()

        assert order["items"][0]["unit_cost"] == demand["MTR-304"]["unit_cost"]

    def test_recommendations_can_be_submitted(self, client):
        """Test that a recommendation set submits within its own budget."""
        rec = client.get("/api/restocking/recommendations?budget=7500").json()
        payload = {
            "budget": rec["budget"],
            "items": [{"sku": i["sku"], "quantity": i["quantity"]} for i in rec["items"]]
        }

        response = client.post("/api/restocking/orders", json=payload)
        assert response.status_code == 201
        assert abs(response.json()["total_value"] - rec["total_cost"]) < 0.01

    def test_create_order_over_budget(self, client):
        """Test that orders exceeding the budget are rejected."""
        payload = {"budget": 10, "items": [{"sku": "FLT-405", "quantity": 100}]}
        response = client.post("/api/restocking/orders", json=payload)
        assert response.status_code == 400
        assert "budget" in response.json()["detail"].lower()

    def test_create_order_unknown_sku(self, client):
        """Test that unknown SKUs are rejected."""
        payload = {"budget": 1000, "items": [{"sku": "NOPE-999", "quantity": 1}]}
        response = client.post("/api/restocking/orders", json=payload)
        assert response.status_code == 400
        assert "NOPE-999" in response.json()["detail"]

    def test_create_order_empty_items(self, client):
        """Test that empty orders are rejected."""
        response = client.post("/api/restocking/orders", json={"budget": 1000, "items": []})
        assert response.status_code == 400

    def test_create_order_non_positive_quantity(self, client):
        """Test that zero quantities are rejected."""
        payload = {"budget": 1000, "items": [{"sku": "FLT-405", "quantity": 0}]}
        response = client.post("/api/restocking/orders", json=payload)
        assert response.status_code == 400

    def test_submitted_orders_listed_newest_first(self, client):
        """Test that submitted orders appear in the list, newest first."""
        for qty in (1, 2):
            client.post("/api/restocking/orders",
                        json={"budget": 1000, "items": [{"sku": "FLT-405", "quantity": qty}]})

        orders = client.get("/api/restocking/orders").json()
        assert [o["order_number"] for o in orders] == ["RST-0002", "RST-0001"]
