# Examples

How the examples that `useful-views example <name>` downloads are published.
What each example contains is in the
[catalogue](../datasets/README.md#examples).

## What gets downloaded

`useful-views example` downloads only what a user starts from: the files
the useful-views release pins, which are `README.md`, `raw/` and `recipes/`,
plus `sources.toml` from `examples-v3` on. Everything else is made on the
user's machine. `init` writes `AGENTS.md` and `.gitignore`, `sync` makes the
views, `datapackage.json` and the catalog, and `useful-views cookbook` writes
`cookbook.json`.

Each example here also commits its `datapackage.json`, catalog
(`useful-views/README.md`), `cookbook.json` and `AGENTS.md`, as any
useful-views project does, so they can be read on GitHub. The generated
records name the project after its folder, so a downloaded copy makes its
own.

## A published example never changes

Each release of useful-views downloads the example files from one tag of this
repository and rejects any file whose SHA-256 differs from the hash pinned in
the package. So:

- Files under a published tag never change in place, and the tag is never
  moved or deleted.
- [`.gitattributes`](.gitattributes) turns off line-ending conversion, so git
  stores and serves the files byte for byte. Don't put them in Git LFS: the
  download URL would then serve the pointer file instead of the data.

| Tag | What changed |
|---|---|
| `examples-v3` | Each recipe's `recipe.toml` lists its steps with their descriptions, and `pwt/sources.toml` records where the raw data came from (URL, DOI, license, citation). |
| `examples-v2` | The `pwt` README covers `check` and the cookbook, and lists what the project makes. |
| `examples-v1` | The first published examples. |

To see which tag your useful-views uses:
`python -c "from useful_views.examples import DATA_TAG; print(DATA_TAG)"`.

## Changing or adding an example

0. For a new example, open a [New dataset issue](https://github.com/jameshorine/useful-views-data/issues/new?template=new-dataset.yml)
   with Kind set to Example, and link it from [#23](https://github.com/jameshorine/useful-views-data/issues/23) with a comment.
1. Start a branch from the latest `dev`: `examples/<name>`.
2. Change or add the files in `examples/<name>/`. Build it with
   `useful-views sync`, run `useful-views cookbook`, and commit the regenerated
   records with it. Keep the raw data small: it is committed and downloaded.
3. Merge into `dev` and then `main` by pull request.
4. Tag the merge on `main` as the next `examples-vN` and push the tag. Then
   add a row to the tag table above.
5. In useful-views, point `DATA_TAG` in `src/useful_views/examples.py` at the
   new tag, update the pinned SHA-256 of every changed file, and update the
   test copy in `tests/data/examples/`.
6. For a new example, add a row to the examples table in the
   [catalogue](../datasets/README.md#examples), close its issue with a
   **Delivered** comment, and mark it `done` in its comment on [#23](https://github.com/jameshorine/useful-views-data/issues/23).
