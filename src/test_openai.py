import os
from openai import OpenAI

def main():
    # Certifique-se de ter exportado sua chave antes:
    # export OPENAI_API_KEY="sua_chave_aqui"
    client = OpenAI()

    try:
        # Faz uma chamada curta para um modelo pequeno
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # modelo leve e rápido
            messages=[
                {"role": "system", "content": "Você é um assistente útil."},
                {"role": "user", "content": "Diga olá em português."}
            ],
            max_tokens=20
        )

        print("✅ Resposta da API:")
        print(response.choices[0].message.content)

    except Exception as e:
        print("❌ Erro ao chamar a API:", e)

if __name__ == "__main__":
    main()
