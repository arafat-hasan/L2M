# Makefile for the L2M M.Engg. project report
#
#   make            build main.pdf
#   make watch      rebuild continuously on file changes
#   make view       build and open the PDF
#   make clean      remove build artifacts, keep main.pdf
#   make distclean  remove build artifacts and main.pdf
#   make toolchain  show which LaTeX binaries will be used
#
# pdflatex and biber must come from the SAME TeX distribution, otherwise
# biber aborts with a .bcf version mismatch. TEXBIN pins both; override it
# on the command line if the auto-detected distribution is not the one you
# want, e.g.  make TEXBIN=/usr/local/texlive/2025/bin/x86_64-linux

MAIN    := main
OUTDIR  := build
PDF     := $(MAIN).pdf

# First directory that provides both pdflatex and biber wins.
TEXBIN ?= $(firstword $(foreach d,/Library/TeX/texbin /usr/local/texlive/*/bin/* /opt/texlive/*/bin/* $(subst :, ,$(PATH)),$(if $(and $(wildcard $(d)/pdflatex),$(wildcard $(d)/biber)),$(d))))

ifeq ($(TEXBIN),)
  $(error No directory found containing both pdflatex and biber; set TEXBIN=/path/to/texbin)
endif

PDFLATEX := $(TEXBIN)/pdflatex
BIBER    := $(TEXBIN)/biber
LATEXMK  := $(TEXBIN)/latexmk

LATEXMKFLAGS := -pdf -interaction=nonstopmode -halt-on-error -file-line-error \
                -outdir=$(OUTDIR)

# latexmk resolves pdflatex/biber through PATH; putting TEXBIN first keeps
# both from the same distribution.
RUN := PATH="$(TEXBIN):$$PATH"

SOURCES := $(wildcard *.tex) $(wildcard chapters/*.tex) references.bib \
           $(wildcard images/*)

.PHONY: all pdf watch view clean distclean toolchain manual

all: pdf
pdf: $(PDF)

$(PDF): $(SOURCES)
	@$(RUN) $(LATEXMK) $(LATEXMKFLAGS) $(MAIN).tex
	@cp $(OUTDIR)/$(PDF) $(PDF)
	@echo "==> built $(PDF)"

# Continuous preview: rebuilds on every save until interrupted.
watch:
	$(RUN) $(LATEXMK) $(LATEXMKFLAGS) -pvc $(MAIN).tex

view: $(PDF)
	@(command -v open >/dev/null && open $(PDF)) || \
	 (command -v xdg-open >/dev/null && xdg-open $(PDF)) || \
	 echo "No PDF viewer found; open $(PDF) manually."

# Fallback when latexmk is unavailable: the classic four-pass sequence.
manual:
	$(PDFLATEX) -interaction=nonstopmode $(MAIN).tex
	$(BIBER) $(MAIN)
	$(PDFLATEX) -interaction=nonstopmode $(MAIN).tex
	$(PDFLATEX) -interaction=nonstopmode $(MAIN).tex

clean:
	@$(LATEXMK) -outdir=$(OUTDIR) -C $(MAIN).tex >/dev/null 2>&1 || true
	@rm -rf $(OUTDIR)
	@rm -f $(MAIN).aux $(MAIN).bbl $(MAIN).bcf $(MAIN).blg $(MAIN).idx \
	       $(MAIN).lof $(MAIN).log $(MAIN).lot $(MAIN).nlo $(MAIN).out \
	       $(MAIN).run.xml $(MAIN).toc $(MAIN).fls $(MAIN).fdb_latexmk
	@echo "==> cleaned build artifacts"

distclean: clean
	@rm -f $(PDF)
	@echo "==> removed $(PDF)"

toolchain:
	@echo "TEXBIN   = $(TEXBIN)"
	@echo "pdflatex = $$($(PDFLATEX) --version | head -1)"
	@echo "biber    = $$($(BIBER) --version)"
	@echo "latexmk  = $$($(LATEXMK) --version | head -1)"
