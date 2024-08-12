from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import sqlite3, os, pandas as pd, numpy as np ,json
from .utils import hash_password, generate_token, verify_token, check_password, get_user
from .cache import cache_get, cache_set, cache_exists, get_redis_connection_url
from celery import Celery
from .mailsender import send_mail
from datetime import date
from celery.schedules import crontab

app = Flask(__name__)
CORS(
    app,
    origins=["http://localhost:3000/", "http://localhost:3000"],
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
    supports_credentials=True,
)  # Allow CORS

celery = Celery(
    app.name, broker=get_redis_connection_url(), backend=get_redis_connection_url()
)
celery.conf.timezone = "Asia/Kolkata"

# backround jobs configuration for celery
celery.conf.beat_schedule = {
    "send-alert-for-pending-ad-requests": {
        "task": "send_alert_for_pending_ad_requests",
        "schedule": crontab(hour=18, minute=0 , day_of_week="*"),
        # "schedule" : 10.0, # 10 seconds
    },
    "send-activity-report": {
        "task": "send-activity-report",
        "schedule": crontab(day_of_month=1),
    },
}

app.extensions["celery"] = celery

PORT = int(os.environ.get("PORT", 8000))
DB_NAME = os.environ.get("DB_NAME", "data.db")
DB_PATH = os.path.join(os.getcwd(), "db.sql")
MAIL_TEMPLATES_PATH = os.path.join(os.getcwd(), "mail-templates")
STATIC_FOLDER_PATH = os.path.join(os.getcwd(), "static")
ROLE_ADMIN, ROLE_INFLUENCER, ROLE_SPONSOR = "ADM", "INF", "SPR"
AVAILABLE_ROLES = [ROLE_ADMIN, ROLE_INFLUENCER, ROLE_SPONSOR]
ALLOWED_SPONSOR_STATUS = [0, 1]
ALLOWED_FLAG_TABLES = ["influencers", "sponsors", "campaigns"]
ALLOWED_USER_TABLES = ["influencers", "sponsors"]
ALLOWED_AD_REQUEST_STATUS = ["pending", "accepted", "rejected"]


# this function connects to the database and returns the connection and cursor
def connect_db():
    conn = sqlite3.connect(DB_NAME)
    return conn, conn.cursor()


# this function creates the database
def create_db():
    with open(DB_PATH) as f:
        conn, cur = connect_db()
        cur.executescript(f.read())
        conn.commit()
        conn.close()


# this login_required decorator checks for token in the request headers and regenerates the token after each request
def check_token(f):
    def wrapper(*args, **kwargs):
        token = request.cookies.get("token", "")

        if not token:
            return jsonify({"msg": "Please login to continue"}), 401

        try:
            payload = verify_token(token)
        except Exception:
            return jsonify({"msg": "Token has expired"}), 401

        new_token = generate_token(payload)

        response = f(*args, **kwargs)
        if isinstance(response, tuple):
            response[0].set_cookie("token", new_token)
        else:
            response.set_cookie("token", new_token)
        return response

    wrapper.__name__ = f.__name__
    return wrapper


# this check_roles decorator checks for the role in the payload and checks if the role is in the roles list
def check_roles(roles):
    def decorator(f):
        def wrapper(*args, **kwargs):

            try:
                payload = get_user(request)
            except Exception:
                return jsonify({"msg": "Please login to continue"}), 401

            role = payload.get("role")
            if role not in roles:
                return (
                    jsonify(
                        {"msg": "Unauthorized , you don't have role for this action"}
                    ),
                    403,
                )
            return f(*args, **kwargs)

        wrapper.__name__ = f.__name__
        return wrapper

    return decorator


# create_db() # Create the sqlite file and tables in it


@app.post("/register")
def register():
    try:
        data = request.json
        role = data.get("role")
        name = data.get("name")
        email = data.get("email")
        password = data.get("password")
        category = data.get("category")
        niche = data.get("niche")
        reach = data.get("reach")
        industry = data.get("industry")
        max_budget = data.get("max_budget")

        full_role = "Influencer" if role == ROLE_INFLUENCER else "Sponsor"

        if not role or not name or not email or not password:
            return jsonify({"msg": "role,name,email,password are required"}), 400

        if role not in AVAILABLE_ROLES:
            return (
                jsonify(
                    {"msg": "Invalid role , must be in " + ", ".join(AVAILABLE_ROLES)}
                ),
                400,
            )

        # check email format
        if not "@" in email or not "." in email:
            return jsonify({"msg": "Invalid email format"}), 400

        # check password length
        if len(password) < 6:
            return jsonify({"msg": "Password must be at least 6 characters"}), 400

        if len(password) > 12:
            return jsonify({"msg": "Password must be at most 12 characters"}), 400

        conn, cur = connect_db()

        if role == ROLE_INFLUENCER:
            if not category or not niche or not reach:
                conn.close()
                return (
                    jsonify(
                        {
                            "msg": "category, niche and reach are required for influencers"
                        }
                    ),
                    400,
                )
            cur.execute("SELECT * FROM influencers WHERE email = ?", (email,))
            user = cur.fetchone()
            if user:
                conn.close()
                return (
                    jsonify({"msg": f"Influencer with email {email} already exists"}),
                    400,
                )
            cur.execute(
                "INSERT INTO influencers (name, email, password , category , niche , reach) VALUES (?, ?, ? , ? , ?, ?)",
                (name, email, hash_password(password), category, niche, reach),
            )
        elif role == ROLE_SPONSOR:
            if not industry or not max_budget:
                conn.close()
                return (
                    jsonify(
                        {"msg": "industry and max_budget are required for sponsors"}
                    ),
                    400,
                )
            cur.execute("SELECT * FROM sponsors WHERE email = ?", (email,))
            user = cur.fetchone()
            if user:
                conn.close()
                return (
                    jsonify({"msg": f"Sponsor with email {email} already exists"}),
                    400,
                )
            cur.execute(
                "INSERT INTO sponsors (name, email, password, industry , max_budget) VALUES (?, ?, ? , ? , ?)",
                (name, email, hash_password(password), industry, max_budget),
            )

        conn.commit()

        cur.execute("SELECT LAST_INSERT_ROWID() as id")
        last_insert = cur.fetchone()
        last_insert = last_insert[0]

        if role == ROLE_INFLUENCER:
            cur.execute("SELECT * FROM influencers WHERE id = ?", (last_insert,))
        elif role == ROLE_SPONSOR:
            cur.execute("SELECT * FROM sponsors WHERE id = ?", (last_insert,))
        
        user = cur.fetchone()
        
        conn.close()

        token = generate_token(
            {
                "role": role,
                "full_role": full_role,
                "email": email,
                "id": user[0],
                "name": user[1],
            }
        )

        response = jsonify({"msg": f"{full_role} registered successfully"})
        response.status_code = 201
        response.set_cookie("token", token)

        return response
    except Exception as e:
        return jsonify({"msg": str(e)}), 500


