#!/usr/bin/env python3
"""
build_film_pages.py — the hindcast film's web page in each of the film's languages.

One template, one block of prose per language, three pages: hindcast_film.html (English),
hindcast_film_cy.html, hindcast_film_pl.html — each with its own <html lang>, its own mp4 and
poster (paths.out_47_lang), and a language line under the title linking the other two. The
pages are generated so they cannot drift apart in structure; the prose is here, in PAGES,
because a page's prose is not a pipeline output. Regenerate after editing:

    python3 tools/build_film_pages.py          writes the three pages
    python3 tools/build_film_pages.py --check  exit 1 if a page on disk differs

The Welsh and Polish prose were written by the 2026-10-13 session and are unchecked by a
speaker; each page says so until one has read it (the UNCHECKED note per language).
"""
from __future__ import annotations

__version__ = "1.0.0"  # Hollingham (2026) — 2026-10-13 (Script 47 1.9.0). First version.

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from utils.config import FILM_LANGS                                  # noqa: E402
from utils.paths import OUT_47_PRESENTATION, out_47_still, out_47_lang  # noqa: E402

STILL_MONTH = "2000-12"          # the wettest month's still is the poster (export_lag PAGES_ROOT)
MP4_MB = "30"                    # the 1.8.0 presentation cut is ~29 MB; the page says so

STYLE = """
    *,*::before,*::after{box-sizing:border-box;margin:0;padding:0;}
    :root{
      --sand:#f4f0e6; --sand-dark:#e8e0cc; --dune:#c8b878; --slate:#3a4a52;
      --water:#4a7a8a; --pine:#3d5c3a; --text:#2a3338; --text-light:#5a6a72; --border:#d4c8a8;
    }
    body{font-family:'Source Sans 3',sans-serif;background:var(--sand);color:var(--text);
         line-height:1.65;-webkit-font-smoothing:antialiased;}
    header{background:var(--slate);color:#fff;padding:2.2rem 1rem 2rem;text-align:center;
           border-bottom:4px solid;border-image:linear-gradient(90deg,var(--dune),var(--water),var(--pine)) 1;}
    header h1{font-family:'Libre Baskerville',serif;font-weight:700;font-size:1.9rem;line-height:1.2;}
    header p{color:var(--dune);margin-top:.5rem;font-size:1.02rem;max-width:44rem;margin-left:auto;margin-right:auto;}
    .back{display:inline-block;margin:1rem auto 0;color:#cfe0e6;text-decoration:none;font-size:.92rem;}
    .back:hover{text-decoration:underline;}
    .lang{margin-top:.9rem;font-size:.92rem;color:#cfe0e6;}
    .lang a{color:#fff;text-decoration:none;border-bottom:1px solid rgba(255,255,255,.4);}
    .lang a:hover{border-bottom-color:#fff;}
    .lang strong{color:var(--dune);font-weight:600;}
    main{max-width:62rem;margin:0 auto;padding:2rem 1rem 3rem;}
    .stage{background:#000;border-radius:8px;overflow:hidden;box-shadow:0 6px 24px rgba(0,0,0,.18);}
    video{display:block;width:100%;height:auto;}
    .dl{font-size:.9rem;color:var(--text-light);text-align:center;margin:.7rem 0 2rem;}
    .dl a{color:var(--water);}
    h2{font-family:'Libre Baskerville',serif;font-size:1.3rem;color:var(--slate);
       margin:2rem 0 .6rem;padding-bottom:.3rem;border-bottom:1px solid var(--border);}
    p{margin:.7rem 0;} ul{margin:.6rem 0 .6rem 1.3rem;} li{margin:.35rem 0;}
    .note{background:var(--sand-dark);border-left:4px solid var(--dune);border-radius:4px;
          padding:1rem 1.2rem;margin:1.4rem 0;}
    .note strong{color:var(--pine);}
    .unchecked{font-size:.9rem;color:var(--text-light);border:1px dashed var(--border);
               border-radius:4px;padding:.7rem 1rem;margin:1.2rem 0;}
    footer{border-top:1px solid var(--border);margin-top:2.5rem;padding:1.4rem 1rem;
           text-align:center;color:var(--text-light);font-size:.88rem;}
    @media(max-width:520px){header h1{font-size:1.45rem;}}
"""

