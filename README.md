# useful-views-data

Example data for [useful-views](https://github.com/jameshorine/useful-views),
the way [seaborn-data](https://github.com/mwaskom/seaborn-data) serves
seaborn. Each folder in [`examples/`](examples/) is a ready-to-run useful-views
project: raw data and recipes. No large data is committed here.

## Examples

| Name | Contents | Published in |
|---|---|---|
| [`pwt`](examples/pwt/) | Penn World Table 11.0 extract for Brazil, Germany, Spain and the United States, with two recipes. | `examples-v1` |

Get one with:

```sh
useful-views example pwt [path]
cd pwt-example && useful-views sync
```

## A published example never changes

Each release of useful-views downloads the example files from one tag of this
repository, such as `examples-v1`, and rejects any file whose SHA-256 differs
from the hash pinned in the package. So:

- Files under a published tag never change in place, and the tag is never
  moved or deleted.
- To change or add an example, commit the new files to `main`, create a new
  tag (`examples-v2`, ...), then point the next useful-views release at that
  tag and update its pinned hashes.
- [`examples/.gitattributes`](examples/.gitattributes) turns off line-ending
  conversion, so git stores and serves the files byte for byte. Don't put them
  in Git LFS: the raw download URL would then serve the pointer file instead of
  the data.

## Dataset projects

This repository used to hold two dataset projects, built before the
useful-views package existed: USDA NASS Crop Sequence Boundaries and USDA FAS
Production, Supply and Distribution (PSD). They have been removed, and will
come back rebuilt on the package. The last version of both is in the git
history at commit `19ab074`.

## Licenses and credit

The code and documentation in this repository are released under the
[MIT License](LICENSE). The data keeps its own terms:

- **Penn World Table 11.0** (`examples/pwt/`) by Robert C. Feenstra, Robert
  Inklaar and Marcel P. Timmer (Groningen Growth and Development Centre) is
  licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
  Source: https://www.rug.nl/ggdc/productivity/pwt/. Please cite Feenstra,
  Robert C., Robert Inklaar and Marcel P. Timmer (2015), "The Next Generation
  of the Penn World Table", *American Economic Review*, 105(10), 3150-3182,
  https://doi.org/10.1257/aer.20130954. The views the recipes make are
  reshaped and derived from it, and are not published or endorsed by the
  Groningen Growth and Development Centre.

## Contributing

I am one person, so help is very welcome: open an
[issue](https://github.com/jameshorine/useful-views-data/issues) or a pull
request.

`main` is stable and `dev` is for integration. Start working branches from
the latest `dev`, and open pull requests into `dev`; `main` receives changes
only from `dev`, and example tags are made on `main`.

| Branch | Purpose | Example |
|---|---|---|
| `main` | Stable. Receives validated changes from `dev` by pull request. | `main` |
| `dev` | Integration. Receives contribution pull requests. | `dev` |
| `examples/<name>` | Add or change an example (it ships under a new tag). | `examples/pwt` |
| `new-dataset/<name>` | Add a dataset project. | `new-dataset/fas-psd` |
| `fix/<description>` | Correct a bug or data-processing error. | `fix/pwt-recipe` |
| `docs/<description>` | Update documentation. | `docs/readme` |

Never commit raw data, intermediate files or Parquet views. Stage files by
name rather than with `git add -A`, and check `git diff --cached --stat`
before you commit.
