from datetime import date, datetime
from io import BytesIO
import sqlite3
import pandas as pd
import plotly.express as px
import streamlit as st
import database as repo

st.set_page_config(page_title='Finanças | Shirley Colares',page_icon='💜',layout='wide')
st.markdown('''<style>
.block-container{padding-top:1.5rem;max-width:1300px}
[data-testid="stMetric"]{background:#f2f4fc;border:1px solid #e2e7f5;border-radius:15px;padding:16px}
h1,h2,h3{color:#233258}
</style>''',unsafe_allow_html=True)
repo.initialize()
BRL=lambda n: f'R$ {n:,.2f}'.replace(',','X').replace('.',',').replace('X','.')
MONTHS=['Janeiro','Fevereiro','Março','Abril','Maio','Junho','Julho','Agosto','Setembro','Outubro','Novembro','Dezembro']
CAT=['Moradia e serviços','Alimentação','Transporte','Cartão','Empréstimos','Saúde','Educação','Lazer','Outros']

def parsed(s): return date.fromisoformat(s)
def changed(msg='Alterações salvas com sucesso.'):
    st.toast(msg,icon='✅');st.rerun()

def format_debts(rows):
    out=[]
    for x in rows:
        out.append({'ID':x['id'],'Descrição':x['description'],'Categoria':x['category'],'Vencimento':x['due_date'],
                    'Valor devido':x['amount'],'Valor pago':x['paid'],'Pendente':x['remaining'],
                    'Status':'Quitada' if x['remaining']<0.005 else ('Parcial' if x['paid']>0 else 'Pendente'),
                    'Origem':'Atraso anterior' if x['origin']=='anterior' else 'Mês de referência'})
    return pd.DataFrame(out)

def table(df):
    moneycols=[c for c in ('Valor devido','Valor pago','Pendente','Valor','Renda') if c in df.columns]
    cfg={c:st.column_config.NumberColumn(c,format='R$ %.2f') for c in moneycols}
    st.dataframe(df,hide_index=True,use_container_width=True,column_config=cfg)

st.title('💜 Gestão Financeira | Shirley Colares')
st.caption('Controle pessoal de contas, dívidas, pagamentos e renda • os valores podem ser alterados a qualquer momento')
debts=repo.fetch_debts();payments=repo.fetch_payments();incomes=repo.fetch_incomes()
all_months=sorted(set([d['due_date'][:7] for d in debts if d['origin']=='mensal']+[i['received_on'][:7] for i in incomes]+[p['paid_on'][:7] for p in payments]))
if not all_months: all_months=[date.today().strftime('%Y-%m')]
with st.sidebar:
    st.header('📅 Período')
    month=st.selectbox('Selecione o mês',all_months,index=all_months.index('2026-11') if '2026-11' in all_months else len(all_months)-1,format_func=lambda s:f'{MONTHS[int(s[5:])-1]} de {s[:4]}')
    year=st.selectbox('Ano do relatório',sorted({int(m[:4]) for m in all_months}),index=0)
    st.divider()
    st.caption('💾 Dados salvos automaticamente em SQLite neste computador.')
    st.caption('📝 A última parcela paga em novembro foi inicialmente registrada como R$ 755,92: confira e edite se necessário.')

month_rows=[d for d in debts if d['due_date'].startswith(month) and d['origin']=='mensal']
old_rows=[d for d in debts if d['origin']=='anterior']
monthly_due=sum(d['amount'] for d in month_rows)
monthly_remaining=sum(d['remaining'] for d in month_rows)
monthly_paid_on=sum(p['amount'] for p in payments if p['paid_on'].startswith(month))
old_remaining=sum(d['remaining'] for d in old_rows)
all_remaining=sum(d['remaining'] for d in debts)
month_income=sum(i['amount'] for i in incomes if i['received_on'].startswith(month))
year_due=sum(d['amount'] for d in debts if d['due_date'].startswith(str(year)) and d['origin']=='mensal')
year_paid=sum(p['amount'] for p in payments if p['paid_on'].startswith(str(year)))
year_remain=sum(d['remaining'] for d in debts if d['due_date'].startswith(str(year)) and d['origin']=='mensal')

