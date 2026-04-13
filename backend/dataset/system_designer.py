from pathlib import Path
from typing import Dict, List

from services.ingestion.ingest import (
    DatasetIndexer,
    Chunk,
    collect_unique_references,
    extract_candidate_sentences,
)


BUILD_GUIDE_STEPS = [
    "Understand requirements and constraints.",
    "Define high-level architecture and core components.",
    "Choose the technology stack and data model.",
    "Design modules and service boundaries.",
    "Plan for scalability, availability, and fault tolerance.",
    "Define security, privacy, and compliance controls.",
    "Test, validate, and iterate with trade-off analysis.",
]


SECTION_KEYWORDS = {
    "requirements": ["requirement", "functional", "non-functional", "sla", "latency", "throughput"],
    "architecture": ["architecture", "component", "microservice", "gateway", "queue", "api"],
    "data": ["database", "storage", "sharding", "replication", "schema", "consistency"],
    "scalability": ["scalability", "cache", "load balancer", "horizontal", "vertical", "throughput"],
    "security": ["security", "privacy", "encryption", "authentication", "authorization", "compliance"],
    "operations": ["monitoring", "observability", "alert", "disaster", "recovery", "testing"],
}


class SystemDesigner:
    """Produces a structured system-design response grounded in the local dataset."""

    def __init__(self, dataset_path: str | None = None):
        if dataset_path is None:
            default_path = Path(__file__).resolve().parents[1] / "dataset" / "dataset.jsonl"
            dataset_path = str(default_path)

        self.indexer = DatasetIndexer(dataset_path)

    def _pick_bullets(self, chunks: List[Chunk], section: str, limit: int = 4) -> List[str]:
        keywords = SECTION_KEYWORDS[section]
        sentences = extract_candidate_sentences(chunks)

        selected: List[str] = []
        seen = set()
        for sentence in sentences:
            lower = sentence.lower()
            if not any(keyword in lower for keyword in keywords):
                continue
            normalized = " ".join(lower.split())
            if normalized in seen:
                continue
            seen.add(normalized)
            selected.append(sentence)
            if len(selected) >= limit:
                break

        return selected

    def design_system(self, prompt: str, top_k: int = 16) -> Dict:
        query = f"{prompt} system design architecture scalability reliability security database api"
        chunks = self.indexer.search(query, top_k=top_k)

        if not chunks:
            return {
                "problem_statement": prompt,
                "summary": "No matching system-design dataset entries were found for this prompt.",
                "build_guide": BUILD_GUIDE_STEPS,
                "recommendations": {},
                "tradeoffs": [],
                "references": [],
            }

        recommendations = {
            "requirements": self._pick_bullets(chunks, "requirements"),
            "architecture": self._pick_bullets(chunks, "architecture"),
            "data": self._pick_bullets(chunks, "data"),
            "scalability": self._pick_bullets(chunks, "scalability"),
            "security": self._pick_bullets(chunks, "security"),
            "operations": self._pick_bullets(chunks, "operations"),
        }

        tradeoffs: List[str] = []
        all_sentences = extract_candidate_sentences(chunks)
        for sentence in all_sentences:
            lower = sentence.lower()
            if "trade-off" in lower or "tradeoff" in lower or "cost vs" in lower or "consistency" in lower:
                tradeoffs.append(sentence)
                if len(tradeoffs) >= 6:
                    break

        references = collect_unique_references(chunks, limit=10)

        return {
            "problem_statement": prompt,
            "summary": "Dataset-grounded system design guidance generated using the build guide workflow.",
            "build_guide": BUILD_GUIDE_STEPS,
            "recommendations": recommendations,
            "tradeoffs": tradeoffs,
            "references": references,
        }
