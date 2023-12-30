# Makefile
# I created this makefile to streamline the usage of a few common tasks

ccyellow = $(shell echo "\033[33m")
ccend = $(shell tput op)

SRC_PATHS=creepclient qi

help:
	@echo "$(ccyellow)------------------------------------------$(ccend)"
	@echo "$(ccyellow)Creep client makefile$(ccend)"
	@echo "$(ccyellow)------------------------------------------$(ccend)"
	@echo "Usage:"
	@echo "  make lint : run linter"
	@echo

lint:
	@echo "$(ccyellow)> Running black...$(ccend)"
	black --exclude tools $(SRC_PATHS)
	@echo
	@echo "$(ccyellow)> Running pylint...$(ccend)"
	pylint $(SRC_PATHS)
	@echo
