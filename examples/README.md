# Examples

Ready-to-run [useful-views](https://github.com/jameshorine/useful-views)
projects. Get one with:

```sh
useful-views example <name> [path]
```

Each release of useful-views pins a tag of this repository and the SHA-256
of every file it downloads, so a published example must never change in
place. To change an example, commit the new files and create a new tag (for
example `examples-v2`), then point the next useful-views release at it.

| Name | Contents |
|---|---|
| `pwt` | Penn World Table 11.0 extract for Brazil, Germany, Spain and the United States, with two recipes. Licensed CC BY 4.0; see `pwt/README.md` for the source and citation. |

Each example holds what a user starts from: `README.md`, `raw/` and
`recipes/`. The views, `datapackage.json` and the catalog are made by
running the recipes.
