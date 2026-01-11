"""Pipeline module for v1.4 architecture."""

from philocr.pipeline.orchestrator import PipelineOrchestrator

__all__ = ["PipelineOrchestrator"]


def process_document(
    pdf_path: str,
    output_dir: str,
    config: "PipelineConfig",  # type: ignore[type-arg]
) -> "Document":  # type: ignore[type-arg]
    """Convenience function to process a document through the full pipeline.

    Args:
        pdf_path: Path to source PDF
        output_dir: Base directory for all stage outputs
        config: Pipeline configuration

    Returns:
        Complete Document object
    """
    orchestrator = PipelineOrchestrator(config, output_dir)
    return orchestrator.process_document(pdf_path)