@app.post("/login")
def login():
    try:
        data = request.json
        email = data.get("email")
        password = data.get("password")
        role = data.get("role")

        full_role = ""

        if not email or not password:
            return jsonify({"msg": "email and password are required"}), 400

        if not role or role not in AVAILABLE_ROLES:
            return (
                jsonify(
                    {"msg": "Invalid role , must be in " + ", ".join(AVAILABLE_ROLES)}
                ),
                400,
            )
        # check email format
        if not "@" in email or not "." in email:
            return jsonify({"msg": "Invalid email format"}), 400

        # check password length
        if len(password) < 6:
            return jsonify({"msg": "Password must be at least 6 characters"}), 400

        if len(password) > 12:
            return jsonify({"msg": "Password must be at most 12 characters"}), 400

        conn, cur = connect_db()

        if role == ROLE_INFLUENCER:
            full_role = "Influencer"
            cur.execute("SELECT * FROM influencers WHERE email = ?", (email,))
            user = cur.fetchone()
        elif role == ROLE_SPONSOR:
            full_role = "Sponser"
            cur.execute("SELECT * FROM sponsors WHERE email = ?", (email,))
            user = cur.fetchone()
        elif role == ROLE_ADMIN:
            full_role = "Admin"
            cur.execute("SELECT * FROM admins WHERE email = ?", (email,))
            user = cur.fetchone()

        conn.close()

        if not user:
            return jsonify({"msg": f"{full_role} with email {email} not found"}), 400

        if not check_password(password, user[3]):
            return jsonify({"msg": f"Invalid password"}), 400

        if role != ROLE_ADMIN:
            if user[7]:
                return (
                    jsonify(
                        {
                            "msg": "You have been flagged by the admin for your actions , please contact support team"
                        }
                    ),
                    400,
                )

        if role == ROLE_SPONSOR:
            if not user[6]:
                return (
                    jsonify(
                        {
                            "msg": "You cannot login until admin approves your profile , please be patient or contact support team"
                        }
                    ),
                    400,
                )

        token = generate_token(
            {
                "role": role,
                "full_role": full_role,
                "email": email,
                "id": user[0],
                "name": user[1],
            }
        )  # generate token

        response = jsonify({"msg": f"Welcome back {full_role} {email}", "id": user[0]})
        response.status_code = 200
        response.set_cookie("token", token)

        return response
    except Exception as e:
        return jsonify({"msg": str(e)}), 500


@app.put("/sponsor-status/<int:sponsor_id>/<int:status>")
@check_roles([ROLE_ADMIN])
@check_token
def update_sponser_status(sponsor_id: int, status: bool):
    try:
        if status not in ALLOWED_SPONSOR_STATUS:
            return jsonify({"msg": "status must be 0 or 1"}), 400

        con, cur = connect_db()

        cur.execute("SELECT * FROM sponsors WHERE ID = ?", (sponsor_id,))
        sponsor = cur.fetchone()

        if not sponsor:
            con.close()
            return jsonify({"msg": f"The Sponsor With Id {sponsor_id} not found"}), 404

        if sponsor[6] == status:
            con.close()
            status_msg = "Approved" if status == 1 else "Rejected"
            return jsonify({"msg": f"The Sponsor is already {status_msg}"}), 400

        cur.execute(
            f"UPDATE sponsors SET is_approved = ? WHERE id = ?", (status, sponsor_id)
        )

        con.commit()
        con.close()
        status_msg = "Approved" if status == 1 else "Rejected"
        return jsonify({"msg": f"Sponsor Status Updated To {status_msg} successfully"})
    except Exception as e:
        return jsonify({"msg": str(e)}), 500


@app.get("/profile/<int:id>")
@check_roles([ROLE_ADMIN, ROLE_SPONSOR, ROLE_INFLUENCER])
@check_token
def get_profile(id: int):
    try:
        logged_in_user = get_user(request)
        user_id = logged_in_user.get("id")
        user_email = logged_in_user.get("email")
        con, _ = connect_db()
        users = pd.read_sql_query(
            "SELECT * FROM influencers WHERE id = ?", con, params=(id,)
        )
        con.close()
        del users["password"]
        users = users.to_dict(orient="records")
        user = users[0]
        return jsonify(
            {
                "user": user,
                "is_me": (user_id == id) and (user_email == user.get("email")),
            }
        )
    except Exception as e:
        return jsonify({"msg": str(e)}), 500


