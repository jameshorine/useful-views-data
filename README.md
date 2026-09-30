# useful-views

## About `useful-views`

A collection of (maybe) useful table views. We subscribe to the `tidy` data model here. Unless you have a SUPER good reason not to. To be honest, you probably know the domain space better than most, so I wont even challenge you on your reason not to use a tidy data model. I am just trying to keep things tidy for myself. 


This repo is structured in the following way: 

```
dataset_name
├──in # raw data goes here on your local
├──out # any processing of the data you need. finalized formats, ect.
├──useful-views # you guessed it - the useful view you find useful! 
├──readme.md
```

This is designed to give us a helping hand in managing the data that we need for various projects. Often the data sets arrive to us in a "less than useful" format or view. This repo is designed to help us collect a few useful views on data that we frequently work with. 

For questions, comments, (and help!) please reach out :D 

The global gitignore is used to essentially screen out the source raw data files from github. 

Each datset project sub folder should (I hope) contain its own independent uv project. This is to help the reproducibility efforts. 

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


