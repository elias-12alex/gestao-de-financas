# Sistema financeiro — Shirley Colares

Aplicação Python local com Streamlit, SQLite, Plotly e exportação de Excel. Não exige servidor externo ou conta online.

## Executar no Windows

1. Instale Python 3.11 ou superior em https://www.python.org/downloads/ (marque **Add Python to PATH**).
2. Extraia o arquivo ZIP e dê duplo clique em **INICIAR_WINDOWS.bat**.
3. Na primeira execução, as bibliotecas serão instaladas; em seguida o navegador abrirá o dashboard.
4. Nas próximas vezes, execute o mesmo arquivo. Para encerrar, pressione Ctrl+C na janela do terminal.

## Executar no terminal (Windows, Linux, macOS)

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## O que pode ser alterado

- Contas: adicione, edite valores, categorias, datas, descrição ou exclua.
- Pagamentos: cadastre pagamentos integrais ou parciais e estorne os lançados incorretamente.
- Rendas: cadastre, edite ou exclua entradas.
- Dashboard: filtre meses e anos; os gráficos e indicadores são recalculados automaticamente.
- Relatórios: exporte planilhas Excel.

## Dados iniciais e ressalvas

- O período pré-carregado é **novembro/2026 a outubro/2027**, com despesas previstas a partir do planejamento enviado.
- A parcela de **R$ 755,92** foi inicialmente considerada como a única paga em novembro. **Confirme esse valor:** se estiver incorreto, estorne o pagamento em **Pagamentos**, edite a conta e registre o valor correto.
- Dez parcelas mensais de **R$ 907,52** foram lançadas como previsões. Verifique se correspondem realmente ao cronograma do empréstimo e remova as que não se aplicarem.
- Dívidas anteriores (3× R$ 900 de moto e R$ 694 + R$ 597,12 de energia) aparecem com a data provisória **31/10/2026**, marcada como *atraso anterior*, e são separadas das contas do mês nos indicadores.
- Valores mensais futuros são **previsões editáveis**; não significam dívidas já vencidas.
- Valores de renda são estimativas previstas inicialmente, não valores comprovadamente recebidos.
- O valor pago considera exclusivamente registros do sistema, não importações bancárias.

## Dados e backup

O sistema cria `shirley_financas.db` ao abrir pela primeira vez. Esse arquivo é o banco de dados e guarda suas alterações. Faça uma cópia periódica com o aplicativo fechado. Não apague esse arquivo ao atualizar o código. Ele contém informações financeiras pessoais: não o publique em repositórios públicos.