@app.post("/profile/update")
@check_roles([ROLE_ADMIN, ROLE_SPONSOR, ROLE_INFLUENCER])
@check_token
def update_profile():
    try:
        data = request.json
        name = data.get("name")
        email = data.get("email")
        password = data.get("password")
        category = data.get("category")
        niche = data.get("niche")
        reach = data.get("reach")
        user_id = data.get("id")

        user = get_user(request)

        if not name or not email:
            return jsonify({"msg": "name,email are required"}), 400

        # check email format
        if not "@" in email or not "." in email:
            return jsonify({"msg": "Invalid email format"}), 400

        conn, cur = connect_db()

        if not category or not niche or not reach:
            conn.close()
            return (
                jsonify(
                    {"msg": "category, niche and reach are required for influencers"}
                ),
                400,
            )

        cur.execute("SELECT * FROM influencers WHERE email = ?", (email,))
        user = cur.fetchone()

        if user and user[0] != user_id:
            conn.close()
            return (
                jsonify({"msg": f"Influencer with email {email} already exists"}),
                400,
            )

        cur.execute(
            "UPDATE influencers SET name = ?, email = ?, category = ? , niche = ? , reach = ?",
            (name, email, category, niche, reach),
        )

        conn.commit()
        conn.close()

        return jsonify({"msg": "Profile updated successfully"})
    except Exception as e:
        return jsonify({"msg": str(e)}), 500


@app.get("/users/<string:table_name>")
@check_roles([ROLE_ADMIN, ROLE_SPONSOR])
@check_token
def get_users(table_name: str):
    try:
        if not table_name or table_name not in ALLOWED_FLAG_TABLES:
            return (
                jsonify(
                    {
                        "msg": "Invalid table name , must be in "
                        + ", ".join(ALLOWED_FLAG_TABLES)
                    }
                ),
                400,
            )
        
        if cache_exists(table_name):
            users = cache_get(table_name)
            return jsonify(users)
        con, _ = connect_db()
        users = pd.read_sql_query(f"SELECT * FROM {table_name}", con)
        if table_name in ALLOWED_USER_TABLES:
            del users['password']
        users = users.to_dict(orient="records")
        con.close()
        cache_set(table_name, users)
        return jsonify(users)
    except Exception as e:
        return jsonify({"msg": str(e)}), 500


@app.post("/flag/<string:table_name>/<int:id>")
@check_roles([ROLE_ADMIN])
@check_token
def flag_object(table_name: str, id: int):
    try:
        if not table_name or table_name not in ALLOWED_FLAG_TABLES:
            return (
                jsonify(
                    {
                        "msg": "Invalid table name , must be in "
                        + ", ".join(ALLOWED_FLAG_TABLES)
                    }
                ),
                400,
            )

        con, cur = connect_db()

        cur.execute(f"SELECT * FROM {table_name} WHERE ID = ?", (id,))
        obj = cur.fetchone()

        if not obj:
            con.close()
            return jsonify({"msg": f"{table_name} With Id {id} not found"}), 404

        cur.execute(f"UPDATE {table_name} SET is_flagged = 1 WHERE ID = ?", (id,))

        con.commit()
        con.close()

        return jsonify({"msg": f"{table_name} With Id {id} is flagged successfully"})
    except Exception as e:
        return jsonify({"msg": str(e)}), 500


@app.post("/unflag/<string:table_name>/<int:id>")
@check_roles([ROLE_ADMIN])
@check_token
def unflag_object(table_name: str, id: int):
    try:
        if not table_name or table_name not in ALLOWED_FLAG_TABLES:
            return (
                jsonify(
                    {
                        "msg": "Invalid table name , must be in "
                        + ", ".join(ALLOWED_FLAG_TABLES)
                    }
                ),
                400,
            )

        con, cur = connect_db()

        cur.execute(f"SELECT * FROM {table_name} WHERE ID = ?", (id,))
        obj = cur.fetchone()

        if not obj:
            con.close()
            return jsonify({"msg": f"{table_name} With Id {id} not found"}), 404

        cur.execute(f"UPDATE {table_name} SET is_flagged = 0 WHERE ID = ?", (id,))

        con.commit()
        con.close()

        return jsonify({"msg": f"{table_name} With Id {id} is un-flagged successfully"})
    except Exception as e:
        return jsonify({"msg": str(e)}), 500


@app.post("/campaigns")
@check_roles([ROLE_SPONSOR])
@check_token
def add_campaign():
    try:
        data = request.json
        payload = get_user(request)

        id = payload.get("id")  # get user id

        name = data.get("name")
        description = data.get("description")
        start_date = data.get("start_date")
        end_date = data.get("end_date")
        budget = data.get("budget")
        goals = data.get("goals")
        is_private = data.get("is_private")

        con, cur = connect_db()

        if not name or not start_date or not end_date or not budget or not goals:
            con.close()
            return (
                jsonify(
                    {
                        "msg": "name, description, start_date, end_date, budget, goals are required"
                    }
                ),
                400,
            )

        # checking for start_date is less than end_date
        if start_date > end_date:
            con.close()
            return jsonify({"msg": "start_date must be less than end_date"}), 400

        # checking if the budget is a positive number
        if int(budget) < 0:
            con.close()
            return jsonify({"msg": "budget must be a positive number"}), 400

        # check for same name is there for the same start_date and end_date
        cur.execute(
            "SELECT * FROM campaigns WHERE name = ? AND start_date = ? AND end_date = ?",
            (name, start_date, end_date),
        )

        campaign = cur.fetchone()

        if campaign:
            con.close()
            return (
                jsonify(
                    {
                        "msg": f"The campaign name {name} already exists for the same start_date {start_date} and end_date {end_date}"
                    }
                ),
                400,
            )

        if description:
            cur.execute(
                "INSERT INTO campaigns (name, description, start_date, end_date, budget, goals, is_private, sponsor_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    name,
                    description,
                    start_date,
                    end_date,
                    budget,
                    goals,
                    1 if is_private else 0,
                    id,
                ),
            )
        else:
            cur.execute(
                "INSERT INTO campaigns (name, start_date, end_date, budget, goals, is_private , sponsor_id) VALUES (?, ?, ?, ?, ?,? ,?)",
                (name, start_date, end_date, budget, goals, is_private, id),
            )

        con.commit()
        con.close()

        return jsonify({"msg": "Campaign added successfully"})
    except Exception as e:
        return jsonify({"msg": str(e)}), 500


