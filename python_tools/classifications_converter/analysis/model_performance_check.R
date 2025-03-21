library(performance)
library(nlme)
library(tidyverse)

# Load and prepare the data
data_directory <- "data/"
csv_files <- c("SC1.csv", "SC2.csv")

df <- csv_files %>%
    map_df(~ read_csv(file.path(data_directory, .))) %>%
    mutate(time = ymd_hms(timestamp, tz = "America/Los_Angeles")) %>%
    arrange(deployment_id, time) %>%
    group_by(deployment_id) %>%
    filter(row_number() %% 2 == 1) %>%
    ungroup() %>%
    as_tibble()

SC4 <- read.csv("data/SC4.csv") %>%
    mutate(time = ymd_hms(timestamp, tz = "America/Los_Angeles")) %>%
    as_tibble()

df <- bind_rows(df, SC4) %>%
    arrange(deployment_id, time)

# Remove night periods (reusing the night_periods definition)
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

is_night_time <- function(timestamp, deployment_periods) {
    any(sapply(deployment_periods, function(period) {
        timestamp >= ymd_hms(period$start, tz = "America/Los_Angeles") &
            timestamp <= ymd_hms(period$end, tz = "America/Los_Angeles")
    }))
}

df <- df %>%
    group_by(deployment_id) %>%
    filter(!mapply(
        function(t, d) is_night_time(t, night_periods[[d]]),
        time,
        deployment_id
    )) %>%
    ungroup()

# Create 30-minute dataset
df30 <- df %>%
    group_by(deployment_id) %>%
    filter(row_number() %% 3 == 1) %>%
    ungroup()

# Calculate monarch changes
calculate_monarch_changes <- function(df) {
    df %>%
        arrange(deployment_id, time) %>%
        group_by(deployment_id) %>%
        mutate(
            prev_count = lag(count),
            raw_change = count - prev_count,
            change_for_log = ifelse(raw_change == 0, 0.1, raw_change),
            monarch_change = log(abs(change_for_log)) * sign(change_for_log),
            time_diff_minutes = as.numeric(difftime(time, lag(time), units = "mins"))
        ) %>%
        ungroup()
}

df30 <- calculate_monarch_changes(df30)

# Add wind metrics
wind <- read_csv("https://raw.githubusercontent.com/kylenessen/masters-wind-data/main/vsfb/vsfb_wind_data.csv")

add_intervals <- function(df) {
    df %>%
        arrange(deployment_id, time) %>%
        group_by(deployment_id) %>%
        mutate(
            interval_end = time,
            interval_start = lag(time)
        ) %>%
        ungroup()
}

calculate_wind_metrics <- function(deploy_id, start_time, end_time) {
    if (is.na(start_time)) {
        return(tibble(
            avg_wind_speed_mph = NA_real_,
            avg_wind_gust_mph = NA_real_,
            max_wind_gust_mph = NA_real_,
            n_wind_obs = 0L
        ))
    }

    wind_interval <- wind %>%
        filter(
            deployment_id == deploy_id,
            time >= start_time,
            time <= end_time
        )

    if (nrow(wind_interval) == 0) {
        return(tibble(
            avg_wind_speed_mph = NA_real_,
            avg_wind_gust_mph = NA_real_,
            max_wind_gust_mph = NA_real_,
            n_wind_obs = 0L
        ))
    }

    wind_interval %>%
        summarize(
            avg_wind_speed_mph = mean(speed_mph, na.rm = TRUE),
            avg_wind_gust_mph = mean(gust_mph, na.rm = TRUE),
            max_wind_gust_mph = max(gust_mph, na.rm = TRUE),
            n_wind_obs = n()
        )
}

df30 <- add_intervals(df30) %>%
    bind_cols(
        pmap_dfr(
            list(
                deploy_id = .$deployment_id,
                start_time = .$interval_start,
                end_time = .$interval_end
            ),
            calculate_wind_metrics
        )
    )

# Prepare data for modeling
model_data <- df30 %>%
    filter(
        !is.na(monarch_change), !is.na(avg_wind_speed_mph),
        !is.na(avg_wind_gust_mph), !is.na(max_wind_gust_mph)
    ) %>%
    mutate(
        avg_wind_speed_scaled = scale(avg_wind_speed_mph),
        avg_wind_gust_scaled = scale(avg_wind_gust_mph),
        max_wind_gust_scaled = scale(max_wind_gust_mph),
        time_numeric = as.numeric(time)
    )

# Fit the model
model_30min <- lme(monarch_change ~ avg_wind_speed_scaled + avg_wind_gust_scaled + max_wind_gust_scaled,
    random = ~ 1 | deployment_id,
    correlation = corAR1(form = ~ time_numeric | deployment_id),
    data = model_data,
    method = "REML"
)

# Create performance check plots
check_model_results <- check_model(model_30min)

# Save the plot
png("figures/model_performance_check.png", width = 1200, height = 1000)
plot(check_model_results)
dev.off()

# Create a detailed model summary
summary_stats <- capture.output({
    cat("\n=== 30-Minute Model Performance Summary ===\n\n")
    cat("Model Information:\n")
    cat("- Observations:", nrow(model_data), "\n")
    cat("- Deployments:", length(unique(model_data$deployment_id)), "\n\n")

    cat("Model Summary:\n")
    print(summary(model_30min))

    cat("\nModel Performance Metrics:\n")
    print(model_performance(model_30min))
})

# Save the summary
writeLines(summary_stats, "figures/model_performance_summary.txt")
