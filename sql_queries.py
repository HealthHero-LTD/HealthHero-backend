check_login_user_id = """
SELECT user_id FROM users WHERE user_id=%s
"""

insert_login_user_id = """
INSERT INTO users (user_id, email) 
VALUES (%s, %s);
"""

get_user = """
SELECT username, level, xp, last_active_date
FROM users
WHERE user_id = %s
"""

fetch_leaderboard = """
SELECT username, level, xp
FROM users 
ORDER BY level DESC, xp DESC;
"""

check_username = """
SELECT username 
FROM users 
WHERE username = %s LIMIT 1
"""

update_username = """
UPDATE users 
SET username = %s 
WHERE user_id = %s
"""

update_users_level = """
UPDATE users
SET level = %s
WHERE user_id = %s
"""

update_users_xp = """
UPDATE users
SET xp = %s
WHERE user_id = %s
"""

update_users_info = """
UPDATE users
SET level = %s, xp = %s, last_active_date = %s
WHERE user_id = %s;
"""

insert_daily_xp = """
INSERT INTO daily (user_id, daily_xp, daily_date)
VALUES (%s, %s, %s)
ON CONFLICT (user_id, daily_date)
DO UPDATE SET daily_xp = %s
"""
