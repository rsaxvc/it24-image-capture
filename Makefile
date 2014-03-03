all: logGraph.parsed.hex logGraph2.parsed.hex logGraph3.parsed.hex logMenu.parsed.hex

%.parsed.hex : % parser
	./parser $< > $@

parser: parser.c

clean:
	rm -f parser
