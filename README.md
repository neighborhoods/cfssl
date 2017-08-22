# cfssl binaries
The official [cfssl repository][] has [official binaries](https://pkg.cfssl.org/) for releases, but releases are infrequent.
The goal of this repo is to provide pre-built binaries for untagged versions.

## Requirements
- Python 3.x (tested on 3.6)
- Docker (tested on 17.06)

## Building
To build the dist files, run the `build.py` script.
The output will be located in the `dist/` directory.

[cfssl repository]: https://github.com/cloudflare/cfssl
