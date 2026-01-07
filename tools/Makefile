.PRECIOUS: %.tex


TEXF_DIR := texf
TEMPLATE := $(TEXF_DIR)/rule-template.tex
OUTPUT_DIR := ../../site/static/rules
TEX_STYLES_DIR := tex-styles

export TEXINPUTS := $(TEX_STYLES_DIR):$(TEXINPUTS)

objects := $(patsubst $(TEXF_DIR)/%.texf,$(OUTPUT_DIR)/%.svg,$(wildcard $(TEXF_DIR)/*.texf))


all: $(objects)

$(OUTPUT_DIR):
	mkdir -p $(OUTPUT_DIR)

%.tex: $(TEXF_DIR)/%.texf $(TEMPLATE)
	pandoc -f latex -t latex --template $(TEMPLATE) -o $@ $<

%.pdf: %.tex
	pdflatex -interaction=nonstopmode -halt-on-error -file-line-error $*

$(OUTPUT_DIR)/%.svg: %.pdf | $(OUTPUT_DIR)
	pdf2svg $< $@

clean:
	rm -f *.tex *.pdf *.aux *.out *.log