@app.get("/campaigns/me")
@check_roles([ROLE_SPONSOR])
@check_token
def get_my_campaigns():
    try:
        payload = get_user(request)
        id = payload.get("id")

        con, _ = connect_db()

        campaigns = pd.read_sql_query(
            "SELECT * FROM campaigns WHERE sponsor_id = ?", con, params=(id,)
        )

        # delete sponser_id column from the dataframe
        del campaigns["sponsor_id"]

        campaigns = campaigns.to_dict(orient="records")
        con.close()

        return jsonify(campaigns)
    except Exception as e:
        return jsonify({"msg": str(e)}), 500
    

@app.get('/test')
def test():
    con , cur = connect_db()

    cur.execute('UPDATE campaigns set is_private = 0')

    con.commit()
    con.close()
    return jsonify({'msg' : "done"})


@app.get("/campaigns/filter")
@check_roles([ROLE_SPONSOR, ROLE_INFLUENCER, ROLE_ADMIN])
@check_token
def filter_campaigns():
    try:
        user = get_user(request)
        user_id = user.get("id")
        user_role = user.get("role")

        params = request.args.to_dict()
        con, _ = connect_db()
        sql = ""

        if params:
            sql = "AND "
            for key, value in params.items():
                if key == "start_date":
                    sql += f"c.{key} >= '{value}' AND "
                    continue
                if key == "end_date":
                    sql += f"c.{key} <= '{value}' AND "
                    continue
                if key == "budget_lte":
                    sql += f"c.budget <= {value} AND "
                    continue
                if key == "budget_gte":
                    sql += f"c.budget >= {value} AND "
                    continue
                sql += f"c.{key} LIKE '%{value}%' AND "
            sql = sql[:-4]

        date_format = "%d-%m-%Y"

        if user_role == ROLE_SPONSOR:  # filter based on sponsor_id
            campaigns = pd.read_sql_query(
                f"""SELECT c.id, c.name, c.description, 
                                      strftime('{date_format}',c.start_date) start_date,  
                                      strftime('{date_format}',c.end_date) end_date, 
                                      c.budget, c.goals,
                                      s.name as sponsor_name FROM campaigns c
                                      JOIN sponsors s ON c.sponsor_id = s.id
                                      WHERE c.sponsor_id = {user_id} AND c.is_flagged = 0 {sql}""",
                con,
            )
        elif user_role == ROLE_INFLUENCER:  # filter based on is_private
            campaigns = pd.read_sql_query(
                f"""SELECT c.id, c.name, c.description, 
                                      strftime('{date_format}',c.start_date) start_date,  
                                      strftime('{date_format}',c.end_date) end_date, 
                                      c.budget, c.goals,
                                      s.name as sponsor_name FROM campaigns c
                                      JOIN sponsors s ON c.sponsor_id = s.id
                                      WHERE c.is_private = 0 AND c.is_flagged = 0 {sql}""",
                con,
            )
        elif user_role == ROLE_ADMIN:  # filter based on all campaigns
            campaigns = pd.read_sql_query(
                f"""SELECT c.id, c.name, c.description,
                                      strftime('{date_format}',c.start_date) start_date,  
                                      strftime('{date_format}',c.end_date) end_date, 
                                      c.budget, c.goals,c.is_private,c.is_flagged,
                                      s.name as sponsor_name FROM campaigns c
                                      JOIN sponsors s ON c.sponsor_id = s.id {sql}""",
                con,
            )

        min_budget, max_budget = campaigns["budget"].min(), campaigns["budget"].max()

        if isinstance(min_budget, np.int64):
            min_budget = int(min_budget)
        if isinstance(max_budget, np.int64):
            max_budget = int(max_budget)

        campaigns = campaigns.to_dict(orient="records")
        con.close()

        return jsonify(
            {"campaigns": campaigns, "min_budget": min_budget, "max_budget": max_budget}
        )
    except Exception as e:
        return jsonify({"msg": str(e)}), 500


@app.put("/campaigns/<int:campaign_id>")
@check_roles([ROLE_SPONSOR])
@check_token
def update_campaign(campaign_id: int):
    try:
        data = request.json

        name = data.get("name")
        description = data.get("description")
        start_date = data.get("start_date")
        end_date = data.get("end_date")
        budget = data.get("budget")
        goals = data.get("goals")
        is_private = data.get("is_private")

        con, cur = connect_db()

        if not name or not start_date or not end_date or not budget or not goals:
            con.close()
            return (
                jsonify(
                    {
                        "msg": "name, description, start_date, end_date, budget, goals are required"
                    }
                ),
                400,
            )

        # checking for start_date is less than end_date
        if start_date > end_date:
            con.close()
            return jsonify({"msg": "start_date must be less than end_date"}), 400

        # checking if the budget is a positive number
        if budget < 0:
            con.close()
            return jsonify({"msg": "budget must be a positive number"}), 400

        # check for same name is there for the same start_date and end_date
        cur.execute(
            "SELECT * FROM campaigns WHERE name = ? AND start_date = ? AND end_date = ?",
            (name, start_date, end_date),
        )

        campaign = cur.fetchone()

        if campaign and campaign[0] != campaign_id:
            con.close()
            return (
                jsonify(
                    {
                        "msg": f"The campaign name {name} already exists for the same start_date {start_date} and end_date {end_date}"
                    }
                ),
                400,
            )

        cur.execute(
            "UPDATE campaigns SET description = ?, start_date = ?, end_date = ?, budget = ?, goals = ? , name = ? , is_private = ? WHERE id = ?",
            (
                description,
                start_date,
                end_date,
                budget,
                goals,
                name,
                1 if is_private else 0,
                campaign_id,
            ),
        )

        con.commit()

        campaigns = pd.read_sql_query(
            "SELECT * FROM campaigns WHERE id = ?", con, params=(campaign_id,)
        )

        campaigns = campaigns.to_dict(orient="records")

        con.close()

        return jsonify(
            {"msg": "Campaign updated successfully", "campaign": campaigns[0]}
        )
    except Exception as e:
        return jsonify({"msg": str(e)}), 500


