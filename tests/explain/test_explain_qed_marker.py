from __future__ import annotations

from opengalois.explain.proof_model import ProofDocument, ProofStatement, par
from opengalois.explain.renderers.latex import render_latex
from opengalois.explain.renderers.markdown import render_markdown


def test_latex_renderer_adds_hollow_square_qed_marker() -> None:
    document = ProofDocument(
        title="Example",
        introduction=(),
        statements=(
            ProofStatement(
                fact_id="F1",
                statement=(par("Claim."),),
                proof=(par("Proof."),),
            ),
        ),
    )

    rendered = render_latex(document)

    assert r"\hfill\(\square\)" in rendered


def test_markdown_renderer_adds_hollow_square_qed_marker() -> None:
    document = ProofDocument(
        title="Example",
        introduction=(),
        statements=(
            ProofStatement(
                fact_id="F1",
                statement=(par("Claim."),),
                proof=(par("Proof."),),
            ),
        ),
    )

    rendered = render_markdown(document)

    assert r"$\square$" in rendered
