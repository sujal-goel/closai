import pytest

from services import live_pricing_service as lps


REQUIRED_KEYS = {
    "provider",
    "service",
    "region",
    "instance_type",
    "price_per_hour",
    "currency",
    "last_updated",
}


def test_normalize_record_has_required_schema():
    record = lps._normalize_record(
        provider="AWS",
        service="EC2",
        region="ap-south-1",
        instance_type="t3.micro",
        price_per_hour=3.14,
        currency="INR",
    )

    assert REQUIRED_KEYS.issubset(record.keys())
    assert record["provider"] == "AWS"
    assert record["service"] == "EC2"
    assert record["region"] == "ap-south-1"
    assert record["instance_type"] == "t3.micro"
    assert isinstance(record["price_per_hour"], float)
    assert record["currency"] == "INR"


@pytest.mark.asyncio
async def test_fetch_live_price_record_prefers_cache(monkeypatch):
    cached = {
        "provider": "AZURE",
        "service": "Virtual Machines",
        "region": "eastus",
        "instance_type": "Standard_B1s",
        "price_per_hour": 0.86,
        "currency": "INR",
        "last_updated": "2026-04-16",
    }

    async def fake_read_cached(provider, service, region, instance_type):
        return cached

    async def fake_azure_fetch_price(service, region, instance_type):
        raise AssertionError("Provider API should not be called when cache hit exists")

    async def fake_write_cache(record):
        raise AssertionError("Cache should not be written on cache hit")

    monkeypatch.setattr(lps, "_read_cached", fake_read_cached)
    monkeypatch.setattr(lps, "_azure_fetch_price", fake_azure_fetch_price)
    monkeypatch.setattr(lps, "_write_cache", fake_write_cache)

    result = await lps.fetch_live_price_record(
        provider="AZURE",
        service="Virtual Machines",
        region="eastus",
        instance_type="Standard_B1s",
    )

    assert result == cached
    assert REQUIRED_KEYS.issubset(result.keys())


@pytest.mark.asyncio
async def test_fetch_live_price_record_azure_returns_normalized_record(monkeypatch):
    writes = []

    async def fake_read_cached(provider, service, region, instance_type):
        return None

    async def fake_azure_fetch_price(service, region, instance_type):
        return 1.234567

    async def fake_write_cache(record):
        writes.append(record)

    monkeypatch.setattr(lps, "_read_cached", fake_read_cached)
    monkeypatch.setattr(lps, "_azure_fetch_price", fake_azure_fetch_price)
    monkeypatch.setattr(lps, "_write_cache", fake_write_cache)

    result = await lps.fetch_live_price_record(
        provider="AZURE",
        service="Virtual Machines",
        region="eastus",
        instance_type="Standard_B1s",
    )

    assert result is not None
    assert REQUIRED_KEYS.issubset(result.keys())
    assert result["provider"] == "AZURE"
    assert result["service"] == "Virtual Machines"
    assert result["region"] == "eastus"
    assert result["instance_type"] == "Standard_B1s"
    assert result["currency"] == "INR"

    # Stored value is normalized/rounded by the service layer.
    assert result["price_per_hour"] == pytest.approx(1.234567)
    assert len(writes) == 1