@app.delete("/campaigns/<int:id>")
@check_roles([ROLE_SPONSOR])
@check_token
def delete_campaign(id: int):
    try:
        con, cur = connect_db()

        user = get_user(request)
        user_id = user.get("id")

        cur.execute("SELECT * FROM campaigns WHERE id = ?", (id,))
        campaign = cur.fetchone()

        if not campaign:
            con.close()
            return jsonify({"msg": f"Campaign with id {id} not found"}), 404

        cur.execute(
            "SELECT count(1) as count FROM ad_requests WHERE campaign_id = ?", (id,)
        )

        campaign_counts = cur.fetchone()

        if campaign_counts[0] > 0:
            con.close()
            return (
                jsonify(
                    {
                        "msg": f"Cannot delete campaign with id {id} , there are {campaign_counts[0]} ad requests for this campaign"
                    }
                ),
                400,
            )

        if campaign[9] != user_id:
            con.close()
            return (
                jsonify(
                    {
                        "msg": f"Unauthorized , you don't have permission to delete this campaign"
                    }
                ),
                403,
            )

        cur.execute("DELETE FROM campaigns WHERE id = ?", (id,))

        con.commit()
        con.close()

        return jsonify({"msg": "Campaign deleted successfully"})
    except Exception as e:
        return jsonify({"msg": str(e)}), 500


@app.get("/campaigns/<int:id>")
@check_roles([ROLE_SPONSOR, ROLE_INFLUENCER, ROLE_ADMIN])
@check_token
def get_campaign(id: int):
    try:
        con, _ = connect_db()
        user = get_user(request)

        user_role = user.get('role')
        user_id = user.get('id')

        campaign = pd.read_sql_query(
            "SELECT * FROM campaigns WHERE id = ?", con, params=(id,)
        )

        if user_role == ROLE_INFLUENCER:
            ad_requests = pd.read_sql_query(
                """SELECT *,(SELECT name FROM influencers WHERE id = a.influencer_id) 
                influencer_name FROM ad_requests a WHERE campaign_id = ? AND a.influencer_id = ?""",
                con,
                params=(id,user_id,),
            )
        else:
             ad_requests = pd.read_sql_query(
                """SELECT *,(SELECT name FROM influencers WHERE id = a.influencer_id) 
                influencer_name FROM ad_requests a WHERE campaign_id = ?""",
                con,
                params=(id,),
            )

        if campaign.empty:
            con.close()
            return jsonify({"msg": f"Campaign with id {id} not found"}), 404

        campaign = campaign.to_dict(orient="records")
        ad_requests = ad_requests.to_dict(orient="records")
        con.close()

        return jsonify(
            {
                "campaign": campaign[0],
                "ad_requests": ad_requests,
            }
        )
    except Exception as e:
        return jsonify({"msg": str(e)}), 500


@app.post("/ad-requests")
@check_roles([ROLE_SPONSOR, ROLE_INFLUENCER])
@check_token
def add_ad_request():
    try:
        data = request.json
        payload = get_user(request)

        id = payload.get("id")  # get user id

        campaign_id = data.get("campaign_id")
        payment_amount = data.get("payment_amount")
        requirements = data.get("requirements")
        influencer_id = data.get("influencer_id")

        if (
            not campaign_id
            or not payment_amount
            or not requirements
            or not influencer_id
        ):
            return (
                jsonify(
                    {
                        "msg": "campaign_id, payment_amount, requirements, influencer_id are required"
                    }
                ),
                400,
            )

        con, cur = connect_db()

        cur.execute("SELECT * FROM campaigns WHERE id = ?", (campaign_id,))
        campaign = cur.fetchone()

        if not campaign:
            con.close()
            return jsonify({"msg": f"Campaign with id {campaign_id} not found"}), 400

        cur.execute("SELECT * FROM influencers WHERE id = ?", (influencer_id,))
        influencer = cur.fetchone()

        if not influencer:
            con.close()
            return (
                jsonify({"msg": f"Influencer with id {influencer_id} not found"}),
                400,
            )

        cur.execute(
            "INSERT INTO ad_requests (campaign_id, payment_amount, requirements,influencer_id) VALUES (?, ?, ?, ?)",
            (campaign_id, payment_amount, requirements, influencer_id),
        )

        cur.execute("SELECT LAST_INSERT_ROWID() as id")

        ad_request = cur.fetchone()

        ad_request_id = ad_request[0]

        actual_ad_requests = pd.read_sql_query(
            f"SELECT * FROM ad_requests WHERE id = {ad_request_id}", con
        )

        con.commit()
        con.close()

        actual_ad_requests = actual_ad_requests.to_dict(orient="records")

        return jsonify(
            {
                "msg": "Ad Request added successfully",
                "ad_request": actual_ad_requests[0],
            }
        )
    except Exception as e:
        return jsonify({"msg": str(e)}), 500


