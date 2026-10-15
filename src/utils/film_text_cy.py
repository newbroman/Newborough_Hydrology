"""
film_text_cy.py - geiriau'r ffilm hindcast, Cymraeg.

The Welsh table (Script 47 1.9.0). Every key of film_text_en.py, in the same order; the
templates take the same fields. Written by the 2026-10-13 session in formal written Welsh
and NOT yet checked by a Welsh speaker - the register row says so, and the page says so,
until one has read outputs/47_hindcast_film/47_05_frame_caveats_cy.txt. Terms are fixed in
NRG_spec_script47_v1_9_languages_2026-10-13: Tywyn Niwbwrch, Ynys Môn, Coedwig Niwbwrch,
RAF y Fali, llaciau twyni, lefel y dŵr daear, llawr gwlyb, dŵr agored, ardal yr astudiaeth,
y tu hwnt i'r cofnod, ffynhonnau monitro.
"""
from __future__ import annotations

__version__ = "1.0.1"  # Hollingham (2026) - 2026-10-15. says_p1 "several times" -> "about twice" (the 1960s
#   carry 1.8-2.4x the other decades' mean winter open water in 47_01); more_p4 (the D-226 datum paragraph)
#   removed - the film keeps one straight story (Martin 2026-10-15: "keep the modeling simple").
# 1.0.0  Hollingham (2026) - 2026-10-13. First Welsh table; unchecked by a Welsh speaker.

NAME = "Cymraeg"
MONTHS = ["Ionawr", "Chwefror", "Mawrth", "Ebrill", "Mai", "Mehefin", "Gorffennaf", "Awst",
          "Medi", "Hydref", "Tachwedd", "Rhagfyr"]
MONTHS_SHORT = ["Ion", "Chwe", "Maw", "Ebr", "Mai", "Meh", "Gorff", "Awst", "Medi", "Hyd",
                "Tach", "Rhag"]

