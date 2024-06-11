# satellite

A toy implementation of the DPLL SAT algorithm written in Python.

This repo may hopefully be interesting to anyone trying to understand the DPLL
SAT algorithm by playing around with a very simple implementation.

The implementation was based on the description found in the following
Wikipedia article: https://en.wikipedia.org/wiki/DPLL_algorithm

We also provide an implementation of the Tseitin transformation based on the
following references:

* https://en.wikipedia.org/wiki/Tseytin_transformation
* https://www.youtube.com/watch?v=fd9gjzZE1-4
* https://www.youtube.com/watch?v=v2uW258qIsM

No docs provided currently :).  If you're curious how things work, have a look
at the test suite.

## Setup

```
git clone git@github.com:davesque/satellite.git
cd satellite
make
```

## Running the tests

From the project root directory:
```
make test
```
