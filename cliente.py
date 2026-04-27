import pika
import sys

def chegar_na_barbearia(nome_cliente):
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()

    # Habilita a confirmação de publicação para sabermos se foi rejeitado
    channel.confirm_delivery()

    # 1. ESPIANDO A FILA: Declaramos a fila com as MESMAS regras do barbeiro.
    # Se ela já existir, o RabbitMQ apenas devolve o status atual dela.
    args = {"x-max-length": 3, "x-overflow": "reject-publish"}
    status_fila = channel.queue_declare(queue='sala_espera', durable=True, arguments=args)
    
    # Pegamos a quantidade de cadeiras ocupadas ANTES desse cliente tentar sentar
    clientes_na_frente = status_fila.method.message_count

    try:
        # Tenta colocar o cliente na fila
        channel.basic_publish(
            exchange='',
            routing_key='sala_espera',
            body=nome_cliente,
            mandatory=True
        )
        
        # --- 2. MENSAGENS PERSONALIZADAS DE CHEGADA ---
        if clientes_na_frente == 0:
             print(f"🚶‍♂️  {nome_cliente} chegou e sentou. Não há ninguém na espera, ele é o próximo!")
        else:
             print(f"🚶‍♂️  {nome_cliente} chegou e sentou. Tem {clientes_na_frente} cliente(s) na frente dele.")
        # ----------------------------------------------
        
    except pika.exceptions.NackError:
        # O x-overflow: reject-publish envia um NACK se a fila estiver cheia
        print(f"🚪 Fila lotada! {nome_cliente} olhou e foi embora.")
        
    connection.close()

if __name__ == '__main__':
    cliente = sys.argv[1] if len(sys.argv) > 1 else "Cliente Anônimo"
    chegar_na_barbearia(cliente)