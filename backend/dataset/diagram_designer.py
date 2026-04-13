from __future__ import annotations

import json
import re
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4


@dataclass
class DiagramBlock:
    name: str
    payload: Dict[str, Any]


class DiagramDesigner:
    """Parses, maps, serializes, and generates cloud-agnostic architecture diagrams."""

    def __init__(self, catalog_path: str | None = None):
        if catalog_path is None:
            catalog_path = str(Path(__file__).resolve().parents[1] / "diagram_service_catalog.json")

        self.catalog_path = Path(catalog_path)
        self.catalog = self._load_catalog()
        self._store: Dict[str, Dict[str, Any]] = {}
        self._seed_store()

    def _load_catalog(self) -> Dict[str, Any]:
        with self.catalog_path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def catalog_snapshot(self) -> Dict[str, Any]:
        return deepcopy(self.catalog)

    def list_diagrams(self) -> List[Dict[str, Any]]:
        return [self._public_view(diagram) for diagram in self._store.values()]

    def get_diagram(self, diagram_id: str) -> Dict[str, Any]:
        if diagram_id not in self._store:
            self._store[diagram_id] = self._blank_diagram(diagram_id)
        return self._public_view(self._store[diagram_id])

    def upsert_diagram(self, diagram_id: str, diagram: Dict[str, Any]) -> Dict[str, Any]:
        normalized = self._normalize_diagram(diagram_id, diagram)
        self._store[diagram_id] = normalized
        return self._public_view(normalized)

    def parse_text(self, text: str, diagram_id: Optional[str] = None) -> Dict[str, Any]:
        diagram, dsl = self._parse_text_to_diagram(text, diagram_id=diagram_id)
        if diagram_id:
            self._store[diagram_id] = diagram
        return {
            "diagram": self._public_view(diagram),
            "dsl": dsl,
        }

    def generate_from_prompt(
        self,
        prompt: str,
        provider: str = "generic",
        diagram_id: Optional[str] = None,
        title: Optional[str] = None,
    ) -> Dict[str, Any]:
        diagram = self._generate_diagram_from_prompt(prompt=prompt, provider=provider, title=title)
        if diagram_id:
            diagram["id"] = diagram_id
            self._store[diagram_id] = diagram
        elif diagram["id"] not in self._store:
            self._store[diagram["id"]] = diagram

        return {
            "diagram": self._public_view(diagram),
            "dsl": diagram["dsl"],
        }

    def save_from_payload(self, diagram_id: str, diagram: Dict[str, Any]) -> Dict[str, Any]:
        normalized = self._normalize_diagram(diagram_id, diagram)
        self._store[diagram_id] = normalized
        return {
            "diagram": self._public_view(normalized),
            "dsl": normalized["dsl"],
        }

    def _seed_store(self) -> None:
        default_diagram = self._generate_diagram_from_prompt(
            prompt="E-commerce backend with frontend, API gateway, compute, cache, and relational database",
            provider="AWS",
            title="Sheet 1",
        )
        default_diagram["id"] = "sheet-1"
        default_diagram["title"] = "Sheet 1"
        second_diagram = self._generate_diagram_from_prompt(
            prompt="Analytics pipeline with event stream, worker, object storage, and search index",
            provider="Azure",
            title="Sheet 2",
        )
        second_diagram["id"] = "sheet-2"
        second_diagram["title"] = "Sheet 2"
        self._store["sheet-1"] = default_diagram
        self._store["sheet-2"] = second_diagram

    def _public_view(self, diagram: Dict[str, Any]) -> Dict[str, Any]:
        public = deepcopy(diagram)
        public["catalog"] = self.catalog_snapshot()
        return public

    def _blank_diagram(self, diagram_id: str) -> Dict[str, Any]:
        title = self._title_from_id(diagram_id)
        payload = {
            "id": diagram_id,
            "title": title,
            "provider": "generic",
            "engine": "mermaid",
            "type": "graph",
            "source_text": "",
            "components": [],
            "edges": [],
        }
        return self._normalize_diagram(diagram_id, payload)

    def _normalize_diagram(self, diagram_id: str, diagram: Dict[str, Any]) -> Dict[str, Any]:
        payload = deepcopy(diagram)
        provider = self._normalize_provider(payload.get("provider", "generic"))
        title = str(payload.get("title") or self._title_from_id(diagram_id))
        engine = str(payload.get("engine") or "mermaid")
        diagram_type = str(payload.get("type") or payload.get("kind") or "graph")
        source_text = str(payload.get("source_text") or payload.get("dsl") or "")

        components = payload.get("components") or payload.get("nodes") or []
        if not isinstance(components, list):
            components = []

        code = str(payload.get("code") or "")
        if code and not components:
            parsed_components, parsed_edges = self._parse_graph_code(code)
            components = parsed_components
            edges = parsed_edges
        else:
            edges = payload.get("edges") or []
            if not isinstance(edges, list):
                edges = []

        normalized_components = [self._normalize_component(component, provider) for component in components]
        normalized_edges = self._normalize_edges(normalized_components, edges)
        laid_out_components = self._apply_layout(normalized_components, normalized_edges)
        dsl = self._serialize_diagram(title=title, provider=provider, engine=engine, diagram_type=diagram_type, components=laid_out_components, code=code or None)

        return {
            "id": diagram_id,
            "title": title,
            "provider": provider,
            "engine": engine,
            "type": diagram_type,
            "source_text": source_text,
            "code": code or None,
            "components": laid_out_components,
            "nodes": deepcopy(laid_out_components),
            "edges": normalized_edges,
            "dsl": dsl,
            "service_map": self._build_service_map(laid_out_components, provider),
            "summary": self._build_summary(laid_out_components, provider),
        }

    def _parse_text_to_diagram(self, text: str, diagram_id: Optional[str] = None) -> Tuple[Dict[str, Any], str]:
        diagram_block = self._extract_block(text, "diagram")
        component_blocks = self._extract_blocks(text, "component")

        if diagram_block is None:
            raise ValueError("No /diagram{...} block was found in the provided text.")

        payload = self._parse_jsonish(diagram_block)
        components = []
        if isinstance(payload.get("components"), list):
            components.extend(payload["components"])
        if isinstance(payload.get("component"), dict):
            components.append(payload["component"])
        for block in component_blocks:
            components.append(self._parse_jsonish(block))

        code = payload.get("code")
        provider = self._normalize_provider(payload.get("provider", "generic"))
        normalized: Dict[str, Any] = {
            "id": diagram_id or str(payload.get("id") or self._slugify(str(payload.get("title") or "diagram"))),
            "title": str(payload.get("title") or self._title_from_id(diagram_id or payload.get("id") or "diagram")),
            "provider": provider,
            "engine": str(payload.get("engine") or "mermaid"),
            "type": str(payload.get("type") or "graph"),
            "source_text": text,
        }

        if code and not components:
            parsed_components, parsed_edges = self._parse_graph_code(str(code))
            normalized["components"] = parsed_components
            normalized["edges"] = parsed_edges
            normalized["code"] = str(code)
        else:
            normalized["components"] = components
            normalized["edges"] = []
            if code:
                normalized["code"] = str(code)

        diagram = self._normalize_diagram(normalized["id"], normalized)
        diagram["source_text"] = text
        return diagram, diagram["dsl"]

    def _generate_diagram_from_prompt(self, prompt: str, provider: str = "generic", title: Optional[str] = None) -> Dict[str, Any]:
        provider = self._normalize_provider(provider)
        prompt_lower = prompt.lower()

        components: List[Dict[str, Any]] = [
            self._component_from_type("Frontend Web App", "Frontend", connects_to=["api_gateway"]),
            self._component_from_type("API Gateway / Gateway", "API Gateway", connects_to=["app_service"]),
            self._component_from_type("Compute", "Application Service", connects_to=["primary_db", "cache"]),
            self._component_from_type("Relational / SQL DB", "Primary Database"),
        ]

        if any(term in prompt_lower for term in ["cache", "session", "low latency", "fast"]):
            components.append(self._component_from_type("Cache", "Cache"))
            self._link_component(components, "app_service", "cache")

        if any(term in prompt_lower for term in ["auth", "identity", "login"]):
            components.append(self._component_from_type("Identity / Auth Provider", "Auth"))
            self._link_component(components, "frontend", "auth")
            self._link_component(components, "api_gateway", "auth")

        if any(term in prompt_lower for term in ["real-time", "realtime", "chat", "stream"]):
            components.append(self._component_from_type("Event Bus / Pub-Pub", "Event Bus", connects_to=["worker"]))
            components.append(self._component_from_type("Worker / Background Processor", "Worker"))
            self._link_component(components, "app_service", "worker")

        if any(term in prompt_lower for term in ["upload", "file", "object storage", "media"]):
            components.append(self._component_from_type("Object Storage", "Object Storage"))
            self._link_component(components, "app_service", "object_storage")

        if any(term in prompt_lower for term in ["search", "index", "text"]):
            components.append(self._component_from_type("Search / Text Index", "Search"))
            self._link_component(components, "app_service", "search")

        if any(term in prompt_lower for term in ["queue", "async", "background", "batch"]):
            components.append(self._component_from_type("Message Queue", "Queue", connects_to=["worker"] if any(c.get("id") == "worker" for c in components) else []))
            if not any(c.get("id") == "worker" for c in components):
                components.append(self._component_from_type("Worker / Background Processor", "Worker"))
            self._link_component(components, "app_service", "queue")

        if any(term in prompt_lower for term in ["monitor", "observability", "logs", "trace"]):
            components.append(self._component_from_type("Monitoring / Metrics Collector", "Monitoring"))
            components.append(self._component_from_type("Logs / Log Collector", "Logs"))
            components.append(self._component_from_type("Tracing / Distributed Tracing", "Tracing"))
            self._link_component(components, "app_service", "monitoring")

        components = self._dedupe_components(components)
        edges = self._build_edges_from_components(components)
        normalized = self._normalize_diagram(
            diagram_id=self._slugify(title or prompt[:40] or "diagram"),
            diagram={
                "id": self._slugify(title or prompt[:40] or "diagram"),
                "title": title or self._title_from_prompt(prompt),
                "provider": provider,
                "engine": "mermaid",
                "type": "graph",
                "source_text": prompt,
                "components": components,
                "edges": edges,
            },
        )
        normalized["source_text"] = prompt
        normalized["prompt"] = prompt
        return normalized

    def _component_from_type(
        self,
        component_type: str,
        label: str,
        connects_to: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        component_id = self._slugify(label)
        return {
            "id": component_id,
            "type": component_type,
            "label": label,
            "connects_to": connects_to or [],
        }

    def _link_component(self, components: List[Dict[str, Any]], source_id: str, target_id: str) -> None:
        for component in components:
            if component.get("id") == source_id:
                targets = component.setdefault("connects_to", [])
                if target_id not in targets:
                    targets.append(target_id)
                return

    def _dedupe_components(self, components: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        seen = set()
        ordered: List[Dict[str, Any]] = []
        for component in components:
            component_id = component.get("id") or self._slugify(str(component.get("label") or component.get("type") or "node"))
            if component_id in seen:
                continue
            seen.add(component_id)
            ordered.append(component)
        return ordered

    def _build_edges_from_components(self, components: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        edges: List[Dict[str, str]] = []
        for component in components:
            source_id = self._slugify(str(component.get("id") or component.get("label") or component.get("type")))
            for target in component.get("connects_to") or []:
                edges.append({"source": source_id, "target": self._slugify(str(target))})
        return self._dedupe_edges(edges)

    def _normalize_component(self, component: Dict[str, Any], provider: str) -> Dict[str, Any]:
        if not isinstance(component, dict):
            raise ValueError("Each component must be an object.")

        component_type = str(component.get("type") or component.get("label") or "Compute")
        generic_entry = self._find_generic_entry(component_type)
        label = str(component.get("label") or generic_entry.get("label") or component_type)
        component_id = str(component.get("id") or self._slugify(label))
        connects_to = component.get("connects_to") or []
        if isinstance(connects_to, str):
            connects_to = [connects_to]
        if not isinstance(connects_to, list):
            connects_to = []

        provider_service = self._map_service(component_type, provider)
        icon = generic_entry.get("icon") or "box"
        category = generic_entry.get("category") or self._category_for_type(component_type)

        normalized = {
            "id": component_id,
            "type": component_type,
            "label": label,
            "region": component.get("region"),
            "x": component.get("x"),
            "y": component.get("y"),
            "connects_to": [str(target) for target in connects_to],
            "provider": provider,
            "provider_service": provider_service,
            "mapped_service": provider_service,
            "icon": icon,
            "category": category,
        }

        for key in ["description", "notes", "color", "icon"]:
            if key in component and component[key] is not None:
                normalized[key] = component[key]

        return normalized

    def _normalize_edges(
        self,
        components: List[Dict[str, Any]],
        edges: List[Dict[str, Any]],
    ) -> List[Dict[str, str]]:
        valid_ids = {component["id"] for component in components}
        normalized: List[Dict[str, str]] = []
        seen = set()

        for component in components:
            for target in component.get("connects_to") or []:
                edge = self._normalize_edge(component["id"], str(target), valid_ids)
                if edge is None:
                    continue
                signature = (edge["source"], edge["target"])
                if signature not in seen:
                    seen.add(signature)
                    normalized.append(edge)

        for edge in edges:
            if not isinstance(edge, dict):
                continue
            source = str(edge.get("source") or edge.get("from") or "")
            target = str(edge.get("target") or edge.get("to") or "")
            normalized_edge = self._normalize_edge(source, target, valid_ids)
            if normalized_edge is None:
                continue
            signature = (normalized_edge["source"], normalized_edge["target"])
            if signature in seen:
                continue
            seen.add(signature)
            normalized.append(normalized_edge)

        return normalized

    def _normalize_edge(self, source: str, target: str, valid_ids: set[str]) -> Optional[Dict[str, str]]:
        if not source or not target:
            return None
        if source not in valid_ids or target not in valid_ids:
            return None
        return {"source": source, "target": target}

    def _dedupe_edges(self, edges: List[Dict[str, str]]) -> List[Dict[str, str]]:
        deduped: List[Dict[str, str]] = []
        seen = set()
        for edge in edges:
            signature = (edge["source"], edge["target"])
            if signature in seen:
                continue
            seen.add(signature)
            deduped.append(edge)
        return deduped

    def _apply_layout(self, components: List[Dict[str, Any]], edges: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        if not components:
            return []

        index_by_id = {component["id"]: idx for idx, component in enumerate(components)}
        incoming: Dict[str, int] = {component["id"]: 0 for component in components}
        adjacency: Dict[str, List[str]] = {component["id"]: [] for component in components}

        for edge in edges:
            source = edge["source"]
            target = edge["target"]
            if source in adjacency and target in incoming:
                adjacency[source].append(target)
                incoming[target] += 1

        levels: Dict[str, int] = {component_id: 0 for component_id in incoming}
        queue = [component_id for component_id, count in incoming.items() if count == 0]
        if not queue:
            queue = [components[0]["id"]]

        visited = set()
        while queue:
            node_id = queue.pop(0)
            visited.add(node_id)
            current_level = levels[node_id]
            for neighbor in adjacency.get(node_id, []):
                levels[neighbor] = max(levels.get(neighbor, 0), current_level + 1)
                incoming[neighbor] = max(0, incoming[neighbor] - 1)
                if incoming[neighbor] == 0 and neighbor not in visited:
                    queue.append(neighbor)

        grouped: Dict[int, List[Dict[str, Any]]] = {}
        for component in components:
            grouped.setdefault(levels.get(component["id"], 0), []).append(component)

        laid_out: List[Dict[str, Any]] = []
        for level in sorted(grouped.keys()):
            row = grouped[level]
            for idx, component in enumerate(row):
                positioned = deepcopy(component)
                if positioned.get("x") is None:
                    positioned["x"] = 100 + level * 260
                if positioned.get("y") is None:
                    positioned["y"] = 90 + idx * 150
                laid_out.append(positioned)

        laid_out.sort(key=lambda component: index_by_id.get(component["id"], 0))
        return laid_out

    def _serialize_diagram(
        self,
        title: str,
        provider: str,
        engine: str,
        diagram_type: str,
        components: List[Dict[str, Any]],
        code: Optional[str] = None,
    ) -> str:
        payload: Dict[str, Any] = {
            "title": title,
            "provider": provider,
            "engine": engine,
            "type": diagram_type,
            "components": components,
        }
        if code:
            payload["code"] = code

        return "/diagram" + self._format_block(payload)

    def _format_block(self, payload: Dict[str, Any]) -> str:
        return json.dumps(payload, indent=2, ensure_ascii=False)

    def _build_service_map(self, components: List[Dict[str, Any]], provider: str) -> List[Dict[str, Any]]:
        service_map: List[Dict[str, Any]] = []
        for component in components:
            service_map.append(
                {
                    "id": component["id"],
                    "type": component["type"],
                    "provider": provider,
                    "service": component.get("provider_service") or component.get("mapped_service") or component["type"],
                    "label": component.get("label"),
                }
            )
        return service_map

    def _build_summary(self, components: List[Dict[str, Any]], provider: str) -> str:
        if not components:
            return f"No components defined for {provider}"
        mapped_services = [component.get("provider_service") or component["type"] for component in components]
        return f"{provider} diagram with {len(components)} components mapped to {', '.join(mapped_services[:5])}"

    def _extract_block(self, text: str, block_name: str) -> Optional[str]:
        blocks = self._extract_blocks(text, block_name)
        return blocks[0] if blocks else None

    def _extract_blocks(self, text: str, block_name: str) -> List[str]:
        results: List[str] = []
        needle = f"/{block_name}"
        index = 0
        while index < len(text):
            start = text.find(needle, index)
            if start == -1:
                break
            brace_start = text.find("{", start)
            if brace_start == -1:
                break
            depth = 0
            in_string = False
            escaped = False
            for cursor in range(brace_start, len(text)):
                char = text[cursor]
                if in_string:
                    if escaped:
                        escaped = False
                    elif char == "\\":
                        escaped = True
                    elif char == '"':
                        in_string = False
                else:
                    if char == '"':
                        in_string = True
                    elif char == "{":
                        depth += 1
                    elif char == "}":
                        depth -= 1
                        if depth == 0:
                            results.append(text[brace_start + 1 : cursor])
                            index = cursor + 1
                            break
            else:
                break
        return results

    def _parse_jsonish(self, raw: str) -> Dict[str, Any]:
        cleaned = self._strip_comments(raw)
        cleaned = self._remove_trailing_commas(cleaned)
        cleaned = self._quote_bare_keys("{" + cleaned + "}")
        try:
            payload = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Unable to parse diagram DSL block: {exc.msg}") from exc
        if not isinstance(payload, dict):
            raise ValueError("Parsed DSL block did not produce an object.")
        return payload

    def _quote_bare_keys(self, text: str) -> str:
        pattern = re.compile(r'(^|[\{,]\s*)([A-Za-z_][A-Za-z0-9_\-]*)\s*:', flags=re.MULTILINE)

        def replace(match: re.Match[str]) -> str:
            prefix = match.group(1)
            key = match.group(2)
            return f'{prefix}"{key}":'

        while True:
            updated = pattern.sub(replace, text)
            if updated == text:
                return updated
            text = updated

    def _strip_comments(self, text: str) -> str:
        result: List[str] = []
        in_string = False
        escaped = False
        index = 0
        while index < len(text):
            char = text[index]
            next_char = text[index + 1] if index + 1 < len(text) else ""
            if in_string:
                result.append(char)
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    in_string = False
                index += 1
                continue
            if char == '"':
                in_string = True
                result.append(char)
                index += 1
                continue
            if char == "/" and next_char == "/":
                while index < len(text) and text[index] not in "\r\n":
                    index += 1
                continue
            result.append(char)
            index += 1
        return "".join(result)

    def _remove_trailing_commas(self, text: str) -> str:
        pattern = re.compile(r",(\s*[}\]])")
        while True:
            updated = pattern.sub(r"\1", text)
            if updated == text:
                return updated
            text = updated

    def _parse_graph_code(self, code: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, str]]]:
        nodes: Dict[str, Dict[str, Any]] = {}
        edges: List[Dict[str, str]] = []
        statements = re.split(r"[\n;]+", code)
        for statement in statements:
            statement = statement.strip()
            if not statement or statement.startswith("graph "):
                continue
            match = re.search(r"([A-Za-z0-9_\-]+)\s*--?>\s*([A-Za-z0-9_\-]+)", statement)
            if not match:
                continue
            source, target = match.group(1), match.group(2)
            for node_id in [source, target]:
                if node_id not in nodes:
                    nodes[node_id] = {
                        "id": node_id,
                        "type": "Compute",
                        "label": self._prettify_label(node_id),
                        "connects_to": [],
                    }
            nodes[source].setdefault("connects_to", [])
            if target not in nodes[source]["connects_to"]:
                nodes[source]["connects_to"].append(target)
            edges.append({"source": source, "target": target})

        return list(nodes.values()), self._dedupe_edges(edges)

    def _map_service(self, component_type: str, provider: str) -> str:
        if provider == "generic":
            return component_type
        mapping = self.catalog.get("serviceMappings", {}).get(component_type, {})
        return str(mapping.get(provider) or mapping.get("generic") or component_type)

    def _find_generic_entry(self, component_type: str) -> Dict[str, Any]:
        for category in self.catalog.get("categories", []):
            for component in category.get("components", []):
                if component.get("type") == component_type:
                    entry = deepcopy(component)
                    entry["category"] = category.get("label")
                    return entry
        return {"type": component_type, "label": component_type, "icon": "box", "category": "Other"}

    def _category_for_type(self, component_type: str) -> str:
        entry = self._find_generic_entry(component_type)
        return str(entry.get("category") or "Other")

    def _normalize_provider(self, provider: Any) -> str:
        provider_text = str(provider or "generic")
        if provider_text.lower() == "generic":
            return "generic"
        for candidate in ["AWS", "Azure", "GCP"]:
            if provider_text.lower() == candidate.lower():
                return candidate
        return "generic"

    def _title_from_prompt(self, prompt: str) -> str:
        compact = " ".join(prompt.strip().split())
        if not compact:
            return "Untitled diagram"
        return compact[:60] + ("..." if len(compact) > 60 else "")

    def _title_from_id(self, diagram_id: Any) -> str:
        if not diagram_id:
            return "Sheet 1"
        text = str(diagram_id).replace("-", " ").replace("_", " ").strip()
        if not text:
            return "Sheet 1"
        return text[:1].upper() + text[1:]

    def _slugify(self, value: str) -> str:
        slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
        return slug or f"node-{uuid4().hex[:6]}"

    def _prettify_label(self, value: str) -> str:
        return value.replace("-", " ").replace("_", " ").title()
