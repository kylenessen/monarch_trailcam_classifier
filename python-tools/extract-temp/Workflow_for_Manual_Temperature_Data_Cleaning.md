---
date: '2025-08-06T04:35:45+00:00'
duration_seconds: 0.2
keywords:
- data cleaning
- time series
- workflow
- interactive plot
- manual review
- master's project
llm_service: openrouter
original_filename: DV-2025-08-05-213539.mp3
processed_date: '2025-08-06T04:37:13.965254'
word_count: 251
---
# Workflow for Manual Temperature Data Cleaning

This is for my master's project on temperature data cleaning. I've corrected a lot of the values, but I still see issues that are difficult to isolate programmatically. Since there aren't too many left, I'm outlining a workflow for manual review.

My goal is to go through the data deployment by deployment.

### Proposed Process

1.  **Load Data**: A script will load a single deployment's data.

2.  **Visualize**: The script will generate an interactive time series plot of temperature vs. time. This will allow me to zoom in and out to inspect the data closely.

3.  **Identify & Mark Points**: I need to be able to select specific, problematic data points directly from the chart for follow-up.
    *   **Ideal Method**: I could click on an observation in the plot to automatically mark it.
    *   **Alternative Method**: If direct marking isn't possible, clicking a point could copy its identifier to my clipboard. I could then paste this information into a separate spreadsheet.

4.  **Export**: When I'm finished reviewing a deployment, the script should export the list of marked points to a CSV file named using the convention: `[deployment_name]_followup.csv`.

5.  **Correct**: I can then feed this `_followup.csv` file into my labeling script to generate the final corrections and incorporate them into the final data frame.

This manual identification process makes sense at this stage, as the number of remaining errors is small, and it will be quick to clean things up once the workflow is established.