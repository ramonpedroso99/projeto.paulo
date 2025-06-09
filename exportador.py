import asyncpg
import pandas as pd
import os

async def exportar_views_para_excel(dados_conexao, views, pasta_destino="exports"):
    os.makedirs(pasta_destino, exist_ok=True)

    conn = await asyncpg.connect(**dados_conexao)
    try:
        for view in views:
            registros = await conn.fetch(f"SELECT * FROM {view}")
            if registros:
                df = pd.DataFrame([dict(r) for r in registros])
                nome_arquivo = os.path.join(pasta_destino, f"{view.replace('.', '_')}.xlsx")
                df.to_excel(nome_arquivo, index=False)
                print(f"✅ Exportado: {nome_arquivo}")
            else:
                print(f"⚠️ Nenhum dado encontrado em: {view}")
    finally:
        await conn.close()

async def listar_views(dados_conexao):
    conn = await asyncpg.connect(**dados_conexao)
    rows = await conn.fetch("""
        SELECT table_schema || '.' || table_name AS view_name
        FROM information_schema.views
        WHERE table_schema NOT IN ('pg_catalog', 'information_schema');
    """)
    await conn.close()
    return [r["view_name"] for r in rows]
