import json
import math
import re
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence


DECISION_DIMENSIONS = [
    "cost",
    "performance",
    "operations",
    "reliability",
    "scalability",
    "security",
    "portability",
]

DEFAULT_PROVIDER_FILTER = ["AWS", "Azure", "GCP", "DigitalOcean"]


@dataclass
class ParsedRequirements:
    workload_type: str
    throughput_rps: float
    latency_ms: float
    availability_pct: float
    budget_inr: Optional[float]
    storage_gib: float
    region: Optional[str]
    compliance: List[str] = field(default_factory=list)
    tech_stack: Optional[str] = None
    gpu_required: bool = False
    hints: List[str] = field(default_factory=list)


@dataclass
class CandidateOption:
    id: str
    provider: str
    archetype: str
    name: str
    services: List[str]
    regions: List[str]
    supported_compliance: List[str]
    gpu_capable: bool
    estimated_monthly_cost: float
    estimated_monthly_cost_inr: float
    estimated_latency_ms: float
    estimated_throughput_rps: float
    estimated_availability_pct: float
    dimension_scores: Dict[str, float]
    gap_penalties: Dict[str, float]
    weighted_score: float
    final_score: float
    eliminated: bool = False
    elimination_reason: Optional[str] = None
    summary: str = ""
    tradeoffs: List[str] = field(default_factory=list)
    rationale: List[str] = field(default_factory=list)
    market_signal: Dict[str, Any] = field(default_factory=dict)


PROVIDER_PROFILES: Dict[str, Dict[str, Any]] = {
    "AWS": {
        "cost_factor": 1.04,
        "reliability": 0.96,
        "security": 0.94,
        "portability": 0.64,
        "throughput_factor": 1.14,
        "latency_factor": 0.94,
        "ops_factor": 0.88,
        "scalability_factor": 0.95,
        "compliance": ["SOC 2", "ISO 27001", "HIPAA", "PCI DSS", "GDPR"],
        "regions": ["us-east-1", "us-west-2", "eu-west-1", "ap-southeast-1", "global"],
    },
    "Azure": {
        "cost_factor": 1.01,
        "reliability": 0.955,
        "security": 0.95,
        "portability": 0.62,
        "throughput_factor": 1.1,
        "latency_factor": 0.95,
        "ops_factor": 0.86,
        "scalability_factor": 0.93,
        "compliance": ["SOC 2", "ISO 27001", "HIPAA", "PCI DSS", "GDPR"],
        "regions": ["eastus", "westus2", "westeurope", "southeastasia", "global"],
    },
    "GCP": {
        "cost_factor": 0.98,
        "reliability": 0.952,
        "security": 0.93,
        "portability": 0.66,
        "throughput_factor": 1.16,
        "latency_factor": 0.93,
        "ops_factor": 0.84,
        "scalability_factor": 0.96,
        "compliance": ["SOC 2", "ISO 27001", "HIPAA", "PCI DSS", "GDPR"],
        "regions": ["us-central1", "us-east1", "europe-west1", "asia-southeast1", "global"],
    },
    "DigitalOcean": {
        "cost_factor": 0.82,
        "reliability": 0.91,
        "security": 0.84,
        "portability": 0.78,
        "throughput_factor": 0.9,
        "latency_factor": 1.0,
        "ops_factor": 0.7,
        "scalability_factor": 0.78,
        "compliance": ["SOC 2", "GDPR"],
        "regions": ["nyc1", "sfo3", "ams3", "sgp1"],
    },
}


