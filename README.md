# finvizlite
A lightweight finviz API that does not use pandas.

The code is a thinned downed version of [finvizfinance](https://github.com/lit26/finvizfinance/). All credit goes to the original author.

### Motivation
The original finvizfinance imports pandas which I dislike as pandas is a fairly slow package. My trading style requires instant actions. Anything slow must be thrown out of the window. I also only need to scrape fundamentals and maybe news (which isn't up-to-date on finviz though). 