t1,t2,t3,t4=st.tabs(['📊 Dashboard','🧾 Contas e dívidas','💸 Pagamentos','💰 Rendas e relatórios'])
with t1:
    st.subheader('Visão geral do mês')
    a,b,c,d=st.columns(4)
    a.metric('Contas do mês',BRL(monthly_due))
    b.metric('Ainda falta pagar (mês)',BRL(monthly_remaining))
    c.metric('Pagamentos feitos no mês',BRL(monthly_paid_on))
    d.metric('Renda cadastrada no mês',BRL(month_income))
    a,b,c=st.columns(3)
    a.metric('Dívidas antigas em aberto',BRL(old_remaining))
    b.metric('Total em aberto (todos os períodos)',BRL(all_remaining))
    c.metric(f'Dívidas previstas em {year}',BRL(year_due))
    st.caption('“Pagamentos feitos no mês” usa a data do pagamento; “falta pagar” usa a competência/vencimento da conta. Assim, pagar uma dívida antiga não altera indevidamente o valor originalmente devido neste mês.')
    st.subheader(f'Resumo anual — {year}')
    a,b,c=st.columns(3)
    a.metric('Contas previstas no ano',BRL(year_due))
    b.metric('Pagamentos realizados no ano',BRL(year_paid))
    c.metric('Saldo pendente das contas do ano',BRL(year_remain))
    chart=[]
    for m in range(1,13):
        k=f'{year}-{m:02d}'
        ds=[d for d in debts if d['due_date'].startswith(k) and d['origin']=='mensal']
        chart.append({'Mês':MONTHS[m-1][:3], 'Previsto':sum(d['amount'] for d in ds),
                      'Pago nas contas':sum(d['paid'] for d in ds), 'Pendente':sum(d['remaining'] for d in ds)})
    ch=pd.DataFrame(chart)
    g1,g2=st.columns([2,1])
    with g1:
        fig=px.bar(ch,x='Mês',y=['Previsto','Pago nas contas','Pendente'],barmode='group',
                   labels={'value':'R$','variable':'Situação'},color_discrete_sequence=['#5661bb','#27a48b','#eb8b80'])
        fig.update_layout(legend_title_text='',margin=dict(l=0,r=0,t=20,b=0))
        st.plotly_chart(fig,use_container_width=True)
    with g2:
        pie=pd.DataFrame([{'Status':'Pago','Valor':sum(x['paid'] for x in month_rows)},
                          {'Status':'Pendente','Valor':monthly_remaining}])
        if pie['Valor'].sum()>0:
            fig=px.pie(pie,names='Status',values='Valor',hole=.6,color='Status',
                       color_discrete_map={'Pago':'#27a48b','Pendente':'#eb8b80'})
            fig.update_layout(margin=dict(l=0,r=0,t=0,b=0),showlegend=True)
            st.plotly_chart(fig,use_container_width=True)
        else: st.info('Nenhuma conta no mês selecionado.')
    st.subheader('Contas do mês selecionado')
    table(format_debts(month_rows)) if month_rows else st.info('Nenhuma conta cadastrada.')

