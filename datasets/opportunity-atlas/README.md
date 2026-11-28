# The Opportunity Atlas

Useful views on [The Opportunity Atlas](https://opportunityinsights.org/paper/the-opportunity-atlas/) by Raj Chetty,
John Friedman, Nathaniel Hendren, Maggie Jones and Sonya Porter (Opportunity Insights and the U.S. Census Bureau). It
asks which places give children from low-income families the best chance to rise. For children born in 1978-1983,
it estimates how they did as adults (household income rank at ages 31-37, and incarceration on 1 April 2010), by the
census tract, county and commuting zone where they grew up, by race and gender. It also gives the neighborhood
characteristics shown on the Atlas, national outcomes at every parental income percentile, and a crosswalk that
carries the main mobility measure to 2020 census tracts.

- Built with [useful-views](https://jameshorine.github.io/useful-views/).
- Tracked in [#64](https://github.com/jameshorine/useful-views-data/issues/64).
- Joins to [`census-acs`](../census-acs/) on 2020 tracts through `tracts-2020` (see "Things to know").

## Quick start

From this folder (`datasets/opportunity-atlas`), with [uv](https://docs.astral.sh/uv/) installed:

```sh
uv sync                      # the exact useful-views, duckdb and certifi versions in uv.lock
uv run python fetch_raw.py   # downloads the nine CSVs (70 MB) into raw/ and checks them
uv run useful-views sync     # builds the eleven views (under a minute)
uv run useful-views check    # expect: No problems found.
```

Plan for about 135 MB of disk: 70 MB of raw data and 61 MB of views.

`fetch_raw.py` pins each file by size and SHA-256; two downloads on 2026-11-27 were byte-identical. The site turns
away Python's default User-Agent (HTTP 403), so the script sends its own.

**Not included:** the full outcomes at every parental income percentile and for more races
(`tract_outcomes.zip` is 2.6 GB; the county and CZ versions are 74 MB and 58 MB), and the tract outcomes for the
1984-1989 cohorts (41 MB). Both are on the same page and can be added as recipes later.

## The views

All in `useful-views/`. The generated catalog, [useful-views/README.md](useful-views/README.md), lists each one's
columns and the steps that made it.

| View | One row per | What it is |
|---|---|---|
| `tract-outcomes` | 2010 census tract | Codebook Table 1, typed: 73,278 tracts × 60 measures (see "Column names"). |
| `county-outcomes` | 2010 county | Table 2: 3,219 counties. |
| `cz-outcomes` | commuting zone (1990) | Table 3: 741 commuting zones. |
| `outcomes-long` | geography × place × outcome × race × gender | The three tables above in long form: 1,231,588 rows, one per published estimate, with its standard error and count. |
| `tract-covariates` | 2010 census tract | Table 9: 74,044 tracts × 33 neighborhood characteristics. |
| `county-covariates` | 2010 county | Table 10: 3,221 counties × 31. |
| `cz-covariates` | commuting zone | Table 11: 741 commuting zones × 33. |
| `national-outcomes` | parent percentile × outcome × race × gender | Table 7 in long form: 97,300 rows, 47 outcomes, 21 race-gender groups, parent percentiles 1-100. |
| `percentile-dollars` | percentile | Table 8: income and wage percentiles 0-100 in 2015 dollars, for children and parents. |
| `tracts-2020` | 2020 census tract | 84,095 tracts with the Atlas's mobility measure carried from 2010 tracts. |
| `tracts-2020-to-2010` | 2020 tract × overlapping 2010 tract | 121,433 pairs with their overlap weights and each 2010 tract's mobility. |

### Sample records

These are real rows. Run each snippet from this folder and you get the same output; the comments say what each
sample shows.

```python
import duckdb
```

**`tract-outcomes`**: two Chicago tracts, in the Near North Side and Greater Grand Crossing community areas.

```python
duckdb.sql("""
    SELECT tract_fips, czname, kfr_pooled_pooled_p25, kfr_pooled_pooled_p25_se, jail_pooled_pooled_p25,
           pooled_pooled_count, kfr_black_pooled_p25, kfr_white_pooled_p25
    FROM 'useful-views/tract-outcomes.parquet'
    WHERE tract_fips IN ('17031081500', '17031690900')
    -- A small tract (39 low-income children) has a wide standard error, and its privacy noise
    -- pushes the incarceration rate below 0. A cell with too few children is empty.
    ORDER BY tract_fips
""").show(max_width=200)
```

```text
┌─────────────┬─────────┬───────────────────────┬──────────────────────────┬────────────────────────┬─────────────────────┬──────────────────────┬──────────────────────┐
│ tract_fips  │ czname  │ kfr_pooled_pooled_p25 │ kfr_pooled_pooled_p25_se │ jail_pooled_pooled_p25 │ pooled_pooled_count │ kfr_black_pooled_p25 │ kfr_white_pooled_p25 │
│   varchar   │ varchar │        double         │          double          │         double         │       double        │        double        │        double        │
├─────────────┼─────────┼───────────────────────┼──────────────────────────┼────────────────────────┼─────────────────────┼──────────────────────┼──────────────────────┤
│ 17031081500 │ Chicago │            0.35667431 │              0.033831961 │          -0.0069488934 │            39.17065 │           0.26565707 │           0.57088655 │
│ 17031690900 │ Chicago │            0.30091813 │              0.010642495 │             0.05287271 │           1041.3051 │            0.3045114 │                 NULL │
└─────────────┴─────────┴───────────────────────┴──────────────────────────┴────────────────────────┴─────────────────────┴──────────────────────┴──────────────────────┘
```

**`county-outcomes`**: the large counties where children from low-income families did best.

```python
duckdb.sql("""
    SELECT county_fips, czname, kfr_pooled_pooled_p25, kfr_pooled_pooled_p25_se, pooled_pooled_count
    FROM 'useful-views/county-outcomes.parquet'
    WHERE pooled_pooled_count >= 50000
    -- Children of parents at the 25th percentile reached the 52nd percentile on average in Bergen County, NJ.
    ORDER BY kfr_pooled_pooled_p25 DESC
    LIMIT 5
""").show(max_width=200)
```

```text
┌─────────────┬───────────────┬───────────────────────┬──────────────────────────┬─────────────────────┐
│ county_fips │    czname     │ kfr_pooled_pooled_p25 │ kfr_pooled_pooled_p25_se │ pooled_pooled_count │
│   varchar   │    varchar    │        double         │          double          │       double        │
├─────────────┼───────────────┼───────────────────────┼──────────────────────────┼─────────────────────┤
│ 34003       │ Newark        │            0.51954651 │             0.0022149759 │           50880.941 │
│ 51059       │ Washington DC │            0.51112968 │              0.001842173 │           62878.445 │
│ 06075       │ San Francisco │            0.50388849 │             0.0019263224 │           58389.926 │
│ 36059       │ New York      │            0.49325207 │             0.0017187045 │           84120.414 │
│ 34023       │ Newark        │            0.48370594 │             0.0021628183 │           51222.891 │
└─────────────┴───────────────┴───────────────────────┴──────────────────────────┴─────────────────────┘
```

**`cz-outcomes`**: three commuting zones, by race for boys.

```python
duckdb.sql("""
    SELECT cz, czname, kfr_pooled_pooled_p25, kfr_black_male_p25, kfr_white_male_p25, jail_black_male_p25, jail_white_male_p25
    FROM 'useful-views/cz-outcomes.parquet'
    WHERE czname IN ('Chicago', 'Atlanta', 'Salt Lake City')
    -- Black and white boys from families at the same income end up far apart, in rank and in incarceration.
    ORDER BY kfr_pooled_pooled_p25 DESC
""").show(max_width=200)
```

```text
┌───────┬────────────────┬───────────────────────┬────────────────────┬────────────────────┬─────────────────────┬─────────────────────┐
│  cz   │     czname     │ kfr_pooled_pooled_p25 │ kfr_black_male_p25 │ kfr_white_male_p25 │ jail_black_male_p25 │ jail_white_male_p25 │
│ int32 │    varchar     │        double         │       double       │       double       │       double        │       double        │
├───────┼────────────────┼───────────────────────┼────────────────────┼────────────────────┼─────────────────────┼─────────────────────┤
│ 36100 │ Salt Lake City │            0.45658013 │         0.35530362 │         0.47868022 │          0.12866446 │         0.032254573 │
│ 24300 │ Chicago        │            0.39687583 │          0.2829102 │          0.4758414 │          0.11359099 │         0.020066068 │
│  9100 │ Atlanta        │            0.35831201 │         0.29056063 │         0.41997957 │          0.09957052 │         0.043349322 │
└───────┴────────────────┴───────────────────────┴────────────────────┴────────────────────┴─────────────────────┴─────────────────────┘
```

**`outcomes-long`**: Cook County, Illinois, by race.

```python
duckdb.sql("""
    SELECT geography, geography_id, czname, outcome, race, gender, estimate, standard_error, children
    FROM 'useful-views/outcomes-long.parquet'
    WHERE geography = 'county' AND geography_id = '17031' AND gender = 'pooled'
    -- One row per estimate; children is the same for both outcomes of a race-gender group.
    ORDER BY outcome, race
""").show(max_width=200)
```

```text
┌───────────┬──────────────┬─────────┬─────────┬─────────┬─────────┬─────────────┬────────────────┬───────────┐
│ geography │ geography_id │ czname  │ outcome │  race   │ gender  │  estimate   │ standard_error │ children  │
│  varchar  │   varchar    │ varchar │ varchar │ varchar │ varchar │   double    │     double     │  double   │
├───────────┼──────────────┼─────────┼─────────┼─────────┼─────────┼─────────────┼────────────────┼───────────┤
│ county    │ 17031        │ Chicago │ jail    │ black   │ pooled  │ 0.051773112 │  0.00086160214 │ 318866.53 │
│ county    │ 17031        │ Chicago │ jail    │ hisp    │ pooled  │ 0.013979021 │  0.00057845633 │  239170.2 │
│ county    │ 17031        │ Chicago │ jail    │ pooled  │ pooled  │ 0.029345687 │  0.00047989286 │ 655515.44 │
│ county    │ 17031        │ Chicago │ jail    │ white   │ pooled  │ 0.010182597 │  0.00054331578 │ 110760.91 │
│ county    │ 17031        │ Chicago │ kfr     │ black   │ pooled  │   0.3089979 │  0.00071617158 │ 318866.53 │
│ county    │ 17031        │ Chicago │ kfr     │ hisp    │ pooled  │   0.4348152 │   0.0012280178 │  239170.2 │
│ county    │ 17031        │ Chicago │ kfr     │ pooled  │ pooled  │  0.38461408 │   0.0006228225 │ 655515.44 │
│ county    │ 17031        │ Chicago │ kfr     │ white   │ pooled  │   0.5045228 │   0.0014186073 │ 110760.91 │
└───────────┴──────────────┴─────────┴─────────┴─────────┴─────────┴─────────────┴────────────────┴───────────┘
```

**`tract-covariates`**: the two Chicago tracts again, with a few of their characteristics.

```python
duckdb.sql("""
    SELECT o.tract_fips, o.kfr_pooled_pooled_p25, c.poor_share2000, c.singleparent_share2000, c.frac_coll_plus2000,
           c.mail_return_rate2010
    FROM 'useful-views/tract-outcomes.parquet' o JOIN 'useful-views/tract-covariates.parquet' c USING (tract_fips)
    WHERE o.tract_fips IN ('17031081500', '17031690900')
    -- Shares are fractions; mail_return_rate2010 alone is a percentage.
    ORDER BY o.tract_fips
""").show(max_width=200)
```

```text
┌─────────────┬───────────────────────┬────────────────┬────────────────────────┬────────────────────┬──────────────────────┐
│ tract_fips  │ kfr_pooled_pooled_p25 │ poor_share2000 │ singleparent_share2000 │ frac_coll_plus2000 │ mail_return_rate2010 │
│   varchar   │        double         │     double     │         double         │       double       │        double        │
├─────────────┼───────────────────────┼────────────────┼────────────────────────┼────────────────────┼──────────────────────┤
│ 17031081500 │            0.35667431 │    0.083849013 │             0.37179488 │         0.70608819 │                 78.0 │
│ 17031690900 │            0.30091813 │     0.24689628 │                  0.722 │         0.13483813 │            64.800003 │
└─────────────┴───────────────────────┴────────────────┴────────────────────────┴────────────────────┴──────────────────────┘
```

**`national-outcomes`**: income rank and college degrees across the parent income distribution.

```python
duckdb.sql("""
    SELECT parent_percentile, outcome, estimate, lowess, children, lowess_fit
    FROM 'useful-views/national-outcomes.parquet'
    WHERE outcome IN ('kfr', 'coll') AND race = 'pooled' AND gender = 'pooled' AND parent_percentile IN (1, 25, 50, 75, 100)
    -- coll is measured only for children in the ACS or the 2000 long form, so its counts are smaller.
    ORDER BY outcome DESC, parent_percentile
""").show(max_width=200)
```

```text
┌───────────────────┬─────────┬────────────┬────────────┬──────────┬────────────┐
│ parent_percentile │ outcome │  estimate  │   lowess   │ children │ lowess_fit │
│       int32       │ varchar │   double   │   double   │  int64   │  varchar   │
├───────────────────┼─────────┼────────────┼────────────┼──────────┼────────────┤
│                 1 │ kfr     │     0.3053 │     0.3127 │   213000 │ monotonic  │
│                25 │ kfr     │ 0.40709999 │ 0.40810001 │   213000 │ monotonic  │
│                50 │ kfr     │ 0.49759999 │ 0.49680001 │   213000 │ monotonic  │
│                75 │ kfr     │ 0.58130002 │ 0.58170003 │   213000 │ monotonic  │
│               100 │ kfr     │ 0.73079997 │ 0.71820003 │   213000 │ monotonic  │
│                 1 │ coll    │     0.1319 │     0.1348 │    19000 │ monotonic  │
│                25 │ coll    │      0.191 │     0.1978 │    22000 │ monotonic  │
│                50 │ coll    │     0.2854 │ 0.29080001 │    26000 │ monotonic  │
│                75 │ coll    │     0.4452 │ 0.44679999 │    27500 │ monotonic  │
│               100 │ coll    │ 0.82870001 │ 0.82520002 │    26500 │ monotonic  │
└───────────────────┴─────────┴────────────┴────────────┴──────────┴────────────┘
  10 rows                                                             6 columns
```

**`percentile-dollars`**: what a percentile is worth.

```python
duckdb.sql("""
    SELECT percentile, parent_hh_income, kid_hh_income, kid_indiv_income, kid_wageflex
    FROM 'useful-views/percentile-dollars.parquet'
    WHERE percentile IN (25, 50, 75, 99)
    -- "Parents at the 25th percentile" earned about $27,000 a year (2015 dollars).
    ORDER BY percentile
""").show(max_width=200)
```

```text
┌────────────┬──────────────────┬───────────────────┬──────────────────┬───────────────────┐
│ percentile │ parent_hh_income │   kid_hh_income   │ kid_indiv_income │   kid_wageflex    │
│   int32    │      double      │      double       │      double      │      double       │
├────────────┼──────────────────┼───────────────────┼──────────────────┼───────────────────┤
│         25 │ 27044.2021484375 │ 15551.20751953125 │   8175.978515625 │ 11.19074201583862 │
│         50 │   55802.23046875 │    42317.11328125 │ 29304.9697265625 │ 17.67184352874756 │
│         75 │    94251.8984375 │      83317.234375 │  53712.001953125 │ 26.59385585784912 │
│         99 │      749596.6875 │      552989.71875 │   342853.6015625 │ 133.6757469177246 │
└────────────┴──────────────────┴───────────────────┴──────────────────┴───────────────────┘
```

**`tracts-2020`** with **`tracts-2020-to-2010`**: two 2020 tracts and the 2010 tracts they overlap.

```python
duckdb.sql("""
    SELECT t.tract_2020, t.kfr_weighted, t.kfr_largest_tract, t.tracts_2010, p.overlap_rank, p.tract_2010, p.overlap_weight, p.kfr_2010
    FROM 'useful-views/tracts-2020.parquet' t JOIN 'useful-views/tracts-2020-to-2010.parquet' p USING (tract_2020)
    WHERE t.tract_2020 IN ('01001020100', '17001010301')
    -- kfr_weighted is the overlap-weighted mean of kfr_2010; kfr_largest_tract is rank 1's.
    ORDER BY t.tract_2020, p.overlap_rank
""").show(max_width=200)
```

```text
┌─────────────┬──────────────┬───────────────────┬─────────────┬──────────────┬─────────────┬────────────────┬────────────┐
│ tract_2020  │ kfr_weighted │ kfr_largest_tract │ tracts_2010 │ overlap_rank │ tract_2010  │ overlap_weight │  kfr_2010  │
│   varchar   │    double    │      double       │    int32    │    int32     │   varchar   │     double     │   double   │
├─────────────┼──────────────┼───────────────────┼─────────────┼──────────────┼─────────────┼────────────────┼────────────┤
│ 01001020100 │   0.36753744 │        0.36781323 │           2 │            1 │ 01001020100 │     0.99459577 │ 0.36781323 │
│ 01001020100 │   0.36753744 │        0.36781323 │           2 │            2 │ 01001020200 │   0.0054042577 │ 0.31678087 │
│ 17001010301 │   0.46304294 │        0.46248481 │           3 │            1 │ 17001010300 │     0.98931336 │ 0.46248481 │
│ 17001010301 │   0.46304294 │        0.46248481 │           3 │            2 │ 17001010200 │   0.0074032065 │ 0.52638775 │
│ 17001010301 │   0.46304294 │        0.46248481 │           3 │            3 │ 17149952400 │    0.003283381 │ 0.48839149 │
└─────────────┴──────────────┴───────────────────┴─────────────┴──────────────┴─────────────┴────────────────┴────────────┘
```

### Things to know before querying

**What the outcomes measure**
- **`kfr`** is a child's household income rank (own plus spouse's income, mean of 2014 and 2015, at ages 31-37),
  from 0 to 1, among all children born in the same year. **`jail`** is the fraction incarcerated on 1 April 2010
  (prisons, jails, detention and juvenile correctional facilities).
- Every estimate here is for **children whose parents were at the 25th percentile** of the national income
  distribution (about $27,000 a year in 2015 dollars; see `percentile-dollars`). They are predicted outcomes at that
  parent income, not the average child in the place.
- **To read a rank in dollars**, look up its percentile in `percentile-dollars` (`kid_hh_income` for `kfr`);
  interpolate between percentiles. A `kfr` of 0.385 (Cook County) falls between the 38th and 39th percentiles,
  about $29,000 of household income in 2015.
- **The counts** (`*_count`, and `children` in `outcomes-long`) are the codebook's preferred population weight: the
  number of children under 18 in the place, from the 2000 Census, whose parents earned less than the national median
  in the analysis sample. They are estimates, so they have decimals.

**Noise, small cells and missing values**
- **Privacy noise.** Opportunity Insights adds a little noise to every estimate, usually under a tenth of its
  standard error; the standard errors include it. So rates near 0 and ranks near 1 can cross those limits. In the
  tracts, 136,726 `jail` estimates are below 0 (out of 568,532) and 6 are above 1; 35 `kfr` estimates are below 0 and
  18 above 1. Counties have 2,677 negative `jail` estimates, commuting zones 447. They are kept as published; don't
  clip them before averaging.
- **Small tracts are noisy.** Tract estimates for a single race and gender can be far off (tract `jail` ranges from
  −1.30 to 1.36). Weight by the count or use the standard error; `outcomes-long` makes this easy.
- **Empty cells:** an estimate is empty where the group is too small. `outcomes-long` leaves those out, so it has
  1,231,588 rows rather than 77,238 places × 24.
- **48 tract estimates have no standard error.** In every one of them, the group's count is 0.

**Column names** (`[outcome]_[race]_[gender]_p25`, `..._se`, `[race]_[gender]_count`)
- Races in the tract, county and CZ tables: `pooled` (everyone), `white`, `black`, `hisp` (Hispanic). Genders:
  `pooled`, `female`, `male`. The national table adds `asian`, `natam` (Native American) and `other`.
- `national-outcomes` has 47 outcomes, from income ranks at several ages (`kfr_24`, `kir_29`, ...) to college
  (`coll`), marriage, work, teen births (`teenbrth`, women only) and staying in the childhood commuting zone
  (`staycz`). Codebook Table 7 defines each one. Its `lowess` is Opportunity Insights' smoothed curve (bandwidth
  0.3), which the codebook says was used to compute the tract, county and CZ estimates at given percentiles. Where a group's curve wasn't monotonic, `lowess_fit` says whether
  the curve was kept or the pooled curve was used instead (`lowess_flag` is the published code: −9, 0 or 1). Its
  `children` and `sample_children` are rounded, as published.

**Geography**
- **All tracts and counties are 2010 boundaries.** FIPS codes are zero-padded text: `tract_fips` (11 digits) and
  `county_fips` (5) are the keys, with `state`, `county` and `tract` alongside. Commuting zones (`cz`, 1990
  definitions) are integers, and `czname` is the CZ's name, not the county's.
- **No commuting zone for:** Puerto Rico (78 municipios, 725 outcome tracts), and Alaska areas newer than the 1990
  definitions: Yakutat (02282), and in the covariates also Kusilvak, which appears under both its old code (02270)
  and its new one (02158), and three tracts of Shannon County, South Dakota (46113, now Oglala Lakota County).
- **Outcomes and covariates don't cover quite the same places.** 79 outcome tracts have no covariates, and 845
  covariate tracts have no outcomes. Counties 02270 and 15005 (Kalawao, Hawaii) have covariates only.
- **To use 2020 tracts** (for example to join `census-acs`), go through `tracts-2020`:
  `state || county || tract` in `census-acs`'s `acs5-2024-geographies` equals `tract_2020`. 83,202 of the ACS's
  85,382 tracts match. The rest are Puerto Rico (981; the crosswalk has none), Connecticut (884, renumbered under the
  planning regions that replaced its counties in 2022) and 315 water and special tracts (codes starting `99`). The 14
  crosswalk tracts in Suffolk County, NY that the ACS lacks are its known errata.
- **The crosswalk carries only one measure,** `kfr_pooled_pooled_p25`. To move another outcome to 2020 tracts, join
  `tracts-2020-to-2010` to `tract-outcomes` on `tract_2010` and weight by `overlap_weight`, as the ReadMe suggests.
  At most five overlapping 2010 tracts are listed per 2020 tract, and their weights don't always sum to 1 (0.94 to
  1.0000001). 291 of the listed 2010 tracts are not in `tract-outcomes`, and 791 2020 tracts have no mobility value.
- **`kfr_weighted` can't always be reproduced.** It equals the overlap-weighted mean of the listed `kfr_2010` values
  (renormalized over the ones given) for all but 443 tracts, where it differs by up to 0.05. The ReadMe doesn't say
  why; the step checks the count.

**Covariates**
- Covariates come from public sources: the 1990, 2000 and 2010 Census, the ACS, LODES job data and the Stanford
  Education Data Archive. The year is in each name. Codebook Tables 9-11 define them.
- Shares are fractions from 0 to 1, except **`mail_return_rate2010`, a percentage from 0 to 100**.
- Dollar amounts are as published. The codebooks give each one's source (for example `med_hhinc2016` from the
  2012-2016 ACS) but not a price year, so check before comparing them across years.

