"""
Chat route — the main conversational endpoint driving the 16-step pipeline.
"""
import uuid
import json
import logging
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, HTTPException, Depends

from models.schemas import (
    ChatRequest, ChatResponse,
    ChatHistoryResponse, RefinementRequest,
    ListChatsResponse, ChatSessionSummary, DeploymentPlan
)
from routes.auth import get_current_user
from services.gemini_service import (
    classify_intent,
    generate_blueprint,
    score_providers,
    generate_explanation,
    summarize_history,
    get_relevant_market_intel,
    fetch_market_intel_documents,
)
from services.database import (
    chats_collection, blueprints_collection, market_intel_collection, is_connected,
)
from services.tavily_service import enrich_market_intel

logger = logging.getLogger(__name__)
router = APIRouter()

COMPACTION_THRESHOLD = 10


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, current_user: dict = Depends(get_current_user)):
    """
    Main conversational endpoint.
    Implements steps 1-10 of the 16-step pipeline:
      1. User input  →  2. Intent classify  →  3. Constraint extract
      4. Gap detect  →  5. Question select  →  6. Q&A
      7. Profile build  →  8. Blueprint gen  →  9. Score  →  10. Unified view  →  11. Aggregated metrics
    """
    try:
        chat_id = req.chat_id or str(uuid.uuid4())
        existing_summary = ""
        session = None

        # ── Step 0: Load Session Context ──
        if is_connected():
            chats = chats_collection()
            session = await chats.find_one({"chatId": chat_id})
            existing_summary = session.get("summary", "") if session else ""

        # ── Step 2-4: Intent Classification + Constraint Extraction ──
        # Build context from history + summary for better analysis
        context_parts = []
        if existing_summary:
            context_parts.append(f"Session Context: {existing_summary}")
        if session and session.get("metadata", {}).get("current_constraints"):
            context_parts.append(f"Previously Known Constraints: {json.dumps(session['metadata']['current_constraints'])}")
            
        if req.history:
            history_text = "\n".join(
                f"{m.get('role', 'user')}: {m.get('content', '')}" for m in req.history[-12:]
            )
            context_parts.append(f"Recent History:\n{history_text}")
        context_parts.append(f"Current Message: {req.message}")

        augmented_query = "\n\n".join(context_parts)
        analysis = await classify_intent(augmented_query)
        logger.info(
            f"Intent: {analysis.get('intent')} | "
            f"Confidence: {analysis.get('confidence')} | "
            f"Missing: {analysis.get('missing_critical', [])}"
        )

        # ── Step 5-6: If critical fields are missing, ask follow-up ──
        missing = analysis.get("missing_critical", [])
        follow_up = analysis.get("follow_up_question")

        if missing and follow_up:
            # Save partial state and ask for clarification
            if is_connected():
                await chats_collection().update_one(
                    {"chatId": chat_id},
                    {
                        "$set": {
                            "chatId": chat_id,
                            "user_email": current_user.get("email"),
                            "metadata.current_constraints": analysis.get("constraints", {}),
                            "metadata.intent": analysis.get("intent"),
                            "metadata.stage": analysis.get("stage"),
                            "updatedAt": datetime.now(timezone.utc),
                        },
                        "$push": {
                            "messages": {
                                "$each": [
                                    {"role": "user", "content": req.message, "ts": datetime.now(timezone.utc).isoformat()},
                                    {"role": "model", "content": follow_up, "ts": datetime.now(timezone.utc).isoformat()},
                                ]
                            }
                        },
                        "$setOnInsert": {
                            "createdAt": datetime.now(timezone.utc),
                            "expiresAt": datetime.now(timezone.utc) + timedelta(days=30),
                        },
                    },
                    upsert=True,
                )

            return ChatResponse(
                chat_id=chat_id,
                phase="clarifying",
                explanation=follow_up,
                follow_up_question=follow_up,
                intent_analysis=analysis,
            )

        # ── Step 7-8: Profile Build + Blueprint Generation ──
        constraints = {}
        for k, v in analysis.get("constraints", {}).items():
            if isinstance(v, dict):
                constraints[k] = v.get("value")
            else:
                constraints[k] = v

        from services.knowledge_service import search_theory
        
        intent = analysis.get("intent", "web_app")
        
        # ── Step 7.5: Execute Local Knowledge Base RAG ──
        # Query the local dataset for theory relevant to the workload and constraints
        search_query = f"{intent} architecture design {' '.join(str(v) for v in constraints.values())}"
        try:
            theory_context = await search_theory(search_query)
        except Exception as e:
            logger.warning(f"Failed to search RAG knowledge base: {e}")
            theory_context = ""
            
        blueprint = await generate_blueprint(intent, constraints, theory_context=theory_context)
        node_count = len(blueprint.get("nodes", []))
        logger.info(f"Blueprint generated: {node_count} nodes, {len(blueprint.get('edges', []))} edges")

        # ── Step 9: Scoring with Market Intel & Daily Macro Pulse ──
        intel_str = ""
        pulse_str = ""
        if is_connected():
            try:
                # 1. Fetch the background async daily pulse for macro changes
                pulse = await market_intel_collection().find_one({"type": "macro_pulse"})
                if pulse and pulse.get("data"):
                    pulse_str = f"DAILY MACRO PULSE (Important Context):\n{pulse['data']}\n\n"
                    
                # 2. Fetch workload-specific precision intel
                intel_data = await enrich_market_intel(
                    "cloud providers",
                    f"{intent} workload",
                    constraints.get("region", "us-east-1"),
                )
                if intel_data:
                    intel_str = pulse_str + f"SPECIFIC INTEL:\n{intel_data.get('answer', '')}"
                else:
                    intel_str = pulse_str
            except Exception as e:
                logger.warning(f"Market intel fetch failed (non-fatal): {e}")

        scoring = await score_providers(blueprint, constraints, market_intel=intel_str, theory_context=theory_context)
        scoring.sort(key=lambda p: p.get("totalScore", 0), reverse=True)

        # ── Step 10: Generate Explanation with Market Intel ──
        # Extract service names from nodes to fetch relevant limits/specs
        service_types = list(set([n.get("type") for n in blueprint.get("nodes", [])]))
        primary_provider = scoring[0].get("id", "aws") if scoring else "aws"
        if scoring and not scoring[0].get("id"):
            logger.warning("LLM scoring[0] missing 'id' field. Falling back to 'aws' for intel.")
        
        market_intel_data = await get_relevant_market_intel(primary_provider, service_types)
        market_intel_raw = await fetch_market_intel_documents(primary_provider, service_types)
        
        explanation = await generate_explanation(
            blueprint, 
            constraints=constraints, 
            theory_context=theory_context,
            market_intel=market_intel_data
        )

        # Calculate aggregated deployment plan before persistence so it is
        # available for metadata writes below.
        plan = calculate_plan_metrics(market_intel_raw)

        # ── Persist to MongoDB ──
        blueprint_id = str(uuid.uuid4())
        if is_connected():
            await blueprints_collection().insert_one({
                "blueprintId": blueprint_id,
                "chatId": chat_id,
                "type": "generic",
                "provider": "generic",
                "intent": intent,
                "constraints": constraints,
                "nodes": blueprint.get("nodes", []),
                "edges": blueprint.get("edges", []),
                "scores": {p.get("id", f"provider_{i}"): p for i, p in enumerate(scoring)},
                "explanation": explanation,
                "theory_context": theory_context,
                "createdAt": datetime.now(timezone.utc),
            })

            # ── Step 11: Compaction ──
            full_history = req.history + [
                {"role": "user", "content": req.message},
                {"role": "model", "content": explanation},
            ]
            new_summary = existing_summary
            if len(full_history) >= COMPACTION_THRESHOLD:
                logger.info("Triggering history compaction...")
                try:
                    new_summary = await summarize_history(full_history, existing_summary)
                except Exception as e:
                    logger.warning(f"Compaction failed (non-fatal): {e}")

            await chats_collection().update_one(
                {"chatId": chat_id},
                {
                    "$set": {
                        "chatId": chat_id,
                        "user_email": current_user.get("email"),
                        "summary": new_summary,
                        "metadata.last_blueprint_id": blueprint_id,
                        "metadata.current_constraints": constraints,
                        "metadata.intent": intent,
                        "metadata.deployment_plan": plan.dict() if hasattr(plan, 'dict') else plan,
                        "updatedAt": datetime.now(timezone.utc),
                    },
                    "$push": {
                        "messages": {
                            "$each": [
                                {"role": "user", "content": req.message, "ts": datetime.now(timezone.utc).isoformat()},
                                {"role": "model", "content": explanation, "ts": datetime.now(timezone.utc).isoformat()},
                            ]
                        }
                    },
                    "$setOnInsert": {
                        "createdAt": datetime.now(timezone.utc),
                        "expiresAt": datetime.now(timezone.utc) + timedelta(days=30),
                    },
                },
                upsert=True,
            )

        return ChatResponse(
            chat_id=chat_id,
            phase="scored",
            explanation=explanation,
            blueprint=blueprint,
            scoring=scoring,
            intent_analysis=analysis,
            theory_context=theory_context,
            deployment_plan=plan
        )

    except Exception as e:
        logger.exception("Chat endpoint error")
        raise HTTPException(status_code=500, detail=str(e))


