from . import controllers
from . import models


def post_init_hook(env):
    """Predvyplni sloupce nastenky, aby nebyly po instalaci prazdne.

    Pousti se jen pri instalaci modulu, ne pri upgradu - co si Honza
    pozdeji prepise, mu nic nepretlaci zpatky. Navic se kazde pole
    zapisuje jen tehdy, kdyz je jeste prazdne.

    Proc hook a ne datovy soubor: stupne patri modulu crm a zapis
    prekladatelnych poli (predmet, telo) se z ciziho datoveho souboru
    neprojevil - prepinac se nastavil, text zustal prazdny.
    """
    # Prejmenovani vychozich sloupcu Odoo tady drive bylo, ale
    # hook bezi az za datovymi soubory - do te doby se sloupce
    # jmenovaly po staru, nic je nenaslo a vedle nich vznikly
    # duplikaty. Resi to crm.stage._hh_zajistit_nastenku, ktera
    # sklada celou nastenku na jednom miste.

    # Pasmo firmy je zaklad pro cely rozvrh terminu: podle nej se
    # prepocitavaji hodiny z nastaveni na ulozeny cas a v nem se posilaji
    # casy v e-mailech. Kdyz zustane prazdne, pocitalo by se v UTC
    # a terminy by byly o dve hodiny vedle.
    firma = env.company.partner_id
    if not firma.tz:
        firma.tz = 'Europe/Prague'

    # Jeden e-mail do knihovny, aby nebyla po instalaci prazdna a bylo
    # na cem videt, jak to funguje. Do zadneho sloupce se nezarazuje:
    # Honza si sam rozhodne, co a kdy komu posle. Kdyby se zaradil,
    # odesel by uz v okamziku, kdy prvni prihlaska spadne do sveho
    # sloupce.
    Sablona = env['hh.mail.sablona']
    if not Sablona.search_count([]):
        Sablona.create({
            'name': 'Děkuju za zájem',
            'predmet': 'Děkuju za zájem',
            'telo': (
                '<p>Ahoj,</p>'
                '<p>děkuju za zájem. Mám tvůj e-mail a co nejdřív se ti '
                'ozvu s dalšími kroky.</p>'
                '<p>Honza Hauzr</p>'
            ),
        })