@app.put("/ad-requests/<int:ad_request_id>")
@check_roles([ROLE_SPONSOR, ROLE_INFLUENCER])
@check_token
def update_ad_request(ad_request_id: int):
    try:
        data = request.json
        payload = get_user(request)

        id = payload.get("id")  # get user id
        role = payload.get("role")
        user_name = payload.get("name")

        campaign_id = data.get("campaign_id")
        payment_amount = data.get("payment_amount")
        requirements = data.get("requirements")
        influencer_id = data.get("influencer_id")  # this is array of influencer ids

        if role == ROLE_SPONSOR:
            if (
                not campaign_id
                or not payment_amount
                or not requirements
                or not influencer_id
            ):
                return (
                    jsonify(
                        {
                            "msg": "campaign_id, payment_amount, requirements, influencer_id are required"
                        }
                    ),
                    400,
                )

        elif role == ROLE_INFLUENCER:
            if not payment_amount:
                return jsonify({"msg": "payment_amount is required"}), 400

        con, cur = connect_db()

        cur.execute("SELECT * FROM campaigns WHERE id = ?", (campaign_id,))
        campaign = cur.fetchone()

        if not campaign:
            con.close()
            return jsonify({"msg": f"Campaign with id {campaign_id} not found"}), 400

        cur.execute("SELECT * FROM ad_requests WHERE id = ?", (ad_request_id,))

        ad_request = cur.fetchone()

        if not ad_request:
            con.close()
            return (
                jsonify({"msg": f"Ad Request with id {ad_request_id} not found"}),
                404,
            )

        msg = ""
        if role == ROLE_SPONSOR:
            cur.execute(
                "UPDATE ad_requests SET payment_amount = ?, requirements = ? , influencer_id = ? WHERE id = ?",
                (payment_amount, requirements, influencer_id, ad_request_id),
            )
            # check if prev amount is updated
            insert_msg = ""
            insert_msg2 = ""

            if ad_request[3] != payment_amount:
                insert_msg = (
                    f"Sponsor {user_name} updated the amount to {payment_amount}"
                )

            if ad_request[2] != requirements:
                insert_msg2 = f"Sponsor {user_name} updated the requirements"
            if insert_msg:
                cur.execute(
                    "INSERT INTO ad_request_activities (ad_request_id,message) VALUES (?,?)",
                    (ad_request_id, insert_msg),
                )
            if insert_msg2:
                cur.execute(
                    "INSERT INTO ad_request_activities (ad_request_id,message) VALUES (?,?)",
                    (ad_request_id, insert_msg2),
                )

            msg = "Ad Request updated successfully"
        elif role == ROLE_INFLUENCER:
            if requirements or influencer_id:
                con.close()
                return (
                    jsonify({"msg": "Influencer can only update payment_amount"}),
                    400,
                )

            cur.execute(
                "UPDATE ad_requests SET payment_amount = ? WHERE id = ?",
                (payment_amount, id),
            )
            insert_msg = ""
            if ad_request[3] != payment_amount:
                insert_msg = (
                    f"Influencer {user_name} updated the amount to {payment_amount}"
                )

            if insert_msg:
                cur.execute(
                    "INSERT INTO ad_request_activities (ad_request_id,message) VALUES (?,?)",
                    (ad_request_id, insert_msg),
                )
            msg = "Payment Amount updated successfully"

        con.commit()
        con.close()

        return jsonify({"msg": msg})
    except Exception as e:
        return jsonify({"msg": str(e)}), 500


@app.put("/ad-requests/<int:ad_request_id>/<string:status>")
@check_roles([ROLE_INFLUENCER])
@check_token
def update_ad_request_status(ad_request_id: int, status: str):
    try:
        user = get_user(request)
        user_name = user.get("name")

        if not status or status not in ALLOWED_AD_REQUEST_STATUS:
            return (
                jsonify(
                    {"msg": "status must be in " + ", ".join(ALLOWED_AD_REQUEST_STATUS)}
                ),
                400,
            )

        con, cur = connect_db()

        cur.execute("SELECT * FROM ad_requests WHERE ID = ?", (ad_request_id,))
        ad_request = cur.fetchone()

        if not ad_request:
            con.close()
            return jsonify({"msg": f"The Ad Request With Id {ad_request_id} not found"})

        cur.execute(
            f"UPDATE ad_requests SET status = ? WHERE id = ?", (status, ad_request_id)
        )

        cur.execute(
            "INSERT INTO ad_request_activities (message , ad_request_id) VALUES (?,?)",
            (f"Influencer {user_name} {status} ad request", ad_request_id),
        )

        con.commit()
        con.close()

        return jsonify({"msg": f"Ad Request Status Updated To {status} successfully"})
    except Exception as e:
        return jsonify({"msg": str(e)}), 500


@app.delete("/ad-requests/<int:ad_request_id>")
@check_roles([ROLE_SPONSOR])
@check_token
def delete_ad_request(ad_request_id: int):
    try:
        user = get_user(request)
        user_id = user.get("id")

        con, cur = connect_db()

        cur.execute("SELECT * FROM ad_requests WHERE id = ?", (ad_request_id,))
        ad_request = cur.fetchone()
        if not ad_request:
            con.close()
            return (
                jsonify({"msg": f"Ad Request with id {ad_request_id} not found"}),
                404,
            )

        cur.execute("SELECT * FROM campaigns WHERE id = ?", (ad_request[4],))
        campaign = cur.fetchone()

        if not campaign:
            con.close()
            return jsonify({"msg": f"Campaign with id {ad_request[4]} not found"}), 404

        if campaign[9] != user_id:
            con.close()
            return (
                jsonify(
                    {
                        "msg": f"Unauthorized , you don't have permission to delete this ad request"
                    }
                ),
                403,
            )

        cur.execute(f"DELETE FROM ad_requests WHERE id = {ad_request_id}")

        con.commit()
        con.close()

        return jsonify({"msg": "Ad Request Deleted successfully"})
    except Exception as e:
        return jsonify({"msg": str(e)}), 500


