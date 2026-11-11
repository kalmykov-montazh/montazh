import re
base = open('/tmp/claude-0/var/out/final.html', encoding='utf-8').read()

# Новый блок чек-листа: яркий, с «листком» и первыми пунктами
old_cl = re.search(r'  <section class="checklist reveal".*?</section>', base, re.S).group(0)
new_cl = '''  <section class="checklist reveal" aria-labelledby="h-check">
    <div class="tx">
      <span class="free">Бесплатно</span>
      <h2 id="h-check">Чек-лист: 10 пунктов проверить до подписи договора аренды</h2>
      <p>Чтобы не потерять залог и не нарваться на «хозяина», который им не является</p>
      <a class="get" id="checkgo" target="_blank" rel="noopener">Получить чек-лист</a>
    </div>
    <div class="paper" aria-hidden="true">
      <b>Чек-лист арендатора</b>
      <i>✓ Кто собственник — nota simple</i>
      <i>✓ Сумма залога по закону</i>
      <i>✓ Кто платит агентству</i>
      <i class="blur">✓ Срок и досрочный выезд</i>
      <i class="blur">✓ Индексация цены</i>
      <span>ещё 5 пунктов</span>
    </div>
  </section>'''
base = base.replace(old_cl, new_cl, 1)

cl_css = '''
/* чек-лист 2.0 */
.checklist{display:grid;grid-template-columns:1fr auto;gap:24px;align-items:center;padding:26px 28px;border-radius:22px;position:relative;overflow:hidden;
  background:radial-gradient(circle at 85% 20%,#fff3c4 0,transparent 45%),linear-gradient(120deg,#ffd166 0%,#ff9f5a 60%,#ff7a59 100%);color:#2a1a0e;box-shadow:0 14px 34px rgba(255,122,89,.28)}
.checklist .doc{display:none}
.checklist .free{background:#1d2b44;color:#ffd166}
.checklist h2{color:#2a1a0e;font-size:24px;margin:6px 0}
.checklist p{color:#3d2a17;opacity:1;margin:0 0 14px}
.checklist .get{background:#1d2b44;color:#fff;box-shadow:0 5px 0 #0c1526;display:inline-flex}
.checklist .get:hover{transform:translateY(-1px)}
.checklist .paper{width:250px;background:#fff;border-radius:12px;padding:16px 16px 12px;transform:rotate(3deg);box-shadow:0 16px 30px rgba(0,0,0,.18);display:flex;flex-direction:column;gap:7px}
.checklist .paper b{font-size:14px;color:#1d2b44;border-bottom:2px solid #ffd166;padding-bottom:6px}
.checklist .paper i{font-style:normal;font-size:13px;color:#2a3a4a}
.checklist .paper i.blur{filter:blur(2.5px);opacity:.7}
.checklist .paper span{font-size:12px;font-weight:700;color:#ff7a59}
@media (max-width:600px){.checklist{grid-template-columns:1fr;padding:20px}.checklist .paper{display:none}.checklist h2{font-size:19px}.checklist .get{display:flex;justify-content:center}}
'''

palettes = {
 'beliy': ('Белый и морской синий', '''
:root{--bg:#f6f8fa!important;--surface:#ffffff!important;--fg:#1d2b36!important;--muted:#64707b!important;--line:#e2e8ee!important;--sea:#0f5a80!important;--accent:#e4572e!important}
body{background:var(--bg)}
.card{background:#fff!important;border:1px solid var(--line)!important;box-shadow:0 1px 2px rgba(16,40,60,.04)}
.card:hover{border-color:var(--t)!important;box-shadow:0 6px 18px rgba(16,40,60,.08)}
.card .ci{background:var(--t)!important;color:#fff!important}
.consult{background:#fff!important;border:1px solid var(--line)!important;border-left:6px solid var(--accent)!important}
.steps li,.consult .prices p{background:#f8fafc!important}
.socials a{background:#fff}
.about,.faq details,.soon div,.partners{background:#fff}
'''),
 'seryj': ('Светло-серый и тёмно-синий', '''
:root{--bg:#eef1f5!important;--surface:#ffffff!important;--fg:#16233a!important;--muted:#5f6b7a!important;--line:#dde3ea!important;--sea:#16294a!important;--accent:#ff6b4a!important}
body{background:var(--bg)}
h1,h2{color:#16294a}
.card{background:#fff!important;border:0!important;box-shadow:0 2px 10px rgba(22,41,74,.07)}
.card:hover{box-shadow:0 10px 26px rgba(22,41,74,.14)}
.card .ci{background:var(--t)!important;color:#fff!important;border-radius:50%!important}
.consult{background:#16294a!important;border:0!important;color:#fff}
.consult h2,.consult li{color:#fff!important}
.consult .kick{color:#ffd166!important}
.consult .note{color:#c9d3e0!important}
.steps li,.consult .prices p{background:rgba(255,255,255,.07)!important;border-color:rgba(255,255,255,.18)!important}
.consult .prices span{color:#c9d3e0!important}
.steps span{color:#fff}
.tgalt{color:#8fd3ff!important}
.socials a{background:#fff;border:0;box-shadow:0 1px 4px rgba(22,41,74,.07)}
.about,.faq details,.soon div,.partners{background:#fff;border-color:transparent}
'''),
}
for key, (title, css) in palettes.items():
    s = base.replace('</style>\n</head>', cl_css + css + '</style>\n</head>', 1)
    open(f'/tmp/claude-0/var/out/{key}.html', 'w', encoding='utf-8').write(s)
print('ok')
