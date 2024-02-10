insert_user_id = """
INSERT INTO users (user_id, email) 
VALUES (%s, %s);
"""

insert_login_user = """
INSERT INTO "users" (googleid)
VALUES (%s);
"""

update_user_id = """
UPDATE "users"
SET steps = %s
WHERE user_id = %s;
"""