ARCHETYPES: Dict[str, Dict[str, Any]] = {
    "serverless": {
        "label": "Serverless PaaS",
        "services": {
            "AWS": ["Lambda", "API Gateway", "DynamoDB", "SQS"],
            "Azure": ["Azure Functions", "API Management", "Cosmos DB", "Service Bus"],
            "GCP": ["Cloud Functions", "API Gateway", "Firestore", "Pub/Sub"],
            "DigitalOcean": ["App Platform", "Managed Databases", "Spaces", "Queues"],
        },
        "cost_multiplier": 0.92,
        "performance_multiplier": 0.94,
        "operations_multiplier": 0.98,
        "reliability_multiplier": 0.97,
        "scalability_multiplier": 1.06,
        "security_multiplier": 1.0,
        "portability_multiplier": 0.62,
        "latency_multiplier": 1.04,
        "gpu_capable": False,
    },
    "managed": {
        "label": "Managed Containers",
        "services": {
            "AWS": ["ECS Fargate", "ALB", "RDS", "ElastiCache"],
            "Azure": ["Container Apps", "Application Gateway", "Azure SQL", "Azure Cache"],
            "GCP": ["Cloud Run", "Cloud Load Balancing", "Cloud SQL", "Memorystore"],
            "DigitalOcean": ["App Platform", "Load Balancer", "Managed PostgreSQL", "Managed Redis"],
        },
        "cost_multiplier": 1.0,
        "performance_multiplier": 1.03,
        "operations_multiplier": 0.78,
        "reliability_multiplier": 1.0,
        "scalability_multiplier": 0.94,
        "security_multiplier": 1.02,
        "portability_multiplier": 0.74,
        "latency_multiplier": 0.93,
        "gpu_capable": False,
    },
    "vm": {
        "label": "VM-based",
        "services": {
            "AWS": ["EC2 Auto Scaling", "ALB", "RDS", "EBS"],
            "Azure": ["Virtual Machine Scale Sets", "Application Gateway", "Azure SQL", "Managed Disks"],
            "GCP": ["Compute Engine MIG", "Cloud Load Balancing", "Cloud SQL", "Persistent Disk"],
            "DigitalOcean": ["Droplets", "Load Balancer", "Managed PostgreSQL", "Block Storage"],
        },
        "cost_multiplier": 1.1,
        "performance_multiplier": 1.06,
        "operations_multiplier": 0.56,
        "reliability_multiplier": 0.93,
        "scalability_multiplier": 0.8,
        "security_multiplier": 0.96,
        "portability_multiplier": 0.91,
        "latency_multiplier": 0.88,
        "gpu_capable": False,
    },
    "gpu": {
        "label": "GPU-capable",
        "services": {
            "AWS": ["EC2 GPU", "ALB", "RDS", "EBS"],
            "Azure": ["GPU VM", "Application Gateway", "Azure SQL", "Managed Disks"],
            "GCP": ["GPU Compute Engine", "Cloud Load Balancing", "Cloud SQL", "Persistent Disk"],
            "DigitalOcean": ["GPU Droplet", "Load Balancer", "Managed PostgreSQL", "Block Storage"],
        },
        "cost_multiplier": 1.48,
        "performance_multiplier": 1.24,
        "operations_multiplier": 0.5,
        "reliability_multiplier": 0.88,
        "scalability_multiplier": 0.72,
        "security_multiplier": 0.94,
        "portability_multiplier": 0.84,
        "latency_multiplier": 0.82,
        "gpu_capable": True,
    },
}


SERVICE_KEYWORD_MAP: Dict[str, List[str]] = {
    "Lambda": ["lambda"],
    "API Gateway": ["api gateway"],
    "DynamoDB": ["dynamodb"],
    "SQS": ["sqs"],
    "Azure Functions": ["azure functions", "functions"],
    "API Management": ["api management"],
    "Cosmos DB": ["cosmos db"],
    "Service Bus": ["service bus"],
    "Cloud Functions": ["cloud functions"],
    "Firestore": ["firestore"],
    "Pub/Sub": ["pubsub", "pub/sub"],
    "App Platform": ["app platform"],
    "Managed Databases": ["managed database"],
    "Spaces": ["spaces"],
    "ECS Fargate": ["ecs", "fargate"],
    "ALB": ["application load balancer", "alb"],
    "RDS": ["rds", "aurora"],
    "ElastiCache": ["elasticache", "redis"],
    "Container Apps": ["container apps", "azure container apps"],
    "Application Gateway": ["application gateway"],
    "Azure SQL": ["azure sql"],
    "Azure Cache": ["azure cache", "redis"],
    "Cloud Run": ["cloud run"],
    "Cloud SQL": ["cloud sql"],
    "Memorystore": ["memorystore"],
    "Load Balancer": ["load balancer"],
}

PRICING_SIGNAL_TERMS = (
    "pricing",
    "price",
    "cost",
    "billing",
    "pay as you go",
    "savings plan",
    "reserved",
    "spot",
)

POLICY_SIGNAL_TERMS = (
    "sla",
    "policy",
    "availability",
    "uptime",
    "compliance",
    "gdpr",
    "hipaa",
    "pci",
    "iso",
    "data residency",
)


WORKLOAD_DEFAULTS = {
    "real-time": {"throughput_rps": 1200, "latency_ms": 150, "availability_pct": 99.95, "storage_gib": 100},
    "transactional": {"throughput_rps": 900, "latency_ms": 220, "availability_pct": 99.95, "storage_gib": 120},
    "analytics": {"throughput_rps": 500, "latency_ms": 800, "availability_pct": 99.9, "storage_gib": 500},
    "batch": {"throughput_rps": 250, "latency_ms": 1200, "availability_pct": 99.5, "storage_gib": 300},
    "general": {"throughput_rps": 400, "latency_ms": 300, "availability_pct": 99.9, "storage_gib": 150},
}


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def _normalize(value: float, source_min: float, source_max: float) -> float:
    if math.isclose(source_min, source_max):
        return 50.0
    return _clamp(((value - source_min) / (source_max - source_min)) * 100.0)


