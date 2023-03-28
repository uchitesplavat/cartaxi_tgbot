DROP TABLE IF EXISTS aggr_order;
DROP TABLE IF EXISTS friend_order;

CREATE TABLE aggr_order (
    id INTEGER CHECK (id = 1 OR id = 2),
    date DATE,
    payout REAL NOT NULL,
    payout_type TEXT NOT NULL CHECK (payout_type IN ('cash', 'air', 'catch')),
    availability BOOLEAN CHECK (availability = TRUE OR availability = FALSE)
);

CREATE TABLE friend_order (
    id INTEGER CHECK (id = 1 OR id = 2),
    date DATE,
    payout REAL NOT NULL,
    availability BOOLEAN CHECK (availability = TRUE OR availability = FALSE)
);


CREATE TABLE salary_and_bank (
                                 date DATE,
                                 salary NUMERIC(10, 2),
                                 cash NUMERIC(10, 2),
                                 air NUMERIC(10, 2),
                                 bank NUMERIC(10, 2)
);