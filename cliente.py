import pika
import sys
from rich.console import Console
from rich.panel import Panel

console = Console()

def chegar_na_barbearia(nome_cliente):
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()

    channel.confirm_delivery()

    # Espia a fila
    args = {"x-max-length": 3, "x-overflow": "reject-publish"}
    status_fila = channel.queue_declare(queue='sala_espera', durable=True, arguments=args)
    clientes_na_frente = status_fila.method.message_count

    try:
        channel.basic_publish(
            exchange='',
            routing_key='sala_espera',
            body=nome_cliente,
            mandatory=True
        )
        
        if clientes_na_frente == 0:
            mensagem = f"[bold green]🚶‍♂️ {nome_cliente} chegou e sentou.[/bold green]\nNão há ninguém na espera, ele é o próximo!"
            console.print(Panel(mensagem, title="[Situação 2]", border_style="green"))
        else:
            mensagem = f"[bold yellow]🚶‍♂️ {nome_cliente} chegou e sentou.[/bold yellow]\nTem [bold white]{clientes_na_frente}[/bold white] cliente(s) na frente dele."
            console.print(Panel(mensagem, title="[Situação 2]", border_style="yellow"))
            
    except pika.exceptions.NackError:
        mensagem = f"[bold red]🚪 Fila lotada![/bold red]\n[bold white]{nome_cliente}[/bold white] olhou as 3 cadeiras ocupadas e foi embora."
        console.print(Panel(mensagem, title="[Situação 3]", border_style="red"))
        
    connection.close()

if __name__ == '__main__':
    cliente = sys.argv[1] if len(sys.argv) > 1 else "Cliente Anônimo"
    chegar_na_barbearia(cliente)