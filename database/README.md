# Database

This folder includes the setup for the RDS Schema and seeds the data.

If you want to set up the database locally, run:
`psql postgres -f schema.sql `

If you want to set up the database in AWS RDS, run:
`psql -h <db_hostname> -p <db_port> -U <db_username> postgres -f schema.sql`
