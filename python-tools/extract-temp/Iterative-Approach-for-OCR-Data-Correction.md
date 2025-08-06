---
date: '2025-08-05T23:28:58+00:00'
duration_seconds: 0.7
keywords:
- data extraction
- OCR
- missing values
- data cleaning
- iterative process
- manual data entry
- loess
- plotly
llm_service: openrouter
original_filename: DV-2025-08-05-162846.mp3
processed_date: '2025-08-05T23:30:20.600955'
word_count: 425
---
# Strategy for Iterative Data Correction

## Project Reflection and Current Status
I just worked on the temperature extraction data, and it did not go well. While I definitely learned something, I didn't solve the problem, which is unfortunate. The main issue now is the large number of missing values—I think around 170—which was messing up all my algorithms. Dealing with these missing values should be its own bite-sized project.

I also need to clean up the project in the future. I want to remove all the extra scripts and intermediate products that won't be used in the final version. I did commit them for posterity, but they should be deleted for clarity.

## Proposed Solution: Manual Data Entry Tool
The OCR didn't work reliably the first time, so I'm questioning why it would work a second time. Instead of trying to battle the OCR and be unsure about the results, I think I should build a simple tool for manual entry. It might be overbuilt, but it will be more reliable.

The idea is to create a piece of software that:
1.  Takes a list of file paths to JPEGs that are currently missing values.
2.  Presents me with an image and a box to enter the temperature value.
3.  After I type the value and hit enter, it shows the next image.
4.  This process continues until it outputs a new CSV file with all the necessary information, which I can then join into my main data table.

## The Iterative Workflow
This manual entry tool enables an iterative process for refining the entire dataset. I can reuse the script not just for missing values, but also to re-enter values for data points that I identify as suspicious later on.

The workflow would be:
1.  Perform the original automated data extraction.
2.  Use the manual entry tool to fill in all the missing values.
3.  Run one of my better analysis approaches, probably the LOESS approach, as it seemed to be working.
4.  Review the output plots and do a number of passes, correcting data until all of the plots look correct to me.

## Tooling and Visualization
The PNG outputs are awesome for a quick scan. However, it would be better to use Plotly once the algorithm is running and I need to identify suspicious values. With an interactive Plotly chart, I can just identify the file name, handcraft a little CSV file with paths to re-check, and feed that into the manual entry tool. I think that is a compelling approach.