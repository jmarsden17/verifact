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
    claim TEXT NOT NULL UNIQUE,
    claim_url TEXT,
    datetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    verdict_id INT NOT NULL,
    technique_id INT NOT NULL,
    summary TEXT NOT NULL,
    claim_embedding VECTOR NOT NULL,
    PRIMARY KEY(claim_id),
    FOREIGN KEY(verdict_id) REFERENCES verdict(verdict_id),
    FOREIGN KEY(technique_id) REFERENCES technique(technique_id),
    CONSTRAINT check_datetime CHECK(datetime <= CURRENT_TIMESTAMP)
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
    source_url VARCHAR(30) NOT NULL,
    source_verification TEXT NOT NULL,
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
    ('politics_uk'),
    ('politics_usa'),
    ('politics_international'),
    ('elections_us'),
    ('elections_uk'),
    ('elections_international'),
    ('war_conflict'),
    ('military'),
    ('terrorism'),
    ('immigration'),
    ('economy_finance'),
    ('trade_tariffs'),
    ('healthcare'),
    ('public_health_pandemic'),
    ('vaccines'),
    ('medicine_treatment'),
    ('science_general'),
    ('climate_environment'),
    ('energy'),
    ('technology'),
    ('artificial_intelligence'),
    ('social_media_platforms'),
    ('cybersecurity'),
    ('education'),
    ('religion'),
    ('race_ethnicity'),
    ('gender_sexuality'),
    ('crime_law_enforcement'),
    ('judiciary_legal'),
    ('government_corruption'),
    ('media_journalism'),
    ('celebrity_entertainment'),
    ('sports'),
    ('natural_disaster'),
    ('conspiracy_theory'),
    ('history_revisionism'),
    ('business_corporate'),
    ('labor_employment'),
    ('foreign_interference'),
    ('public_figure_statement'),
    ('other')
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
    ('ai_genereated_content'),
    ('manipulated_media'),
    ('deepfake'),
    ('misleading_context'),
    ('miscaptioned'),
    ('satire_mistaken_as_real'),
    ('statistical_distortion'),
    ('cherry_picking'),
    ('outdated_content'),
    ('unverified_claim'),
    ('opinion_stated_as_fact'),
    ('pseudoscience'),
    ('conspiracy_narrative'),
    ('astroturfing'),
    ('bot_amplification'),
    ('none')
ON CONFLICT (technique) 
DO NOTHING;
