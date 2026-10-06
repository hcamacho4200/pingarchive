CREATE TABLE IF NOT EXISTS ping_measurements (
    sent_time TIMESTAMP,
    destination_id LONG,
    destination_name SYMBOL CAPACITY 256 CACHE,
    received_time TIMESTAMP,
    rtt_us LONG,
    outcome SYMBOL CAPACITY 8 CACHE,
    sequence LONG,
    worker_id LONG,
    target_address VARCHAR,
    source_address VARCHAR,
    error_message VARCHAR
) TIMESTAMP(sent_time)
PARTITION BY DAY
DEDUP UPSERT KEYS (sent_time, destination_id, worker_id, sequence);
