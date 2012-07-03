HTML = $(shell find assets/ -name '*.jade' |\
	   sed -e 's/assets\/jade\//templates\//g' -e 's/\.jade/\.html/g')

CSS = $(shell find assets/styl/ -name '*.styl' |\
	  sed -e 's/assets\/styl\//static\/css\//g' -e 's/\.styl/\.css/g')

JS = $(shell find assets/js/ -name '*.js' | sed -e 's/assets\//static\//g')

DIRS = templates static/css static/js

all: $(DIRS) $(HTML) $(CSS) $(JS)

templates static/css static/js:
	mkdir -p $@

templates/%.html: assets/jade/%.jade
	jade < $< > $@

static/css/%.css: assets/styl/%.styl
	stylus < $< > $@

static/js/%.js: assets/js/%.js
	uglifyjs -o $@ $<

clean:
	rm -rf templates/ static/
