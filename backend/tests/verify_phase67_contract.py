"""Phase 6/7 public contract verification tests.

Verifies that the expected public API surface exists across the RAG and
chat service modules touched during phases 6 and 7.
"""

import ast
import pytest
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent / "app"

EXPECTED = {
    "rag/retriever.py": {
        "retrieve": ["question", "document_ids"],
    },
    "rag/prompt.py": {
        "build_prompt": ["question", "contexts", "citations"],
    },
    "rag/answer_service.py": {
        "generate_answer": ["prompt_text", "model"],
    },
    "rag/query_router.py": {
        "classify": ["question"],
    },
    "services/chat_service.py": {
        "ChatService": [],
        "ChatService.answer": ["self", "question", "document_ids"],
    },
    "utils/citation_builder.py": {
        "build_citations": ["retrieved"],
    },
    "api/chat_routes.py": {
        "chat_bp": [],
        "ask": [],
        "messages": ["session_id"],
    },
}


def parse_file(path: Path) -> ast.AST:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def module_functions(tree: ast.AST) -> dict:
    classes: dict[str, ast.ClassDef] = {}
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.ClassDef):
            classes[node.name] = node

    methods: dict[str, list[str]] = {}
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.FunctionDef):
            methods[node.name] = [a.arg for a in node.args.args]

    out = dict(methods)
    for cls_name, cls_node in classes.items():
        m: dict[str, list[str]] = {}
        for item in ast.iter_child_nodes(cls_node):
            if isinstance(item, ast.FunctionDef):
                m[item.name] = [a.arg for a in item.args.args]
        out[cls_name] = m
    return out


def module_assignments(tree: ast.AST) -> dict[str, str]:
    out: dict[str, str] = {}
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    out[target.id] = "assigned"
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            out[node.target.id] = "annotated"
    return out


def check_contract_for(rel: str, want: dict[str, list[str] | dict[str, list[str]]]) -> list[str]:
    """Run contract checks for one module and return any problems found."""
    path = BASE / rel
    tree = parse_file(path)
    funcs = module_functions(tree)
    assigns = module_assignments(tree)

    problems: list[str] = []
    for name, expected in want.items():
        # dotted name like ChatService.answer
        if "." in name:
            head, _, tail = name.partition(".")
            cls = funcs.get(head)
            if not isinstance(cls, dict) or tail not in cls:
                problems.append(f"MISSING {rel}::{name}")
                continue
            if cls[tail] != expected:
                problems.append(
                    f"METHOD_ARITY {rel}::{name}: "
                    f"expected {expected}, got {cls[tail]}"
                )
            continue

        got = funcs.get(name)
        if got is None:
            if name in assigns:
                continue
            problems.append(f"MISSING {rel}::{name}")
            continue

        if isinstance(got, dict):
            # class
            if expected != []:
                for m, margs in expected.items():
                    if m not in got:
                        problems.append(f"MISSING_METHOD {rel}::{name}::{m}")
                    elif got[m] != margs:
                        problems.append(
                            f"METHOD_ARITY {rel}::{name}::{m}: "
                            f"expected {margs}, got {got[m]}"
                        )
            continue

        if not isinstance(got, list):
            problems.append(f"NOT_A_FUNC {rel}::{name}")
            continue
        if got != expected:
            problems.append(
                f"ARITY_MISMATCH {rel}::{name}: "
                f"expected {expected}, got {got}"
            )

    return problems


@pytest.mark.parametrize("rel,want", EXPECTED.items())
def test_public_contract(rel: str, want: dict) -> None:
    """Each touched module exposes the expected public functions/classes."""
    problems = check_contract_for(rel, want)
    assert not problems, "\n".join(f" - {p}" for p in problems)


def test_full_contract() -> None:
    """All modules together satisfy the phase 6/7 public contract."""
    all_problems: list[str] = []
    for rel, want in EXPECTED.items():
        all_problems.extend(check_contract_for(rel, want))

    assert not all_problems, "\n".join(f" - {p}" for p in all_problems)
