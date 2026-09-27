from pathlib import Path
import re


ROOT = Path(__file__).resolve().parent
README = ROOT / "README.md"
DOCS = ROOT / "docs"


def split_sections(lines):
    sections = []
    current_title = None
    current_lines = []

    for line in lines:
        match = re.match(r"^## (.+?)\s*$", line)
        if match:
            if current_title is not None:
                sections.append((current_title, current_lines))
            current_title = match.group(1)
            current_lines = [line]
        elif current_title is None:
            current_lines.append(line)
        else:
            current_lines.append(line)

    if current_title is not None:
        sections.append((current_title, current_lines))
    return sections


def write_page(filename, title, content):
    shifted = []
    for line in content:
        match = re.match(r"^(#{3,6}) (.+)$", line)
        if match:
            line = f"{match.group(1)[1:]} {match.group(2)}"
        shifted.append(line)
    body = "\n".join(shifted).strip()
    (DOCS / filename).write_text(f"# {title}\n\n{body}\n", encoding="utf-8")


def main():
    source = README.read_text(encoding="utf-8").splitlines()
    DOCS.mkdir(exist_ok=True)
    sections = split_sections(source)

    intro_end = next(
        (i for i, line in enumerate(source) if line.strip() == "## Table of contents"),
        None,
    )
    if intro_end is None:
        raise ValueError("README.md is missing its Table of contents heading")

    intro = source[:intro_end]
    if intro and intro[0].strip() == "---":
        closing = next(
            (i for i in range(1, len(intro)) if intro[i].strip() == "---"),
            None,
        )
        if closing is None:
            raise ValueError("README.md has an unterminated front matter block")
        intro = intro[closing + 1:]
    intro = [line for line in intro if line.strip() != "# NCP-AIN Detailed Study Guide"]
    intro.extend(
        [
            "",
            "## Chapters",
            "",
            "- [Study plan](study-plan.md)",
            "- [Topology case studies and packet flows](topology.md)",
            "- [AI Data Center Design and Optimization — 5%](chapter-1.md)",
            "- [NVIDIA Spectrum Networking — 30%](chapter-2.md)",
            "- [NVIDIA InfiniBand Networking — 30%](chapter-3.md)",
            "- [Kubernetes Integration — 5%](chapter-4.md)",
            "- [Troubleshooting Tools — 20%](chapter-5.md)",
            "- [Automation and Configuration — 10%](chapter-6.md)",
            "- [Official resources](resources.md)",
            "- [Suggested readings](readings.md)",
            "- [Guided study curriculum](curriculum.md)",
        ]
    )
    write_page("index.md", "NCP-AIN Detailed Study Guide", intro)

    pages = {
        "Study plan": ("study-plan.md", "Study plan"),
        "Topology case studies and packet flows": ("topology.md", "Topology case studies and packet flows"),
        "1. AI Data Center Design and Optimization — 5%": ("chapter-1.md", "1. AI Data Center Design and Optimization — 5%"),
        "2. NVIDIA Spectrum Networking — 30%": ("chapter-2.md", "2. NVIDIA Spectrum Networking — 30%"),
        "3. NVIDIA InfiniBand Networking — 30%": ("chapter-3.md", "3. NVIDIA InfiniBand Networking — 30%"),
        "4. Kubernetes Integration — 5%": ("chapter-4.md", "4. Kubernetes Integration — 5%"),
        "5. Troubleshooting Tools — 20%": ("chapter-5.md", "5. Troubleshooting Tools — 20%"),
        "6. Automation and Configuration — 10%": ("chapter-6.md", "6. Automation and Configuration — 10%"),
    }

    found = set()
    for title, lines in sections:
        if title in pages:
            filename, page_title = pages[title]
            write_page(filename, page_title, lines[1:])
            found.add(title)
        elif title == "Official resources":
            content = lines[1:]
            suggested = next(
                (i for i, line in enumerate(content) if line.strip() == "### Suggested readings"),
                None,
            )
            curriculum = next(
                (i for i, line in enumerate(content) if line.strip() == "### Guided study curriculum"),
                None,
            )
            if suggested is None or curriculum is None or curriculum <= suggested:
                raise ValueError("Official resources must contain suggested readings and curriculum")

            write_page("resources.md", "Official resources", content[:suggested])
            write_page("readings.md", "Suggested readings", content[suggested + 1:curriculum])
            write_page("curriculum.md", "Guided study curriculum", content[curriculum + 1:])
            found.add(title)

    expected = set(pages) | {"Official resources"}
    missing = expected - found
    if missing:
        raise ValueError(f"README.md is missing expected sections: {sorted(missing)}")


if __name__ == "__main__":
    main()