@app.get("/ad-requests/me")
@check_roles([ROLE_INFLUENCER])
@check_token
def get_my_invites():
    try:
        user = get_user(request)
        user_id = user.get("id")
        date_format = "%d-%m-%Y %H:%M:%S"
        con, _ = connect_db()
        ad_requests = pd.read_sql_query(
            f"""SELECT c.name campaign_name,c.budget campaign_budget,
                                        c.goals campaign_goals,
                                        ar.requirements ad_requirements,
                                        ar.payment_amount ad_budget,
                                        s.name sponsor_name,
                                        ar.status,
                                        strftime('{date_format}',c.start_date) campaign_start_date,
                                        strftime('{date_format}',c.end_date) campaign_end_date
                                        FROM ad_requests ar
                                        JOIN campaigns c ON ar.campaign_id = c.id
                                        JOIN sponsors s ON c.sponsor_id = s.id
                                        WHERE ar.influencer_id = ?""",
            con,
            params=(user_id,),
        )
        ad_requests = ad_requests.to_dict(orient="records")

        return jsonify(ad_requests)
    except Exception as e:
        return jsonify({"msg": str(e)}), 500


@app.get("/activity/<int:ad_request_id>")
@check_roles([ROLE_SPONSOR, ROLE_INFLUENCER])
@check_token
def get_ad_activity(ad_request_id: int):
    try:
        con, _ = connect_db()
        ad_activities = pd.read_sql_query(
            "SELECT message FROM ad_request_activities WHERE ad_request_id = ? ORDER BY ID DESC",
            con,
            params=(ad_request_id,),
        )
        ad_activities = ad_activities.to_dict(orient="records")
        return jsonify(ad_activities)
    except Exception as e:
        return jsonify({"msg": str(e)}), 500


@app.get("/dashboard")
@check_roles([ROLE_ADMIN])
@check_token
def get_dashboard():
    try:
        if cache_exists("dashboard"):
            return jsonify(cache_get("dashboard"))
        con, _ = connect_db()
        # need count of campaigns (public/private), ad requests and their status, flagged sponsors/influencers etc in a single query
        data = pd.read_sql_query(
            """SELECT 
            (SELECT COUNT(1) FROM campaigns WHERE is_private = 0) as public_campaigns,
            (SELECT COUNT(1) FROM campaigns WHERE is_private = 1) as private_campaigns,
            (SELECT COUNT(1) FROM ad_requests WHERE status = 'Pending') as pending_ad_requests,
            (SELECT COUNT(1) FROM ad_requests WHERE status = 'accepted') as accepted_ad_requests,
            (SELECT COUNT(1) FROM ad_requests WHERE status = 'rejected') as rejected_ad_requests,
            (SELECT COUNT(1) FROM sponsors WHERE is_flagged = 1) as flagged_sponsors,
            (SELECT COUNT(1) FROM influencers WHERE is_flagged = 1) as flagged_influencers,
            (SELECT COUNT(1) FROM campaigns WHERE is_flagged = 1) as flagged_campaigns,
            (SELECT COUNT(1) FROM influencers) as total_influencers,
            (SELECT COUNT(1) FROM sponsors) as total_sponsors
            """,
            con,
        )

        to_approve_sponsers = pd.read_sql_query(
            "SELECT id,name,email FROM sponsors WHERE is_approved = 0", con
        )
        rencent_ad_requests = pd.read_sql_query(
            """SELECT ar.id,c.name campaign_name,ar.requirements,s.name sponsor_name,ar.status,i.name influencer_name
            FROM ad_requests ar
            JOIN campaigns c ON ar.campaign_id = c.id
            JOIN sponsors s ON c.sponsor_id = s.id
            JOIN influencers i ON ar.influencer_id = i.id
            ORDER BY ar.id DESC LIMIT 5""",
            con,
        )

        rencent_ad_requests = rencent_ad_requests.to_dict(orient="records")
        to_approve_sponsers = to_approve_sponsers.to_dict(orient="records")
        data = data.to_dict(orient="records")

        con.close()
        response = {
            "data": [
                {"title": "Total Sponsors", "count": data[0]["total_sponsors"]},
                {"title": "Flagged Sponsors", "count": data[0]["flagged_sponsors"]},
                {"title": "Total Influencers", "count": data[0]["total_influencers"]},
                {
                    "title": "Flagged Influencers",
                    "count": data[0]["flagged_influencers"],
                },
                {
                    "title": "Total Campaigns",
                    "count": data[0]["public_campaigns"] + data[0]["private_campaigns"],
                },
                {"title": "Public Campaigns", "count": data[0]["public_campaigns"]},
                {"title": "Private Campaigns", "count": data[0]["private_campaigns"]},
                {"title": "Flagged Campaigns", "count": data[0]["flagged_campaigns"]},
                {
                    "title": "Total Ad Requests",
                    "count": data[0]["pending_ad_requests"]
                    + data[0]["accepted_ad_requests"]
                    + data[0]["rejected_ad_requests"],
                },
                {
                    "title": "Pending Ad Requests",
                    "count": data[0]["pending_ad_requests"],
                },
                {
                    "title": "Accepted Ad Requests",
                    "count": data[0]["accepted_ad_requests"],
                },
                {
                    "title": "Rejected Ad Requests",
                    "count": data[0]["rejected_ad_requests"],
                },
            ],
            "to_approve_sponsors": to_approve_sponsers,
            "recent_ad_requests": rencent_ad_requests,
        }
        cache_set("dashboard", response)
        return jsonify(response)
    except Exception as e:
        return jsonify({"msg": str(e)}), 500


@app.post("/reports/campaigns")
@check_roles([ROLE_SPONSOR])
@check_token
def export_campaigns():
    try:
        new_celery_task = send_campaigns_report.delay(get_user(request).get("id"))
        return jsonify(
            {
                "msg": "Export is in progress , you will be notified when it is done",
                "task_id": new_celery_task.id,
            }
        )
    except Exception as e:
        return jsonify({"msg": str(e)}), 500


