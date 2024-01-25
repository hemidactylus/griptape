from __future__ import annotations

from attr import define, field, Factory
from typing import IO, Optional

from pathlib import Path
from pypdf import PdfReader

from griptape.utils import str_to_hash, execute_futures_dict
from griptape.artifacts import TextArtifact
from griptape.chunkers import PdfChunker
from griptape.loaders import TextLoader


@define
class PdfLoader(TextLoader):
    chunker: PdfChunker = field(
        default=Factory(lambda self: PdfChunker(tokenizer=self.tokenizer, max_tokens=self.max_tokens), takes_self=True),
        kw_only=True,
    )

    def load(self, source: str | IO | Path, password: Optional[str] = None, *args, **kwargs) -> list[TextArtifact]:
        return self._load_pdf(source, password)

    def load_collection(
        self, sources: list[str | IO | Path], password: Optional[str] = None, *args, **kwargs
    ) -> dict[str, list[TextArtifact]]:
        return execute_futures_dict(
            {
                str_to_hash(s.decode())
                if isinstance(s, bytes)
                else str_to_hash(str(s)): self.futures_executor.submit(self._load_pdf, s, password)
                for s in sources
            }
        )

    def _load_pdf(self, stream: str | IO | Path, password: Optional[str]) -> list[TextArtifact]:
        reader = PdfReader(stream, strict=True, password=password)

        return self.text_to_artifacts("\n".join([p.extract_text() for p in reader.pages]))
