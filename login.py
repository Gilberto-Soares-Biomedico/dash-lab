import bcrypt

# O dicionário agora guarda os HASHES das senhas (gerados pelo bcrypt)
# Nota: Os hashes reais sempre começam com algo como $2b$12$...
USERS = {
    "admin": "$2b$12$VAuYa/ivzcMqjLU/2Ub4M.6HVCt/b8sU46afHt57BYTy1BDbi5RIq", 
    "gilberto": "$2b$12$pbFcgkZA3vVo1vLWj9Ptgu/wF21/7WwmNSjDFCkagWvs9VBJEArF6",
    "secretaria": "$2b$12$rau5BoJkBlIWygCH87dAx.ShHurPamoW7S59zlwMqHxuCHbmSMIwK"
}

def valida_senha(username, password):
    # 1. Verifica se o usuário existe no dicionário
    if username in USERS:
        hash_salvo = USERS[username].encode('utf-8') # Converte o hash salvo para bytes
        senha_digitada = password.encode('utf-8')    # Converte a senha digitada para bytes
        
        # 2. O bcrypt compara a senha digitada diretamente com o hash salvo
        return bcrypt.checkpw(senha_digitada, hash_salvo)
    return False