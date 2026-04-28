"""input-structure Skill — convert PDF/PPTX/DOCX/TXT to structured Markdown."""

__all__ = ["structure"]


def __getattr__(name):
    if name == "structure":
        from .main import structure
        return structure
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
