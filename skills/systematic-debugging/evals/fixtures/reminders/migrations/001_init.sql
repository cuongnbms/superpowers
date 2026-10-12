CREATE TABLE customers (
  id INTEGER PRIMARY KEY,
  email TEXT NOT NULL,
  name TEXT
);

CREATE TABLE subscriptions (
  id INTEGER PRIMARY KEY,
  customer_id INTEGER NOT NULL REFERENCES customers(id),
  plan TEXT NOT NULL,                 -- 'monthly' or 'annual'
  status TEXT NOT NULL,               -- 'active' or 'cancelled'
  renews_at TEXT NOT NULL,            -- next renewal, ISO date YYYY-MM-DD
  source TEXT NOT NULL DEFAULT 'web'  -- 'web' or 'stripe'
);

CREATE TABLE reminder_log (
  subscription_id INTEGER NOT NULL,
  renews_at TEXT NOT NULL,
  sent_at TEXT NOT NULL,
  PRIMARY KEY (subscription_id, renews_at)
);
