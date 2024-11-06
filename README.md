# UnOld

UnOld - List outdated package versions in containerfiles/dockerfiles.

**WARNING:** This software is far from finished. Use with caution. **WARNING:**

<!-- vale off -->

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<!-- vale on -->

## Getting started

### Prerequisites

- `docker` or `podman` installed
- Python >= 3.9
- Some containerfile/dockerfile to analyze

### Installation

For now, just download the `src/` directory, just plainly or with `git clone`. Then install `requirements.txt` in some
way, e.g.:

```
pip3 install -r requirements.txt
```

In the future there will be a [pypi](https://pypi.org/) package for this.

## Usage

For example, with this file named `Containerfile`:

```
FROM alpine:3.20

RUN apk add --no-cache \
    git==2.43.0-r0 \
    nginx==1.26.2-r0
```

Run:

```bash
unold.py Containerfile
```

Run, but with `podman` instead of `docker`:

```bash
unold.py -c podman Containerfile
```

Which might show:

```txt
Package 'git' with version 2.43.0-r0 starting at line 3 in file 'Containerfile' is not up to date. The latest version is 2.45.2-r0.
```

Check files recursively with the `.Containerfile` file extension:

```bash
# If it's a git repository
git ls-files '*.Containerfile' -z | xargs -r0 unold.py
# If it's just a directory
find -name '*.Containerfile' -print0 | xargs -r0 unold.py
```

### Supported package managers

- [`apk`](https://wiki.alpinelinux.org/wiki/Alpine_Package_Keeper)

In the future support for more package managers will be added:

- `apt-get`
- `dnf`
- `pacman`
- `yum`
- `zypper`

### Limitations

- Ordinary containerfiles are supported. With intention it is easy to trick UnOld.
- This is not a general containerfile linter. Recommendations for that are linters such as
  [hadolint](https://github.com/hadolint/hadolint) and [Docker build checks](https://docs.docker.com/build/checks/).

## How does it work?

In broad strokes UnOld does the following:

1. Locate installations of packages in a containerfile
2. Generate a temporary containerfile based on that containerfile. This temporary containerfile cuts off at the point of
   package installation and instead lists package versions.
3. Build an image from the containerfile
4. Run an instance of the image
5. Compare the listed versions with available ones

Why do it this way? Although UnOld might do some extra work it will work with many different containerfiles.

<!-- vale off -->

## Alternatives

<!-- vale on -->

Some projects try to solve the problem in other ways:

- [version-helper](https://github.com/DockerToolbox/version-helper)
- [Renovate?](https://github.com/renovatebot/renovate)

## Contributing

Open a GitHub issue or pull request.

## License

<!-- vale off -->

[MIT license](LICENSE).

<!-- vale on -->
