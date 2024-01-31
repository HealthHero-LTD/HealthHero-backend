create_user_table_query = """
CREATE TABLE IF NOT EXISTS "user-profile" (
    username VARCHAR(50) PRIMARY KEY,
    google_email_address VARCHAR(50) UNIQUE,
    steps INTEGER,
    token VARCHAR(256)
);
"""

insert_user_query = """
INSERT INTO "user-profile" (username, google_email_address, steps)
VALUES (%s, %s, %s);
"""

update_token_query = """
UPDATE "user-profile"
SET token = %s
WHERE username = %s;
"""

insert_token_id = """
INSERT INTO users (token_id, email) 
VALUES (%s, %s);
"""

insert_login_user = """
INSERT INTO "users" (googleid)
VALUES (%s);
"""

update_googleID = """
UPDATE "users"
SET steps = %s
WHERE googleid = %s;
"""

get_sorted_leaderboard = """
SELECT username, "level", steps 
FROM LEADERBOARD 
ORDER BY "level" DESC, STEPS DESC;
"""
