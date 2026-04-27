import pika
import time
import sys

def main():
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()

    # Fila durável, com 3 cadeiras e rejeição de excedentes
    args = {"x-max-length": 3, "x-overflow": "reject-publish"}
    channel.queue_declare(queue='sala_espera', durable=True, arguments=args)

    # Variável de estado (usamos um dicionário para poder alterá-la dentro da função)
    estado = {"dormindo": True}

    def cortar_cabelo(ch, method, properties, body):
        cliente = body.decode()
        
        # --- 1. VALIDAÇÃO DO ESTADO INICIAL ---
        if estado["dormindo"]:
            print(f"🥱 [Barbeiro] Acordou no susto e está cortando o cabelo de: {cliente}")
            estado["dormindo"] = False # Agora ele está acordado
        else:
            print(f"🗣️ [Barbeiro] Chamou o próximo da fila e está cortando o cabelo de: {cliente}")
        
        # --- LÓGICA DA BARRA DE PROGRESSO ---
        tempo_total_corte = 15.0
        tamanho_da_barra = 30
        tempo_por_passo = tempo_total_corte / tamanho_da_barra
        
        for i in range(tamanho_da_barra + 1):
            porcentagem = (i / tamanho_da_barra) * 100
            barra_preenchida = '█' * i
            barra_vazia = '-' * (tamanho_da_barra - i)
            sys.stdout.write(f"\r⏳ Progresso do corte: |{barra_preenchida}{barra_vazia}| {porcentagem:.0f}%")
            sys.stdout.flush()
            if i < tamanho_da_barra:
                time.sleep(tempo_por_passo)
        # ------------------------------------
        
        print(f"\n✅ [Barbeiro] Finalizou o corte de {cliente}.")
        
        # Avisa a fila que o cliente foi atendido (libera a cadeira)
        ch.basic_ack(delivery_tag=method.delivery_tag)

        # --- 2. VERIFICAÇÃO SE A FILA ESVAZIOU ---
        # passive=True apenas lê o status da fila no RabbitMQ sem modificá-la
        status_fila = ch.queue_declare(queue='sala_espera', durable=True, passive=True)
        clientes_esperando = status_fila.method.message_count
        
        if clientes_esperando == 0:
            print("💤 A fila ficou vazia. O barbeiro voltou a dormir...\n")
            estado["dormindo"] = True # Atualiza o estado para dormir
        else:
            print(f"👀 [Barbeiro] Olhou para as cadeiras e puxou o próximo. Restam {clientes_esperando} cliente(s) esperando.\n")

    # Garante que o barbeiro pegue apenas 1 cliente por vez
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue='sala_espera', on_message_callback=cortar_cabelo)

    print('💤  Barbearia abriu agora. Barbeiro dormindo, aguardando clientes...\n')
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        print("\n🛑 Fechando a barbearia e encerrando o expediente...")
        channel.stop_consuming()
    connection.close()

if __name__ == '__main__':
    main()