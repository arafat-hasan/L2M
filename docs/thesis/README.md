# L2M Thesis

Thesis defense document for **L2M: An LLM-Driven Lyrics-to-Melody Generation
System with Emotion-Aware Alignment**, in the format of
[arafat-hasan/undergraduate-thesis](https://github.com/arafat-hasan/undergraduate-thesis)
(Dept. of CSE, MBSTU).

## Build

```bash
make
```

Output lands in `main.pdf`; intermediate files stay in `build/`. Other
targets:

| Target | Effect |
|---|---|
| `make` | build `main.pdf` (rebuilds only when a source changed) |
| `make watch` | rebuild continuously on every save |
| `make view` | build, then open the PDF |
| `make clean` | remove build artifacts, keep `main.pdf` |
| `make distclean` | remove build artifacts and `main.pdf` |
| `make toolchain` | print the LaTeX binaries that will be used |
| `make manual` | four-pass `pdflatex`/`biber` build without latexmk |

`pdflatex` and `biber` must come from the same TeX distribution, otherwise
biber fails with a `.bcf` version mismatch. The Makefile picks the first
directory providing both; override it if it guesses wrong:

```bash
make TEXBIN=/usr/local/texlive/2025/bin/x86_64-linux
```

## Structure

- `main.tex` — document skeleton (front matter, chapters, bibliography)
- `preamble.tex` — all styling (fonts, headers, TOC, captions) from the template
- `titlepage.tex`, `evaluation.tex`, `approval.tex`, `authorship.tex`,
  `dedication.tex`, `abstract.tex`, `acknowledgment.tex` — front matter
- `chapters/NN.*.tex` — chapter bodies; `chapters/nameN.tex` — divider pages
- `references.bib` — bibliography (biblatex, IEEE style)

## Placeholders to update before submission

- Student ID on title page / approval / declaration (currently `CE-210926`)
- Submission month/year (currently August 2026)
- Evaluation committee names in `evaluation.tex`
- Chairman name in `approval.tex`
