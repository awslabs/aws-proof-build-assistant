HTML_DEPS = head1.html style.css head2.html index.tmp.html foot.html

index.html: $(HTML_DEPS)
	cat $(HTML_DEPS) > $@

.INTERMEDIATE: index.tmp.html
index.tmp.html: index.md
	markdown $^ > $@

open: index.html
	open index.html