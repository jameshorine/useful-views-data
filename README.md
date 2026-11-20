# useful-views-data

Data for [useful-views](https://jameshorine.github.io/useful-views/), in two
kinds:

- **Examples** (`examples/`): small, ready-to-run projects that
  `useful-views example <name>` downloads, the way
  [seaborn-data](https://github.com/mwaskom/seaborn-data) serves seaborn. Each
  published version is a tag that never changes; see
  [`examples/README.md`](examples/README.md).
- **Datasets** (`datasets/`): full projects on real data. Their raw data is
  never committed: each downloads it from the publisher, checks every file's
  SHA-256, and builds its views on your machine.

The [catalogue](datasets/README.md) lists every example and dataset, with
its source, its views and a link to its generated catalog.

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
- **U.S. Census Bureau, American Community Survey** (`datasets/census-acs/`):
  a work of the U.S. federal government, in the public domain (17 U.S.C.
  §105). Credit: U.S. Census Bureau, 2020-2024 American Community Survey
  5-Year Estimates. Not affiliated with or endorsed by the U.S. Census Bureau.
  Only the recipes and records are in git; the data is downloaded from Census.

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
