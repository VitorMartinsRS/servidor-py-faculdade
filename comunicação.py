import psycopg2

conn = psycopg2.connect(
dbname="postgres",
user="postgres",
password="V!9p/TmUwMwDUCd",
host="db.wveigyviaktmdrdczjyn.supabase.co", 
port=5432

)



cur = conn.cursor()

cur.execute("SELECT NOW();")

print(cur.fetchone())

cur.close()

conn.close()