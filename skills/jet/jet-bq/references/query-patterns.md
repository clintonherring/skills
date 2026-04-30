# BigQuery SQL Patterns

## Table of Contents
- [Common Table Expressions (CTEs)](#common-table-expressions-ctes)
- [Window Functions](#window-functions)
- [Date and Time Handling](#date-and-time-handling)
- [Working with Arrays and Structs](#working-with-arrays-and-structs)
- [Pivoting Data](#pivoting-data)
- [Conditional Aggregation](#conditional-aggregation)
- [Approximate Functions](#approximate-functions)
- [Funnel Analysis](#funnel-analysis)
- [Cohort Analysis](#cohort-analysis)
- [Gap and Island Detection](#gap-and-island-detection)
- [Deduplication](#deduplication)
- [Running Totals and Moving Averages](#running-totals-and-moving-averages)

## Common Table Expressions (CTEs)

Use CTEs to break complex queries into readable steps:

```sql
WITH daily_orders AS (
  SELECT
    DATE(created_at) AS order_date,
    customer_id,
    COUNT(*) AS order_count,
    SUM(total_amount) AS revenue
  FROM `project.dataset.orders`
  WHERE created_at >= TIMESTAMP('2024-01-01')
  GROUP BY 1, 2
),
customer_summary AS (
  SELECT
    customer_id,
    COUNT(DISTINCT order_date) AS active_days,
    SUM(order_count) AS total_orders,
    SUM(revenue) AS total_revenue
  FROM daily_orders
  GROUP BY 1
)
SELECT *
FROM customer_summary
WHERE total_orders >= 5
ORDER BY total_revenue DESC
LIMIT 100
```

## Window Functions

### Ranking

```sql
-- ROW_NUMBER: unique sequential rank
SELECT *,
  ROW_NUMBER() OVER (PARTITION BY category ORDER BY revenue DESC) AS rank
FROM sales

-- RANK: same rank for ties, gaps after ties
SELECT *,
  RANK() OVER (PARTITION BY category ORDER BY revenue DESC) AS rank
FROM sales

-- DENSE_RANK: same rank for ties, no gaps
SELECT *,
  DENSE_RANK() OVER (ORDER BY score DESC) AS rank
FROM leaderboard
```

### Lag/Lead (previous/next row)

```sql
SELECT
  event_date,
  metric_value,
  LAG(metric_value) OVER (ORDER BY event_date) AS prev_value,
  LEAD(metric_value) OVER (ORDER BY event_date) AS next_value,
  metric_value - LAG(metric_value) OVER (ORDER BY event_date) AS day_over_day_change
FROM daily_metrics
```

### Running aggregates

```sql
SELECT
  order_date,
  daily_revenue,
  SUM(daily_revenue) OVER (ORDER BY order_date) AS cumulative_revenue,
  AVG(daily_revenue) OVER (
    ORDER BY order_date
    ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
  ) AS rolling_7day_avg
FROM daily_revenue
```

### FIRST_VALUE / LAST_VALUE

```sql
SELECT
  user_id,
  event_timestamp,
  event_name,
  FIRST_VALUE(event_name) OVER (
    PARTITION BY user_id ORDER BY event_timestamp
  ) AS first_event,
  FIRST_VALUE(event_name) OVER (
    PARTITION BY user_id ORDER BY event_timestamp DESC
  ) AS last_event
FROM events
```

## Date and Time Handling

BQ has four date/time types: `DATE`, `DATETIME`, `TIMESTAMP`, `TIME`.

### Type conversions

```sql
-- TIMESTAMP to DATE
SELECT DATE(timestamp_col)

-- STRING to DATE
SELECT PARSE_DATE('%Y-%m-%d', '2024-01-15')

-- STRING to TIMESTAMP
SELECT PARSE_TIMESTAMP('%Y-%m-%dT%H:%M:%S', '2024-01-15T10:30:00')

-- DATE to TIMESTAMP
SELECT TIMESTAMP(date_col)
```

### Date arithmetic

```sql
-- Subtract days
SELECT DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)

-- Add months
SELECT DATE_ADD(start_date, INTERVAL 3 MONTH)

-- Difference in days
SELECT DATE_DIFF(end_date, start_date, DAY)

-- Difference in months
SELECT DATE_DIFF(end_date, start_date, MONTH)

-- Truncate to week/month/quarter/year
SELECT DATE_TRUNC(order_date, WEEK)
SELECT DATE_TRUNC(order_date, MONTH)
SELECT DATE_TRUNC(order_date, QUARTER)

-- Extract parts
SELECT EXTRACT(YEAR FROM order_date) AS year
SELECT EXTRACT(DAYOFWEEK FROM order_date) AS dow  -- 1=Sun, 7=Sat
```

### Timestamp arithmetic

```sql
-- Subtract interval from timestamp
SELECT TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)

-- Difference in seconds/minutes/hours
SELECT TIMESTAMP_DIFF(end_ts, start_ts, SECOND) AS duration_secs
```

### Common date filters

```sql
-- Last 7 days
WHERE date_col >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)

-- This month
WHERE date_col >= DATE_TRUNC(CURRENT_DATE(), MONTH)

-- Previous month
WHERE date_col >= DATE_TRUNC(DATE_SUB(CURRENT_DATE(), INTERVAL 1 MONTH), MONTH)
  AND date_col < DATE_TRUNC(CURRENT_DATE(), MONTH)

-- Last N complete weeks (Mon-Sun)
WHERE date_col >= DATE_TRUNC(DATE_SUB(CURRENT_DATE(), INTERVAL 4 WEEK), ISOWEEK)
  AND date_col < DATE_TRUNC(CURRENT_DATE(), ISOWEEK)
```

## Working with Arrays and Structs

### UNNEST arrays

```sql
-- Flatten array column
SELECT
  order_id,
  item.product_id,
  item.quantity,
  item.price
FROM `dataset.orders`,
UNNEST(line_items) AS item

-- Flatten with offset (for array index)
SELECT
  order_id,
  offset AS item_index,
  item.product_id
FROM `dataset.orders`,
UNNEST(line_items) AS item WITH OFFSET AS offset
```

### Create arrays

```sql
-- Aggregate into array
SELECT
  user_id,
  ARRAY_AGG(product_id ORDER BY purchase_date) AS products_purchased
FROM purchases
GROUP BY user_id

-- Array of structs
SELECT
  user_id,
  ARRAY_AGG(STRUCT(product_id, quantity, price) ORDER BY purchase_date) AS items
FROM purchases
GROUP BY user_id
```

### Array functions

```sql
-- Check if array contains a value
WHERE 'premium' IN UNNEST(tags)

-- Array length
SELECT ARRAY_LENGTH(tags) AS tag_count

-- Subquery in array
SELECT ARRAY(SELECT DISTINCT tag FROM UNNEST(tags) AS tag ORDER BY tag) AS unique_tags
```

### Access struct fields

```sql
SELECT
  user.name,
  user.address.city,
  user.address.country
FROM `dataset.users`
```

## Pivoting Data

### Manual pivot with conditional aggregation

```sql
SELECT
  product_category,
  SUM(IF(EXTRACT(MONTH FROM order_date) = 1, revenue, 0)) AS jan,
  SUM(IF(EXTRACT(MONTH FROM order_date) = 2, revenue, 0)) AS feb,
  SUM(IF(EXTRACT(MONTH FROM order_date) = 3, revenue, 0)) AS mar
FROM orders
GROUP BY product_category
```

### PIVOT operator (Standard SQL)

```sql
SELECT *
FROM (
  SELECT product_category, EXTRACT(MONTH FROM order_date) AS month, revenue
  FROM orders
)
PIVOT (
  SUM(revenue)
  FOR month IN (1 AS jan, 2 AS feb, 3 AS mar)
)
```

### UNPIVOT (columns to rows)

```sql
SELECT *
FROM monthly_metrics
UNPIVOT (
  metric_value
  FOR month IN (jan, feb, mar, apr, may, jun)
)
```

## Conditional Aggregation

Prefer `COUNTIF`/`SUMIF` over `CASE WHEN` + aggregate:

```sql
SELECT
  DATE(created_at) AS day,
  COUNT(*) AS total_orders,
  COUNTIF(status = 'completed') AS completed,
  COUNTIF(status = 'cancelled') AS cancelled,
  COUNTIF(status = 'completed') / COUNT(*) AS completion_rate,
  SUMIF(total_amount, status = 'completed') AS completed_revenue
FROM orders
GROUP BY 1
```

Use `IF` inside aggregates for computed conditionals:

```sql
SELECT
  country,
  AVG(IF(is_premium, order_total, NULL)) AS avg_premium_order,
  AVG(IF(NOT is_premium, order_total, NULL)) AS avg_standard_order
FROM orders
GROUP BY 1
```

## Approximate Functions

For large tables, approximate functions are faster and cheaper:

```sql
-- Approximate distinct count (typically < 1% error)
SELECT APPROX_COUNT_DISTINCT(user_id) AS unique_users
FROM events

-- Approximate quantiles (percentiles)
SELECT APPROX_QUANTILES(response_time_ms, 100)[OFFSET(50)] AS p50,
       APPROX_QUANTILES(response_time_ms, 100)[OFFSET(95)] AS p95,
       APPROX_QUANTILES(response_time_ms, 100)[OFFSET(99)] AS p99
FROM requests

-- Approximate top N values
SELECT APPROX_TOP_COUNT(page_url, 10) AS top_pages
FROM pageviews
```

## Funnel Analysis

```sql
WITH user_events AS (
  SELECT
    user_id,
    MAX(IF(event_name = 'page_view', 1, 0)) AS did_view,
    MAX(IF(event_name = 'add_to_cart', 1, 0)) AS did_add_to_cart,
    MAX(IF(event_name = 'begin_checkout', 1, 0)) AS did_begin_checkout,
    MAX(IF(event_name = 'purchase', 1, 0)) AS did_purchase
  FROM events
  WHERE event_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
  GROUP BY user_id
)
SELECT
  COUNTIF(did_view = 1) AS step1_view,
  COUNTIF(did_add_to_cart = 1) AS step2_cart,
  COUNTIF(did_begin_checkout = 1) AS step3_checkout,
  COUNTIF(did_purchase = 1) AS step4_purchase,
  ROUND(COUNTIF(did_add_to_cart = 1) / COUNTIF(did_view = 1), 4) AS view_to_cart_rate,
  ROUND(COUNTIF(did_purchase = 1) / COUNTIF(did_view = 1), 4) AS view_to_purchase_rate
FROM user_events
```

### Sequential funnel (ordered steps)

```sql
WITH user_steps AS (
  SELECT
    user_id,
    MIN(IF(event_name = 'page_view', event_timestamp, NULL)) AS view_ts,
    MIN(IF(event_name = 'add_to_cart', event_timestamp, NULL)) AS cart_ts,
    MIN(IF(event_name = 'purchase', event_timestamp, NULL)) AS purchase_ts
  FROM events
  WHERE event_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
  GROUP BY user_id
)
SELECT
  COUNT(*) AS total_users,
  COUNTIF(view_ts IS NOT NULL) AS viewed,
  COUNTIF(cart_ts IS NOT NULL AND cart_ts > view_ts) AS added_to_cart_after_view,
  COUNTIF(purchase_ts IS NOT NULL AND purchase_ts > cart_ts) AS purchased_after_cart
FROM user_steps
```

## Cohort Analysis

### Retention by signup cohort

```sql
WITH user_cohorts AS (
  SELECT
    user_id,
    DATE_TRUNC(signup_date, MONTH) AS cohort_month
  FROM users
),
user_activity AS (
  SELECT
    user_id,
    DATE_TRUNC(activity_date, MONTH) AS activity_month
  FROM events
  GROUP BY 1, 2
)
SELECT
  c.cohort_month,
  DATE_DIFF(a.activity_month, c.cohort_month, MONTH) AS months_since_signup,
  COUNT(DISTINCT a.user_id) AS active_users,
  COUNT(DISTINCT a.user_id) / MAX(cohort_size.cnt) AS retention_rate
FROM user_cohorts c
JOIN user_activity a USING (user_id)
JOIN (
  SELECT cohort_month, COUNT(DISTINCT user_id) AS cnt
  FROM user_cohorts
  GROUP BY 1
) cohort_size USING (cohort_month)
WHERE DATE_DIFF(a.activity_month, c.cohort_month, MONTH) BETWEEN 0 AND 12
GROUP BY 1, 2
ORDER BY 1, 2
```

## Gap and Island Detection

Find consecutive date ranges (islands) and gaps:

```sql
WITH numbered AS (
  SELECT
    user_id,
    activity_date,
    DATE_DIFF(activity_date, DATE '1970-01-01', DAY)
      - ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY activity_date) AS grp
  FROM (SELECT DISTINCT user_id, activity_date FROM daily_activity)
)
SELECT
  user_id,
  MIN(activity_date) AS streak_start,
  MAX(activity_date) AS streak_end,
  DATE_DIFF(MAX(activity_date), MIN(activity_date), DAY) + 1 AS streak_length
FROM numbered
GROUP BY user_id, grp
ORDER BY user_id, streak_start
```

## Deduplication

### Keep latest row per key

```sql
SELECT * EXCEPT(rn)
FROM (
  SELECT *,
    ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY updated_at DESC) AS rn
  FROM `dataset.users`
)
WHERE rn = 1
```

### QUALIFY (cleaner deduplication)

```sql
SELECT *
FROM `dataset.users`
QUALIFY ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY updated_at DESC) = 1
```

## Running Totals and Moving Averages

```sql
SELECT
  order_date,
  daily_revenue,
  -- Cumulative total
  SUM(daily_revenue) OVER (ORDER BY order_date) AS running_total,
  -- 7-day moving average
  AVG(daily_revenue) OVER (
    ORDER BY order_date
    ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
  ) AS ma_7day,
  -- 30-day moving average
  AVG(daily_revenue) OVER (
    ORDER BY order_date
    ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
  ) AS ma_30day,
  -- Month-to-date total
  SUM(daily_revenue) OVER (
    PARTITION BY DATE_TRUNC(order_date, MONTH)
    ORDER BY order_date
  ) AS mtd_revenue
FROM daily_revenue_summary
ORDER BY order_date
```
