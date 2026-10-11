# useful-views


## Directory of `useful-views`

| Dataset | Useful View | Useful for | Get it |
|---|---|---|---|
| Crop Sequence Boundaries | `csb_field_year` (Parquet) | Land cover for every field, every year 2018-2025. The tidy core. | [Generate locally](crop-sequence-boundaries/README.md#building-the-views) |
| Crop Sequence Boundaries | `csb_field` (GeoParquet) | Field acres, location and geometry. | [Generate locally](crop-sequence-boundaries/README.md#building-the-views) |
| Crop Sequence Boundaries | `county` (Parquet) | County names and ASDs by 5-digit county GEOID. | [Generate locally](crop-sequence-boundaries/README.md#building-the-views) |
| Crop Sequence Boundaries | `land_cover_codes` (Parquet) | Putting names to the CDL land-cover codes. You will get to practice your left-joins :) | [Generate locally](crop-sequence-boundaries/README.md#building-the-views) |
| FAS Production, Supply and Distribution | `psd_alldata` (Parquet) | The USDA FAS PSD file as published: production, trade, use and stocks for 63 commodities, about 200 countries, 1960 on. | [Generate locally](fas-psd/README.md#build) |
| FAS Production, Supply and Distribution | `commodity_attribute` (Parquet) | What PSD reports for each commodity, and in what unit. | [Generate locally](fas-psd/README.md#build) |
| FAS Production, Supply and Distribution | `world_balance` (Parquet) | Every country summed to world totals: world supply, use and stocks by commodity and year. | [Generate locally](fas-psd/README.md#build) |



## About `useful-views`

`useful-views` are designed to be data-assets or data-products that help enable various data/analytics/science/engineering use cases. 

Think of these as collection of (maybe) useful table views. We (currently are trying to) subscribe to the [`tidy` data model](https://vita.had.co.nz/papers/tidy-data.pdf). That is to say, useful-views naturally extends `frictionlessdata`'s `datapackage` methodology to include the build details as steps that are tested against a reviewed and known `datapackage.json` file type. 


There are very likely some very good reasons to split from the `tidy` data view, and if you have one of those reasons, I trust you. You (almost surely) know the problme and domain space much better than most. I wont even challenge you, however I will want to understand, and will seek your help in understanding why! 

This is really just my attempt at keeping myself super organized.


As a result of doing a lot of this work in github, the repo implies a project strucutre as follows:

```
dataset-name/
├── .python-version
├── .venv/ # local Python environment
├── README.md
├── pyproject.toml
├── uv.lock
├── in/ # raw data goes here on your local
│   └── SOURCES.md # where each input came from, with checksums
├── out/ # processed data and intermediate outputs, gitignored
├── sandbox/
│   ├── sandbox.ipynb
│   └── example_queries.ipynb
├── src/
│   └── dataset_name/
│       ├── __init__.py # main(): runs every step in order
│       ├── config.py # paths, release name, expected input facts
│       ├── step1_<does_what>.py
│       ├── ...
│       └── stepN_datapackage.py # writes the release's datapackage.json
└── useful-views/ # the useful tables, in Parquet, gitignored
    └── <release>/ # one folder per source release
        └── datapackage.json # data bill of materials: checksums, schemas, provenance (committed)
```

This is designed to give us a helping hand in managing the data that we need for various projects. Often the data sets arrive to us in a "less than useful" format or view. This repo is designed to help us collect a few useful views on data that we frequently work with. 

For questions, comments, (and help!) please reach out :D 

The global gitignore is used to essentially screen out the source raw data files from github. 

Each datset project sub folder should (I hope) contain its own independent uv project. This is to help reproducibility at all steps!  

## Getting Started with `useful-views`

### Python Dependencies

#### New Project

With uv installed, open a terminal in the data project’s folder, then run:

1. `uv init --bare` to initialize the project.
2. `uv add polars` to add Polars and create the local .venv and lockfile.
3. `uv add --dev ipykernel` if you’ll use notebooks.


#### Existing Project

1. Clone the repo (if you have not already)
2. open a terminal in the projects data folder, or navigate there
3. Run `uv sync --locked` to recreate its `.venv`. No need to run `uv init` again.

#### Working with Either

- Add a dependency with uv add <package>, for example uv add polars.
- Run a script with uv run python <script.py>, replacing <script.py> with its relative path.
- For notebooks, select the project's .venv as the kernel environment in VS Code. With Polars installed, use import polars as pl.
- Commit dependency manifest and lockfile changes; keep .venv ignored by Git.


### Running the scripts on local

From a dataset's folder, after `uv sync --locked`:

```sh
uv run <dataset-name>
```

This runs every step in order and builds that dataset's `useful-views/`. For example, `uv run crop-sequence-boundaries`. Each dataset's README lists its steps, inputs and outputs.

## Contributing to `useful-views`
I am one person, please send help :D 

Really though, either reach out, or submit a PR. I am almost surely to need help. 

### Branching workflow

We (lets be real, its just me, its one person, I) use `dev` to integrate changes and `main` for stable, validated work. 

- main receives changes only through pull requests from dev.
- dev receives contribution pull requests and is where changes are validated together.
- Working branches start from the latest dev. Use a descriptive prefix such as feature/, fix/, or docs/, for example feature/csb-summary.




| Branch | Purpose | Example |
|---|---|---|
| `main` | Permanent stable branch; receives validated changes from `dev` via PR. | `main` |
| `dev` | Permanent integration branch; receives contribution PRs. | `dev` |
| `new-dataset/<dataset-name>` | Add a new dataset project. | `new-dataset/crop-sequence-boundaries` |
| `feature/<description>` | Add functionality or views to an existing project. | `feature/csb-summary` |
| `fix/<description>` | Correct a bug or data-processing error. | `fix/csb-import` |
| `docs/<description>` | Update documentation or examples. | `docs/uv-setup` |



When contributing a new data set, please use `new-dataset/<dataset-name>`. for example: `new-dataset/crop-sequence-boundaries`. 

The branches represent the contributions, not the permanent homes for data sets. 



## The Future of `useful-views`

Right now `useful-views` is a pattern that two datasets (Crop Sequence Boundaries and FAS PSD) follow. The plan is to turn it into a package that any dataset can use. Roughly in order:

- **A second dataset first.** One example can't show which parts are the pattern and which are specific to CSB. The second dataset, FAS PSD, is how we find out what is actually shared. So far: the data package writer and the verification step carried over almost unchanged, while the view steps are specific to each dataset.
- **A shared `useful_views` Python package.** The generic parts move out of the CSB project and into one place: path and input checks (`config.py` helpers), the data package writer (step 4), the verification step (step 5), and the check that every column is documented. Each dataset then keeps only its own steps and declarations. Datasets would stay separate uv projects, sharing the package through a uv workspace.
- **A written spec.** A short document saying what a `useful-views` dataset MUST and SHOULD have: the folder layout, `in/SOURCES.md`, release folders, a committed `datapackage.json`, and the `build` section.
- **A Frictionless Data Package profile.** A versioned JSON Schema that extends Data Package with the `build` section, so any `datapackage.json` can be checked against the `useful-views` rules, not just the base standard.
- **A geometry convention.** Table Schema has no type for GeoParquet geometry. CSB already handles this by typing geometry columns `"any"` and adding a custom `geoparquet` property (encoding, geometry types, CRS, bounding box) copied from the file's GeoParquet metadata, plus an OGC Simple Features `rdfType`. The profile should make that convention a rule.
- **Portable build records.** Record the full commit hash and the repository URL, so a `datapackage.json` still says where it came from once it leaves this repo.
- **Two levels of "same data".** Today a rebuild counts as identical only if the files are byte-for-byte the same. Tool upgrades can change the bytes without changing the data, so the plan is to add a content check (did the data itself change?) alongside the file hash.
- **A command-line tool.** Something like `useful-views new <dataset-name>` to scaffold a new dataset, and `useful-views verify` to check any dataset against its committed `datapackage.json`.
