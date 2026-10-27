"""Confere referências locais em Markdown e a assinatura dos arquivos PNG."""

from pathlib import Path
from urllib.parse import unquote, urlsplit
import re
import sys


LINK = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def validar(root: Path) -> list[str]:
    root = root.resolve()
    errors = []
    for source in sorted(root.rglob("*.md")):
        if ".git" in source.relative_to(root).parts:
            continue
        text = source.read_text(encoding="utf-8")
        for match in LINK.finditer(text):
            raw_target = match.group(1).strip().split(' "', 1)[0].strip("<>")
            parsed = urlsplit(raw_target)
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            path = unquote(parsed.path)
            target = ((root / path.lstrip("/")) if path.startswith("/") else (source.parent / path)).resolve()
            if not target.is_relative_to(root) or not target.exists():
                line = text.count("\n", 0, match.start()) + 1
                errors.append(f"{source.relative_to(root)}:{line}: referência local ausente: {raw_target}")
    for picture in sorted(root.rglob("*.png")):
        if ".git" in picture.relative_to(root).parts:
            continue
        with picture.open("rb") as stream:
            signature = stream.read(8)
        if signature != PNG_SIGNATURE:
            errors.append(f"{picture.relative_to(root)}: assinatura PNG inválida")
    return errors


if __name__ == "__main__":
    repository = Path(__file__).resolve().parents[1]
    problems = validar(repository)
    if problems:
        print("\n".join(problems))
        sys.exit(1)
    print("Referências locais em Markdown e assinaturas PNG verificadas.")