@app.get("/export-task/<string:task_id>")
@check_roles([ROLE_SPONSOR])
@check_token
def get_export_task(task_id: str):
    try:
        # check for the celery task status
        celery_task = celery.AsyncResult(task_id)
        if celery_task.state == "SUCCESS":
            return send_file(
                celery_task.result, as_attachment=True, download_name="campaigns.csv"
            )
        return (
            jsonify(
                {"msg": "Task is in progress , you will be notified when it is done"}
            ),
            400,
        )
    except Exception as e:
        print(str(e))
        return jsonify({"msg": str(e)}), 500


@app.get("/logout")
@check_roles(AVAILABLE_ROLES)
@check_token
def logout():
    response = jsonify({"msg": "Logged out successfully"})
    response.delete_cookie("token", path="/")
    return response


# @app.get('/test-mails')
# def test_mail():
    try:
        con, _ = connect_db()
        ad_requests = pd.read_sql_query(
            """SELECT ar.id ad_request_id, 
                i.name influencer_name, i.email influencer_email
                FROM ad_requests ar
                JOIN influencers i ON ar.influencer_id = i.id
                WHERE ar.status = 'Pending'""",
            con,
        )
        ad_requests = ad_requests.to_dict(orient="records")
        print(ad_requests)
        con.close()
        with open(
            os.path.join(MAIL_TEMPLATES_PATH, "pending-ad-requests.html")
        ) as html_template_file:
            html = html_template_file.read()
            
        for single_ad_request in ad_requests:
            influencer = (
                single_ad_request.get("influencer_name"),
                single_ad_request.get("influencer_email"),
            )
            subject = "Ad Request Pending"
            html = html.replace(
                "{{invite_link}}",
                f"http://localhost:3000/influencer/ad-requests/{single_ad_request.get('ad_request_id')}",
            )
            html = html.replace("{{current_year}}", str(pd.Timestamp.now().year))
            html = html.replace("{{influencer_name}}", influencer[0])
            send_mail(influencer[1], subject, html)
        return jsonify({'msg' : 'completred'})
    except Exception as e:
        raise e
        print(str(e))
        return jsonify({'msg' : str(e)})

@celery.task(name="send_alert_for_pending_ad_requests")
def send_mails_for_pending_ad_requests():
    try:
        con, _ = connect_db()
        ad_requests = pd.read_sql_query(
            """SELECT ar.id ad_request_id, 
                i.name influencer_name, i.email influencer_email
                FROM ad_requests ar
                JOIN influencers i ON ar.influencer_id = i.id
                WHERE ar.status = 'Pending'""",
            con,
        )
        ad_requests = ad_requests.to_dict(orient="records")
        con.close()
        html_template_file = open(
            os.path.join(MAIL_TEMPLATES_PATH, "pending-ad-requests.html")
        )
        html = html_template_file.read()
        html_template_file.close()
        for single_ad_request in ad_requests:
            influencer = (
                single_ad_request.get("influencer_name"),
                single_ad_request.get("influencer_email"),
            )
            subject = "Ad Request Pending"
            html = html.replace(
                "{{invite_link}}",
                f"http://localhost:8000/influencer/ad-requests/{single_ad_request.get('ad_request_id')}",
            )
            html = html.replace("{{current_year}}", str(pd.Timestamp.now().year))
            html = html.replace("{{influencer_name}}", influencer[0])
            send_mail(influencer[1], subject, html)
    except Exception as e:
        print(str(e))


@celery.task(name="send_campaigns_report")
def send_campaigns_report(sponsor_id: int):
    try:
        con, _ = connect_db()
        campaigns = pd.read_sql_query(
            "SELECT c.*, (SELECT COUNT(1) FROM ad_requests WHERE campaign_id = c.id) total_ad_count FROM campaigns c WHERE c.sponsor_id = ?",
            con,
            params=(sponsor_id,),
        )
        con.close()
        file_name = f"campaigns_{str(date.today())}_{sponsor_id}.csv"
        csv_path = os.path.join(STATIC_FOLDER_PATH, file_name)
        campaigns.to_csv(csv_path, index=False)
        return csv_path
    except Exception as e:
        print(str(e))


@celery.task(name="send-activity-report")
def send_activity_report():
    """The activity report can consist of campaign details, how many
    advertisements done, growth in sales of products due to
    campaigns, budget used/remaining etc."""
    try:
        html_template_file = open(
            os.path.join(MAIL_TEMPLATES_PATH, "activity-report.html"), "rb"
        )
        html = html_template_file.read()
        html_template_file.close()

        con, _ = connect_db()
        sponsors = pd.read_sql_query("SELECT id,email,max_budget FROM sponsors", con)
        sponsors = sponsors.to_dict(orient="records")

        for sponsor in sponsors:
            sponsor_id = sponsor.get("id")
            max_budget = sponsor.get("max_budget")
            sponsor_email = sponsor.get("email")
            campaigns = pd.read_sql_query(
                "SELECT * FROM campaigns WHERE sponsor_id = ?",
                con,
                params=(sponsor_id,),
            )
            ad_requests = pd.read_sql_query(
                "SELECT * FROM ad_requests WHERE sponsor_id = ?",
                con,
                params=(sponsor_id,),
            )
            total_budget_used = ad_requests["payment_amount"].sum()
            remaining_budget = float(max_budget) - float(total_budget_used)

            # send mail to sponsor
            html = html.replace("{{current_year}}", str(pd.Timestamp.now().year))
            html = html.replace("{{sponsor_name}}", sponsor.get("name").encode())
            html = html.replace("{{total_budget_used}}", str(total_budget_used))
            html = html.replace("{{remaining_budget}}", str(remaining_budget))
            html = html.replace("{{campaigns}}", campaigns.to_html())
            html = html.replace("{{ad_requests}}", ad_requests.to_html())
            send_mail(sponsor_email, "Activity Report", html)

        con.close()
    except Exception as e:
        print(str(e))


if __name__ == "__main__":
    app.run(debug=True, port=PORT, host="0.0.0.0")
