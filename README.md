# remarkable-cli

An unofficial command line interface (CLI) for interacting with the Remarkable paper tablet.

Features:

- [x] Backup reMarkable `xochitl` files directly to the local machine
- [x] Convert `.rm` files into `.pdf` or `.svg`
- [x] Backup reMarkable documents as `pdf` directly to the local machine
- [ ] Push files to reMarkable for annotation & reading
- [ ] ...and more

## Getting Started

```bash
pip install remarkable-cli

# Pull raw xochitl files and render them into readable pdf
remarkable-cli -a pull

# with DEBUG logging, clean the local backup directory before pulling all the raw xochitl files and rendering pdf
remarkable-cli -vvvv -a clean-local -a pull

# show the CLI usage/help
remarkable-cli -h
```

## License

[Apache-2.0](./LICENSE)

```text
Copyright 2021, Alexander Wong

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at
http://www.apache.org/licenses/LICENSE-2.0
Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
```
