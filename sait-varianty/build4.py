import re
block = '''  <section class="bonus reveal" aria-labelledby="h-bonus">
    <span class="bkick">Бонус для новичков в Испании</span>
    <h2 id="h-bonus">Откройте счёт в BBVA и получите до 450 €</h2>
    <ul>
      <li>до <b>50 €</b> — за покупки картой в первые 45 дней</li>
      <li>ещё <b>400 €</b> — если на счёт приходит зарплата или пенсия от 800 €</li>
    </ul>
    <div class="code">
      <div><small>Код приглашения</small><b id="bbvacode">14C70020F574B9</b></div>
      <button type="button" id="copybbva">Скопировать код</button>
    </div>
    <p class="how">Скачайте приложение BBVA, при открытии счёта введите этот код. Условия задаёт банк и может их менять — проверьте в приложении перед открытием</p>
  </section>
'''
css = '''
.bonus{margin:28px 0;padding:24px 26px;border-radius:20px;background:#fff;border:2px solid #0050b3;box-shadow:0 10px 26px rgba(0,40,110,.10)}
.bonus .bkick{display:inline-block;background:#0050b3;color:#fff;font-size:12px;font-weight:700;padding:5px 10px;border-radius:99px;letter-spacing:.3px}
.bonus h2{margin:10px 0 8px;font-size:22px;color:#0b2a55}
.bonus ul{margin:0 0 14px;padding-left:20px;color:#2a3a4a;line-height:1.55}
.bonus .code{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;background:#eef4ff;border:1px dashed #0050b3;border-radius:14px;padding:12px 14px}
.bonus .code small{display:block;font-size:12px;color:#5a6b80}
.bonus .code b{font-size:22px;letter-spacing:2px;color:#0b2a55;font-family:ui-monospace,Consolas,monospace}
.bonus button{background:#0050b3;color:#fff;border:0;border-radius:12px;padding:12px 18px;font-weight:700;font-size:15px;cursor:pointer;box-shadow:0 4px 0 #003070}
.bonus button.ok{background:#1f9d55;box-shadow:0 4px 0 #136b39}
.bonus .how{margin:12px 0 0;font-size:13px;color:#64707b}
@media (max-width:600px){.bonus{padding:20px}.bonus h2{font-size:19px}.bonus .code{flex-direction:column;align-items:stretch;text-align:center}.bonus button{width:100%}}
'''
js = '''<script>
(function(){var b=document.getElementById('copybbva');if(!b)return;b.addEventListener('click',function(){var c=document.getElementById('bbvacode').textContent;
function done(){b.textContent='Скопировано ✓';b.classList.add('ok');setTimeout(function(){b.textContent='Скопировать код';b.classList.remove('ok')},2500)}
if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(c).then(done,fallback)}else fallback();
function fallback(){var t=document.createElement('textarea');t.value=c;document.body.appendChild(t);t.select();try{document.execCommand('copy')}catch(e){}document.body.removeChild(t);done()}})})();
</script>
'''
for key in ('beliy', 'seryj'):
    p = f'/tmp/claude-0/var/out/{key}.html'
    s = open(p, encoding='utf-8').read()
    if 'class="bonus' in s:
        continue
    anchor = '  <section class="head" aria-labelledby="h-soon">'
    assert anchor in s
    s = s.replace(anchor, block + anchor, 1)
    s = s.replace('</style>\n</head>', css + '</style>\n</head>', 1)
    s = s.replace('</body>', js + '</body>', 1)
    open(p, 'w', encoding='utf-8').write(s)
print('ok')

# телефон: все 8 значков соцсетей в одну строку
fix = '@media (max-width:600px){.socials{flex-wrap:nowrap!important;gap:0!important;justify-content:space-between!important}.socials a{width:38px!important}.socials .ic{width:38px!important;height:38px!important}.socials .ic svg{width:19px!important;height:19px!important}}\n'
for key in ('beliy', 'seryj'):
    p = f'/tmp/claude-0/var/out/{key}.html'
    s = open(p, encoding='utf-8').read()
    if 'flex-wrap:nowrap!important;gap:0' not in s:
        s = s.replace('</style>\n</head>', fix + '</style>\n</head>', 1)
        open(p, 'w', encoding='utf-8').write(s)
print('fix ok')
