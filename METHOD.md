# Registration and measurement notes

Six screenshots of one Дэлгэрмөрөн bend were selected. Dates were supplied by the user, with month precision only for July and September 2021. No acquisition day, map scale, ground control, or coordinate system is inferred from a screenshot or copyright year.

## Method

Use the raw 2022 screenshot's pixel coordinates. Estimate a least-squares 2D similarity transform for each selected screenshot from matching land-side landmarks. The landmarks are the eastern intersections of two cross-lot fence lines, a circular garden feature south of the middle lot, and the center of a light roof where visible. Use the first three in 2011. The transform estimates one uniform scale, rotation, and translation. Fitted landmark residuals are 0–2.76 reference pixels. These quantify the fit to manually picked landmarks and do not establish positional accuracy at the river.

Mark the visible land–water edge and the relevant riverside fence at three fixed horizontal image rows. Use reference-pixel integer coordinates, approximate to the local visible boundary. The gap is fence x minus edge x. Positive apparent edge movement is toward land on these rows. These are horizontal screen-axis comparisons, not perpendicular survey cross-sections, ground distances, confirmed bank-top positions, or road clearances.

## Interpretation

| Date | T01, y=180 | T02, y=220 | T03, y=255 |
| --- | ---: | ---: | ---: |
| 2011 | 75 | 64 | 56 |
| 2020 | 40 | 33 | 25 |
| 2021-07 | 32 | 21 | — |
| 2021-09 | — | — | — |
| 2022 | 26 | 15 | 10 |
| 2026 | — | — | — |

All numeric widths are reference px. July 2021 has a discontinuous fence trace at T03. September 2021 is retained as qualitative context because the water obscures a comparable edge. The target riverside fence is unidentifiable at all three rows in 2026, so the user-reported relocation cannot be quantified with these transects.

From 2011 to 2022, the three gaps narrow by 49, 49, and 46 reference px. The 2011–2022 visible edge moves landward by 36, 36, and 37 reference px, while the digitized fence lies 13, 13, and 9 reference px farther riverward in the 2022 registered view. The widths reflect both traced features. Fence movement before 2026 is not independently verified. Registration, fence interpretation, water stage, and imagery quality all affect the comparison. Do not interpret the full gap reduction as bank erosion.

For 2022–2026, the visible edge is at x=479→475, 500→496, and 516→514. The small riverward differences (4, 4, and 2 px) do not establish a geomorphic trend. The user reported that the owner moved the fence farther from the river by 2026. The images do not identify its new matching intersections on the fixed rows, and the fence action is separate from observed edge position.

The 2012, 2014, and 2019 screenshots show seasonal surface conditions that complicate direct visual comparison. The 2016–2018 screenshots provide intermediate visual context. The six selected images anchor the comparison and illustrate the within-2021 contrast.

## Reproduction

Run `python app.py` from the project folder to regenerate the dashboard, SVG figures, and CSV table. `data/observations.json` contains the per-frame manual landmark picks and transform coefficients, each selected point in the registered coordinates, and the corresponding image filenames in `images/`. The formula is x′ = a·x − b·y + tx and y′ = b·x + a·y + ty. A null mark is left unmeasured and is shown as an empty CSV cell. Coordinates in the JSON are the digitized inputs, and the application computes widths from these coordinates.
