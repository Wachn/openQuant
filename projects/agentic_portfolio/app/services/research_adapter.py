from __future__ import annotations

import importlib
import sys
from pathlib import Path
from typing import Dict, List


def query_quant_rag(query: str, workspace: Path, topk: int = 8) -> Dict[str, object]:
    quant_rag_project = Path(__file__).resolve().parents[3] / "quant_rag"
    if not quant_rag_project.exists():
        raise FileNotFoundError(f"quant_rag project not found at {quant_rag_project}")

    project_path = str(quant_rag_project)
    if project_path not in sys.path:
        sys.path.insert(0, project_path)

    rag_module = importlib.import_module("rag")
    rag_module_path = Path(rag_module.__file__).resolve()
    expected_root = quant_rag_project.resolve()
    if expected_root not in rag_module_path.parents:
        raise ImportError(f"Unexpected rag module path: {rag_module_path}")

    from rag.agents.rag_agent import RAGAgent
    from rag.config import WorkspaceConfig
    from rag.retrieval.retriever import HybridRetriever

    ws = WorkspaceConfig(root=workspace)
    retriever = HybridRetriever(ws)
    retriever.load_indexes()
    agent = RAGAgent(retriever, llm=None)
    result = agent.answer(query, topk=topk)

    evidence: List[Dict[str, object]] = []
    for item in result.evidence:
        evidence.append(
            {
                "evidence_id": f"chunk:{item.chunk_id}",
                "source_type": item.source_type,
                "summary": item.snippet,
                "source_ref": item.source_path,
                "locator": item.locator,
                "chunk_id": item.chunk_id,
            }
        )

    return {
        "answer": result.answer,
        "confidence": float(result.confidence),
        "evidence": evidence,
        "workspace": str(workspace.resolve()),
    }
