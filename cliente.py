import requests
import requests

BASE_URL = "http://localhost:8000/tasks"

def listar_tarefas():
    try:
        resposta = requests.get(BASE_URL)
        if resposta.status_code == 200:
            tarefas = resposta.json()
            if not tarefas:
                print("Nenhuma tarefa encontrada.")
            else:
                for tarefa in tarefas:
                    done = "✅ Concluída" if tarefa['done'] else "❌ Pendente"
                    print(f"ID: {tarefa['id']} | {tarefa['title']} | {done}")
                    print(f"Descrição: {tarefa.get('description', 'Sem descrição')}")
                    print("-" * 50)
        else:
            print("Erro ao buscar tarefas.")
    except requests.exceptions.ConnectionError:
        print("⚠️ Servidor está desligado ou inacessível. Tente novamente mais tarde")
    except requests.exceptions.RequestException as e:
        print(f"⚠️ Erro de requisição: {e}")

def criar_tarefa(title):
    description = input("Digite a descrição da tarefa (opcional): ")
    nova_tarefa = {"title": title}
    if description.strip():
        nova_tarefa["description"] = description
    try:
        resposta = requests.post(BASE_URL, json=nova_tarefa)
        if resposta.status_code == 201:
            print("Tarefa criada com sucesso!")
        else:
            print("Erro ao criar tarefa.")
    except requests.exceptions.ConnectionError:
        print("⚠️ Servidor está desligado ou inacessível. Tente novamente mais tarde")
    except requests.exceptions.RequestException as e:
        print(f"⚠️ Erro de requisição: {e}")

def atualizar_tarefa(id, title=None, done=None):
    dados = {}
    if title:
        dados["title"] = title
    if done is not None:
        dados["done"] = done
    try:
        resposta = requests.put(f"{BASE_URL}/{id}", json=dados)
        if resposta.status_code == 200:
            print("Tarefa atualizada com sucesso!")
        else:
            print("Erro ao atualizar tarefa.")
    except requests.exceptions.ConnectionError:
        print("⚠️ Servidor está desligado ou inacessível. Tente novamente mais tarde")
    except requests.exceptions.RequestException as e:
        print(f"⚠️ Erro de requisição: {e}")

def deletar_tarefa(id):
    try:
        resposta = requests.delete(f"{BASE_URL}/{id}")
        if resposta.status_code == 200:
            print("Tarefa deletada com sucesso!")
        else:
            print("Erro ao deletar tarefa.")
    except requests.exceptions.ConnectionError:
        print("⚠️ Servidor está desligado ou inacessível. Tente novamente mais tarde")
    except requests.exceptions.RequestException as e:
        print(f"⚠️ Erro de requisição: {e}")

def visualizar_tarefa(id):
    try:
        resposta = requests.get(f"{BASE_URL}/{id}")
        if resposta.status_code == 200:
            tarefa = resposta.json()
            done = "✅ Concluída" if tarefa['done'] else "❌ Pendente"
            print(f"ID: {tarefa['id']} | {tarefa['title']} | {done}")
            print(f"Descrição: {tarefa.get('description', 'Sem descrição')}")
            print("-" * 50)
        else:
            print("Tarefa não encontrada.")
    except requests.exceptions.ConnectionError:
        print("⚠️ Servidor está desligado ou inacessível. Tente novamente mais tarde")
    except requests.exceptions.RequestException as e:
        print(f"⚠️ Erro de requisição: {e}")

def menu():
    while True:
        print("\n=== Menu ===")
        print("1 - Listar tarefas")
        print("2 - Criar tarefa")
        print("3 - Atualizar tarefa")
        print("4 - Deletar tarefa")
        print("5 - Visualizar tarefa")
        print("0 - Sair")

        opcao = input("Escolha uma opção: ")

        if opcao == "1":
            listar_tarefas()
        elif opcao == "2":
            title = input("Digite o título da tarefa: ")
            criar_tarefa(title)
        elif opcao == "3":
            id = input("Digite o ID da tarefa: ")
            novo_title = input("Digite o novo título (ou deixe vazio para não alterar): ")
            done_input = input("Marcar como concluída? (s/n, deixe vazio para não alterar): ")
            done = True if done_input.lower() == "s" else False if done_input.lower() == "n" else None
            atualizar_tarefa(id, novo_title or None, done)
        elif opcao == "4":
            id = input("Digite o ID da tarefa: ")
            deletar_tarefa(id)
        elif opcao == "5":
            id = input("Digite o ID da tarefa: ")
            visualizar_tarefa(id)
        elif opcao == "0":
            print("Saindo...")
            break
        else:
            print("Opção inválida!")

if __name__ == "__main__":
    menu()
