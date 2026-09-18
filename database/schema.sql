-- This file should contain all code required to create & seed database tables.

DROP DATABASE disinformation;
CREATE DATABASE disinformation;
\c disinformation 

CREATE EXTENSION VECTOR;


-- Creating the tables:

CREATE TABLE verdict (
    verdict_id INT GENERATED ALWAYS AS IDENTITY,
    verdict VARCHAR(30) NOT NULL UNIQUE,
    PRIMARY KEY(verdict_id)
);

CREATE TABLE technique (
    technique_id INT GENERATED ALWAYS AS IDENTITY,
    technique VARCHAR(30) NOT NULL UNIQUE,
    PRIMARY KEY(technique_id)
);

CREATE TABLE claim (
    claim_id INT GENERATED ALWAYS AS IDENTITY,
    claim TEXT NOT NULL,
    publish_datetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    access_datetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    verdict_id INT NOT NULL,
    technique_id INT NOT NULL,
    summary TEXT NOT NULL,
    claim_embedding VECTOR NOT NULL,
    confidence_score FLOAT NOT NULL, 
    PRIMARY KEY(claim_id),
    FOREIGN KEY(verdict_id) REFERENCES verdict(verdict_id),
    FOREIGN KEY(technique_id) REFERENCES technique(technique_id),
    CONSTRAINT check_publish_datetime CHECK(publish_datetime <= CURRENT_TIMESTAMP),
    CONSTRAINT check_access_datetime CHECK (access_datetime <= CURRENT_TIMESTAMP),
    CONSTRAINT check_confidence CHECK (0 <= confidence_score AND 1 >= confidence_score),
    UNIQUE (claim, publish_datetime, access_datetime)
);


CREATE TABLE tags (
    tag_id INT GENERATED ALWAYS AS IDENTITY,
    tag VARCHAR(30) NOT NULL UNIQUE,
    PRIMARY KEY(tag_id)
);

CREATE TABLE claim_tags (
    claim_tags_id INT GENERATED ALWAYS AS IDENTITY,
    claim_id INT NOT NULL,
    tag_id INT NOT NULL,
    PRIMARY KEY(claim_tags_id),
    FOREIGN KEY(claim_id) REFERENCES claim(claim_id),
    FOREIGN KEY(tag_id) REFERENCES tags(tag_id),
    UNIQUE (claim_id, tag_id)
);

CREATE TABLE outlet (
    outlet_id INT GENERATED ALWAYS AS IDENTITY,
    outlet VARCHAR(30) NOT NULL UNIQUE,
    PRIMARY KEY(outlet_id)
);

CREATE TABLE source (
    source_id INT GENERATED ALWAYS AS IDENTITY,
    source_url TEXT NOT NULL,
    source_reasoning TEXT NOT NULL,
    outlet_id INT NOT NULL,
    PRIMARY KEY(source_id),
    FOREIGN KEY(outlet_id) REFERENCES outlet(outlet_id)
);

CREATE TABLE claim_source (
    claim_source_id INT GENERATED ALWAYS AS IDENTITY,
    claim_id INT NOT NULL,
    source_id INT NOT NULL,
    PRIMARY KEY(claim_source_id),
    FOREIGN KEY(claim_id) REFERENCES claim(claim_id),
    FOREIGN KEY(source_id) REFERENCES source(source_id),
    UNIQUE (claim_id, source_id)
);


-- Seeding the tables:

INSERT INTO tags (tag)
VALUES
    ('Politics UK'),
    ('Politics USA'),
    ('Politics International'),
    ('Elections US'),
    ('Elections UK'),
    ('Elections International'),
    ('War/Conflict'),
    ('Military'),
    ('Terrorism'),
    ('Abortion'),
    ('Immigration'),
    ('Economy Finance'),
    ('Trade Tariffs'),
    ('Healthcare'),
    ('Public Health Pandemic'),
    ('Vaccines'),
    ('Medicine Treatment'),
    ('Science General'),
    ('Climate Change'),
    ('Environment'),
    ('Energy'),
    ('Technology'),
    ('Artificial Intelligence'),
    ('Social Media Platforms'),
    ('Cybersecurity'),
    ('Education'),
    ('Religion'),
    ('Race Ethnicity'),
    ('Gender Sexuality'),
    ('Crime Law Enforcement'),
    ('Judiciary Legal'),
    ('Government Corruption'),
    ('Media Journalism'),
    ('Celebrity Entertainment'),
    ('Sports'),
    ('Natural Disaster'),
    ('Conspiracy Theory'),
    ('History Revisionism'),
    ('Business Corporate'),
    ('Labor Employment'),
    ('Foreign Interference'),
    ('Public Figure Statement'),
    ('Europe'),
    ('Asia'),
    ('Africa'),
    ('Americas'),
    ('Middle East'),
    ('Oceania'),
    ('Other')
ON CONFLICT (tag) 
DO NOTHING;


INSERT INTO outlet (outlet)
VALUES
    ('Reuters Fact Check'),
    ('BBC Verify'),
    ('Full Fact'),
    ('Wikipedia API')
ON CONFLICT (outlet) 
DO NOTHING;


INSERT INTO verdict (verdict)
VALUES
    ('Supported'),
    ('Contradicted'),
    ('Mixed / Missing Context'),
    ('Unclear / Not enough evidence')
ON CONFLICT (verdict) 
DO NOTHING;


INSERT INTO technique (technique)
VALUES
    ('AI Generated Content'),
    ('Manipulated Media'),
    ('Deepfake'),
    ('Misleading Context'),
    ('Miscaptioned'),
    ('Satire Mistaken As Real'),
    ('Statistical Distortion'),
    ('Cherry Picking'),
    ('Outdated Content'),
    ('Unverified Claim'),
    ('Opinion Stated As Fact'),
    ('Pseudoscience'),
    ('Conspiracy Narrative'),
    ('Astroturfing'),
    ('Bot Amplification'),
    ('None')
ON CONFLICT (technique) 
DO NOTHING;