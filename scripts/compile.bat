@echo off
latexmk -xelatex -auxdir=build/ -outdir=dist/ paper/main.tex