## If a download no longer matches

`fetch_raw.py` keeps the new download as `raw/<name>_download.csv`. Opportunity Insights has not changed these files
since 2018 (2020 for the covariates, 2021 for the crosswalk). Compare the new download with the pinned file using
DuckDB:
- **The rows are unchanged but the bytes differ:** update the size and SHA-256 in `fetch_raw.py`, in the recipe step
  that reads the file, and in `sources.toml`.
- **The rows changed:** treat it as a new release. Update the pin as above, then the known facts in the steps,
  `sources.toml`, the counts and sample records in this README, and this dataset's row in
  [`../README.md`](../README.md).

After either change, run `uv run useful-views sync --all` and `uv run useful-views cookbook`.

## Sources and credit

Raj Chetty, John N. Friedman, Nathaniel Hendren, Maggie R. Jones and Sonya R. Porter, "The Opportunity Atlas:
Mapping the Childhood Roots of Social Mobility", *American Economic Review* 116(1): 1-51, 2026 (NBER Working Paper
25147, 2018). Data: https://opportunityinsights.org/data/ and
https://opportunityinsights.org/paper/the-opportunity-atlas/. The codebooks for Tables 1-3 and 7-11 and the
crosswalk's ReadMe are linked from that page and named in `sources.toml`.

Opportunity Insights states no license for the data; the site's footer reads "©2026 Opportunity Insights. All rights
reserved." This repository publishes recipes and records, not the data, and each user downloads the files from
Opportunity Insights. The Atlas's page carries this disclaimer:

> Any opinions and conclusions expressed herein are those of the authors and do not necessarily reflect the views of
> the U.S. Census Bureau.

The codebooks say the statistics "have been cleared by the Census Bureau's Disclosure Review Board release
authorization number CBDRB-FY18-319".
