import psycopg2

try:
    conn = psycopg2.connect(
        "postgresql://postgres.agbgzyebakbsxbziecsj:%40Zadu0204%23%3D@aws-1-sa-east-1.pooler.supabase.com:6543/postgres?sslmode=require"
    )

    cur = conn.cursor()

    # 🔍 listar tabelas
    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema='public';
    """)

    tabelas = cur.fetchall()
    print("📦 Tabelas no banco:")
    print(tabelas)

    cur.close()
    conn.close()

except Exception as e:
    print("❌ Erro:", e)