with t2:
    st.subheader('Contas e dívidas — cadastro editável')
    with st.expander('➕ Cadastrar nova conta',expanded=False):
        with st.form('new_debt',clear_on_submit=True):
            a,b=st.columns(2)
            description=a.text_input('Descrição',placeholder='Ex.: Conta de água')
            category=b.selectbox('Categoria',CAT)
            a,b,c=st.columns(3)
            due=a.date_input('Vencimento',value=parsed(month+'-15'))
            amount=b.number_input('Valor devido (R$)',min_value=0.01,step=10.0)
            origin=c.selectbox('Origem', ['mensal','anterior'],format_func=lambda x:'Conta do mês' if x=='mensal' else 'Dívida antiga')
            notes=st.text_input('Observações (opcional)')
            if st.form_submit_button('Salvar conta',type='primary'):
                if not description.strip(): st.error('Informe a descrição.')
                else: repo.add_debt(description.strip(),category,due,amount,origin,notes);changed()
    st.caption('É possível editar a descrição, o vencimento, a categoria e os valores; contas antigas aparecem separadamente no painel.')
    selected_scope=st.radio('Mostrar', ['Todas','Mês selecionado','Atrasos anteriores'],horizontal=True)
    shown=debts if selected_scope=='Todas' else month_rows if selected_scope=='Mês selecionado' else old_rows
    table(format_debts(shown)) if shown else st.info('Nenhuma conta encontrada.')
    if debts:
        opts={d['id']:f"#{d['id']} · {d['description']} · {BRL(d['remaining'])} pendente" for d in debts}
        chosen=st.selectbox('Selecione a conta para editar ou excluir',list(opts),format_func=lambda x:opts[x])
        item=next(d for d in debts if d['id']==chosen)
        with st.form('edit_debt'):
            a,b=st.columns(2)
            description=a.text_input('Descrição',value=item['description'])
            category=b.selectbox('Categoria',CAT+([item['category']] if item['category'] not in CAT else []),index=(CAT+([item['category']] if item['category'] not in CAT else [])).index(item['category']))
            a,b,c=st.columns(3)
            due=a.date_input('Vencimento',value=parsed(item['due_date']))
            amount=b.number_input('Valor devido (R$)',min_value=float(item['paid']),value=float(item['amount']),step=10.0)
            origin=c.selectbox('Origem', ['mensal','anterior'],index=0 if item['origin']=='mensal' else 1,format_func=lambda x:'Conta do mês' if x=='mensal' else 'Dívida antiga')
            notes=st.text_input('Observações',value=item['notes'])
            if st.form_submit_button('Salvar alterações',type='primary'):
                if not description.strip():st.error('Preencha a descrição.')
                else:
                    try:repo.update_debt(chosen,description.strip(),category,due,amount,origin,notes);changed()
                    except ValueError as ex:st.error(str(ex))
        with st.expander('🗑️ Excluir esta conta'):
            st.warning('Ao excluir uma conta, os pagamentos vinculados a ela também serão excluídos.')
            ok=st.checkbox('Confirmo a exclusão desta conta',key=f'confirm_del_{chosen}')
            if st.button('Excluir definitivamente',disabled=not ok):repo.delete_debt(chosen);changed('Conta excluída.')

with t3:
    st.subheader('Registrar pagamento (inclusive parcial)')
    pending=[d for d in debts if d['remaining']>=0.005]
    if pending:
        opts={d['id']:f"{d['description']} · vence {d['due_date']} · falta {BRL(d['remaining'])}" for d in pending}
        with st.form('new_payment'):
            debt_id=st.selectbox('Conta que está sendo paga',list(opts),format_func=lambda x:opts[x])
            obj=next(d for d in pending if d['id']==debt_id)
            a,b=st.columns(2)
            pay_date=a.date_input('Data do pagamento',value=date.today())
            pay_amount=b.number_input('Valor pago (R$)',min_value=0.01,max_value=float(round(obj['remaining'],2)),value=float(round(obj['remaining'],2)),step=10.0)
            notes=st.text_input('Observações')
            if st.form_submit_button('Registrar pagamento',type='primary'):
                try:repo.add_payment(debt_id,pay_date,pay_amount,notes);changed('Pagamento registrado.')
                except ValueError as ex:st.error(str(ex))
    else:st.success('Todas as contas cadastradas estão quitadas!')
    st.subheader('Histórico de pagamentos')
    if payments:
        pdf=pd.DataFrame([{'ID':p['id'],'Conta':p['description'],'Data':p['paid_on'],'Valor':p['amount'],'Observações':p['notes']} for p in payments])
        table(pdf)
        po={p['id']:f"#{p['id']} — {p['description']} — {BRL(p['amount'])} ({p['paid_on']})" for p in payments}
        with st.expander('↩️ Estornar pagamento lançado por engano'):
            pid=st.selectbox('Pagamento',list(po),format_func=lambda x:po[x])
            confirmed=st.checkbox('Confirmo que quero desfazer o registro')
            if st.button('Estornar',disabled=not confirmed):repo.delete_payment(pid);changed('Pagamento estornado.')
    else:st.info('Ainda não há pagamentos.')

