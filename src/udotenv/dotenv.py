def load_dotenv(filename=".env"):
    env_vars = {}
    try:
        with open(filename, 'r') as f:
            for line in f:
                line = line.strip()
                # Ignora linhas vazias e comentários
                if not line or line.startswith('#'):
                    continue
                
                # Divide chave e valor
                if '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
    except OSError:
        print(f"Arquivo {filename} não encontrado.")
    
    return env_vars