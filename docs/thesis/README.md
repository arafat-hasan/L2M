# L2M Undergraduate Thesis

Thesis defense document for **L2M: An LLM-Driven Lyrics-to-Melody Generation
System with Emotion-Aware Alignment**, in the format of
[arafat-hasan/undergraduate-thesis](https://github.com/arafat-hasan/undergraduate-thesis)
(Dept. of CSE, MBSTU).

## Build

```bash
pdflatex main.tex
biber main
pdflatex main.tex
pdflatex main.tex
```

Note: `pdflatex` and `biber` must come from the same TeX distribution
(e.g., both from MacTeX at `/Library/TeX/texbin/`), otherwise biber fails
with a `.bcf` version mismatch.

## Structure

- `main.tex` — document skeleton (front matter, chapters, bibliography)
- `preamble.tex` — all styling (fonts, headers, TOC, captions) from the template
- `titlepage.tex`, `evaluation.tex`, `approval.tex`, `authorship.tex`,
  `dedication.tex`, `abstract.tex`, `acknowledgment.tex` — front matter
- `chapters/NN.*.tex` — chapter bodies; `chapters/nameN.tex` — divider pages
- `references.bib` — bibliography (biblatex, IEEE style)

## Placeholders to update before submission

- Student ID on title page / approval / declaration (currently `CE-16024`)
- Submission month/year (currently August 2026)
- Evaluation committee names in `evaluation.tex`
- Chairman name in `approval.tex`
