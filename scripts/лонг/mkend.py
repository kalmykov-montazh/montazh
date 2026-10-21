from PIL import Image,ImageDraw,ImageFont
im=Image.new('RGB',(1920,1080),(13,25,43));d=ImageDraw.Draw(im)
d.rectangle([60,0,78,1080],fill=(245,166,35))
B=ImageFont.truetype('/usr/share/fonts/opentype/inter/Inter-Black.otf',96);M=ImageFont.truetype('/usr/share/fonts/opentype/inter/Inter-Bold.otf',48)
d.text((150,180),'Спасибо, что досмотрели',font=B,fill='white')
d.text((150,320),'Подпишитесь на канал и выберите следующее видео',font=M,fill=(245,166,35))
im.save('endcard.png')
