-- This file should contain all code required to create & seed database tables.

DROP DATABASE disinformation;
CREATE DATABASE disinformation;
\c disinformation 

CREATE TABLE tags (
    tag_id INT GENERATED ALWAYS AS IDENTITY,
    tag VARCHAR(30) NOT NULL,
    PRIMARY KEY(tag_id)
);

CREATE TABLE claim_tags (
    claim_tags_id INT GENERATED ALWAYS AS IDENTITY,
    claim_tags VARCHAR(30) NOT NULL,
    PRIMARY KEY(claim_tags_id)
);

CREATE TABLE outlet (
    outlet_id INT GENERATED ALWAYS AS IDENTITY,
    outlet VARCHAR(30) NOT NULL,
    PRIMARY KEY(outlet_id)
);

CREATE TABLE source (
    source_id INT GENERATED ALWAYS AS IDENTITY,
    source_url VARCHAR(30) NOT NULL,
    source_verification TEXT, -- DOUBLE CHECK THIS!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    outlet_id INT NOT NULL,
    PRIMARY KEY(source_id)
);

CREATE TABLE claim_source (
    claim_source_id INT GENERATED ALWAYS AS IDENTITY,
    claim_id INT NOT NULL,
    source_id INT NOT NULL,
    PRIMARY KEY(claim_source_id)
);

CREATE TABLE verdict (
    verdict_id INT GENERATED ALWAYS AS IDENTITY,
    verdict VARCHAR(30) NOT NULL,
    PRIMARY KEY(verdict_id)
);

CREATE TABLE claim (
    claim_id INT GENERATED ALWAYS AS IDENTITY,
    claim VARCHAR(30) NOT NULL,
    claim_url TEXT,
    datetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    verdict_id INT NOT NULL,
    summary TEXT NOT NULL,
    claim_embedding VECTOR NOT NULL,
    PRIMARY KEY(claim_id),
    CONSTRAINT datetime CHECK(datetime <= CURRENT_TIMESTAMP)
    UNIQUE(claim)
);

INSERT INTO tags 
    (tag)
VALUES
    (''),
    ('')
