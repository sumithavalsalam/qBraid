# qBraid SDK
<!-- [![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black) -->

The qBraid SDK provides a platform for running quantum algorithms on various quantum computers and
quantum simulators.

<a href="https://qbraid.com/">
    <img src="/docs/_static/logo.png"
         alt="qbraid logo"
         width="250px"
         align="right">
</a>

## Installation
You can install from source by cloning this repository and running a pip install command in the
root directory:

```
git clone https://github.com/qbraid/qBraid.git
cd qBraid
python -m pip install -e .
```

## Documentation
To generate the API reference documentation locally:
```
pip install tox
tox -e docs
``` 
Alternatively:
```
pip install -e ".[docs]"
cd docs
make html
```
Both methods will run Sphinx in your shell. If the build succeeded, it will say 
`The HTML pages are in build/html`. You can view the generated documentation
in your browser using:
```
open build/html/index.html  # On OS X
```
You can also view it by running a web server in that directory:
```
cd build/html
python3 -m http.server
```
Then open your browser to http://localhost:8000. If you make changes to the docs that aren't
reflected in subsequent builds, run `make clean html`, which will force a full rebuild.

## Testing
To run all unit tests:
```
tox -e unit-tests
```
You can also pass in various pytest arguments to run selected tests:
```
tox -e unit-tests -- {your-arguments}
```
Alternatively:
```
pip install -e ".[test]"
pytest tests/{path-to-test}
```
Running unit tests with tox will automatically generate a coverage report, which can be found in
`tests/_coverage/index.html`, and can be viewed in your browser using the same procedure described
in Documentation, above.

To run linters and doc generators and unit tests:
```
tox
```

