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
    nazvy = {
        'crm.stage_lead1': 'Chci odebírat',
        'crm.stage_lead2': '3denní výzva',
        'crm.stage_lead3': 'Rezervace',
        'crm.stage_lead4': 'Placené',
    }
    # Nazvy jsou prekladatelne - zapisuji se pro kazdy nainstalovany
    # jazyk, jinak by v tom druhem zustal puvodni anglicky nazev.
    jazyky = [kod for kod, _ in env['res.lang'].get_installed()]

    for xmlid, cesky in nazvy.items():
        stupen = env.ref(xmlid, raise_if_not_found=False)
        if not stupen:
            continue
        for jazyk in jazyky:
            stupen.with_context(lang=jazyk).name = cesky

    # Pasmo firmy je zaklad pro cely rozvrh terminu: podle nej se
    # prepocitavaji hodiny z nastaveni na ulozeny cas a v nem se posilaji
    # casy v e-mailech. Kdyz zustane prazdne, pocitalo by se v UTC
    # a terminy by byly o dve hodiny vedle.
    firma = env.company.partner_id
    if not firma.tz:
        firma.tz = 'Europe/Prague'

    # Text e-mailu se predvyplni, ale odesilani zustava vypnute.
    # Honza si sam rozhodne, co a kdy komu posle - kdyby se e-mail
    # odesilal sam, odesel by uz v okamziku, kdy prihlaska ze
    # tridenni vyzvy spadne do sveho sloupce.
    vyzva = env.ref('crm.stage_lead2', raise_if_not_found=False)
    if vyzva and not vyzva.hh_mail_subject:
        vyzva.hh_mail_enabled = False
        vyzva.hh_mail_subject = 'Děkuju za zájem'
        vyzva.hh_mail_body = (
            '<p>Ahoj,</p>'
            '<p>děkuju za zájem. Mám tvůj e-mail a co nejdřív se ti ozvu '
            's dalšími kroky.</p>'
            '<p>Honza Hauzr</p>'
        )
