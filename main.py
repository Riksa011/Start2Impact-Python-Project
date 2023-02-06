import json
import time
import schedule
import requests
from operator import itemgetter
from collections import OrderedDict
from pprint import pprint
from datetime import datetime


def richiede_dati_cmc():
    url = ' https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest'
    params = {
        'start': '1',
        'limit': '100',
        'convert': 'USD'
    }
    headers = {
        'Accepts': 'application/json',
        'X-CMC_PRO_API_KEY': 'c55d5be6-7193-4912-8e79-2b5a59afbdae'
    }
    dati_cmc_funzione = requests.get(url=url, headers=headers, params=params).json()
    return dati_cmc_funzione


def crea_rinomina_scrive_filejson(dizionario_report):
    # funzione che crea e rinomina con data e ora corrente un file json e scrive al suo interno il report
    data_ora_attuale = datetime.now()
    data_ora_attuale_formattata = data_ora_attuale.strftime('%d-%m-%Y  %H:%M:%S')
    with open(f'{data_ora_attuale_formattata}.json', "w") as outfile:
        json.dump(dizionario_report, outfile, indent=4)  # scrive il report nel file


def r1_moneta_vol24h_maggiore(dati_cmc):
    moneta_vol24h_maggiore = {'quote': {'USD': {'volume_24h': 0}}}
    for moneta in dati_cmc['data']:
        if moneta['quote']['USD']['volume_24h'] > moneta_vol24h_maggiore['quote']['USD']['volume_24h']:
            moneta_vol24h_maggiore = moneta
    return moneta_vol24h_maggiore


def r2_monete_migliori_24h(dati_cmc, report):
    simbolo_e_prezzo24h_monete = []
    for moneta in dati_cmc['data']:
        simbolo_e_prezzo24h_monete.append(
            {'simbolo': moneta['symbol'], 'prezzo24h': round(moneta['quote']['USD']['percent_change_24h'], ndigits=2)})
    monete_per_prezzo24h_decrescente = sorted(simbolo_e_prezzo24h_monete, key=itemgetter('prezzo24h'), reverse=True)
    contatore = 0
    for moneta in monete_per_prezzo24h_decrescente:
        contatore += 1
        if contatore < 11:
            report[str(contatore) + '\' moneta con performance MIGLIORI nelle 24h'] = moneta['simbolo'] + ': +' + str(moneta['prezzo24h']) + '%'
    return report, simbolo_e_prezzo24h_monete


def r2_monete_peggiori_24h(report, simbolo_e_prezzo24h_monete):
    monete_per_prezzo24h_crescente = sorted(simbolo_e_prezzo24h_monete, key=itemgetter('prezzo24h'))
    contatore = 0
    for moneta in monete_per_prezzo24h_crescente:
        contatore += 1
        if contatore < 11:
            report[str(contatore) + '\' moneta con performance PEGGIORI nelle 24h'] = moneta['simbolo'] + ': ' + str(moneta['prezzo24h']) + '%'
    return report


def r3_dollari_prime20_monete(dati_cmc):
    dollari_per_unita_prime20monete = 0
    for moneta in dati_cmc['data']:
        if moneta['cmc_rank'] <= 20:
            dollari_per_unita_prime20monete += moneta['quote']['USD']['price']
    return dollari_per_unita_prime20monete


def r4_dollari_monete_vol24_maggiore76m(dati_cmc):
    dollari_per_unita_monete_vol24_76m = 0
    for moneta in dati_cmc['data']:
        if moneta['quote']['USD']['volume_24h'] >= 76000000:
            dollari_per_unita_monete_vol24_76m += moneta['quote']['USD']['price']
    return dollari_per_unita_monete_vol24_76m


