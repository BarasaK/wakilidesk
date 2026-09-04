from __future__ import annotations

import html
import re


def render_markdown_document(markdown_text: str) -> str:
    lines = markdown_text.splitlines()
    output: list[str] = []
    list_type: str | None = None
    in_code = False
    code_language = ""
    code_lines: list[str] = []

    for line in lines:
        if line.startswith("```"):
            if in_code:
                output.append(_render_code_block(code_language, code_lines))
                in_code = False
                code_language = ""
                code_lines = []
            else:
                list_type = _close_list(output, list_type)
                in_code = True
                code_language = line.removeprefix("```").strip()
            continue

        if in_code:
            code_lines.append(line)
            continue

        stripped = line.strip()
        if not stripped:
            list_type = _close_list(output, list_type)
            continue

        heading = re.match(r"^(#{1,6})\s+(.+)$", stripped)
        if heading:
            list_type = _close_list(output, list_type)
            level = min(len(heading.group(1)), 4)
            output.append(f"<h{level}>{_render_inline(heading.group(2))}</h{level}>")
            continue

        bullet = re.match(r"^-\s+(.+)$", stripped)
        if bullet:
            if list_type != "ul":
                list_type = _switch_list(output, list_type, "ul")
            output.append(f"<li>{_render_inline(bullet.group(1))}</li>")
            continue

        ordered = re.match(r"^\d+\.\s+(.+)$", stripped)
        if ordered:
            if list_type != "ol":
                list_type = _switch_list(output, list_type, "ol")
            output.append(f"<li>{_render_inline(ordered.group(1))}</li>")
            continue

        list_type = _close_list(output, list_type)
        output.append(f"<p>{_render_inline(stripped)}</p>")

    if in_code:
        output.append(_render_code_block(code_language, code_lines))
    _close_list(output, list_type)
    return "\n".join(output)


def _switch_list(output: list[str], current: str | None, next_type: str) -> str:
    _close_list(output, current)
    output.append(f"<{next_type}>")
    return next_type


def _close_list(output: list[str], current: str | None) -> None:
    if current:
        output.append(f"</{current}>")
    return None


def _render_code_block(language: str, lines: list[str]) -> str:
    content = html.escape("\n".join(lines))
    if language == "mermaid":
        return f'<div class="mermaid">{content}</div>'
    language_class = f' class="language-{html.escape(language)}"' if language else ""
    return f"<pre><code{language_class}>{content}</code></pre>"


def _render_inline(value: str) -> str:
    escaped = html.escape(value)
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(
        r"\[([^\]]+)\]\((https?://[^)]+)\)",
        r'<a href="\2">\1</a>',
        escaped,
    )
    return escaped
