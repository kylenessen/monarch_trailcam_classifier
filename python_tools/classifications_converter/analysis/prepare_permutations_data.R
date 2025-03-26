#!/usr/bin/env Rscript

# Script to prepare a comprehensive CSV file containing all permutations of monarch count data
# with associated metrics for further analysis.

library(tidyverse)

# Define data directory
data_directory <- "data/"

# Function to generate all possible permutations for a given interval
generate_permutations <- function(df, interval) {
    permutations <- list()
    for (offset in 1:interval) {
        permutations[[offset]] <- df %>%
            group_by(deployment_id) %>%
            filter((row_number() - offset) %% interval == 0) %>%
            ungroup()
    }
    names(permutations) <- paste0("perm_", 1:interval)
    return(permutations)
}

# Function to calculate monarch count changes
calculate_monarch_changes <- function(df) {
    df %>%
        arrange(deployment_id, time) %>%
        group_by(deployment_id) %>%
        mutate(
            prev_count = lag(count),
            raw_change = count - prev_count,
            # Replace zero changes with 0.1 before log transform
            change_for_log = ifelse(raw_change == 0, 0.1, raw_change),
            monarch_change = log(abs(change_for_log)) * sign(change_for_log),
            time_diff_minutes = as.numeric(difftime(time, lag(time), units = "mins"))
        ) %>%
        ungroup()
}

# Define night periods
night_periods <- list(
    SC1 = list(
        list(start = "20231117174001", end = "20231118062001"),
        list(start = "20231118172501", end = "20231119061501"),
        list(start = "20231119171001", end = "20231120062001")
    ),
    SC2 = list(
        list(start = "20231117172501", end = "20231118062001"),
        list(start = "20231118171501", end = "20231119061501")
    ),
    SC4 = list(
        list(start = "20231203171001", end = "20231204063001")
    )
)

# Function to check if a timestamp falls within any night period
is_night_time <- function(timestamp, deployment_periods) {
    any(sapply(deployment_periods, function(period) {
        timestamp >= ymd_hms(period$start, tz = "America/Los_Angeles") &
            timestamp <= ymd_hms(period$end, tz = "America/Los_Angeles")
    }))
}

# Load and process wind data
wind <- read_csv("https://raw.githubusercontent.com/kylenessen/masters-wind-data/main/vsfb/vsfb_wind_data.csv")

# Helper function to create empty wind summary
create_empty_wind_summary <- function() {
    tibble(
        avg_wind_speed_mph = NA_real_,
        avg_wind_gust_mph = NA_real_,
        max_wind_gust_mph = NA_real_,
        n_wind_obs = 0L
    )
}

# Function to calculate wind metrics between intervals
calculate_wind_metrics <- function(deploy_id, start_time, end_time) {
    if (is.na(start_time)) {
        return(create_empty_wind_summary())
    }

    wind_interval <- wind %>%
        filter(
            deployment_id == deploy_id,
            time >= start_time,
            time <= end_time
        )

    if (nrow(wind_interval) == 0) {
        return(create_empty_wind_summary())
    }

    wind_interval %>%
        summarize(
            avg_wind_speed_mph = mean(speed_mph, na.rm = TRUE),
            avg_wind_gust_mph = mean(gust_mph, na.rm = TRUE),
            max_wind_gust_mph = max(gust_mph, na.rm = TRUE),
            n_wind_obs = n()
        )
}

# Main processing
main <- function() {
    # Load 5-min interval datasets and downsample to 10 mins
    df <- c("SC1.csv", "SC2.csv") %>%
        map_df(~ read_csv(file.path(data_directory, .))) %>%
        mutate(time = ymd_hms(timestamp, tz = "America/Los_Angeles")) %>%
        arrange(deployment_id, time) %>%
        group_by(deployment_id) %>%
        filter(row_number() %% 2 == 1) %>%
        ungroup() %>%
        as_tibble()

    # Load SC4 data (already at 10-min intervals)
    SC4 <- read.csv("data/SC4.csv") %>%
        mutate(time = ymd_hms(timestamp, tz = "America/Los_Angeles")) %>%
        as_tibble()

    # Combine all data
    df <- bind_rows(df, SC4) %>%
        arrange(deployment_id, time) %>%
        mutate(
            day = as.Date(time, tz = "America/Los_Angeles"),
            observation_period = paste(deployment_id, day)
        )

    # Remove night periods
    df <- df %>%
        group_by(deployment_id) %>%
        filter(!mapply(
            function(t, d) is_night_time(t, night_periods[[d]]),
            time,
            deployment_id
        )) %>%
        ungroup()

    # Generate permutations for each interval
    intervals <- c(10, 20, 30, 60, 90, 120)
    all_permutations <- list()

    # 10 minutes (keep all rows)
    all_permutations[["10"]] <- list(df)
    names(all_permutations[["10"]]) <- "perm_1"

    # Generate permutations for other intervals
    for (interval in intervals[-1]) {
        all_permutations[[as.character(interval)]] <- generate_permutations(df, interval / 10)
    }

    # Calculate metrics for each permutation
    processed_data <- map_dfr(names(all_permutations), function(interval) {
        interval_num <- as.numeric(interval)
        map_dfr(names(all_permutations[[interval]]), function(perm) {
            perm_num <- as.numeric(gsub("perm_", "", perm))
            df_perm <- all_permutations[[interval]][[perm]] %>%
                calculate_monarch_changes()

            # Add interval and permutation info
            df_perm %>%
                mutate(
                    interval_minutes = interval_num,
                    permutation_number = perm_num
                )
        })
    })

    # Save to CSV
    write_csv(processed_data, "data/processed_permutations.csv")
    cat("Processed data saved to data/processed_permutations.csv\n")
}

# Run the script
main()