T = {
    # ---- y teitl, y pennawd, y llinell awdur, y clip agoriadol -------------------------
    "title": "Tywyn Niwbwrch dan ganrif o dywydd",
    "subtitle": "Gwarchodfa heddiw dan dywydd pob mis er 1930: beth-petai, nid hanes",
    "byline": "Astudiaeth hydroleg Tywyn Niwbwrch, 2026 · Martin Hollingham",
    "open_clip_label": "Y degawd diwethaf",
    "contents": "Cynnwys",
    "chapter_opening": "Agoriad",
    "chapter_clip": "{label}: {y0}–{y1}",
    "chapter_title": "Teitl a chynnwys",
    "chapter_film": "Y ffilm: {y0}–{y1}",
    "slide_count": "{a} / {b}",

    # ---- y ffrâm: y darlleniad, yr hydrograff, y capsiwn ---------------------------------
    "readout_water_table": "lefel y dŵr daear",
    "readout_open_water": "dŵr agored",
    "readout_wet_floor": "llawr gwlyb",
    "study": "ardal yr astudiaeth {floor_ha:.0f} ha",
    "beyond": "Y TU HWNT I'R COFNOD",
    "hydro_ylabel": "lefel y dŵr daear, m\n(0 = y ddaear)",
    "era_before": "cyn y ffynhonnau: y model yn unig, wedi'i gywiro i flynyddoedd y ffynhonnau",
    "era_wells": "ffynhonnau wedi'u mesur",
    "era_above": "uwchlaw llifogydd 2021: y tu hwnt i unrhyw beth a fesurwyd",
    "arrival_wet_floor": "llawr gwlyb o",
    "arrival_open_water": "dŵr agored o",
    "caption": (
        "Gwarchodfa heddiw dan dywydd\npob mis a fu. Nid yr hyn a ddigwyddodd\n"
        "mewn gwirionedd: beth-petai. Cywirir lefel dŵr\ndaear y model i gyd-fynd â'r ffynhonnau dros 2005–2026.\n\n"
        "Glas: dŵr agored.  Melyn: llawr gwlyb.\nSgwariau 10 m o luniau lloeren, 2016–2026.\n"
        "Nid map llifogydd: mae pyllau bach ac ymylon\nyn rhy fach i'w dangos.\n\n"
        "Yr amlinell yw ardal yr astudiaeth: llawr llaciau'r\ntywyn. Nid asesir dim y tu allan iddi.\n\n"
        "Daw'r cyfansymiau yn y teitl o'r lefel dŵr daear\nwedi'i chywiro; mae dŵr agored yn gywir i\n"
        "ffactor o {s_ow:.1f}, llawr gwlyb i tua {wf_pct:.0f} %."),
    "caption_beyond_head": "MAE'R MIS HWN Y TU HWNT I'R COFNOD.",
    "caption_beyond": (
        "\n\nMAE'R MIS HWN Y TU HWNT I'R COFNOD.\nMae lefel y dŵr daear uwchlaw llifogydd 2021,\n"
        "y gwlypaf a fesurwyd erioed. Y cyfansymiau yw'r\ncromliniau wedi'u rhedeg heibio diwedd y data;\n"
        "oren golau yw llawr llaciau na welwyd erioed\nyn wlyb — gwlypach na dim ar gofnod, ond ble\n"
        "yn union, ni wyddys."),

    # ---- y sleid gymharu a'r mân-luniau ----------------------------------------------------
    "compare_left": "Sentinel-2, gwir liw",
    "compare_right": "Y ffilm, yr un mis",
    "compare_row": "{when} · model {lvl} m · {aw:.0f} ha dŵr agored, {af:.0f} ha llawr gwlyb",
    "thumb_label": "{when} · ffynhonnau {lvl} m",
    "rel_same": "y {kind}",
    "rel_other": "{n} mis {dir} {kind} {when}",
    "peak": "brig",
    "trough": "cafn",
    "after": "ar ôl",
    "before": "cyn",

    # ---- siart rhediad rhydd y ffilm ei hun (47_06) ------------------------------------------
    "fr_label_model": "y model: tywydd yn unig, yn rhedeg er 1930",
    "fr_label_model_stats": " (R² {r2:.2f}, {bias} cm ar gyfartaledd)",
    "fr_label_wells": "y ffynhonnau monitro: canolrif y rhwydwaith cyfeirio (misoedd â {n}+ ffynnon)",
    "fr_ylabel": "lefel y dŵr daear, m (0 = y ddaear)",
    "fr_title": "Lefel dŵr daear y tywyn: y model yn erbyn y ffynhonnau",

    # ---- cyfeiriadau at ffigurau yn nhroed y sleidiau --------------------------------------
    "foot_none": "Ffigur yr adroddiad",
    "foot_one": "Ffigur {num} yr adroddiad",
    "foot_one_section": ", adran {sec}",
    "foot_many": "Ffigurau'r adroddiad ",
    "foot_many_section": " (adran {sec})",
    "foot_and": " a ",
    "foot_model_run": " · y model yn erbyn y ffynhonnau: rhediad y ffilm hon ei hun",
    "cop": "Yn cynnwys data Copernicus Sentinel wedi'i addasu",
    "cop_years": "Yn cynnwys data Copernicus Sentinel wedi'i addasu {years}",

    # ---- sleidiau'r dull -------------------------------------------------------------------
    "f4_number": "Ffigur {n4}",
    "f4_none": "Y ffigur hinsawdd",
    "low_phrase": ", ar gyfartaledd {cm:.0f} cm yn rhy {dir}",
    "low": "isel",
    "high": "uchel",
    "m1_title": "1.  Model dŵr daear a yrrir gan y tywydd",
    "m1_p1": (
        "{f4} (chwith) yw'r tywydd a lefel y dŵr daear gyda'i gilydd, 2005–2026. (a) Glaw, fis "
        "wrth fis, â'i gyfartaledd hirdymor yn llinell doredig. (b) Anweddiad, sy'n cyrraedd ei "
        "uchafbwynt bob haf. (c) Cydbwysedd rhedegog glaw llai anweddiad: mae'n dringo drwy "
        "rediadau gwlyb o fisoedd ac yn disgyn drwy rai sych. (d) Lefel y dŵr daear, ar "
        "gyfartaledd dros ffynhonnau monitro'r warchodfa, â'r gwasgariad rhwng ffynhonnau wedi'i "
        "gysgodi. Mae paneli (c) a (d) yn codi ac yn disgyn gyda'i gilydd: dyna'r cyswllt y "
        "codwyd y model arno."),
    "m1_p2": (
        "Ohono dysgodd yr astudiaeth reol fisol syml: mae lefel y dŵr daear yn codi gyda glaw y "
        "mis, yn disgyn gyda'i anweddiad, ac yn draenio'n ôl yn gymesur â pha mor uchel y saif."),
    "m1_p3": (
        "Y siart uchod ar y dde yw'r prawf y mae'r ffilm hon yn dibynnu arno. Y llinell las yw'r "
        "model, wedi'i redeg ar ddim ond tywydd RAF y Fali er 1930 heb unrhyw ddarlleniad ffynnon "
        "i'w gywiro; y llinell ddu yw'r hyn a fesurodd y ffynhonnau monitro. Mae'r model yn dilyn "
        "blynyddoedd gwlyb a sych y tywyn{low}: y gogwydd y mae'r sleid nesaf yn ei dynnu."),
    "m2_title": "Cywiro'r model i'r ffynhonnau",
    "m2_p1": (
        "O'i redeg yn rhydd am ganrif, mae'r model yn drifftio: nid oes ffynhonnau i'w ddal. Felly "
        "fe'i cywirir lle mae'r ffynhonnau'n bodoli. Dros 2005–2026 rhestrir misoedd y model yn "
        "nhrefn eu maint yn erbyn y misoedd a fesurwyd, a rhoddir yn lle pob lefel a fodelwyd y "
        "lefel a fesurwyd o'r un safle yn y drefn."),
    "m2_p2": (
        "Trefn y misoedd gwlyb a sych yw trefn y model ei hun; dim ond tynnu ei ogwydd y mae'r "
        "cywiriad. Yna cludir yr un cywiriad yn ôl drwy'r blynyddoedd cyn y ffynhonnau."),
    "m3_title": "2.  Lluniau lloeren: y calibradu cyntaf",
    "m3_p1": (
        "Mae Sentinel-2 wedi tynnu llun o'r tywyn bob ychydig ddyddiau er 2016, mewn sgwariau "
        "10 m. Yn yr isgoch agos, mae dŵr yn ddu a glaswellt yn olau, felly mae llawr llac gwlyb "
        "yn ymddangos fel darn tywyll. Roedd {n} llun gaeaf yn glir o gwmwl."),
    "m3_p2": (
        "Ym mhob un cyfrifir y sgwariau tywyll ar lawr y llaciau, wedi'u rhannu'n ddŵr agored "
        "(y tywyllaf) a llawr gwlyb, a'u gosod yn erbyn y lefel dŵr daear a fesurodd y ffynhonnau "
        "monitro yn yr un mis. Un llun yw pob pâr o bwyntiau ar y ffigur. Dangosir pedwar ohonynt "
        "isod yn y band isgoch agos hwnnw, o'r sychaf i'r gwlypaf, pob un wedi'i raddio i "
        "ddisgleirdeb ei lawr llac ei hun fel y mae'r dull yn ei ddarllen; mae pob llinell yn "
        "arwain at ei phwyntiau."),
    "m3_p3": (
        "Mae'r pwyntiau'n disgyn ar ddwy gromlin esmwyth. Mae llawr gwlyb yn tyfu'n araf wrth i "
        "lefel y dŵr daear godi; erys dŵr agored bron yn ddim nes bod y dŵr yn agos at yr wyneb, "
        "yna'n dringo'n serth. Y cromliniau hyn sy'n troi lefel dŵr daear y ffilm yn hectarau ei "
        "theitl."),
    "m3_p4": (
        "Fe'u ffitiwyd rhwng {lo_s} m a {hi_s} m, yr ystod a welodd y lluniau. Uwchlaw hynny, "
        "dywed y ffilm Y TU HWNT I'R COFNOD."),
    "m4_title": "Y gwiriad: y model yn erbyn y lloeren",
    "m4_p1": (
        "Cyn ymddiried y cromliniau i'r model, fe'u profir ag ef. Yma gyrrir y cromliniau gan "
        "lefel dŵr daear y model yn lle'r ffynhonnau, a chymharir yr arwynebedd a ragfynegant, "
        "fis wrth fis, â'r arwynebedd a fesurodd y lloeren mewn gwirionedd."),
    "m4_p2": (
        "Nid yw'r lloeren yn rhan o'r model, felly prawf annibynnol o lefel y dŵr daear ei hun yw "
        "hwn, nid o'r cromliniau'n unig. Mae'r un pedwar llun isgoch agos isod; mae pob llinell yn "
        "arwain at ei mis ar y panel uchaf ac yn enwi'r brig neu'r cafn y perthyn iddo."),
    "m4_p3": (
        "Atgynhyrchir llawr gwlyb yn agos. Atgynhyrchir dŵr agored, sy'n ymddangos yn sydyn wrth "
        "i'r dŵr gyrraedd yr wyneb, yn llai da: mae gwall bach yn lefel y dŵr daear yn gwneud un "
        "mawr yn arwynebedd y pyllau. Dyna pam mai glas y ffilm yw'r lliw llai sicr."),
    "m5_title": "3.  I ble'r â'r dŵr: yr ail galibradu",
    "m5_p1": (
        "Dywed y cromliniau faint o'r llawr sy'n wlyb; ni ddywedant ble. Ar gyfer hynny, "
        "defnyddir hanes pob sgwâr 10 m ei hun yn y lluniau: y lefel dŵr daear y darllenodd "
        "lawr gwlyb arni gyntaf (a, y map uchaf) a dŵr agored gyntaf (b, y map isaf)."),
    "m5_p2": (
        "Y pantiau isaf sy'n newid gyntaf, yr ymylon uwch olaf. Ni newidiodd sgwariau llwyd "
        "erioed o fewn yr ystod a welodd y lluniau, a gadewir y goedwig allan am mai'r canopi, "
        "nid y ddaear, a wêl y lloeren dan goed."),
    "m5_p3": (
        "Mae'r ffilm yn goleuo pob sgwâr pan fo lefel dŵr daear y model yn cyrraedd ei lefel. "
        "Dysgwyd BLE y mae'r lliwiau'n ymddangos o'r lloeren; y model yw PRYD."),
    "m6_title": "Sut olwg sydd ar y tywyn o'r gofod",
    "m6_p1": (
        "Y sychaf a'r gwlypaf o'r pedwar llun hynny, pob un wrth ymyl map y ffilm ei hun o'r un "
        "mis."),
    "m6_p2": (
        "Yn y lluniau, lloriau'r llaciau dan ddŵr yw'r darnau tywyll rhwng y twyni golau. Mae'r "
        "ffilm yn goleuo ei melyn a'i glas yn yr un pantiau wrth i'w lefel dŵr daear godi."),
    "m6_p3": (
        "Darlun yw hwn, nid prawf. Dysgwyd ble y mae'r lliwiau'n ymddangos o'r union luniau hyn, "
        "felly mae peth o'r tebygrwydd wedi'i adeiladu i mewn. Y prawf annibynnol yw'r gwiriad "
        "ddwy sleid yn ôl, lle nad yw'r lloeren yn rhan o'r model."),
    "m6_foot": "{cop} {y0}, {y1}",

    # ---- y sleidiau cyn y ffilm -------------------------------------------------------------
    "about_title": "Am y ffilm hon",
    "about_p1": (
        "Ffilm o ba mor wlyb y byddai llaciau'r twyni wedi bod, fis wrth fis, o 1930 hyd 2026 — "
        "pe bai'r warchodfa fel y saif heddiw wedi byw drwy dywydd pob un o'r blynyddoedd hynny."),
    "about_p2": (
        "Gwarchodfa twyni tywod ar Ynys Môn yw Tywyn Niwbwrch. Rhwng y twyni mae cannoedd o "
        "bantiau isel a elwir yn llaciau. Mewn gaeaf gwlyb mae lefel y dŵr daear yn codi iddynt: "
        "mae'r tir yn gwlychu, mae pyllau'n ymddangos, ac mewn gwanwyn gwlyb iawn saif llaciau "
        "cyfan dan ddŵr."),
    "about_p3": (
        "Dim ond y tywyn a fodelir, nid y goedwig. Mae popeth yma'n ymwneud â llaciau twyni agored "
        "Tywyn Niwbwrch — ardal yr astudiaeth a amlinellir ar y map. Nid yw'r goedwig a blannwyd "
        "wrth eu hymyl yn rhan o'r model ac nid asesir hi; nid yw absenoldeb celloedd melyn a glas "
        "yn golygu absenoldeb llifogydd, ond yn hytrach nad yw wedi'i fodelu."),
    "howto_title": "Sut i ddarllen y ffilm",
    "howto_p1": "MELYN yw llawr gwlyb: tir dirlawn, neu haen denau o ddŵr wedi'i chuddio yn y glaswellt.",
    "howto_p2": "GLAS yw dŵr agored: pyllau y gallech eu gweld o'r awyr.",
    "howto_p3": (
        "Yr amlinell ar y map yw ardal yr astudiaeth — {floor_ha:.0f} hectar o lawr llaciau o "
        "fewn y tywyn. Mae popeth a ddywed y ffilm yn ymwneud â'r tir y tu mewn iddi. Ni aseswyd "
        "tir gwag y tu allan i'r amlinell; nid honiad ydyw ei fod yn sych."),
    "howto_p4": (
        "Mae'r teitl yn rhoi cyfanswm pob un ar draws ardal yr astudiaeth, mewn hectarau (mae "
        "hectar ychydig yn fwy na chae rygbi)."),
    "howto_p5": (
        "Y llinell ar y gwaelod yw lefel y dŵr daear — pa mor bell islaw neu uwchlaw'r ddaear y "
        "saif y dŵr daear, ar gyfartaledd dros ffynhonnau monitro'r warchodfa. Y marciwr coch yw "
        "lle mae'r ffilm wedi cyrraedd. Mae'r cloc yn rhedeg ar dair eiliad y flwyddyn; rhwng "
        "darlleniad un mis a'r nesaf tynnir y map ar lefelau rhyngddynt, fel bod y dŵr yn codi "
        "ac yn draenio'n esmwyth, ond y misoedd yw'r darlleniadau."),
    "howto_p6": (
        "Mae'r sleidiau sy'n dilyn yn dangos sut y'i gwnaed: model dŵr daear, lluniau lloeren a "
        "map o ble'r â'r dŵr, wedi'u huno, pob un wrth ymyl ffigurau'r adroddiad sy'n ei galibradu "
        "ac yn ei brofi."),
    "hear_title": "Yr hyn a glywch",
    "hear_p1": "Gwneir y sain o'r dŵr, fis wrth fis. Nid oes dim ynddi wedi'i recordio.",
    "hear_p2": (
        "Mae cord meddal yn rhedeg drwyddi draw. Tra bo'r misoedd yn chwarae, mae un o'i leisiau'n "
        "chwyddo gyda glaw pob mis, un arall gyda'i anweddiad, a'r uchaf yn agor wrth i lefel y "
        "dŵr daear godi; yn y misoedd y tu hwnt i'r cofnod mae'n crynu."),
    "hear_p3": (
        "Mae cord cyson yn codi gyda lefel y dŵr daear, o dawelwch yn y misoedd sychaf i'w lawn "
        "ar frig y cofnod; uwchlaw'r llinell felen mae seithfed yn ymuno ag ef, ac mae'r cord yn "
        "tynhau wrth i'r tywyn orlifo, gan bwyso tuag at ble mae'r dŵr: i'r dde am ddwyrain y "
        "tywyn, i'r chwith am y gorllewin."),
    "hear_p4": (
        "Mae nodau daliedig yn seinio tra bo lefel y dŵr daear uwchlaw'r llinellau ar y siart ar y "
        "gwaelod: un uwchlaw'r llinell felen, lle mae llawr gwlyb yn ymddangos; un uwch uwchlaw'r "
        "llinell las, lle mae dŵr agored yn ymddangos; a'r uchaf uwchlaw llifogydd 2021."),
    "hear_p5": (
        "Oddi tano, anadl: un nodyn meddal drwy hanner gaeaf pob blwyddyn, tawelwch drwy'r haf, "
        "fel bod blwyddyn yn para tair eiliad."),
    "read_title": "Darllenwch hyn cyn gwylio",
    "read_p1": (
        "Tywyn heddiw ydyw, nid tywyn y cyfnod. Dysgwyd y rheolau o 2005–2026 ac arolwg 2023 yw'r "
        "tir, â Choedwig Niwbwrch ar ei maint presennol. Dim ond rhwng 1947 a 1965 y plannwyd y "
        "goedwig, ac mae coedwig yn gostwng lefel y dŵr daear o'i chwmpas. Yn 1939 nid oedd "
        "coedwig. Mae'r ffilm yn ateb beth-petai — beth fyddai'r warchodfa fel y mae yn awr wedi'i "
        "wneud dan y tywydd hwnnw — nid yr hyn a ddigwyddodd mewn gwirionedd."),
    "read_p2": (
        "Mae'r map yn cwmpasu ardal astudiaeth y tywyn yn unig; mae gwag y tu allan iddi'n golygu "
        "heb ei asesu, nid sych."),
    "read_p3": (
        "Lluniau lloeren: {cop_years}. Daw ffigurau'r adroddiad o astudiaeth hydroleg Tywyn "
        "Niwbwrch."),
    "big_title": "Mae'r llifogydd mwyaf y tu hwnt i unrhyw beth a fesurwyd",
    "big_p1": (
        "Y gwanwyn gwlypaf ar gofnod oedd 2021. Mewn rhai misoedd — 1939, 1959, 1961–62 a 2000–01 — "
        "mae'r model yn gwthio lefel y dŵr daear yn uwch na hynny, uwchlaw'r {hmax:+.2f} m y "
        "ffitiwyd y cromliniau iddo."),
    "big_p2": (
        "Nid oes llun wedi gweld y tywyn felly. Felly nodir y misoedd hynny Y TU HWNT I'R COFNOD, "
        "y cyfansymiau yw'r cromliniau wedi'u rhedeg heibio diwedd y data, ac mae gweddill llawr y "
        "llaciau'n troi'n OREN GOLAU: gwlypach na dim ar gofnod, ond ble yn union, ni allwn ddweud."),
    "big_p3": "Yr honiad gonest am y gaeafau hynny yw eu bod yn fwy na 2021, a dim manylach.",

    # ---- y sleidiau ar ôl y ffilm ----------------------------------------------------------
    "says_title": "Yr hyn a ddywed y ffilm, â'i rybuddion",
    "says_p1": (
        "Y 1960au oedd y degawd gwlyb, â thua dwywaith dŵr agored gaeaf cyffredin yn y degawdau "
        "eraill."),
    "says_p2": (
        "Mae gaeafau 1961–62 a 2000–01 yn sefyll allan fel dwy lifogydd fawr y ganrif, â 1938–39 "
        "a 1958–59 y tu ôl iddynt; 2015–16 oedd y gwlypaf o oes y lloeren ar ôl 2021."),
    "says_p3": (
        "Y 1970au a'r 1990au oedd y degawdau sych, â'r nesaf peth i ddim dŵr agored mewn gaeaf "
        "cyffredin."),
    "says_p4": (
        "Cyfrif y model o'r hyn a wnâi'r tywydd i'r warchodfa fel y saif heddiw yw'r cyfan ohono."),
    "more_title": "Ac ychydig yn rhagor",
    "more_p1": (
        "Nid map llifogydd ydyw. Mae'r sgwariau'n 10 m ar draws; mae ymylon cul, pyllau bach a "
        "haenau tenau dros laswellt yn anweledig ar y maint hwnnw — tua thraean y dŵr mewn "
        "llifogydd mawr. Dim ond i o fewn pump neu ddeg centimetr o lefel dŵr daear y gwyddys yr "
        "eiliad y mae sgwâr yn goleuo."),
    "more_p2": (
        "Mae camgymeriadau'r model yn cario drwodd. Hyd yn oed wedi'i gywiro i'r ffynhonnau, mae'n "
        "atgynhyrchu'r lefel dŵr daear a fesurwyd i tua ugain centimetr, ac mae'n dal i redeg tua "
        "deg centimetr yn rhy isel yn y misoedd gwlypaf. Mae gwall o ddeg centimetr yn newid "
        "arwynebedd y dŵr agored tua'i hanner, am fod pyllau'n ymddangos yn sydyn unwaith y daw'r "
        "dŵr yn agos at yr wyneb. Melyn yw'r lliw mwy sefydlog, yn dda i tua {wf_pct:.0f} %; mae "
        "glas yn gywir i ffactor o {s_ow:.1f}. Y ddwy flynedd gyntaf yw'r model yn ymsefydlu o'i "
        "ddyfaliad cychwynnol."),
    "more_p3": (
        "Y gaeaf sy'n rheoli drwy'r flwyddyn. Daw'r cromliniau o luniau Tachwedd-i-Fawrth; mae "
        "misoedd yr haf yn dangos yr hyn a awgrymai lefel y dŵr daear, nid yr hyn a ddangosai "
        "ffotograff haf."),
    "credits_title": "Cydnabyddiaethau a ffynonellau",
    "credits_p1": "Astudiaeth hydroleg Tywyn Niwbwrch, 2026 — Martin Hollingham.",
    "credits_p2": (
        "Tywydd: cofnod misol RAF y Fali, 1930–2026. Lefel y dŵr daear: rhwydwaith ffynhonnau "
        "monitro'r warchodfa, 2005–2026. Tir: arolwg 2023."),
    "credits_p3": (
        "Delweddau: Copernicus Sentinel-2, 2016–2026, yn rhad ac am ddim ac yn agored dan "
        "drwydded Copernicus. {cop_years}."),
    "credits_p4": (
        "Model, cod a data: github.com/newbroman/Newborough_Hydrology. Cofnodir y dull fel "
        "penderfyniad D-178; mae'r canllaw ysgrifenedig llawn yn cyd-fynd â'r ffilm hon."),
    "credits_p5": (
        "Sain: wedi'i syntheseiddio gan god y ffilm ei hun o'r lefel dŵr daear a'r arwynebeddau a "
        "fodelwyd; dim recordiadau."),
}