TEMPLATE = """<!DOCTYPE html>
<html lang="{lang}">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title_tag}</title>
  <meta name="description" content="{description}">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Libre+Baskerville:ital,wght@0,400;0,700;1,400&family=Source+Sans+3:wght@300;400;600&display=swap" rel="stylesheet">
  <style>{style}  </style>
</head>
<body>
  <header>
    <h1>{h1}</h1>
    <p>{strap}</p>
    <p class="lang">{lang_line}</p>
    <a class="back" href="index.html">&larr; {back}</a>
  </header>

  <main>
    <div class="stage">
      <video controls preload="none" playsinline
             poster="{poster}">
        <source src="{mp4}" type="video/mp4">
        {no_video}
        <a href="{mp4}">{download_short}</a>.
      </video>
    </div>
    <p class="dl"><a href="{mp4}">{download}</a></p>
{unchecked}
    <div class="note">
      {note}
    </div>

    <h2>{h_read}</h2>
    <ul>
{read_items}
    </ul>

    <h2>{h_made}</h2>
    <p>{made_lead}</p>
    <ul>
{made_items}
    </ul>

    <h2>{h_before}</h2>
    <p>{before}</p>

    <h2>{h_big}</h2>
    <p>{big}</p>
  </main>

  <footer>
    {footer} &middot;
    <a href="index.html" style="color:var(--water);">{home}</a>
  </footer>
</body>
</html>
"""

LANG_NAMES = {"en": "English", "cy": "Cymraeg", "pl": "Polski"}
PAGE_NAME = {"en": "hindcast_film.html", "cy": "hindcast_film_cy.html", "pl": "hindcast_film_pl.html"}

