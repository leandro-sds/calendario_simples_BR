# Calendário Simples BR (NVDA Add-on)

Complemento do **NVDA** que oferece um calendário simples e acessível, com navegação rápida e anúncios claros de data.

- **Atalho principal:** `NVDA+Shift+C` (abre o Calendário Simples BR)
- Também disponível em **NVDA → Ferramentas → Calendário Simples BR**

## Recursos

- Navegação por **dia**, **semana**, **mês** e **ano**
- Anúncio da data atual e do dia da semana
- Interface simples e focada no uso com leitor de telas
- Contagem de dias corridos, úteis, fins de semana e feriados entre duas datas

## Contar dias entre datas

No calendário, navegue até a data inicial e pressione **U**. Navegue até a data final e pressione **Shift+U** para abrir os resultados. Ao navegar pelas datas marcadas, o NVDA anuncia início ou fim. Pressione **Ctrl+U** para limpar as duas marcações. A data final pode ser anterior à inicial para contar retroativamente. As duas datas são incluídas; o intervalo deve estar entre 2000 e 2099.

Na janela, use as setas nos campos de dias úteis, dias corridos ou dias de fim de semana para alterar o fim do intervalo; o início permanece fixo. Os demais resultados são atualizados e a nova data final é anunciada após 500 milissegundos sem alterações. Ao aumentar a contagem, o fim se afasta do início; ao diminuir, se aproxima, preservando a direção escolhida mesmo ao alcançar o início. Se várias datas tiverem a mesma contagem, o ajuste usa a primeira ao se afastar e a última ao se aproximar. Ao fechar a janela, a data final ajustada permanece marcada.

Dias úteis são de segunda a sexta, descontando os feriados nacionais e a Sexta-feira Santa. O Dia da Consciência Negra é considerado feriado nacional a partir de 2024. A terça-feira de Carnaval e Corpus Christi também são descontados; a observância dessas datas depende da localidade e da instituição. Feriados estaduais e municipais não são incluídos. Feriados em fins de semana aparecem na lista, mas não são descontados duas vezes. Para prazos, confira as regras específicas aplicáveis.

## Requisitos

- NVDA **2024.1** ou superior.

## Licença

GPL v2.
