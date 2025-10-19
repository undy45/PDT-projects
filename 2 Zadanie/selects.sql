EXPLAIN ANALYZE
SELECT *
FROM users
WHERE screen_name = 'realDonaldTrump';

SET max_parallel_workers_per_gather = 4;
SET max_parallel_workers = 4;

CREATE INDEX idx_users_screen_name ON users (screen_name);

CREATE INDEX idx_follower_count ON users (followers_count);

CREATE INDEX idx_name ON users (name);
CREATE INDEX idx_friends_count ON users (friends_count);
CREATE INDEX idx_description ON users (description);

drop INDEX idx_description, idx_friends_count, idx_name, idx_follower_count, idx_users_screen_name;

INSERT INTO users (id, screen_name, name, followers_count, friends_count, description)
values (3, 'undy', 'undy', 0, 0, 'dkjfhvikusewhfiuoesw');

EXPLAIN ANALYZE
SELECT *
FROM users
where 100 <= followers_count
  AND followers_count <= 1000;


CREATE INDEX idx_retweet_count ON tweets (retweet_count);
CREATE INDEX idx_full_text ON tweets (full_text);


CREATE EXTENSION pageinspect;
SELECT *
FROM bt_metap('idx_full_text');
SELECT type, live_items, dead_items, avg_item_size, page_size, free_size
FROM bt_page_stats('idx_full_text', 1000);
SELECT itemoffset, itemlen, data
FROM bt_page_items('idx_full_text', 1)
LIMIT 1000;

explain analyze
select *
from tweets
where full_text LIKE 'DANGER: WARNING:%';

explain analyze
select *
from tweets
where full_text LIKE '%Gates%';

SELECT id,
       full_text,
       to_tsvector('english', full_text),
       to_tsvector('english', full_text) @@ plainto_tsquery('Gates') AS vec
FROM tweets
WHERE full_text ILIKE '%Gates%'
LIMIT 10;

SELECT tweets.full_text
FROM tweets
WHERE to_tsvector('english', full_text) @@ plainto_tsquery('english', 'Gates');

CREATE INDEX idx_full_text_start ON tweets (full_text text_pattern_ops);

CREATE INDEX idx_full_text_end ON tweets (reverse(full_text) text_pattern_ops);

EXPLAIN ANALYZE
select *
from tweets
where reverse(full_text) LIKE reverse('%LUCIFERASE');

ANALYZE tweets;
EXPLAIN ANALYZE
SELECT *
FROM tweets
WHERE to_tsvector('english', full_text) @@ plainto_tsquery('english', 'Gates');

SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'tweets';

CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE INDEX idx_full_text_gin ON tweets USING gin (to_tsvector('english', full_text));

explain analyse
select *
from users
where followers_count < 1000
  and friends_count > 1000
order by statuses_count;

CREATE INDEX idx_combined_all ON users (followers_count, friends_count);


CREATE INDEX idx_combined_all ON tweets (retweet_count);

explain analyse
select distinct t.*, u.followers_count
from tweets t
         join users u on t.user_id = u.id
where 1 = 1
  and u.description LIKE '%comedian%'
  and t.full_text LIKE '%conspiracy%'
  and (t.retweet_count <= 10 or t.retweet_count >= 50)
  and NOT EXISTS (SELECT 1
                  FROM tweet_hashtag th
                  WHERE th.tweet_id = t.id)
order by u.followers_count DESC;