def r5_perc_realizzata_acquistando_ieri_prime20_monete(dati_cmc):
    valore_prime20monete_ieri = 0
    valore_prime20monete_oggi = 0
    for moneta in dati_cmc['data']:
        if moneta['cmc_rank'] <= 20:
            valore_prime20monete_oggi += moneta['quote']['USD']['price']
            x = 100 + moneta['quote']['USD']['percent_change_24h']
            valore_prime20monete_ieri += (100 * moneta['quote']['USD']['price']) / x
    perc_realizzata = (valore_prime20monete_oggi - valore_prime20monete_ieri) * 100 / valore_prime20monete_ieri
    return perc_realizzata


def assembla_report():
    print('Sto facendo il report, è questione di pochi secondi...\n')

    # creo il dizionario ordinato in cui inserire i risultati dell'analisi
    report = OrderedDict()

    # richiamo la funzione che richiede i dati sul mercato crypto a cmc
    dati_cmc = richiede_dati_cmc()

    # 1 richiamo la funzione relativa alla moneta con volume maggiore nelle 24h e aggiungo il risultato al report
    moneta_vol24h_maggiore = r1_moneta_vol24h_maggiore(dati_cmc)
    report['moneta con VOLUME nelle 24h maggiore'] = moneta_vol24h_maggiore['symbol'] + ': ' + str(int(moneta_vol24h_maggiore['quote']['USD']['volume_24h'])) + ' $'

    # 2 richiamo le funzioni relative alle 10 monete migliori e peggiori nelle 24h e aggiungo i risultati al report
    report, simbolo_e_prezzo24h_monete = r2_monete_migliori_24h(dati_cmc, report)
    report = r2_monete_peggiori_24h(report, simbolo_e_prezzo24h_monete)

    # 3 richiamo la funzione relativa ai $ necessari ad acquistare un'unità delle prime 20 monete e aggiungo il risultato al report
    dollari_per_unita_prime20monete = r3_dollari_prime20_monete(dati_cmc)
    report['$ necessari per acquistare un\'unità di ognuna delle PRIME 20 monete per capitalizzazione'] = str(round(dollari_per_unita_prime20monete)) + ' $'

    # 4 richiamo la funzione relativa ai $ necessari ad acquistare un'unità delle monete con volume superiore $ nelle 24h a 76milioni$ e aggiungo il risultato al report
    dollari_per_unita_monete_vol24_76m = r4_dollari_monete_vol24_maggiore76m(dati_cmc)
    report['$ necessari per acquistare un\'unità di ognuna delle monete con VOLUME nelle 24h SUPERIORE a 76.000.000$'] = str(round(dollari_per_unita_monete_vol24_76m)) + ' $'

    # 5 richiamo la funzione relativa alla % che avrei realizzato avendo acquistato ieri un'unità delle prime 20 monete e aggiungo il risultato al report
    perc_acquisto_prime20monete_ieri = r5_perc_realizzata_acquistando_ieri_prime20_monete(dati_cmc)
    if perc_acquisto_prime20monete_ieri >= 0:
        report['% realizzata avendo acquistato IERI un\'unità di ognuna delle PRIME 20 monete per capitalizzazione'] = '+' + str(round(perc_acquisto_prime20monete_ieri, ndigits=2)) + '%'
    else:
        report['% realizzata avendo acquistato IERI un\'unità di ognuna delle PRIME 20 monete per capitalizzazione'] = str(round(perc_acquisto_prime20monete_ieri, ndigits=2)) + '%'

    # richiamo la funzione che scrive all'interno di un file json il report appena fatto
    crea_rinomina_scrive_filejson(dizionario_report=report)

    # stampo a schermo un'anteprima del report
    print('Report completato! Eccone un\'anteprima:\n')
    pprint(report)


# chiedo all'utente l'ora in cui fare il report, avendo come default le 10.00
schedule.every().day.at(input('Inserisci l\'orario in cui fare il report nel formato \"ore:minuti\", se non inserisci un\'orario il report verrà fatto di default alle 10:00: ') or '10:00').do(assembla_report)
print(f'\nRicevuto!\n')
print('Ricorda di interrompere il programma manualmente una volta che il report sarà completato\n\n')
while True:
    schedule.run_pending()
    time.sleep(1)
    print('Attendo l\'orario stabilito per effettuare il report')
