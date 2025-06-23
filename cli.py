import customtkinter as ctk
import asyncio
from datetime import datetime
import asyncpg
import pandas as pd
from tkinter import filedialog

ctk.set_appearance_mode("dark")


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
    
        self.title("Consulta de Atendimentos")
        self.geometry("1000x750")
        self.iconbitmap("imagens/excel.ico")

        # Frame superior com campos de data
        self.frame_datas = ctk.CTkFrame(self)
        self.frame_datas.pack(pady=10)

        self.label_data_inicio = ctk.CTkLabel(self.frame_datas, text="Data Início (YYYY-MM-DD HH:MM:SS):")
        self.label_data_inicio.pack(side="left", padx=10)
        self.entrada_data_inicio = ctk.CTkEntry(self.frame_datas, width=200)
        self.entrada_data_inicio.pack(side="left", padx=10)

        self.label_data_fim = ctk.CTkLabel(self.frame_datas, text="Data Fim (YYYY-MM-DD HH:MM:SS):")
        self.label_data_fim.pack(side="left", padx=10)
        self.entrada_data_fim = ctk.CTkEntry(self.frame_datas, width=200)
        self.entrada_data_fim.pack(side="left", padx=10)

        # Botão buscar atendimentos
        self.botao_buscar_atendimentos = ctk.CTkButton(self, text="Buscar Atendimentos", command=self.buscar_atendimentos)
        self.botao_buscar_atendimentos.pack(pady=8)

        # Lista de atendimentos
        self.lista_atendimentos = ctk.CTkOptionMenu(self, values=["Nenhum"])
        self.lista_atendimentos.pack(pady=8)

        # Botão buscar detalhes
        self.botao_buscar_detalhes = ctk.CTkButton(self, text="Buscar Detalhes do Atendimento", command=self.buscar_detalhes)
        self.botao_buscar_detalhes.pack(pady=8)

        # Status
        self.status_label = ctk.CTkLabel(self, text="", text_color="gray")
        self.status_label.pack(pady=5)

        # Cria o tabview
        self.tabs = ctk.CTkTabview(self, width=950, height=400)
        self.tabs.pack(pady=10)

        # Aba Resultados
        self.tab_resultados = self.tabs.add("📋 Resultados")

        self.label_consumo = ctk.CTkLabel(self.tab_resultados, text="--- CONSUMOS ---")
        self.label_consumo.pack()
        self.frame_consumo = ctk.CTkScrollableFrame(self.tab_resultados, width=920, height=200)
        self.frame_consumo.pack(pady=5)

        self.label_diarias = ctk.CTkLabel(self.tab_resultados, text="--- DIÁRIAS ---")
        self.label_diarias.pack()
        self.frame_diarias = ctk.CTkScrollableFrame(self.tab_resultados, width=920, height=150)
        self.frame_diarias.pack(pady=5)

        # Aba Exportar
        self.tab_exportar = self.tabs.add("📤 Exportar")

        self.chk_diarias = ctk.CTkCheckBox(self.tab_exportar, text="Exportar Diárias", command=self.atualizar_checklist_diarias)
        self.chk_diarias.pack(pady=10)
        self.chk_diarias.select()

        self.checklist_diarias = ctk.CTkScrollableFrame(self.tab_exportar, width=400, height=150)
        self.checklist_diarias.pack(pady=5)

        self.chk_consumo = ctk.CTkCheckBox(self.tab_exportar, text="Exportar Consumos", command=self.atualizar_checklist_consumo)
        self.chk_consumo.pack(pady=10)
        self.chk_consumo.select()

        self.checklist_consumo = ctk.CTkScrollableFrame(self.tab_exportar, width=400, height=150)
        self.checklist_consumo.pack(pady=5)

        botao_salvar = ctk.CTkButton(self.tab_exportar, text="Salvar Arquivo", command=self.exportar_excel)
        botao_salvar.pack(pady=20)

        self.checkboxes_diarias = {}
        self.checkboxes_consumo = {}

        # Dados para exportação
        self.dados_diarias = []
        self.dados_consumo = []

    def atualizar_checklist_diarias(self):
        for widget in self.checklist_diarias.winfo_children():
            widget.destroy()
        if self.dados_diarias:
            colunas = list(self.dados_diarias[0].keys())
            for col in colunas:
                cb = ctk.CTkCheckBox(self.checklist_diarias, text=col)
                cb.pack(anchor="w")
                cb.select()
                self.checkboxes_diarias[col] = cb

    def atualizar_checklist_consumo(self):
        for widget in self.checklist_consumo.winfo_children():
            widget.destroy()
        if self.dados_consumo:
            colunas = list(self.dados_consumo[0].keys())
            for col in colunas:
                cb = ctk.CTkCheckBox(self.checklist_consumo, text=col)
                cb.pack(anchor="w")
                cb.select()
                self.checkboxes_consumo[col] = cb

    def exibir_tabela(self, frame, dados):
        for widget in frame.winfo_children():
            widget.destroy()

        if not dados:
            ctk.CTkLabel(frame, text="Nenhum dado encontrado.").pack()
            return

        colunas = list(dados[0].keys())

        for j, col in enumerate(colunas):
            ctk.CTkLabel(frame, text=col, font=("Arial", 10, "bold")).grid(row=0, column=j, padx=5, pady=2)

        for i, linha in enumerate(dados, start=1):
            for j, col in enumerate(colunas):
                valor = linha[col]
                ctk.CTkLabel(frame, text=str(valor)).grid(row=i, column=j, padx=5, pady=2)

    def buscar_atendimentos(self):
        data_inicio = self.entrada_data_inicio.get()
        data_fim = self.entrada_data_fim.get()

        try:
            dt_inicio = datetime.strptime(data_inicio, "%Y-%m-%d %H:%M:%S")
            dt_fim = datetime.strptime(data_fim, "%Y-%m-%d %H:%M:%S")
            asyncio.run(self.executar_busca_atendimentos(dt_inicio, dt_fim))
        except ValueError:
            self.status_label.configure(text="⚠️ Formato de data inválido. Use: YYYY-MM-DD HH:MM:SS")

    async def executar_busca_atendimentos(self, dt_inicio, dt_fim):
        try:
            conn = await asyncpg.connect(user='sadt', password='S@dt2000', database='db1', host='187.93.239.226')
            query = """
                SELECT DISTINCT atendimento_numero
                FROM "PACIENTE".vw_diarias
                WHERE data_entrada BETWEEN $1 AND $2
                ORDER BY atendimento_numero
            """
            registros = await conn.fetch(query, dt_inicio, dt_fim)
            await conn.close()

            atendimentos = [str(r['atendimento_numero']) for r in registros]
            if atendimentos:
                self.lista_atendimentos.configure(values=atendimentos)
                self.lista_atendimentos.set(atendimentos[0])
                self.status_label.configure(text=f"✅ {len(atendimentos)} atendimentos encontrados.")
            else:
                self.status_label.configure(text="Nenhum atendimento encontrado nesse período.")

        except Exception as e:
            self.status_label.configure(text=f"Erro ao consultar banco de dados: {e}")

    def buscar_detalhes(self):
        numero = self.lista_atendimentos.get()
        if numero != "Nenhum":
            asyncio.run(self.executar_busca_detalhes(numero))

    async def executar_busca_detalhes(self, numero):
        try:
            conn = await asyncpg.connect(user='sadt', password='S@dt2000', database='db1', host='187.93.239.226')

            query_diarias = """
                SELECT * FROM "PACIENTE".vw_diarias WHERE atendimento_numero = $1
            """
            query_consumo = """
                SELECT * FROM "PACIENTE".r_consumo WHERE numero_atendimento = $1
            """

            diarias = await conn.fetch(query_diarias, numero)
            consumo = await conn.fetch(query_consumo, numero)
            await conn.close()

            self.dados_diarias = [dict(d) for d in diarias]
            self.dados_consumo = [dict(c) for c in consumo]

            self.exibir_tabela(self.frame_diarias, self.dados_diarias)
            self.exibir_tabela(self.frame_consumo, self.dados_consumo)
            self.status_label.configure(text=f"📋 Exibindo detalhes do atendimento {numero}.")

            self.atualizar_checklist_diarias()
            self.atualizar_checklist_consumo()
            self.tabs.set("📋 Resultados")

        except Exception as e:
            self.status_label.configure(text=f"Erro ao buscar detalhes: {e}")

    def exportar_excel(self):
        exportar_diarias = self.chk_diarias.get()
        exportar_consumo = self.chk_consumo.get()

        if not exportar_diarias and not exportar_consumo:
            self.status_label.configure(text="⚠️ Selecione ao menos uma tabela para exportar.")
            return

        try:
            agora = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            nome_padrao = f"atendimento_export_{agora}.xlsx"

            file_path = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                initialfile=nome_padrao,
                filetypes=[("Excel Files", "*.xlsx")],
                title="Salvar como"
            )
            if not file_path:
                return

            with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
                if exportar_diarias and self.dados_diarias:
                    colunas = [col for col, cb in self.checkboxes_diarias.items() if cb.get()]
                    pd.DataFrame(self.dados_diarias)[colunas].to_excel(writer, sheet_name="Diarias", index=False)
                if exportar_consumo and self.dados_consumo:
                    colunas = [col for col, cb in self.checkboxes_consumo.items() if cb.get()]
                    pd.DataFrame(self.dados_consumo)[colunas].to_excel(writer, sheet_name="Consumo", index=False)

            self.status_label.configure(text=f"✅ Exportado com sucesso para '{file_path}'")

        except Exception as e:
            self.status_label.configure(text=f"Erro ao exportar Excel: {e}")


if __name__ == '__main__':
    app = App()
    app.mainloop()
