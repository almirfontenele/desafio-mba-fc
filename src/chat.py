import os
import sys
from dotenv import load_dotenv
from search import search_and_answer

# Load environment variables
load_dotenv()

def print_banner():
    """Print welcome banner"""
    print("=" * 60)
    print("🤖 CHAT SEMÂNTICO - LangChain + PostgreSQL + pgVector")
    print("=" * 60)
    print("Digite 'sair' ou 'quit' para encerrar o chat")
    print("Digite 'help' para ver comandos disponíveis")
    print("-" * 60)

def print_help():
    """Print help information"""
    print("\n📋 COMANDOS DISPONÍVEIS:")
    print("• Digite sua pergunta normalmente")
    print("• 'sair' ou 'quit' - Encerrar o chat")
    print("• 'help' - Mostrar esta ajuda")
    print("• 'status' - Verificar status do sistema")
    print("\n💡 DICAS:")
    print("• Faça perguntas específicas sobre o conteúdo do PDF")
    print("• O sistema só responde com base no conteúdo ingerido")
    print("• Se não houver informação no PDF, receberá uma resposta padrão")

def check_system_status():
    """Check system status"""
    try:
        from search import get_vector_store
        get_vector_store()
        print("✅ Sistema funcionando corretamente")
        print("✅ Conexão com banco de dados: OK")
        print("✅ Vector store: OK")
        return True
    except Exception as e:
        print(f"❌ Erro no sistema: {str(e)}")
        print("Verifique se:")
        print("1. O banco de dados está rodando (docker compose up -d)")
        print("2. A ingestão foi executada (python src/ingest.py)")
        print("3. As variáveis de ambiente estão configuradas")
        return False

def main():
    """Main chat function"""
    print_banner()
    
    # Check system status
    if not check_system_status():
        print("\n❌ Sistema não está funcionando. Encerrando...")
        return
    
    print("\n🚀 Chat iniciado! Faça sua primeira pergunta:")
    
    while True:
        try:
            # Get user input
            user_input = input("\n👤 PERGUNTA: ").strip()
            
            # Handle special commands
            if user_input.lower() in ['sair', 'quit', 'exit']:
                print("\n👋 Até logo! Chat encerrado.")
                break
            
            if user_input.lower() == 'help':
                print_help()
                continue
            
            if user_input.lower() == 'status':
                check_system_status()
                continue
            
            if not user_input:
                print("❓ Por favor, digite uma pergunta.")
                continue
            
            # Process question
            print("🔍 Buscando informações...")
            response = search_and_answer(user_input)
            
            # Display response
            print(f"\n🤖 RESPOSTA: {response}")
            
        except KeyboardInterrupt:
            print("\n\n👋 Chat encerrado pelo usuário.")
            break
        except Exception as e:
            print(f"\n❌ Erro inesperado: {str(e)}")
            print("Tente novamente ou digite 'help' para ajuda.")

if __name__ == "__main__":
    main()