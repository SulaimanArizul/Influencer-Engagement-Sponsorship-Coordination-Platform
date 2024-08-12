create table admins (
  id integer PRIMARY key AUTOINCREMENT,
  name varchar(20) not null,
  email VARCHAR(50) not null,
  password varchar(100) not null
);

insert into admins (name, email, password) values ('admin', 'admin@gmail.com', '$2b$12$OoVY1dfuHqC1O1FHAErTeepFJlHh1fTACUtZ.7eaEFLzmipk2W.Jq');

create table influencers (
    id integer PRIMARY key AUTOINCREMENT,
    name varchar(20) not null,
    email VARCHAR(50) not null,
    password varchar(100) not null,
    category varchar(30) not null,
    niche varchar(30) not null,
    reach int default 0,
    is_flagged BOOLEAN DEFAULT 0
);

create table sponsors (
    id integer PRIMARY key AUTOINCREMENT,
    name varchar(20) not null,
    email VARCHAR(50) not null,
    password varchar(100) not null,
    industry varchar(30) not null,
    max_budget decimal(10, 2) not null,
    is_approved BOOLEAN DEFAULT 0,
    is_flagged BOOLEAN DEFAULT 0
);

create table campaigns (
    id integer PRIMARY key AUTOINCREMENT,
    name varchar(30) not null,
    description text null,
    goals text not null,
    start_date datetime not NULL,
    end_date datetime not NULL,
    budget decimal(10, 2) not null,
    is_private boolean DEFAULT 0,
    is_flagged BOOLEAN DEFAULT 0,
    sponsor_id int,
    FOREIGN key (sponsor_id) REFERENCES sponsors (id)
);

create table ad_requests (
    id integer PRIMARY key AUTOINCREMENT,
    status varchar(30) default 'Pending',
    requirements text not null,
    payment_amount decimal(10, 2) not null,
    campaign_id int,
    influencer_id int,
    FOREIGN key (campaign_id) REFERENCES campaigns (id),
    FOREIGN key (influencer_id) REFERENCES influencers (id)
);

create table ad_request_activities (
    id integer PRIMARY key AUTOINCREMENT,
    ad_request_id int,
    message text not null,
    activity_date datetime DEFAULT CURRENT_TIMESTAMP,
    FOREIGN key (ad_request_id) REFERENCES ad_requests (id)
);

-- create table ad_request_invites (
--     id integer PRIMARY key AUTOINCREMENT,
--     ad_request_id int,
--     campaign_id int,
--     influencer_id int,
--     FOREIGN key (campaign_id) REFERENCES campaigns (id),
--     FOREIGN key (ad_request_id) REFERENCES ad_requests (id),
--     FOREIGN key (influencer_id) REFERENCES influencers (id)
-- );

create table messages (
    influencer_id int,
    ad_request_id int,
    sponsor_id int,
    FOREIGN key (influencer_id) REFERENCES influencers (id),
    FOREIGN key (sponsor_id) REFERENCES sponsors (id),
    FOREIGN key (ad_request_id) REFERENCES ad_requests (id)
);
