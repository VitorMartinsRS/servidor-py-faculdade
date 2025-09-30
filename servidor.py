import psycopg2
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse


# --- Configuração do Banco (use variáveis de ambiente se quiser mais segurança) ---
DB_CONFIG = {
    "dbname": os.getenv("DB_NAME", "postgres"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASS", "V!9p/TmUwMwDUCd"),
    "host": os.getenv("DB_HOST", "db.wveigyviaktmdrdczjyn.supabase.co"),
    "port": int(os.getenv("DB_PORT", 5432)),
}


def get_db_connection():
    """Tenta estabelecer e retornar uma nova conexão com o DB."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"Erro ao conectar ao banco de dados: {e}")
        return None


def create_tasks_table():
    """Cria a tabela 'tarefas' se ela não existir."""
    conn = get_db_connection()
    if not conn:
        return
    try:
        cur = conn.cursor()
        sql = """
        CREATE TABLE IF NOT EXISTS tarefas (
            id SERIAL PRIMARY KEY,
            titulo VARCHAR(100) NOT NULL,
            descricao TEXT,
            status VARCHAR(20) DEFAULT 'pendente',
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        cur.execute(sql)
        conn.commit()
        print("Tabela 'tarefas' verificada/criada com sucesso.")
        cur.close()
    except Exception as e:
        print(f"Erro ao criar tabela: {e}")
        conn.rollback()
    finally:
        conn.close()


def db_create_task(titulo, descricao):
    """Insere uma nova tarefa no DB."""
    conn = get_db_connection()
    if not conn:
        return None
    task_id = None
    try:
        cur = conn.cursor()
        sql = """
        INSERT INTO tarefas (titulo, descricao) VALUES (%s, %s) 
        RETURNING id;
        """
        cur.execute(sql, (titulo, descricao))
        task_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
    except Exception as e:
        print(f"Erro ao criar tarefa: {e}")
        conn.rollback()
    finally:
        conn.close()
    return task_id


def db_get_all_tasks():
    """Retorna todas as tarefas."""
    conn = get_db_connection()
    if not conn:
        return []
    tasks = []
    try:
        cur = conn.cursor()
        sql = "SELECT id, titulo, descricao, status, criado_em FROM tarefas ORDER BY id;"
        cur.execute(sql)
        columns = [desc[0] for desc in cur.description]
        for row in cur.fetchall():
            task = dict(zip(columns, row))
            task['criado_em'] = task['criado_em'].isoformat()
            tasks.append(task)
        cur.close()
    except Exception as e:
        print(f"Erro ao buscar todas as tarefas: {e}")
    finally:
        conn.close()
    return tasks


def db_get_task_by_id(task_id):
    """Retorna uma tarefa específica pelo ID."""
    conn = get_db_connection()
    if not conn:
        return None
    task = None
    try:
        cur = conn.cursor()
        sql = "SELECT id, titulo, descricao, status, criado_em FROM tarefas WHERE id = %s;"
        cur.execute(sql, (task_id,))
        row = cur.fetchone()
        if row:
            columns = [desc[0] for desc in cur.description]
            task = dict(zip(columns, row))
            task['criado_em'] = task['criado_em'].isoformat()
        cur.close()
    except Exception as e:
        print(f"Erro ao buscar tarefa {task_id}: {e}")
    finally:
        conn.close()
    return task


def db_update_task(task_id, titulo=None, descricao=None, status=None):
    """Atualiza título, descrição e/ou status de uma tarefa."""
    conn = get_db_connection()
    if not conn:
        return False
    updates = []
    params = []
    if titulo is not None:
        updates.append("titulo = %s")
        params.append(titulo)
    if descricao is not None:
        updates.append("descricao = %s")
        params.append(descricao)
    if status is not None:
        updates.append("status = %s")
        params.append(status)
    if not updates:
        return False
    params.append(task_id)
    try:
        cur = conn.cursor()
        sql = f"UPDATE tarefas SET {', '.join(updates)} WHERE id = %s;"
        cur.execute(sql, tuple(params))
        updated = cur.rowcount > 0
        conn.commit()
        cur.close()
        return updated
    except Exception as e:
        print(f"Erro ao atualizar tarefa {task_id}: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def db_delete_task(task_id):
    """Deleta uma tarefa pelo ID."""
    conn = get_db_connection()
    if not conn:
        return False
    try:
        cur = conn.cursor()
        sql = "DELETE FROM tarefas WHERE id = %s;"
        cur.execute(sql, (task_id,))
        deleted = cur.rowcount > 0
        conn.commit()
        cur.close()
        return deleted
    except Exception as e:
        print(f"Erro ao deletar tarefa {task_id}: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


# --- Classe do Servidor HTTP Personalizado ---
class TaskServer(BaseHTTPRequestHandler):

    def _set_headers(self, status_code=200, content_type='application/json'):
        """Define os cabeçalhos de resposta."""
        self.send_response(status_code)
        self.send_header('Content-type', content_type)
        self.end_headers()

    def do_GET(self):
        parsed_url = urlparse(self.path)
        path_parts = [p for p in parsed_url.path.split('/') if p]

        if path_parts == ['tasks']:
            tasks = db_get_all_tasks()
            self._set_headers(200)
            self.wfile.write(json.dumps(tasks).encode('utf-8'))
            return

        if len(path_parts) == 2 and path_parts[0] == 'tasks':
            try:
                task_id = int(path_parts[1])
            except ValueError:
                self._set_headers(400)
                self.wfile.write(json.dumps({"error": "ID inválido"}).encode('utf-8'))
                return
            task = db_get_task_by_id(task_id)
            if task:
                self._set_headers(200)
                self.wfile.write(json.dumps(task).encode('utf-8'))
            else:
                self._set_headers(404)
                self.wfile.write(json.dumps({"error": "Tarefa não encontrada"}).encode('utf-8'))
            return

        self._set_headers(404)
        self.wfile.write(json.dumps({"error": "Rota não encontrada"}).encode('utf-8'))

    def do_POST(self):
        parsed_url = urlparse(self.path)
        path_parts = [p for p in parsed_url.path.split('/') if p]

        if path_parts == ['tasks']:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode('utf-8'))
                titulo = data.get('titulo')
                descricao = data.get('descricao', None)
            except (json.JSONDecodeError, AttributeError):
                self._set_headers(400)
                self.wfile.write(json.dumps({"error": "JSON inválido"}).encode('utf-8'))
                return
            if not titulo:
                self._set_headers(400)
                self.wfile.write(json.dumps({"error": "O campo 'titulo' é obrigatório"}).encode('utf-8'))
                return
            task_id = db_create_task(titulo, descricao)
            if task_id:
                task = db_get_task_by_id(task_id)
                self._set_headers(201)
                self.wfile.write(json.dumps(task).encode('utf-8'))
            else:
                self._set_headers(500)
                self.wfile.write(json.dumps({"error": "Erro ao salvar a tarefa"}).encode('utf-8'))
            return

        self._set_headers(404)
        self.wfile.write(json.dumps({"error": "Rota não encontrada"}).encode('utf-8'))

    def do_PUT(self):
        parsed_url = urlparse(self.path)
        path_parts = [p for p in parsed_url.path.split('/') if p]

        if len(path_parts) == 2 and path_parts[0] == 'tasks':
            try:
                task_id = int(path_parts[1])
            except ValueError:
                self._set_headers(400)
                self.wfile.write(json.dumps({"error": "ID inválido"}).encode('utf-8'))
                return
            content_length = int(self.headers['Content-Length'])
            put_data = self.rfile.read(content_length)
            try:
                data = json.loads(put_data.decode('utf-8'))
            except json.JSONDecodeError:
                self._set_headers(400)
                self.wfile.write(json.dumps({"error": "JSON inválido"}).encode('utf-8'))
                return
            if not db_get_task_by_id(task_id):
                self._set_headers(404)
                self.wfile.write(json.dumps({"error": "Tarefa não encontrada"}).encode('utf-8'))
                return
            updated = db_update_task(
                task_id,
                titulo=data.get('titulo'),
                descricao=data.get('descricao'),
                status=data.get('status')
            )
            if updated:
                task = db_get_task_by_id(task_id)
                self._set_headers(200)
                self.wfile.write(json.dumps(task).encode('utf-8'))
            else:
                self._set_headers(400)
                self.wfile.write(json.dumps({"error": "Nenhum dado válido para atualizar"}).encode('utf-8'))
            return

        self._set_headers(404)
        self.wfile.write(json.dumps({"error": "Rota não encontrada"}).encode('utf-8'))

    def do_DELETE(self):
        parsed_url = urlparse(self.path)
        path_parts = [p for p in parsed_url.path.split('/') if p]

        if len(path_parts) == 2 and path_parts[0] == 'tasks':
            try:
                task_id = int(path_parts[1])
            except ValueError:
                self._set_headers(400)
                self.wfile.write(json.dumps({"error": "ID inválido"}).encode('utf-8'))
                return
            deleted = db_delete_task(task_id)
            if deleted:
                self.send_response(204)
                self.end_headers()
            else:
                self._set_headers(404)
                self.wfile.write(json.dumps({"error": "Tarefa não encontrada"}).encode('utf-8'))
            return

        self._set_headers(404)
        self.wfile.write(json.dumps({"error": "Rota não encontrada"}).encode('utf-8'))


# --- Função Principal ---
def run_server():
    HOST_NAME = 'localhost'
    SERVER_PORT = 8000
    create_tasks_table()
    webServer = ThreadingHTTPServer((HOST_NAME, SERVER_PORT), TaskServer)
    print("-" * 50)
    print(f"Servidor Backend iniciado em http://{HOST_NAME}:{SERVER_PORT}")
    print("Pressione Ctrl+C para encerrar.")
    print("-" * 50)
    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass
    webServer.server_close()
    print("Servidor encerrado.")


if __name__ == "__main__":
    run_server()
