#!/usr/bin/env python3
# 17.11.2026 (ночная перепроверка): в хуках перезапусков стояли картинки не про Испанию — американские паспорт,
# конверт, почтовый ящик, «HOME FOR SALE», эстонское удостоверение, английские документы с Sears/Safeway,
# табличка «POLICE», руль BMW, ярлык British Airways, французское ущелье, чужие люди. Правило «ОБЛОЖКИ И КАРТИНКИ —
# ЖЁСТКО» (13.11): только Испания. Скрипт меняет такие картинки в hf/perezapusk/spisok.json:
#   1) картинка из «Испания — картинки по темам», названная как тема ролика (банк собирался под эти ролики),
#   2) иначе — нейтральная без надписей (евро, ключи, часы, испанские дома и мэрии).
# Запуск на машине GitHub (ves-bash): python3 scripts/zamena_kartinok_perezapusk.py bank.txt papki.txt
#   bank.txt  — rclone lsf -R по банку («раздел/название.jpg»), papki.txt — «путь<TAB>номер» неопубликованных перезапусков
# Печатает план замен и пишет: zamena_copy.txt («путь в банке<TAB>новое имя в Предметы_ov»), zamena_nomera.txt
import sys, json, re, difflib, os

BAD = {'calendar_1.jpg', 'calendar_4.jpg', 'caraccident_1.jpg', 'documents_6.jpg', 'forsale_1.jpg', 'keys2_1.jpg',
       'luggage2_3.jpg', 'n11_documents_folder_4.jpg', 'n11_electric_bill_2.jpg', 'n11_electricity_meter_3.jpg',
       'n11_identity_card_3.jpg', 'n11_letter_envelope_3.jpg', 'n11_letter_envelope_4.jpg', 'n11_mailbox_1.jpg',
       'n11_mailbox_4.jpg', 'n11_police_station_1.jpg', 'n11_property_document_1.jpg', 'n11_steering_wheel_car_2.jpg',
       'n11_salary_envelope_2.jpg', 'passport_1.jpg', 'passport_2.jpg', 'road_3.jpg', 'greencoast_1.jpg',
       'n11_trash_container_4.jpg', 'n11_calendar_reminder_3.jpg'}
SAFE = ['eurobills_4.jpg', 'n11_town_hall_spain_5.jpg', 'n11_apartment_building_spain_1.jpg', 'clock_4.jpg',
        'eurobills_1.jpg', 'n11_town_hall_spain_1.jpg', 'carkeys_2.jpg', 'n11_euro_bills_2.jpg', 'door2_3.jpg',
        'contractsign_1.jpg', 'n11_town_hall_spain_4.jpg', 'calculator2_4.jpg', 'n11_euro_coins_5.jpg']
# тема → раздел банка, если по названию не нашлось
CAT = [(r'ВНЖ|защит|ПМЖ|контракт|паспорт|TIE|прописк|адрес|поездк', 'Документы, ВНЖ, защита'),
       (r'полиц|штраф|собак|кошел|телефон за', 'Полиция, штрафы, закон'),
       (r'аренд|жиль|залог|кастинг|хозяин|котёл|сосед', 'Аренда'),
       (r'налог|IBI|квартир|покупк|нота|Nota|энерго|Cédula|дарени|новостро|комунидад|модель|720', 'Покупка, налоги, дом'),
       (r'машин|авто|маячок|номер', 'Авто'), (r'страхов|наличн|деньг|зарплат|банк', 'Деньги, банк, страховки'),
       (r'врач|плохо|лекарств|рецепт', 'Медицина и аптека'), (r'отель|поездк', 'Путешествия')]

bank = [l.strip() for l in open(sys.argv[1], encoding='utf-8') if l.strip().endswith('.jpg') and '/_' not in l]
papki = {}
for l in open(sys.argv[2], encoding='utf-8'):
    if '\t' in l:
        p, n = l.rstrip('\n').split('\t'); papki[n] = p
L = json.load(open('hf/perezapusk/spisok.json', encoding='utf-8'))
copy, nums, used_bank = [], [], set()
for it in L:
    n = it['n']
    if n not in papki: continue
    cur = [it['img']] + it.get('imgs', [])
    if not any(x in BAD for x in cur): continue
    title = papki[n].rstrip('/').split('/')[-1]
    title_s = re.sub(r'^\d+\s+', '', title)
    names = {b.split('/')[-1][:-4]: b for b in bank}
    best = difflib.get_close_matches(title_s, list(names), n=1, cutoff=0.45)
    topic = names[best[0]] if best else None
    if not topic:
        for rx, cat in CAT:
            if re.search(rx, title_s, re.I):
                cands = [b for b in bank if b.startswith(cat + '/') and b not in used_bank]
                if cands: topic = cands[0]
                break
    new = []
    for x in cur:
        if x not in BAD: new.append(x); continue
        if topic and f'es_t{n}.jpg' not in new:
            nm = f'es_t{n}.jpg'; copy.append((topic, nm)); used_bank.add(topic); new.append(nm); continue
        alt = next(s for s in SAFE if s not in new and s not in cur)
        new.append(alt)
    print(f"{n} {title_s}: {cur} -> {new}" + (f"  [банк: {topic}]" if topic else ''))
    it['img'], it['imgs'] = new[0], new[1:]
    it['dest'] = papki[n].rstrip('/')
    nums.append(n)
json.dump(L, open('hf/perezapusk/spisok.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
open('zamena_copy.txt', 'w').write('\n'.join(f'{a}\t{b}' for a, b in copy))
open('zamena_nomera.txt', 'w').write(','.join(nums))
print('ИТОГО к пересборке:', len(nums), ','.join(nums))
