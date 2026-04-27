import pika
import time
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeRemainingColumn

# Instancia o console da Rich
console = Console()

def main():
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()

    args = {"x-max-length": 3, "x-overflow": "reject-publish"}
    channel.queue_declare(queue='sala_espera', durable=True, arguments=args)

    estado = {"dormindo": True}

    def cortar_cabelo(ch, method, properties, body):
        cliente = body.decode()
        
        # --- ESTADO INICIAL COM PAINÉIS COLORIDOS ---
        if estado["dormindo"]:
            mensagem = f"[bold yellow]🥱 Acordou no susto![/bold yellow]\nO barbeiro começou a cortar o cabelo de: [bold cyan]{cliente}[/bold cyan]"
            console.print(Panel(mensagem, title="[Barbeiro]", border_style="yellow"))
            estado["dormindo"] = False 
        else:
            mensagem = f"[bold green]🗣️ Chamou o próximo da fila![/bold green]\nO barbeiro puxou: [bold cyan]{cliente}[/bold cyan]"
            console.print(Panel(mensagem, title="[Barbeiro]", border_style="green"))
        
        # --- BARRA DE PROGRESSO ANIMADA DA RICH ---
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(), # Calcula o tempo restante automaticamente
            console=console
        ) as progress:
            # Cria a tarefa com meta de 100%
            task = progress.add_task(f"[cyan]Cortando cabelo de {cliente}...", total=100)
            
            # Simulando os 15 segundos que você definiu (100 passos de 0.15 segundos)
            for _ in range(100):
                time.sleep(0.15)
                progress.update(task, advance=1)
        # ------------------------------------------
        
        console.print(f"[bold green]✅ Finalizou o corte de {cliente}.[/bold green]\n")
        
        ch.basic_ack(delivery_tag=method.delivery_tag)

        # --- VERIFICAÇÃO DA FILA ---
        status_fila = ch.queue_declare(queue='sala_espera', durable=True, passive=True)
        clientes_esperando = status_fila.method.message_count
        
        if clientes_esperando == 0:
            console.print(Panel("[bold blue]💤 A fila ficou vazia.[/bold blue]\nO barbeiro voltou a dormir...", title="[Situação 1]", border_style="blue"))
            estado["dormindo"] = True 
        else:
            console.print(f"[bold magenta]👀 Olhou para as cadeiras... Restam {clientes_esperando} cliente(s) esperando.[/bold magenta]\n")

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue='sala_espera', on_message_callback=cortar_cabelo)

    # Mensagem inicial ao ligar o servidor
    console.print(Panel("[bold blue]💤 Barbearia abriu agora.[/bold blue]\nBarbeiro dormindo, aguardando clientes...", title="[Situação 1]", border_style="blue"))
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        console.print("\n[bold red]🛑 Fechando a barbearia e encerrando o expediente...[/bold red]")
        channel.stop_consuming()
    connection.close()

if __name__ == '__main__':
    main()