with t4:
    st.subheader('Rendas — cadastro e edição')
    st.caption('As rendas cadastradas são valores previstos ou informados e podem ser alteradas. Não são vinculadas automaticamente às contas bancárias.')
    with st.expander('➕ Adicionar renda'):
        with st.form('new_income'):
            desc=st.text_input('Origem da renda',value='Renda adicional')
            a,b=st.columns(2)
            received=a.date_input('Data da renda',value=parsed(month+'-01'))
            val=b.number_input('Valor (R$)',min_value=0.00,step=50.0)
            if st.form_submit_button('Adicionar renda',type='primary'):
                if desc.strip():repo.add_income(desc.strip(),received,val);changed()
    if incomes:
        table(pd.DataFrame([{'ID':i['id'],'Descrição':i['description'],'Data':i['received_on'],'Valor':i['amount']} for i in incomes]))
        io={i['id']:f"#{i['id']} · {i['description']} · {i['received_on']}" for i in incomes}
        iid=st.selectbox('Editar renda',list(io),format_func=lambda x:io[x])
        item=next(i for i in incomes if i['id']==iid)
        with st.form('edit_income'):
            desc=st.text_input('Descrição',value=item['description'])
            a,b=st.columns(2)
            rdate=a.date_input('Data',value=parsed(item['received_on']))
            val=b.number_input('Valor (R$)',value=float(item['amount']),min_value=0.0,step=50.0)
            if st.form_submit_button('Salvar renda',type='primary'):
                if desc.strip():repo.update_income(iid,desc.strip(),rdate,val);changed()
        with st.expander('🗑️ Excluir renda selecionada'):
            if st.checkbox('Confirmar exclusão da renda'):
                if st.button('Excluir renda'):repo.delete_income(iid);changed()
    st.divider()
    st.subheader('📥 Exportar relatório')
    yearly=[]
    for m in range(1,13):
        k=f'{year}-{m:02d}'
        ds=[d for d in debts if d['origin']=='mensal' and d['due_date'].startswith(k)]
        yearly.append({'Mês':k,'Renda':sum(i['amount'] for i in incomes if i['received_on'].startswith(k)),
                       'Contas':sum(d['amount'] for d in ds),'Pago nas contas':sum(d['paid'] for d in ds),
                       'Pendente':sum(d['remaining'] for d in ds),
                       'Pagamentos pela data':sum(p['amount'] for p in payments if p['paid_on'].startswith(k))})
    table(pd.DataFrame(yearly))
    output=BytesIO()
    with pd.ExcelWriter(output,engine='xlsxwriter') as writer:
        pd.DataFrame(yearly).to_excel(writer,index=False,sheet_name='Resumo mensal')
        format_debts(debts).to_excel(writer,index=False,sheet_name='Contas')
        pd.DataFrame(payments).to_excel(writer,index=False,sheet_name='Pagamentos')
        pd.DataFrame(incomes).to_excel(writer,index=False,sheet_name='Rendas')
    st.download_button('Baixar relatório Excel',data=output.getvalue(),file_name=f'Relatorio_Shirley_{year}.xlsx',
                       mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    st.caption('Para um backup completo, copie também o arquivo shirley_financas.db com o aplicativo fechado.')