def calculate_plan_metrics(intel_list: list) -> DeploymentPlan:
    """Aggregates node-level intel into a top-level deployment plan."""
    # Better default estimates if no intel found
    # If it's empty, we should still try to be 
    if not intel_list:
        return DeploymentPlan(
            expected_latency_ms=450, # More realistic default for serverless cold-starts
            concurrency_limit=50, 
            total_users_capacity=5000, 
            compliance_status=["SOC2 (Standard)"],
            scalability_rating="Medium"
        )
    
    latencies = []
    concurrencies = []
    certs = set()
    
    for item in intel_list:
        data = item.get("data", {})
        perf = data.get("performance", {})
        comp = data.get("compliance", {})
        
        l_val = perf.get("latency_ms")
        if l_val:
            # If latency is given as a string or range, try to parse
            try:
                if isinstance(l_val, str):
                    import re
                    digits = [int(d) for d in re.findall(r'\d+', l_val)]
                    if digits: latencies.append(sum(digits)/len(digits))
                else:
                    latencies.append(float(l_val))
            except: pass
            
        c_val = perf.get("concurrent_users_limit")
        if c_val:
            try:
                concurrencies.append(float(c_val))
            except: pass

        if comp.get("certifications"): 
            for c in comp["certifications"]: certs.add(c)

    # Use avg for latency, min for concurrency (bottleneck principle)
    avg_latency = int(sum(latencies) / len(latencies)) if latencies else 350
    min_concurrency = int(min(concurrencies)) if concurrencies else 200

    return DeploymentPlan(
        expected_latency_ms=avg_latency,
        concurrency_limit=min_concurrency,
        total_users_capacity=min_concurrency * 20, # Rough heuristic
        compliance_status=list(certs) if certs else ["ISO27001", "SOC2"],
        scalability_rating="High" if avg_latency < 50 else "High (Auto-scale)"
    )