PAGES = {
    "en": dict(
        title_tag="Century hindcast film — Newborough Warren",
        description="A film of how wet the dune slacks of Newborough Warren would have been, month by month, 1930–2026, under a century of weather — the reserve as it stands today.",
        h1="Newborough Warren under a century of weather",
        strap="How wet the dune slacks would have been, month by month, from 1930 to 2026 — if the reserve as it stands today had lived through the weather of each of those years.",
        back="Back to the research home",
        no_video="Your browser cannot play this video.",
        download_short="Download the film (MP4)",
        download=f"Download the film (MP4, ~{MP4_MB}&nbsp;MB)",
        unchecked="",
        note=("<strong>Only the warren is modelled, not the forest.</strong> Everything here is about the open\n"
              "      dune slacks of Newborough Warren — the study area outlined on the map. The planted forest beside\n"
              "      them is not part of the model and is not assessed; the absence of yellow and blue cells does not\n"
              "      imply an absence of flooding, only that it has not been modelled. The map covers the warren study\n"
              "      area only (307&nbsp;hectares of slack floor); blank ground outside the outline means not assessed,\n"
              "      not dry."),
        h_read="How to read the film",
        read_items=[
            "<strong>Yellow</strong> is wet floor: saturated ground, or a thin sheet of water hidden in the grass.",
            "<strong>Blue</strong> is open water: pools you could see from the air.",
            "The title gives the total of each across the study area, in hectares.",
            "The line at the bottom is the water table — how far below or above the ground the groundwater\n"
            "          sits, averaged over the reserve's monitoring wells. The red marker is where the film has got\n"
            "          to; the clock runs at three seconds a year, and between one month's reading and the next the\n"
            "          map is drawn at levels in between, so the water rises and drains smoothly.",
        ],
        h_made="How it was made",
        made_lead="Three things joined together:",
        made_items=[
            "<strong>A weather-driven groundwater model.</strong> Since 2005 the reserve's dipwells have\n"
            "          been read monthly, and from them a simple rule was learned for how the water table rises with\n"
            "          rain and falls with evaporation and drainage. RAF Valley has kept weather records since 1930,\n"
            "          so the rule can be run through the whole century, steered by nothing but the weather. Where the\n"
            "          wells exist, the model's water table is corrected to match them.",
            "<strong>Satellite pictures.</strong> Sentinel-2 has photographed the warren every few days since\n"
            "          2016 in 10&nbsp;m squares. In the near-infrared, water is dark and grass is bright, so a wet\n"
            "          slack floor is a dark patch. Counting the dark squares in 43 clear winter scenes and comparing\n"
            "          with the water table gives two smooth curves — one for open water, one for wet floor.",
            "<strong>Where the water goes.</strong> Each 10&nbsp;m square has its own history in those\n"
            "          pictures, so we know the level at which it usually turns dark. The film lights each square when\n"
            "          the model reaches that level: <em>where</em> the colours appear was learned from the satellite,\n"
            "          <em>when</em> is the model.",
        ],
        h_before="Please read this before watching",
        before=("It is today's warren, not the warren of the time. The rules were learned from 2005–2026 and the\n"
                "       ground is the 2023 survey, with Newborough Forest at its present size. The forest was only planted\n"
                "       between 1947 and 1965, and a forest lowers the water table around it — in 1939 there was no forest.\n"
                "       The film answers a what-if: what the reserve <em>as it is now</em> would have done under that\n"
                "       weather, not what actually happened. It is an illustration of the area–level relationship, not a\n"
                "       flood map."),
        h_big="The biggest floods go beyond anything measured",
        big=("The wettest spring on record was 2021. In some months — 1939, 1959, 1961–62 and 2000–01 — the model\n"
             "       pushes the water table higher than that, above the level the curves were fitted to. No satellite\n"
             "       picture has seen the warren that wet, so those months are marked <em>beyond the record</em>: the\n"
             "       totals are the curves run past the end of the data, and the rest of the slack floor turns pale\n"
             "       orange — wetter than anything on record, where exactly we cannot say. The honest claim for those\n"
             "       winters is that they were bigger than 2021, nothing finer."),
        footer="Newborough Warren hydrology study, 2026 &middot; Martin Hollingham",
        home="research home",
    ),
    "cy": dict(
        title_tag="Ffilm hindcast y ganrif — Tywyn Niwbwrch",
        description="Ffilm o ba mor wlyb y byddai llaciau twyni Tywyn Niwbwrch wedi bod, fis wrth fis, 1930–2026, dan ganrif o dywydd — y warchodfa fel y saif heddiw.",
        h1="Tywyn Niwbwrch dan ganrif o dywydd",
        strap="Pa mor wlyb y byddai llaciau'r twyni wedi bod, fis wrth fis, o 1930 hyd 2026 — pe bai'r warchodfa fel y saif heddiw wedi byw drwy dywydd pob un o'r blynyddoedd hynny.",
        back="Yn ôl i hafan yr ymchwil",
        no_video="Ni all eich porwr chwarae'r fideo hwn.",
        download_short="Lawrlwytho'r ffilm (MP4)",
        download=f"Lawrlwytho'r ffilm (MP4, ~{MP4_MB}&nbsp;MB)",
        unchecked=("Cyfieithiad gan yr awdur a'i gynorthwyydd yw'r fersiwn Gymraeg hon, ac nid yw eto wedi'i "
                   "gwirio gan siaradwr Cymraeg. Mae'r Saesneg yn aros yn fersiwn awdurdodol; byddem yn "
                   "croesawu cywiriadau."),
        note=("<strong>Dim ond y tywyn a fodelir, nid y goedwig.</strong> Mae popeth yma'n ymwneud â llaciau twyni\n"
              "      agored Tywyn Niwbwrch — ardal yr astudiaeth a amlinellir ar y map. Nid yw'r goedwig a blannwyd\n"
              "      wrth eu hymyl yn rhan o'r model ac nid asesir hi; nid yw absenoldeb celloedd melyn a glas yn\n"
              "      golygu absenoldeb llifogydd, dim ond nad yw wedi'i fodelu. Mae'r map yn cwmpasu ardal astudiaeth\n"
              "      y tywyn yn unig (307&nbsp;hectar o lawr llaciau); mae tir gwag y tu allan i'r amlinell yn golygu\n"
              "      heb ei asesu, nid sych."),
        h_read="Sut i ddarllen y ffilm",
        read_items=[
            "<strong>Melyn</strong> yw llawr gwlyb: tir dirlawn, neu haen denau o ddŵr wedi'i chuddio yn y glaswellt.",
            "<strong>Glas</strong> yw dŵr agored: pyllau y gallech eu gweld o'r awyr.",
            "Mae'r teitl yn rhoi cyfanswm pob un ar draws ardal yr astudiaeth, mewn hectarau.",
            "Y llinell ar y gwaelod yw lefel y dŵr daear — pa mor bell islaw neu uwchlaw'r ddaear y saif y\n"
            "          dŵr daear, ar gyfartaledd dros ffynhonnau monitro'r warchodfa. Y marciwr coch yw lle mae'r\n"
            "          ffilm wedi cyrraedd; mae'r cloc yn rhedeg ar dair eiliad y flwyddyn, a rhwng darlleniad un mis\n"
            "          a'r nesaf tynnir y map ar lefelau rhyngddynt, fel bod y dŵr yn codi ac yn draenio'n esmwyth.",
        ],
        h_made="Sut y'i gwnaed",
        made_lead="Tri pheth wedi'u huno:",
        made_items=[
            "<strong>Model dŵr daear a yrrir gan y tywydd.</strong> Er 2005 darllenwyd ffynhonnau monitro'r\n"
            "          warchodfa bob mis, ac ohonynt dysgwyd rheol syml ar gyfer sut mae lefel y dŵr daear yn codi\n"
            "          gyda glaw ac yn disgyn gydag anweddiad a draeniad. Mae RAF y Fali wedi cadw cofnodion tywydd er\n"
            "          1930, felly gellir rhedeg y rheol drwy'r ganrif gyfan, wedi'i llywio gan ddim ond y tywydd. Lle\n"
            "          mae'r ffynhonnau'n bodoli, cywirir lefel dŵr daear y model i gyd-fynd â hwy.",
            "<strong>Lluniau lloeren.</strong> Mae Sentinel-2 wedi tynnu llun o'r tywyn bob ychydig ddyddiau er\n"
            "          2016 mewn sgwariau 10&nbsp;m. Yn yr isgoch agos, mae dŵr yn dywyll a glaswellt yn olau, felly\n"
            "          darn tywyll yw llawr llac gwlyb. Mae cyfrif y sgwariau tywyll mewn 43 golygfa aeaf glir a'u\n"
            "          cymharu â lefel y dŵr daear yn rhoi dwy gromlin esmwyth — un ar gyfer dŵr agored, un ar gyfer\n"
            "          llawr gwlyb.",
            "<strong>I ble'r â'r dŵr.</strong> Mae gan bob sgwâr 10&nbsp;m ei hanes ei hun yn y lluniau hynny,\n"
            "          felly gwyddom y lefel y mae fel arfer yn troi'n dywyll arni. Mae'r ffilm yn goleuo pob sgwâr\n"
            "          pan fo'r model yn cyrraedd y lefel honno: dysgwyd <em>ble</em> y mae'r lliwiau'n ymddangos o'r\n"
            "          lloeren, y model yw <em>pryd</em>.",
        ],
        h_before="Darllenwch hyn cyn gwylio",
        before=("Tywyn heddiw ydyw, nid tywyn y cyfnod. Dysgwyd y rheolau o 2005–2026 ac arolwg 2023 yw'r tir, â\n"
                "       Choedwig Niwbwrch ar ei maint presennol. Dim ond rhwng 1947 a 1965 y plannwyd y goedwig, ac mae\n"
                "       coedwig yn gostwng lefel y dŵr daear o'i chwmpas — yn 1939 nid oedd coedwig. Mae'r ffilm yn ateb\n"
                "       beth-petai: beth fyddai'r warchodfa <em>fel y mae yn awr</em> wedi'i wneud dan y tywydd hwnnw, nid\n"
                "       yr hyn a ddigwyddodd mewn gwirionedd. Darlun o'r berthynas rhwng arwynebedd a lefel ydyw, nid\n"
                "       map llifogydd."),
        h_big="Mae'r llifogydd mwyaf y tu hwnt i unrhyw beth a fesurwyd",
        big=("Y gwanwyn gwlypaf ar gofnod oedd 2021. Mewn rhai misoedd — 1939, 1959, 1961–62 a 2000–01 — mae'r\n"
             "       model yn gwthio lefel y dŵr daear yn uwch na hynny, uwchlaw'r lefel y ffitiwyd y cromliniau iddi.\n"
             "       Nid oes llun lloeren wedi gweld y tywyn mor wlyb â hynny, felly nodir y misoedd hynny <em>y tu hwnt\n"
             "       i'r cofnod</em>: y cyfansymiau yw'r cromliniau wedi'u rhedeg heibio diwedd y data, ac mae gweddill\n"
             "       llawr y llaciau'n troi'n oren golau — gwlypach na dim ar gofnod, ond ble yn union, ni allwn ddweud.\n"
             "       Yr honiad gonest am y gaeafau hynny yw eu bod yn fwy na 2021, a dim manylach."),
        footer="Astudiaeth hydroleg Tywyn Niwbwrch, 2026 &middot; Martin Hollingham",
        home="hafan yr ymchwil",
    ),
    "pl": dict(
        title_tag="Film hindcastowy stulecia — Newborough Warren",
        description="Film o tym, jak mokre byłyby obniżenia międzywydmowe Newborough Warren, miesiąc po miesiącu, 1930–2026, pod stuleciem pogody — rezerwat w dzisiejszym kształcie.",
        h1="Newborough Warren pod stuleciem pogody",
        strap="Jak mokre byłyby obniżenia międzywydmowe, miesiąc po miesiącu, od 1930 do 2026 roku — gdyby rezerwat w dzisiejszym kształcie przeżył pogodę każdego z tych lat.",
        back="Powrót do strony głównej badań",
        no_video="Twoja przeglądarka nie może odtworzyć tego filmu.",
        download_short="Pobierz film (MP4)",
        download=f"Pobierz film (MP4, ok. {MP4_MB}&nbsp;MB)",
        unchecked=("Ta polska wersja jest tłumaczeniem autora i jego asystenta i nie została jeszcze sprawdzona "
                   "przez rodzimego użytkownika języka. Wersja angielska pozostaje miarodajna; poprawki są mile "
                   "widziane."),
        note=("<strong>Modelowane są tylko wydmy, nie las.</strong> Wszystko tutaj dotyczy otwartych obniżeń\n"
              "      międzywydmowych Newborough Warren — obszaru badań obrysowanego na mapie. Posadzony obok las nie\n"
              "      jest częścią modelu i nie jest oceniany; brak żółtych i niebieskich komórek nie oznacza braku\n"
              "      zalania, a jedynie to, że nie zostało zamodelowane. Mapa obejmuje tylko obszar badań na wydmach\n"
              "      (307&nbsp;hektarów dna obniżeń); puste miejsce poza obrysem znaczy „nieoceniane”, nie „suche”."),
        h_read="Jak czytać film",
        read_items=[
            "<strong>Żółty</strong> to mokre dno: grunt nasycony wodą albo cienka warstwa wody ukryta w trawie.",
            "<strong>Niebieski</strong> to otwarta woda: rozlewiska widoczne z powietrza.",
            "Tytuł podaje sumę każdej z nich na obszarze badań, w hektarach.",
            "Linia u dołu to zwierciadło wód gruntowych — jak głęboko pod gruntem lub jak wysoko nad nim stoi\n"
            "          woda gruntowa, uśrednione po piezometrach rezerwatu. Czerwony znacznik pokazuje, dokąd film\n"
            "          doszedł; zegar biegnie trzy sekundy na rok, a między odczytem jednego miesiąca a następnego\n"
            "          mapa jest rysowana dla poziomów pośrednich, więc woda podnosi się i opada płynnie.",
        ],
        h_made="Jak go zrobiono",
        made_lead="Trzy rzeczy połączone razem:",
        made_items=[
            "<strong>Model wód gruntowych sterowany pogodą.</strong> Od 2005 roku piezometry rezerwatu są\n"
            "          odczytywane co miesiąc i z nich wyprowadzono prostą regułę, jak zwierciadło podnosi się z\n"
            "          opadem i opada z parowaniem i drenażem. RAF Valley prowadzi zapis pogody od 1930 roku, więc\n"
            "          regułę można przepuścić przez całe stulecie, sterowaną wyłącznie pogodą. Tam, gdzie istnieją\n"
            "          piezometry, zwierciadło modelu jest korygowane do ich pomiarów.",
            "<strong>Zdjęcia satelitarne.</strong> Sentinel-2 fotografuje wydmy co kilka dni od 2016 roku w\n"
            "          kwadratach 10&nbsp;m. W bliskiej podczerwieni woda jest ciemna, a trawa jasna, więc mokre dno\n"
            "          obniżenia to ciemna plama. Zliczenie ciemnych kwadratów na 43 bezchmurnych zimowych scenach i\n"
            "          porównanie ze zwierciadłem daje dwie gładkie krzywe — jedną dla otwartej wody, drugą dla mokrego\n"
            "          dna.",
            "<strong>Dokąd idzie woda.</strong> Każdy kwadrat 10&nbsp;m ma na tych zdjęciach własną historię, więc\n"
            "          wiemy, przy jakim poziomie zwykle ciemnieje. Film zapala każdy kwadrat, gdy model sięga tego\n"
            "          poziomu: <em>gdzie</em> pojawiają się barwy, nauczono się z satelity, <em>kiedy</em> — to model.",
        ],
        h_before="Przeczytaj to przed obejrzeniem",
        before=("To dzisiejsze wydmy, nie wydmy tamtych czasów. Reguł nauczono się na latach 2005–2026, a grunt\n"
                "       pochodzi z pomiarów z 2023 roku, z lasem Newborough w obecnym rozmiarze. Las posadzono dopiero w\n"
                "       latach 1947–1965, a las obniża wokół siebie zwierciadło wód gruntowych — w 1939 roku lasu nie\n"
                "       było. Film odpowiada na pytanie „co by było, gdyby”: co zrobiłby rezerwat <em>taki, jaki jest\n"
                "       teraz</em>, pod tamtą pogodą, a nie co naprawdę się stało. To ilustracja związku między\n"
                "       powierzchnią a poziomem, nie mapa powodziowa."),
        h_big="Największe powodzie wykraczają poza wszystko, co zmierzono",
        big=("Najmokrzejszą wiosną w zapisie była wiosna 2021 roku. W niektórych miesiącach — 1939, 1959, 1961–62\n"
             "       i 2000–01 — model wypycha zwierciadło wyżej, powyżej poziomu, do którego dopasowano krzywe. Żadne\n"
             "       zdjęcie satelitarne nie widziało wydm tak mokrych, więc te miesiące są oznaczone <em>poza\n"
             "       zapisem</em>: sumy to krzywe przedłużone poza koniec danych, a reszta dna obniżeń przybiera blady\n"
             "       pomarańcz — mokrzej niż cokolwiek w zapisie, gdzie dokładnie, nie umiemy powiedzieć. Uczciwe\n"
             "       twierdzenie o tych zimach brzmi: były większe niż 2021, nic ponadto."),
        footer="Studium hydrologiczne Newborough Warren, 2026 &middot; Martin Hollingham",
        home="strona główna badań",
    ),
}


