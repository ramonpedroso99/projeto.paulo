import typer
import asyncio
import json
from exportador import exportar_views_para_excel, listar_views

app = typer.Typer()

@app.command()
def exportar(cliente: str):
    """Exporta views específicas de um cliente para arquivos Excel"""
    with open("clientes.json", "r") as f:
        config = json.load(f)

    if cliente not in config:
        typer.echo(f"❌ Cliente '{cliente}' não encontrado.")
        raise typer.Exit()

    dados_conexao = config[cliente]

    views_disponiveis = asyncio.run(listar_views(dados_conexao))

    if not views_disponiveis:
        typer.echo("⚠️ Nenhuma view encontrada.")
        return

    typer.echo("📋 Views disponíveis:")
    for i, view in enumerate(views_disponiveis, 1):
        typer.echo(f"{i}. {view}")

    selecao = typer.prompt("Digite os números das views desejadas separados por vírgula (ex: 1,3,4)")
    try:
        indices = [int(i.strip()) - 1 for i in selecao.split(",")]
        views_escolhidas = [views_disponiveis[i] for i in indices if 0 <= i < len(views_disponiveis)]
    except Exception:
        typer.echo("❌ Entrada inválida.")
        raise typer.Exit()

    if not views_escolhidas:
        typer.echo("❌ Nenhuma view selecionada.")
        return

    asyncio.run(exportar_views_para_excel(dados_conexao, views_escolhidas))
    typer.echo("✅ Exportação concluída.")

if __name__ == "__main__":
    app()
