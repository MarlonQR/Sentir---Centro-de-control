import os
import psycopg2

def obtener_conexion():
    default_db_url = "postgresql://postgres.eqwbqrnocrixypzbzrli:cgY2CXj5rYUHzCJp@aws-0-us-east-1.pooler.supabase.com:6543/postgres"
    
    db_url = os.getenv("DATABASE_URL", default_db_url)
    return psycopg2.connect(db_url)