def lang_line(lang: str) -> str:
    parts = []
    for l_ in FILM_LANGS:
        name = LANG_NAMES[l_]
        parts.append(f"<strong>{name}</strong>" if l_ == lang else f'<a href="{PAGE_NAME[l_]}" hreflang="{l_}">{name}</a>')
    return " &middot; ".join(parts)


def page(lang: str) -> str:
    d = dict(PAGES[lang])
    mp4 = out_47_lang(OUT_47_PRESENTATION, lang).relative_to(ROOT).as_posix()
    poster = out_47_lang(out_47_still(STILL_MONTH), lang).relative_to(ROOT).as_posix()
    d["read_items"] = "\n".join(f"      <li>{x}</li>" for x in d["read_items"])
    d["made_items"] = "\n".join(f"      <li>{x}</li>" for x in d["made_items"])
    d["unchecked"] = (f'\n    <p class="unchecked">{d["unchecked"]}</p>\n' if d["unchecked"] else "")
    return TEMPLATE.format(lang=lang, style=STYLE, mp4=mp4, poster=poster, lang_line=lang_line(lang), **d)


def main() -> int:
    check = "--check" in sys.argv
    rc = 0
    for lang in FILM_LANGS:
        target = ROOT / PAGE_NAME[lang]
        html = page(lang)
        if " " in html:
            print(f"  FAULT {target.name}: em space"); rc = 1
        if check:
            if not target.exists() or target.read_text(encoding="utf-8") != html:
                print(f"  STALE {target.name}: regenerate with tools/build_film_pages.py"); rc = 1
        else:
            target.write_text(html, encoding="utf-8")
            print(f"  wrote {target.name} ({len(html.splitlines())} lines)")
    if check and rc == 0:
        print(f"  build_film_pages: OK — {len(FILM_LANGS)} pages current")
    return rc


if __name__ == "__main__":
    sys.exit(main())