@router.get("/chat/{chat_id}", response_model=ChatHistoryResponse)
async def get_chat_history(chat_id: str, current_user: dict = Depends(get_current_user)):
    """Retrieve the full conversation history for a chat session."""
    if not is_connected():
        raise HTTPException(status_code=503, detail="Database unavailable")

    session = await chats_collection().find_one({"chatId": chat_id})
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")

    return ChatHistoryResponse(
        chat_id=chat_id,
        messages=session.get("messages", []),
        summary=session.get("summary", ""),
        metadata=session.get("metadata", {}),
    )


@router.post("/chat/refine")
async def refine_architecture(req: RefinementRequest, current_user: dict = Depends(get_current_user)):
    """
    Step 12: User refines constraints → re-generate blueprint + re-score.
    Keeps the same chat session but creates a new blueprint version.
    """
    try:
        if not is_connected():
            raise HTTPException(status_code=503, detail="Database unavailable")

        # Load existing blueprint
        existing = await blueprints_collection().find_one({"blueprintId": req.blueprint_id})
        if not existing:
            raise HTTPException(status_code=404, detail="Blueprint not found")

        # Merge constraints
        old_constraints = existing.get("constraints", {})
        merged = {**old_constraints, **req.updated_constraints}
        intent = existing.get("intent", "web_app")

        # ── Step 12.5: Execute Local Knowledge Base RAG for Refinement ──
        from services.knowledge_service import search_theory
        search_query = f"{intent} architecture design {' '.join(str(v) for v in merged.values())}"
        try:
            theory_context = await search_theory(search_query)
        except Exception as e:
            logger.warning(f"Failed to search RAG knowledge base during refinement: {e}")
            theory_context = ""

        # Re-generate
        blueprint = await generate_blueprint(intent, merged, theory_context=theory_context)
        scoring = await score_providers(blueprint, merged, theory_context=theory_context)
        scoring.sort(key=lambda p: p.get("totalScore", 0), reverse=True)
        explanation = await generate_explanation(blueprint, constraints=merged, theory_context=theory_context)

        # Persist new version
        new_id = str(uuid.uuid4())
        await blueprints_collection().insert_one({
            "blueprintId": new_id,
            "chatId": req.chat_id,
            "parentId": req.blueprint_id,
            "type": "generic",
            "provider": "generic",
            "intent": intent,
            "constraints": merged,
            "nodes": blueprint.get("nodes", []),
            "edges": blueprint.get("edges", []),
            "scores": {p.get("id", f"provider_{i}"): p for i, p in enumerate(scoring)},
            "explanation": explanation,
            "createdAt": datetime.now(timezone.utc),
        })

        # Update chat metadata
        await chats_collection().update_one(
            {"chatId": req.chat_id},
            {"$set": {
                "metadata.last_blueprint_id": new_id,
                "metadata.current_constraints": merged,
                "updatedAt": datetime.now(timezone.utc),
            }},
        )

        return ChatResponse(
            chat_id=req.chat_id,
            phase="scored",
            explanation=explanation,
            blueprint=blueprint,
            scoring=scoring,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Refinement error")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chats", response_model=ListChatsResponse)
async def list_chats(current_user: dict = Depends(get_current_user)):
    """Retrieve all chat sessions for the current user."""
    if not is_connected():
        raise HTTPException(status_code=503, detail="Database unavailable")

    user_email = current_user.get("email")
    if not user_email:
        raise HTTPException(status_code=400, detail="User email not found")

    cursor = chats_collection().find(
        {"user_email": user_email},
        {"chatId": 1, "metadata.intent": 1, "summary": 1, "updatedAt": 1}
    ).sort("updatedAt", -1)

    chats = []
    async for doc in cursor:
        chats.append(ChatSessionSummary(
            chat_id=doc.get("chatId", ""),
            intent=doc.get("metadata", {}).get("intent", "web_app"),
            summary=doc.get("summary", ""),
            updated_at=doc.get("updatedAt").isoformat() if doc.get("updatedAt") else None
        ))

    return ListChatsResponse(chats=chats)
