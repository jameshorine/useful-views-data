# awesome-urban-datasets

Projects built from [awesome-urban-datasets](https://github.com/urban-toolkit/awesome-urban-datasets), a list of open
urban datasets curated by the [Urban Toolkit](https://urbantk.org/) lab at the University of Illinois Chicago.
- The list, its choice of datasets and its taxonomy (natural phenomena, human-driven phenomena, built and natural
  environment, others) are theirs. The projects here are ours.
- The list has no license, so the descriptions here are written for this repository.

Every entry on the list was checked on 22–23 November 2026. The triage and progress are tracked in
[#59](https://github.com/jameshorine/useful-views-data/issues/59): what can be built now, what waits on a way to pin
live data, and what is gated or too heavy.

## Projects

| Project | Source | Section of the list | Views |
|---|---|---|---|
| [`chicago-energy-usage-2010`](chicago-energy-usage-2010/) | City of Chicago Data Portal, [Energy Usage 2010](https://data.cityofchicago.org/d/8yq3-m6wp) (`8yq3-m6wp`) | Built & natural environment › Buildings & lots | 3: the table typed, monthly kWh and therms, and totals by community area |
| [`guangzhou-traffic-speed`](guangzhou-traffic-speed/) | Chen, Chen and He, [Urban Traffic Speed Dataset of Guangzhou](https://doi.org/10.5281/zenodo.1205229) (Zenodo, CC BY 4.0) | Human-driven phenomena › Mobility | 2: every 10-minute speed typed, and a summary per road segment |

## Notes for every project here

- **Socrata portals** (Chicago, NYC): fetch through the SODA2 endpoint `/resource/<id>.csv`, whose header row uses
  the API field names.
  - Don't use the `rows.csv` export: on both portals it returns `Sunset: Tue, 22 Dec 2026`.
  - Chicago's certificate chain ends at GlobalSign Root R46, which some Python installations lack, so fetch scripts
    use certifi's certificates.
- **Geometry:** projects keep coordinates and geographic codes as plain columns until useful-views 0.4.0
  ([useful-views#43](https://github.com/jameshorine/useful-views/issues/43)) can fingerprint geometry columns. Then
  they gain GeoParquet views.
