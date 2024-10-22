from flask import Flask, request, jsonify
import psycopg2

app = Flask(__name__)

# Função para conectar ao banco de dados
def conectar():
    return psycopg2.connect(
        host="localhost",
        database="postgres",
        user="postgres",
        password="postgre",
      
    )


@app.route('/criar', methods=['POST'])
def criar_registro():
    try:
        dados = request.json
        if not dados:
            return jsonify({"erro": "Corpo da requisição vazio"})
        
        tabela = dados.get('tabela')

        bd = conectar()
        cursor = bd.cursor()

        #Inserir fornecedor
        if tabela == 'fornecedor':
            nome = dados.get('nome')
            telefone = dados.get('telefone')
            email = dados.get('email')
            id_endereco = dados.get('id_endereco')

            cursor.execute(
                """
                INSERT INTO mydb.Fornecedor (nome, telefone, email, id_endereco)
                VALUES (%s, %s, %s, %s)
                """,
                (nome, telefone, email, id_endereco)
            )

        #Inserir equipamento e adicionar à tabela da relação
        elif tabela == 'equipamento':
            #Início da transação
            bd.autocommit = False
            
            id_fornecedor = dados.get('id_fornecedor')
            nome = dados.get('nome')
            preco = dados.get('preco')
            quantidade = dados.get('quantidade')
            
            #Verifica se o fornecedor existe, caso não exista, retorna que não foi encontrado
            cursor.execute("SELECT * FROM mydb.fornecedor WHERE id_fornecedor = %s", (id_fornecedor,))
            fornecedor = cursor.fetchone()
            
            if not fornecedor:
                return jsonify("Fornecedor não encontrado")

            cursor.execute(
                """
                INSERT INTO mydb.Equipamento (nome, preco, quantidade)
                VALUES (%s, %s, %s) RETURNING id_equipamento
                """,
                (nome, preco, quantidade)
            )
        
            
            id_equipamento = cursor.fetchone()[0]
            data_fornecimento = dados.get('data_fornecimento')

            cursor.execute(
                """
                INSERT INTO mydb.fornece_Equipamento (id_equipamento, id_fornecedor, data_fornecimento)
                VALUES (%s, %s, %s)
                """,
                (id_equipamento, id_fornecedor, data_fornecimento)
            )

        else:
            return jsonify({"erro": "Tabela inválida"})
        #Confirma a transação
        bd.commit()
        
        return jsonify(f"Registro criado na tabela {tabela} com sucesso!")
    except (psycopg2.Error, ConnectionError) as e:
        #Dá rollback no sistema caso haja erro na transação
        bd.rollback()
        return jsonify({"erro": str(e)})
    
    finally:
        cursor.close()
        bd.close()

@app.route('/obter', methods=['GET'])
def obter_registro():
    try:
        dados = request.json
        tabela = dados.get('tabela')
        
        bd = conectar()
        cursor = bd.cursor()

        #Estruturas para consulta dinâmica
        campos = []
        valores = []
        
        #Consulta de fornecedor por nome ou id
        if tabela == 'fornecedor':
            if 'nome' in dados:
                campos.append('nome')
                valores.append(dados.get('nome'))
                
            elif 'id_fornecedor' in dados:
                campos.append('id_fornecedor')
                valores.append(dados.get('id_fornecedor'))
                
            if campos:
                coluna = campos[0]
                query = f"SELECT * FROM mydb.Fornecedor WHERE {coluna} = %s"
                cursor.execute(query, (tuple(valores)))
                resultado = cursor.fetchall()
            else:
                return jsonify("Nenhum campo de busca fornecido")

        #Consulta de equipamento por nome ou id
        elif tabela == 'equipamento':   
            if 'nome' in dados:
                campos.append('nome')
                valores.append(dados.get('nome'))
                
            elif 'id_equipamento' in dados:
                campos.append('id_equipamento')
                valores.append(dados.get('id_equipamento'))
                
            if campos:
                coluna = campos[0]
                query = f"SELECT * FROM mydb.equipamento WHERE {coluna} = %s"
                cursor.execute(query, tuple(valores))
                resultado = cursor.fetchall()
            else:
                return jsonify("Nenhum campo de busca fornecido")

        #Consulta à tabela da relação por id do equipamento e fornecedor ou data de fornecimeto
        elif tabela == 'fornece_equipamento':
            if 'id_equipamento' and 'id_fornecedor' in dados:
                campos.append(f'id_equipamento = %s AND id_fornecedor')
               
                valores.append(dados.get('id_equipamento'))
                valores.append(dados.get('id_fornecedor'))
                
            elif 'data_fornecimento' in dados:
                campos.append('data_fornecimento')
                valores.append(dados.get('data_fornecimento'))
            
            if campos:
                colunas = campos[0]
                query = f"SELECT * FROM mydb.fornece_Equipamento WHERE {colunas} = %s"
                cursor.execute(query, tuple(valores))
                resultado = cursor.fetchall()
            else:
                return jsonify("Nenhum campo de busca fornecido")
            
            
        else:
            return jsonify({"erro": "Tabela inválida especificada"})

        #Tratamento de resposta à consulta (Deixar mais entendível)
        ra = []
        if resultado:
            for result in resultado:
                if tabela == 'fornecedor':
                    
                    ra.append({
                        "id_fornecedor": result[0],
                        "nome": result[1],
                        "telefone": result[2],
                        "email": result[3],
                        "id_endereco": result[4]
                    })
                elif tabela == 'equipamento':
                    
                    ra.append({
                        "id_equipamento": result[0],
                        "nome": result[1],
                        "preco": result[2],
                        "quantidade": result[3]
                    })
                elif tabela == 'fornece_equipamento':
                    
                    ra.append({
                        "id_equipamento": result[0],
                        "id_fornecedor": result[1],
                        "data_fornecimento": result[2]
                    })

            return jsonify({"dados": ra})
                
            
        else:
            return jsonify({"erro": "Registro não encontrado"})
    
    except (psycopg2.Error, ConnectionError) as e:
        return jsonify({"erro": str(e)})
    
    finally:
        cursor.close()
        bd.close()


