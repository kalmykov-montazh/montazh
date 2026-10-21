EXT = {'01':(1187,697),'02':(1223,805),'03':(1619,769),'04':(1612,795),'05':(1339,864),'06':(1209,706),'07':(1199,700),'08':(1135,745),'09':(1573,789)}
def slide(k):
    mx, my = EXT[k]
    x0, y0 = 30, 40
    w = max(1250, mx + 25) - x0; w -= w % 2
    h = max(700, my + 25) - y0; h -= h % 2
    sc = 1080 / w; oh = int(h * sc) // 2 * 2; ow = 1080
    if oh > 650: oh = 650; ow = int(w * 650 / h) // 2 * 2
    flt = f"crop={w}:{h}:{x0}:{y0}"
    if x0 + w > 1287 and y0 + h > 643:  # закрыть угол с камерой
        flt += f",drawbox=x={1287-x0-4}:y={643-y0-4}:w={w}:h={h}:c=0x0E1A2A:t=fill"
    flt += f",scale={ow}:{oh}:flags=lanczos,pad=1080:{oh}:(ow-iw)/2:0:color=0x0E1A2A"
    return flt, oh