def _normalize_inverse(value: float, source_min: float, source_max: float) -> float:
    if math.isclose(source_min, source_max):
        return 50.0
    return _clamp(((source_max - value) / (source_max - source_min)) * 100.0)


def _extract_first_number(pattern: str, text: str) -> Optional[float]:
    match = re.search(pattern, text, flags=re.IGNORECASE)
    if not match:
        return None
    try:
        return float(match.group(1))
    except ValueError:
        return None


def _normalize_weights(weights: Optional[Dict[str, float]]) -> Dict[str, float]:
    if not weights:
        return {dimension: 1.0 / len(DECISION_DIMENSIONS) for dimension in DECISION_DIMENSIONS}

    sanitized: Dict[str, float] = {dimension: max(0.0, float(weights.get(dimension, 0.0))) for dimension in DECISION_DIMENSIONS}
    total = sum(sanitized.values())
    if total <= 0:
        return {dimension: 1.0 / len(DECISION_DIMENSIONS) for dimension in DECISION_DIMENSIONS}
    return {dimension: value / total for dimension, value in sanitized.items()}


def _unique_preserve_order(values: Iterable[str]) -> List[str]:
    seen = set()
    result: List[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def _region_family(value: str) -> str:
    normalized = value.lower().replace(" ", "").replace("_", "").replace("-", "")
    if normalized.startswith("useast") or normalized == "eastus":
        return "us-east"
    if normalized.startswith("uswest") or normalized == "westus":
        return "us-west"
    if normalized.startswith("europewest") or normalized.startswith("euwest") or normalized == "westeurope":
        return "europe-west"
    if normalized.startswith("asiasoutheast") or normalized == "southeastasia" or normalized == "sgp1":
        return "asia-southeast"
    if normalized == "global":
        return "global"
    return normalized


def _region_matches(requested: str, candidate_regions: Sequence[str]) -> bool:
    requested_family = _region_family(requested)
    candidate_families = {_region_family(region) for region in candidate_regions}
    return requested_family in candidate_families or "global" in candidate_families


class MarketKnowledgeSignals:
    def __init__(self, dataset_root: Optional[str] = None):
        self.dataset_root = Path(dataset_root) if dataset_root else Path(__file__).resolve().parents[1] / "dataset" / "market_data"
        self.provider_corpus = self._load_provider_corpus()

    def score_adjustments(self, provider: str, services: Sequence[str]) -> Dict[str, Any]:
        corpus = self.provider_corpus.get(provider, [])
        if not corpus:
            return {
                "adjustments": {},
                "confidence": 0.0,
                "evidence": [],
                "stats": {"pricing_hits": 0, "policy_hits": 0, "service_hits": 0},
            }

        pricing_hits = 0
        policy_hits = 0
        service_hits = 0
        evidence: List[str] = []
        service_keywords = self._service_keywords(services)

        for sentence in corpus:
            lower = sentence.lower()
            pricing_match = any(term in lower for term in PRICING_SIGNAL_TERMS)
            policy_match = any(term in lower for term in POLICY_SIGNAL_TERMS)
            service_match = any(keyword in lower for keyword in service_keywords) if service_keywords else False

            if pricing_match:
                pricing_hits += 1
            if policy_match:
                policy_hits += 1
            if service_match and (pricing_match or policy_match):
                service_hits += 1
                if len(evidence) < 3:
                    evidence.append(sentence[:220])

        confidence = min(1.0, (service_hits * 0.18) + (pricing_hits * 0.02) + (policy_hits * 0.02))
        if confidence <= 0:
            return {
                "adjustments": {},
                "confidence": 0.0,
                "evidence": [],
                "stats": {"pricing_hits": pricing_hits, "policy_hits": policy_hits, "service_hits": service_hits},
            }

        adjustments = {
            "cost": round(min(5.0, (service_hits * 0.55) + (pricing_hits * 0.08)), 2),
            "operations": round(min(3.5, (service_hits * 0.4) + (policy_hits * 0.05)), 2),
            "security": round(min(3.5, policy_hits * 0.08), 2),
            "reliability": round(min(3.0, policy_hits * 0.06), 2),
        }

        return {
            "adjustments": {dimension: score for dimension, score in adjustments.items() if score > 0},
            "confidence": round(confidence, 3),
            "evidence": evidence,
            "stats": {"pricing_hits": pricing_hits, "policy_hits": policy_hits, "service_hits": service_hits},
        }

    def _service_keywords(self, services: Sequence[str]) -> List[str]:
        keywords: List[str] = []
        for service in services:
            keywords.extend(SERVICE_KEYWORD_MAP.get(service, []))
            normalized = str(service).lower().replace("/", " ")
            keywords.extend(token for token in re.split(r"\s+", normalized) if len(token) >= 4)
        return _unique_preserve_order(keywords)

    def _load_provider_corpus(self) -> Dict[str, List[str]]:
        provider_corpus: Dict[str, List[str]] = {"AWS": [], "Azure": [], "GCP": [], "DigitalOcean": []}
        provider_aliases = {
            "aws": "AWS",
            "azure": "Azure",
            "gcp": "GCP",
            "google": "GCP",
            "digitalocean": "DigitalOcean",
        }

        if not self.dataset_root.exists():
            return provider_corpus

        for path in self.dataset_root.glob("**/dataset.jsonl"):
            provider = None
            folder_hint = path.parent.name.lower()
            for alias, canonical in provider_aliases.items():
                if alias in folder_hint:
                    provider = canonical
                    break
            if not provider:
                continue

            with path.open("r", encoding="utf-8") as handle:
                for line in handle:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        payload = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    blocks = payload.get("text")
                    if not isinstance(blocks, list):
                        continue

                    for block in blocks:
                        if not isinstance(block, dict):
                            continue
                        if block.get("type") not in {"text", "heading"}:
                            continue
                        value = str(block.get("value") or "").strip()
                        if len(value) < 30:
                            continue
                        provider_corpus[provider].append(value)

        return provider_corpus


class DecisionMatrixGenerator:
    def __init__(self, market_dataset_root: Optional[str] = None):
        self.market_signals = MarketKnowledgeSignals(dataset_root=market_dataset_root)

    def _parse_requirements(self, prompt: str) -> ParsedRequirements:
        text = prompt.lower()
        workload_type = "general"
        if any(token in text for token in ["real-time", "realtime", "websocket", "stream"]):
            workload_type = "real-time"
        elif any(token in text for token in ["transaction", "banking", "payment", "checkout"]):
            workload_type = "transactional"
        elif any(token in text for token in ["analytics", "warehouse", "reporting", "bi"]):
            workload_type = "analytics"
        elif any(token in text for token in ["batch", "etl", "offline", "nightly"]):
            workload_type = "batch"

        defaults = WORKLOAD_DEFAULTS[workload_type]
        throughput_rps = _extract_first_number(r"(\d+(?:\.\d+)?)\s*(?:rps|req/s|requests per second)", text)
        latency_ms = _extract_first_number(r"(?:under|below|within|<|<=)?\s*(\d+(?:\.\d+)?)\s*ms", text)
        availability_pct = _extract_first_number(r"(\d+(?:\.\d+)?)\s*%\s*(?:availability|uptime)", text)
        budget_inr = _extract_first_number(r"(?:₹|rs\.?|rupees|inr)\s*(\d+(?:\.\d+)?)", text)
        budget_inr = budget_inr / 83.0 if budget_inr is not None else None
        storage_gib = _extract_first_number(r"(\d+(?:\.\d+)?)\s*(?:gib|gb|tb)\s*(?:storage|data|uploads|objects)?", text)

        if storage_gib is None:
            storage_gib = defaults["storage_gib"]
        elif "tb" in text:
            storage_gib *= 1024.0

        region = None
        region_match = re.search(
            r"\b(us[- ]east(?:-?1)?|us[- ]west(?:-?2)?|europe[- ]west(?:-?1)?|westeurope|eastus|westus2|us-central1|us-east1|asia-southeast1|southeastasia|sgp1|ams3|sfo3|nyc1)\b",
            text,
        )
        if region_match:
            region = region_match.group(1).replace(" ", "-")

        compliance: List[str] = []
        for tag in ["hipaa", "pci", "gdpr", "soc 2", "iso 27001"]:
            if tag in text:
                if tag == "pci":
                    compliance.append("PCI DSS")
                elif tag == "hipaa":
                    compliance.append("HIPAA")
                elif tag == "gdpr":
                    compliance.append("GDPR")
                elif tag == "soc 2":
                    compliance.append("SOC 2")
                else:
                    compliance.append("ISO 27001")

        gpu_required = any(token in text for token in ["gpu", "cuda", "ml inference", "machine learning", "training"])
        tech_stack_terms = [
            ("Next.js", ["next.js", "nextjs", "react"]),
            ("Node.js", ["node.js", "nodejs", "express", "nestjs", "javascript", "typescript"]),
            ("Python", ["python", "fastapi", "django", "flask"]),
            ("Java", ["java", "spring", "spring boot"]),
            (".NET", [".net", "dotnet", "c#", "asp.net"]),
            ("Go", ["golang", "go ", "go-lang"]),
            ("Docker", ["docker", "container"]),
            ("Kubernetes", ["kubernetes", "k8s"]),
        ]
        detected_stack: List[str] = []
        for label, patterns in tech_stack_terms:
            if any(pattern in text for pattern in patterns):
                detected_stack.append(label)
        tech_stack = ", ".join(_unique_preserve_order(detected_stack)) if detected_stack else None
        hints: List[str] = []
        if throughput_rps is None:
            hints.append("No explicit throughput target was found; using workload-based defaults.")
            throughput_rps = defaults["throughput_rps"]
        if latency_ms is None:
            hints.append("No explicit latency target was found; using workload-based defaults.")
            latency_ms = defaults["latency_ms"]
        if availability_pct is None:
            hints.append("No explicit uptime target was found; using workload-based defaults.")
            availability_pct = defaults["availability_pct"]
        if not compliance:
            hints.append("No compliance framework was specified.")
        if tech_stack is None:
            hints.append("No explicit tech stack or runtime preference was found.")

        return ParsedRequirements(
            workload_type=workload_type,
            throughput_rps=float(throughput_rps),
            latency_ms=float(latency_ms),
            availability_pct=float(availability_pct),
            budget_inr=float(budget_inr) if budget_inr is not None else None,
            storage_gib=float(storage_gib),
            region=region,
            compliance=compliance,
            tech_stack=tech_stack,
            gpu_required=gpu_required,
            hints=hints,
        )

    def _candidate_profile(self, provider: str, archetype: str, req: ParsedRequirements) -> Dict[str, Any]:
        provider_profile = PROVIDER_PROFILES[provider]
        archetype_profile = ARCHETYPES[archetype]

        load_units = max(1.0, req.throughput_rps / 300.0)
        storage_units = max(1.0, req.storage_gib / 120.0)
        compliance_units = max(1.0, len(req.compliance) or 1.0)
        gpu_units = 1.0 if req.gpu_required else 0.0

        base_cost = 68.0 * load_units + 16.0 * storage_units + 20.0 * compliance_units + (70.0 * gpu_units)
        cost_multiplier = provider_profile["cost_factor"] * archetype_profile["cost_multiplier"]
        estimated_monthly_cost = base_cost * cost_multiplier

        workload_latency_factor = {
            "real-time": 0.86,
            "transactional": 0.94,
            "analytics": 1.12,
            "batch": 1.18,
            "general": 1.0,
        }[req.workload_type]

        latency_bias = provider_profile["latency_factor"] * archetype_profile["latency_multiplier"] * workload_latency_factor
        estimated_latency_ms = max(20.0, req.latency_ms * latency_bias)

        workload_throughput_factor = {
            "real-time": 1.08,
            "transactional": 1.02,
            "analytics": 0.96,
            "batch": 0.88,
            "general": 1.0,
        }[req.workload_type]
        throughput_capacity = req.throughput_rps * provider_profile["throughput_factor"] * archetype_profile["performance_multiplier"] * workload_throughput_factor

        availability_bias = provider_profile["reliability"] * archetype_profile["reliability_multiplier"]
        estimated_availability_pct = min(99.995, 97.4 + (availability_bias * 2.8))

        supported_compliance = _unique_preserve_order([tag for tag in provider_profile["compliance"] if tag in ["SOC 2", "ISO 27001", "HIPAA", "PCI DSS", "GDPR"]])
        regions = list(provider_profile["regions"])

        services = list(archetype_profile["services"][provider])
        if req.gpu_required and archetype == "gpu":
            services.append("GPU-optimized runtime")

        return {
            "services": services,
            "regions": regions,
            "supported_compliance": supported_compliance,
            "gpu_capable": bool(archetype_profile["gpu_capable"]),
            "estimated_monthly_cost": round(estimated_monthly_cost, 2),
            "estimated_monthly_cost_inr": round(estimated_monthly_cost * 83, 2),
            "estimated_latency_ms": round(estimated_latency_ms, 1),
            "estimated_throughput_rps": round(throughput_capacity, 1),
            "estimated_availability_pct": round(estimated_availability_pct, 3),
            "provider_profile": provider_profile,
            "archetype_profile": archetype_profile,
        }

    def _hard_constraint_reason(self, profile: Dict[str, Any], req: ParsedRequirements) -> Optional[str]:
        if req.gpu_required and not profile["gpu_capable"]:
            return "GPU is required but this option is not GPU-capable."
        if req.region and not _region_matches(req.region, profile["regions"]):
            return f"Region {req.region} is not supported by this option."
        if req.compliance:
            supported = set(profile["supported_compliance"])
            required = set(req.compliance)
            if not required.issubset(supported):
                missing = ", ".join(sorted(required - supported))
                return f"Missing required compliance support: {missing}."
        if profile["estimated_throughput_rps"] < req.throughput_rps:
            return "Estimated throughput does not meet the requested target."
        if profile["estimated_latency_ms"] > req.latency_ms * 1.08:
            return "Estimated latency exceeds the requested target."
        if profile["estimated_availability_pct"] < req.availability_pct:
            return "Estimated availability does not meet the requested target."
        if req.budget_inr is not None and profile["estimated_monthly_cost"] > req.budget_inr:
            return f"Estimated monthly cost exceeds the stated budget of ₹{req.budget_inr * 83:.2f}."
        return None

    def _dimension_scores(self, profile: Dict[str, Any], req: ParsedRequirements) -> Dict[str, float]:
        provider_profile = profile["provider_profile"]
        archetype_profile = profile["archetype_profile"]

        cost_score = 100.0
        if req.budget_inr:
            cost_score = _normalize_inverse(profile["estimated_monthly_cost"], 0.0, req.budget_inr * 1.6)
            # Prioritize serverless for low budget (under $100 / ₹8300)
            if req.budget_inr < 100.0 and archetype_profile.get("label") == "Serverless PaaS":
                cost_score = _clamp(cost_score + 15.0)

        latency_score = _normalize_inverse(profile["estimated_latency_ms"], req.latency_ms * 0.55, req.latency_ms * 1.45)
        throughput_score = _normalize(profile["estimated_throughput_rps"], req.throughput_rps * 0.75, req.throughput_rps * 1.6)
        performance_score = _clamp((latency_score * 0.58) + (throughput_score * 0.42))

        operations_score = _clamp((provider_profile["ops_factor"] * 60.0) + (archetype_profile["operations_multiplier"] * 40.0))
        reliability_score = _clamp((profile["estimated_availability_pct"] - 97.0) * 33.0)
        scalability_score = _clamp((provider_profile["scalability_factor"] * 55.0) + (archetype_profile["scalability_multiplier"] * 45.0))

        compliance_hits = len(set(req.compliance).intersection(profile["supported_compliance"]))
        compliance_ratio = 1.0 if not req.compliance else compliance_hits / max(1, len(req.compliance))
        security_score = _clamp((provider_profile["security"] * 72.0) + (compliance_ratio * 28.0))

        portability_score = _clamp((provider_profile["portability"] * 58.0) + (archetype_profile["portability_multiplier"] * 42.0))

        return {
            "cost": round(cost_score, 2),
            "performance": round(performance_score, 2),
            "operations": round(operations_score, 2),
            "reliability": round(reliability_score, 2),
            "scalability": round(scalability_score, 2),
            "security": round(security_score, 2),
            "portability": round(portability_score, 2),
        }

    def _gap_penalties(self, profile: Dict[str, Any], req: ParsedRequirements) -> Dict[str, float]:
        penalty = {
            "latency": 0.0,
            "throughput": 0.0,
            "availability": 0.0,
            "budget": 0.0,
            "compliance": 0.0,
        }

        latency_gap = max(0.0, profile["estimated_latency_ms"] - req.latency_ms) / max(req.latency_ms, 1.0)
        throughput_gap = max(0.0, req.throughput_rps - profile["estimated_throughput_rps"]) / max(req.throughput_rps, 1.0)
        availability_gap = max(0.0, req.availability_pct - profile["estimated_availability_pct"]) / max(req.availability_pct, 1.0)
        compliance_gap = 0.0
        if req.compliance:
            compliance_gap = max(0.0, len(set(req.compliance) - set(profile["supported_compliance"]))) / max(1.0, float(len(req.compliance)))
        budget_gap = 0.0
        if req.budget_inr is not None:
            budget_gap = max(0.0, profile["estimated_monthly_cost"] - req.budget_inr) / max(req.budget_inr, 1.0)

        penalty["latency"] = round(latency_gap * 18.0, 2)
        penalty["throughput"] = round(throughput_gap * 20.0, 2)
        penalty["availability"] = round(availability_gap * 15.0, 2)
        penalty["budget"] = round(budget_gap * 18.0, 2)
        penalty["compliance"] = round(compliance_gap * 22.0, 2)
        return penalty

    def _weighted_sum(self, scores: Dict[str, float], weights: Dict[str, float]) -> float:
        return sum(scores[dimension] * weights.get(dimension, 0.0) for dimension in DECISION_DIMENSIONS)

    def _explain(self, option: CandidateOption, req: ParsedRequirements) -> List[str]:
        lines = [
            f"{option.provider} {option.archetype} is estimated at ₹{option.estimated_monthly_cost_inr:.2f}/month with {option.estimated_latency_ms:.1f}ms latency and {option.estimated_availability_pct:.3f}% availability.",
        ]
        best_dimension = max(option.dimension_scores.items(), key=lambda item: item[1])[0]
        weakest_dimension = min(option.dimension_scores.items(), key=lambda item: item[1])[0]
        lines.append(f"Its strongest dimension is {best_dimension}, while the main trade-off is {weakest_dimension}.")
        if req.budget_inr is not None:
            if option.estimated_monthly_cost <= req.budget_inr:
                lines.append("It stays within the stated budget.")
            else:
                lines.append("It exceeds the stated budget, so cost pressure is a visible trade-off.")
        if req.region:
            lines.append(f"Region preference was checked against {req.region}.")
        if req.compliance:
            lines.append(f"Compliance fit covers: {', '.join(sorted(set(req.compliance).intersection(option.supported_compliance))) or 'none'}.")
        if req.tech_stack:
            lines.append(f"Tech stack preference considered: {req.tech_stack}.")
        confidence = float(option.market_signal.get("confidence", 0.0)) if option.market_signal else 0.0
        if confidence > 0:
            lines.append(f"Market-data evidence contributed with confidence {confidence:.2f} from provider pricing/policy knowledge base entries.")
        return lines

    def _pareto_front(self, options: List[CandidateOption]) -> List[str]:
        feasible = [option for option in options if not option.eliminated]
        front: List[str] = []
        for candidate in feasible:
            dominated = False
            for other in feasible:
                if other.id == candidate.id:
                    continue
                better_or_equal = all(other.dimension_scores[d] >= candidate.dimension_scores[d] for d in DECISION_DIMENSIONS)
                strictly_better = any(other.dimension_scores[d] > candidate.dimension_scores[d] for d in DECISION_DIMENSIONS)
                if better_or_equal and strictly_better:
                    dominated = True
                    break
            if not dominated:
                front.append(candidate.id)
        return front

    def _rank(self, options: List[CandidateOption]) -> List[CandidateOption]:
        return sorted(options, key=lambda option: (option.eliminated, -option.final_score, -option.weighted_score, option.estimated_monthly_cost))

    def _sensitivity(self, options: List[CandidateOption], weights: Dict[str, float]) -> Dict[str, Any]:
        feasible = [option for option in options if not option.eliminated]
        if not feasible:
            return {"scenarios": [], "stability": []}

        scenarios: List[Dict[str, Any]] = []
        perturbations = []
        for dimension in DECISION_DIMENSIONS:
            up = dict(weights)
            up[dimension] = up[dimension] * 1.15
            perturbations.append((f"{dimension}_up", _normalize_weights(up)))

            down = dict(weights)
            down[dimension] = down[dimension] * 0.85
            perturbations.append((f"{dimension}_down", _normalize_weights(down)))

        perturbations.insert(0, ("baseline", weights))

        for label, scenario_weights in perturbations:
            reranked = sorted(
                feasible,
                key=lambda option: (
                    -sum(option.dimension_scores[d] * scenario_weights.get(d, 0.0) for d in DECISION_DIMENSIONS),
                    option.estimated_monthly_cost,
                ),
            )
            top_ids = [option.id for option in reranked[:3]]
            scenarios.append(
                {
                    "scenario": label,
                    "top_option_ids": top_ids,
                    "top_provider": reranked[0].provider,
                    "top_score": round(sum(reranked[0].dimension_scores[d] * scenario_weights.get(d, 0.0) for d in DECISION_DIMENSIONS), 2),
                }
            )

        stability: List[Dict[str, Any]] = []
        for option in feasible:
            top1_hits = sum(1 for scenario in scenarios if scenario["top_option_ids"] and scenario["top_option_ids"][0] == option.id)
            top3_hits = sum(1 for scenario in scenarios if option.id in scenario["top_option_ids"])
            rank_samples = []
            for _, scenario_weights in perturbations:
                reranked = sorted(
                    feasible,
                    key=lambda candidate: (
                        -sum(candidate.dimension_scores[d] * scenario_weights.get(d, 0.0) for d in DECISION_DIMENSIONS),
                        candidate.estimated_monthly_cost,
                    ),
                )
                for index, candidate in enumerate(reranked, start=1):
                    if candidate.id == option.id:
                        rank_samples.append(index)
                        break
            stability.append(
                {
                    "option_id": option.id,
                    "provider": option.provider,
                    "archetype": option.archetype,
                    "top1_rate": round(top1_hits / len(scenarios), 3),
                    "top3_rate": round(top3_hits / len(scenarios), 3),
                    "average_rank": round(sum(rank_samples) / len(rank_samples), 2),
                    "worst_rank": max(rank_samples),
                }
            )

        return {"scenarios": scenarios, "stability": stability}

    def generate(
        self,
        prompt: str,
        weights: Optional[Dict[str, float]] = None,
        providers: Optional[Sequence[str]] = None,
    ) -> Dict[str, Any]:
        req = self._parse_requirements(prompt)
        normalized_weights = _normalize_weights(weights)
        provider_list = list(providers or DEFAULT_PROVIDER_FILTER)

        options: List[CandidateOption] = []
        for provider in provider_list:
            if provider not in PROVIDER_PROFILES:
                continue
            for archetype in ARCHETYPES:
                profile = self._candidate_profile(provider, archetype, req)
                reason = self._hard_constraint_reason(profile, req)
                dimension_scores = self._dimension_scores(profile, req)
                market_signal = self.market_signals.score_adjustments(provider=provider, services=profile["services"])
                for dimension, bump in market_signal.get("adjustments", {}).items():
                    if dimension in dimension_scores:
                        dimension_scores[dimension] = round(_clamp(dimension_scores[dimension] + float(bump)), 2)
                gap_penalties = self._gap_penalties(profile, req)
                weighted_sum = self._weighted_sum(dimension_scores, normalized_weights)
                penalty_points = sum(gap_penalties.values())
                final_score = round(max(0.0, weighted_sum - penalty_points), 2)

                option = CandidateOption(
                    id=f"{provider.lower()}-{archetype}-{uuid.uuid4().hex[:8]}",
                    provider=provider,
                    archetype=archetype,
                    name=f"{provider} {ARCHETYPES[archetype]['label']}",
                    services=profile["services"],
                    regions=profile["regions"],
                    supported_compliance=profile["supported_compliance"],
                    gpu_capable=profile["gpu_capable"],
                    estimated_monthly_cost=profile["estimated_monthly_cost"],
                    estimated_monthly_cost_inr=profile["estimated_monthly_cost_inr"],
                    estimated_latency_ms=profile["estimated_latency_ms"],
                    estimated_throughput_rps=profile["estimated_throughput_rps"],
                    estimated_availability_pct=profile["estimated_availability_pct"],
                    dimension_scores=dimension_scores,
                    gap_penalties=gap_penalties,
                    weighted_score=round(weighted_sum, 2),
                    final_score=final_score,
                    market_signal=market_signal,
                )

                option.eliminated = reason is not None
                option.elimination_reason = reason
                option.summary = (
                    f"{option.provider} {option.archetype} balances {max(option.dimension_scores, key=option.dimension_scores.get)} better than {min(option.dimension_scores, key=option.dimension_scores.get)}."
                )
                option.tradeoffs = [
                    f"Cost score: {option.dimension_scores['cost']:.1f}",
                    f"Operations score: {option.dimension_scores['operations']:.1f}",
                    f"Security score: {option.dimension_scores['security']:.1f}",
                ]
                option.rationale = self._explain(option, req)
                options.append(option)

        ranked = self._rank(options)
        feasible = [option for option in ranked if not option.eliminated]
        eliminated = [option for option in ranked if option.eliminated]
        pareto_front = self._pareto_front(ranked)
        sensitivity = self._sensitivity(ranked, normalized_weights)

        recommendation = feasible[0] if feasible else None
        open_questions = list(req.hints)
        if not req.region:
            open_questions.append("Which region or country must the deployment run in?")
        if not req.compliance:
            open_questions.append("Do you need any compliance frameworks such as HIPAA, PCI DSS, or GDPR?")
        if req.budget_inr is None:
            open_questions.insert(0, "CRITICAL: Please provide a monthly budget ceiling in rupees to finalize a cost-effective recommendation.")
        if req.tech_stack is None:
            open_questions.append("Which stack, runtime, or existing platform must this recommendation preserve?")

        return {
            "problem_statement": prompt,
            "parsed_requirements": asdict(req),
            "weights": normalized_weights,
            "dimensions": DECISION_DIMENSIONS,
            "summary": (
                f"Generated {len(feasible)} feasible options across {len(provider_list)} providers, with {len(eliminated)} eliminated by hard constraints."
            ),
            "open_questions": open_questions,
            "ranked_options": [asdict(option) for option in ranked],
            "feasible_options": [asdict(option) for option in feasible],
            "eliminated_options": [asdict(option) for option in eliminated],
            "pareto_front": pareto_front,
            "recommendation": asdict(recommendation) if recommendation else None,
            "sensitivity": sensitivity,
        }
