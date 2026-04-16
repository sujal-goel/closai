"""
Live cloud pricing service.
Fetches structured prices from provider APIs and stores normalized records.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

import httpx

from services.database import is_connected, skus_collection

logger = logging.getLogger(__name__)

USD_TO_INR = 83.0
CACHE_TTL_HOURS = 24


def _now_iso_date() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def _normalize_record(
    provider: str,
    service: str,
    region: str,
    instance_type: str,
    price_per_hour: float,
    currency: str = "INR",
) -> dict[str, Any]:
    return {
        "provider": provider,
        "service": service,
        "region": region,
        "instance_type": instance_type,
        "price_per_hour": round(float(price_per_hour), 6),
        "currency": currency,
        "last_updated": _now_iso_date(),
        "fetched_at": datetime.now(timezone.utc),
    }


async def _read_cached(provider: str, service: str, region: str, instance_type: str) -> dict[str, Any] | None:
    if not is_connected():
        return None
    try:
        cutoff = datetime.now(timezone.utc).timestamp() - (CACHE_TTL_HOURS * 3600)
        doc = await skus_collection().find_one(
            {
                "provider": provider,
                "service": service,
                "region": region,
                "instance_type": instance_type,
                "fetched_at": {"$gte": datetime.fromtimestamp(cutoff, tz=timezone.utc)},
            }
        )
        return doc
    except Exception as e:
        logger.warning(f"Failed to read cached pricing: {e}")
        return None


async def _write_cache(record: dict[str, Any]) -> None:
    if not is_connected():
        return
    try:
        await skus_collection().update_one(
            {
                "provider": record["provider"],
                "service": record["service"],
                "region": record["region"],
                "instance_type": record["instance_type"],
            },
            {"$set": record},
            upsert=True,
        )
    except Exception as e:
        logger.warning(f"Failed to cache pricing record: {e}")


def _aws_location_name(region: str) -> str:
    mapping = {
        "ap-south-1": "Asia Pacific (Mumbai)",
        "us-east-1": "US East (N. Virginia)",
        "us-west-2": "US West (Oregon)",
        "eu-west-1": "EU (Ireland)",
    }
    return mapping.get(region, "Asia Pacific (Mumbai)")


def _aws_fetch_price_sync(service: str, region: str, instance_type: str) -> float | None:
    try:
        import boto3

        service_code = {
            "EC2": "AmazonEC2",
            "RDS": "AmazonRDS",
            "S3": "AmazonS3",
        }.get(service, "AmazonEC2")

        client = boto3.client("pricing", region_name="us-east-1")
        filters = [
            {"Type": "TERM_MATCH", "Field": "location", "Value": _aws_location_name(region)},
        ]
        if service_code == "AmazonEC2":
            filters.extend(
                [
                    {"Type": "TERM_MATCH", "Field": "instanceType", "Value": instance_type},
                    {"Type": "TERM_MATCH", "Field": "operatingSystem", "Value": "Linux"},
                    {"Type": "TERM_MATCH", "Field": "capacitystatus", "Value": "Used"},
                    {"Type": "TERM_MATCH", "Field": "tenancy", "Value": "Shared"},
                    {"Type": "TERM_MATCH", "Field": "preInstalledSw", "Value": "NA"},
                ]
            )

        resp = client.get_products(ServiceCode=service_code, Filters=filters, MaxResults=10)
        for raw in resp.get("PriceList", []):
            import json

            data = json.loads(raw)
            terms = data.get("terms", {}).get("OnDemand", {})
            for _, term in terms.items():
                dimensions = term.get("priceDimensions", {})
                for _, dim in dimensions.items():
                    usd = dim.get("pricePerUnit", {}).get("USD")
                    if usd:
                        return float(usd) * USD_TO_INR
        return None
    except Exception as e:
        logger.warning(f"AWS pricing fetch failed: {e}")
        return None


async def _gcp_fetch_price(service: str, region: str, instance_type: str, api_key: str | None) -> float | None:
    if not api_key:
        return None

    service_hint = {
        "Compute Engine": "compute",
        "Cloud SQL": "sql",
        "Cloud Storage": "storage",
    }.get(service, "compute")

    base = "https://cloudbilling.googleapis.com/v1"
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            services_resp = await client.get(f"{base}/services", params={"key": api_key})
            services_resp.raise_for_status()
            services = services_resp.json().get("services", [])
            service_id = None
            for s in services:
                name = (s.get("displayName") or "").lower()
                if service_hint in name:
                    service_id = s.get("name", "").split("/")[-1]
                    break
            if not service_id:
                return None

            skus_resp = await client.get(
                f"{base}/services/{service_id}/skus",
                params={"currencyCode": "INR", "key": api_key, "pageSize": 200},
            )
            skus_resp.raise_for_status()
            skus = skus_resp.json().get("skus", [])

            best_price = None
            for sku in skus:
                desc = (sku.get("description") or "").lower()
                if "core" not in desc and "instance" not in desc and service_hint == "compute":
                    continue
                if region and not any(region in r for r in sku.get("serviceRegions", [])):
                    continue

                rates = sku.get("pricingInfo", [])
                if not rates:
                    continue
                expression = rates[0].get("pricingExpression", {})
                tiered = expression.get("tieredRates", [])
                if not tiered:
                    continue
                unit = tiered[0].get("unitPrice", {})
                units = float(unit.get("units", 0) or 0)
                nanos = float(unit.get("nanos", 0) or 0) / 1_000_000_000
                price = units + nanos
                if price <= 0:
                    continue
                if best_price is None or price < best_price:
                    best_price = price

            return best_price
        except Exception as e:
            logger.warning(f"GCP pricing fetch failed: {e}")
            return None


async def _azure_fetch_price(service: str, region: str, instance_type: str) -> float | None:
    service_name = {
        "Virtual Machines": "Virtual Machines",
        "Azure SQL": "SQL Database",
        "Blob Storage": "Storage",
    }.get(service, "Virtual Machines")

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            filt = f"serviceName eq '{service_name}' and armRegionName eq '{region}'"
            if instance_type:
                filt += f" and armSkuName eq '{instance_type}'"

            resp = await client.get(
                "https://prices.azure.com/api/retail/prices",
                params={"$filter": filt},
            )
            resp.raise_for_status()
            items = resp.json().get("Items", [])

            best_usd = None
            for item in items:
                price = item.get("retailPrice")
                if price is None:
                    continue
                price = float(price)
                if best_usd is None or price < best_usd:
                    best_usd = price

            if best_usd is None:
                return None
            return best_usd * USD_TO_INR
        except Exception as e:
            logger.warning(f"Azure pricing fetch failed: {e}")
            return None


async def fetch_live_price_record(
    provider: str,
    service: str,
    region: str,
    instance_type: str,
    gcp_api_key: str | None = None,
) -> dict[str, Any] | None:
    provider_upper = provider.upper()
    cached = await _read_cached(provider_upper, service, region, instance_type)
    if cached:
        return cached

    price_per_hour = None
    if provider_upper == "AWS":
        price_per_hour = await asyncio.to_thread(_aws_fetch_price_sync, service, region, instance_type)
    elif provider_upper == "GCP":
        price_per_hour = await _gcp_fetch_price(service, region, instance_type, gcp_api_key)
    elif provider_upper == "AZURE":
        price_per_hour = await _azure_fetch_price(service, region, instance_type)

    if price_per_hour is None:
        return None

    record = _normalize_record(
        provider=provider_upper,
        service=service,
        region=region,
        instance_type=instance_type,
        price_per_hour=price_per_hour,
        currency="INR",
    )
    await _write_cache(record)
    return record