@app.route('/atualizar', methods=['PUT'])
def atualizar_registro():
    try:
        dados = request.json
        tabela = dados.get('tabela')

        
        bd = conectar()
        cursor = bd.cursor()

        
        campos = []
        valores = []

        # Atualizar Fornecedor
        if tabela == 'fornecedor':
            id_fornecedor = dados.get('id_fornecedor')

            if 'nome' in dados:
                campos.append('nome = %s')
                valores.append(dados.get('nome'))

            if 'telefone' in dados:
                campos.append('telefone = %s')
                valores.append(dados.get('telefone'))

            if 'email' in dados:
                campos.append('email = %s')
                valores.append(dados.get('email'))
                

            if 'id_endereco' in dados:
                campos.append('id_endereco = %s')
                valores.append(dados.get('id_endereco'))

            
            if campos:
                valores.append(id_fornecedor)  
                query = f"UPDATE mydb.Fornecedor SET {', '.join(campos)} WHERE id_fornecedor = %s"
                cursor.execute(query, tuple(valores))
            else:
                return jsonify("Nenhum campo de busca fornecido")
            

        # Atualizar Equipamento
        elif tabela == 'equipamento':
            id_equipamento = dados.get('id_equipamento')

            if 'nome' in dados:
                campos.append('nome = %s')
                valores.append(dados.get('nome'))

            if 'preco' in dados:
                campos.append('preco = %s')
                valores.append(dados.get('preco'))

            if 'quantidade' in dados:
                campos.append('quantidade = %s')
                valores.append(dados.get('quantidade'))

            
            if campos:
                valores.append(id_equipamento)  
                query = f"UPDATE mydb.Equipamento SET {', '.join(campos)} WHERE id_equipamento = %s"
                cursor.execute(query, tuple(valores))
            else:
                return jsonify("Nenhum campo de busca fornecido")

        
        elif tabela == 'fornece_equipamento':
            id_equipamento = dados.get('id_equipamento')
            
            id_fornecedor = dados.get('id_fornecedor')
            

            if 'data_fornecimento' in dados:
                campos.append('data_fornecimento = %s')
                valores.append(dados.get('data_fornecimento'))
            
            
              
                      
            if campos:
                valores.extend([id_equipamento, id_fornecedor]) 
                query = f"UPDATE mydb.fornece_Equipamento SET {', '.join(campos)} WHERE id_equipamento = %s AND id_fornecedor = %s"
                cursor.execute(query, tuple(valores))
            else:
                return jsonify("Nenhum campo de busca fornecido")

        else:
            return jsonify({"erro": "Tabela inválida especificada"})

        bd.commit()
        return jsonify(f"Registro da tabela {tabela} atualizado com sucesso!")
    
    except (psycopg2.Error, ConnectionError) as e:
        bd.rollback()
        return jsonify({"erro": str(e)})
    
    finally:
        cursor.close()
        bd.close()

@app.route('/deletar', methods=['DELETE'])
def deletar_registro():
    try:
        dados = request.json
        tabela = dados.get('tabela')

        bd = conectar()
        cursor = bd.cursor()

        if tabela == 'fornecedor':
            id_fornecedor = dados.get('id_fornecedor')
            cursor.execute("DELETE FROM mydb.Fornecedor WHERE id_fornecedor = %s", (id_fornecedor,))

        elif tabela == 'equipamento':
            id_equipamento = dados.get('id_equipamento')
            cursor.execute("DELETE FROM mydb.Equipamento WHERE id_equipamento = %s", (id_equipamento,))

        elif tabela == 'fornece_equipamento':
            id_equipamento = dados.get('id_equipamento')
            id_fornecedor = dados.get('id_fornecedor')
            cursor.execute(
                """
                DELETE FROM mydb.fornece_Equipamento
                WHERE id_equipamento = %s AND id_fornecedor = %s
                """, 
                (id_equipamento, id_fornecedor)
            )

        else:
            return jsonify({"erro": "Tabela inválida especificada"})

        bd.commit()
        
        return jsonify(f"Registro da tabela {tabela} deletado com sucesso!")
    
    except (psycopg2.Error, ConnectionError) as e:
        bd.rollback()
        return jsonify({"erro": str(e)})
    
    
    finally:
        cursor.close()
        bd.close()
        
if __name__ == '__main__':
    app.run(debug=True)
