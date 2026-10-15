"""
film_text_pl.py - słowa filmu hindcastowego, polski.

The Polish table (Script 47 1.9.0). Every key of film_text_en.py, in the same order; the
templates take the same fields. Written by the 2026-10-13 session in standard written Polish
and NOT yet checked by a native speaker - the register row says so, and the page says so,
until one has read outputs/47_hindcast_film/47_05_frame_caveats_pl.txt. Terms are fixed in
NRG_spec_script47_v1_9_languages_2026-10-13: Newborough Warren (nazwa własna), Anglesey,
las Newborough, RAF Valley, obniżenia międzywydmowe, zwierciadło wód gruntowych ("wody
gruntowe" w odczycie), mokre dno, otwarta woda, obszar badań, poza zapisem, piezometry.
"""
from __future__ import annotations

__version__ = "1.0.1"  # Hollingham (2026) - 2026-10-15. says_p1 "several times" -> "about twice" (the 1960s
#   carry 1.8-2.4x the other decades' mean winter open water in 47_01); more_p4 (the D-226 datum paragraph)
#   removed - the film keeps one straight story (Martin 2026-10-15: "keep the modeling simple").
# 1.0.0  Hollingham (2026) - 2026-10-13. First Polish table; unchecked by a native speaker.

NAME = "Polski"
MONTHS = ["Styczeń", "Luty", "Marzec", "Kwiecień", "Maj", "Czerwiec", "Lipiec", "Sierpień",
          "Wrzesień", "Październik", "Listopad", "Grudzień"]
MONTHS_SHORT = ["sty", "lut", "mar", "kwi", "maj", "cze", "lip", "sie", "wrz", "paź", "lis", "gru"]

T = {
    # ---- tytuł, podtytuł, autor, klip otwierający ---------------------------------------
    "title": "Newborough Warren pod stuleciem pogody",
    "subtitle": "Dzisiejszy rezerwat pod pogodą każdego miesiąca od 1930 roku: „co by było, gdyby”, nie historia",
    "byline": "Studium hydrologiczne Newborough Warren, 2026 · Martin Hollingham",
    "open_clip_label": "Ostatnia dekada",
    "contents": "Spis treści",
    "chapter_opening": "Otwarcie",
    "chapter_clip": "{label}: {y0}–{y1}",
    "chapter_title": "Tytuł i spis treści",
    "chapter_film": "Film: {y0}–{y1}",
    "slide_count": "{a} / {b}",

    # ---- kadr: odczyt, hydrogram, podpis ---------------------------------------------------
    "readout_water_table": "wody gruntowe",
    "readout_open_water": "otwarta woda",
    "readout_wet_floor": "mokre dno",
    "study": "obszar badań {floor_ha:.0f} ha",
    "beyond": "POZA ZAPISEM",
    "hydro_ylabel": "zwierciadło wód gruntowych, m\n(0 = grunt)",
    "era_before": "przed piezometrami: sam model, skorygowany do lat z pomiarami",
    "era_wells": "pomiary w piezometrach",
    "era_above": "powyżej powodzi 2021: poza wszystkim, co zmierzono",
    "arrival_wet_floor": "mokre dno od",
    "arrival_open_water": "otwarta woda od",
    "caption": (
        "Dzisiejszy rezerwat pod pogodą\nkażdego minionego miesiąca. Nie to, co się\n"
        "naprawdę zdarzyło: „co by było, gdyby”. Zwierciadło\nwód gruntowych modelu jest skorygowane do\n"
        "pomiarów w piezometrach z lat 2005–2026.\n\n"
        "Niebieski: otwarta woda.  Żółty: mokre dno.\nKwadraty 10 m ze zdjęć satelitarnych, 2016–2026.\n"
        "To nie mapa powodziowa: kałuże i brzegi są\nza małe, by je pokazać.\n\n"
        "Obrys to obszar badań: dna obniżeń\nmiędzywydmowych. Nic poza nim nie jest oceniane.\n\n"
        "Sumy w tytule pochodzą ze skorygowanego\nzwierciadła; otwarta woda jest trafna z dokładnością\n"
        "do czynnika {s_ow:.1f}, mokre dno do około {wf_pct:.0f} %."),
    "caption_beyond_head": "TEN MIESIĄC JEST POZA ZAPISEM.",
    "caption_beyond": (
        "\n\nTEN MIESIĄC JEST POZA ZAPISEM.\nZwierciadło wód gruntowych jest powyżej powodzi\n"
        "2021 roku, najwyższej, jaką zmierzono. Sumy to\nkrzywe przedłużone poza koniec danych; blady\n"
        "pomarańcz to dno obniżeń nigdy nie widziane\nmokre — mokrzej niż cokolwiek w zapisie,\n"
        "gdzie dokładnie, nie wiadomo."),

    # ---- slajd porównawczy i miniatury -------------------------------------------------------
    "compare_left": "Sentinel-2, barwy naturalne",
    "compare_right": "Film, ten sam miesiąc",
    "compare_row": "{when} · model {lvl} m · {aw:.0f} ha otwartej wody, {af:.0f} ha mokrego dna",
    "thumb_label": "{when} · piezometry {lvl} m",
    "rel_same": "{kind}",
    "rel_other": "{kind} {when}, {n} mies. {dir}",
    "peak": "szczyt",
    "trough": "minimum",
    "after": "później",
    "before": "wcześniej",

    # ---- własny wykres filmu: bieg swobodny (47_06) -------------------------------------------
    "fr_label_model": "model: sama pogoda, bieg od 1930 roku",
    "fr_label_model_stats": " (R² {r2:.2f}, średnio {bias} cm)",
    "fr_label_wells": "piezometry: mediana sieci referencyjnej (miesiące z co najmniej {n} piezometrami)",
    "fr_ylabel": "zwierciadło wód gruntowych, m (0 = grunt)",
    "fr_title": "Zwierciadło wód gruntowych wydm: model wobec piezometrów",

    # ---- odnośniki do rycin w stopkach slajdów ------------------------------------------------
    "foot_none": "Rycina z raportu",
    "foot_one": "Rycina {num} raportu",
    "foot_one_section": ", rozdział {sec}",
    "foot_many": "Ryciny raportu ",
    "foot_many_section": " (rozdział {sec})",
    "foot_and": " i ",
    "foot_model_run": " · model wobec piezometrów: własny bieg tego filmu",
    "cop": "Zawiera zmodyfikowane dane Copernicus Sentinel",
    "cop_years": "Zawiera zmodyfikowane dane Copernicus Sentinel {years}",

    # ---- slajdy o metodzie ------------------------------------------------------------------
    "f4_number": "Rycina {n4}",
    "f4_none": "Rycina klimatyczna",
    "low_phrase": ", średnio o {cm:.0f} cm za {dir}",
    "low": "nisko",
    "high": "wysoko",
    "m1_title": "1.  Model wód gruntowych sterowany pogodą",
    "m1_p1": (
        "{f4} (po lewej) to pogoda i zwierciadło wód gruntowych razem, 2005–2026. (a) Opad, miesiąc "
        "po miesiącu, z wieloletnią średnią jako linią przerywaną. (b) Parowanie, które osiąga "
        "szczyt każdego lata. (c) Bieżący bilans opadu minus parowanie: rośnie w mokrych ciągach "
        "miesięcy i spada w suchych. (d) Zwierciadło wód gruntowych, uśrednione po piezometrach "
        "rezerwatu, z rozrzutem między piezometrami zaznaczonym cieniem. Panele (c) i (d) rosną i "
        "opadają razem: na tym związku zbudowano model."),
    "m1_p2": (
        "Z tego studium wyprowadziło prostą miesięczną regułę: zwierciadło podnosi się z opadem "
        "danego miesiąca, opada z jego parowaniem i drenuje się proporcjonalnie do tego, jak "
        "wysoko stoi."),
    "m1_p3": (
        "Wykres u góry po prawej to test, od którego zależy ten film. Niebieska linia to model "
        "uruchomiony wyłącznie na pogodzie z RAF Valley od 1930 roku, bez żadnego pomiaru z "
        "piezometrów, który by go korygował; czarna linia to to, co zmierzyły piezometry. Model "
        "podąża za mokrymi i suchymi latami wydm{low}: to odchylenie usuwa następny slajd."),
    "m2_title": "Korekta modelu do piezometrów",
    "m2_p1": (
        "Puszczony swobodnie na stulecie model dryfuje: nie ma piezometrów, które by go trzymały. "
        "Jest więc korygowany tam, gdzie piezometry istnieją. Dla lat 2005–2026 miesiące modelu "
        "są porządkowane według wielkości wobec miesięcy zmierzonych, a każdy modelowany poziom "
        "zastępuje się zmierzonym poziomem o tej samej randze."),
    "m2_p2": (
        "Kolejność mokrych i suchych miesięcy jest własna modelu; korekta usuwa tylko jego "
        "odchylenie. Ta sama korekta jest potem przenoszona wstecz na lata sprzed piezometrów."),
    "m3_title": "2.  Zdjęcia satelitarne: pierwsza kalibracja",
    "m3_p1": (
        "Sentinel-2 fotografuje wydmy co kilka dni od 2016 roku, w kwadratach 10 m. W bliskiej "
        "podczerwieni woda jest czarna, a trawa jasna, więc mokre dno obniżenia widać jako ciemną "
        "plamę. {n} zimowych zdjęć było wolnych od chmur."),
    "m3_p2": (
        "Na każdym z nich zlicza się ciemne kwadraty na dnie obniżeń, dzieląc je na otwartą wodę "
        "(najciemniejsze) i mokre dno, i zestawia ze zwierciadłem, które piezometry zmierzyły w "
        "tym samym miesiącu. Każda para punktów na rycinie to jedno zdjęcie. Cztery z nich pokazano "
        "poniżej w tym paśmie bliskiej podczerwieni, od najsuchszego do najmokrzejszego, każde "
        "przeskalowane do własnej jasności dna obniżeń, tak jak odczytuje ją metoda; każda linia "
        "prowadzi do swoich punktów."),
    "m3_p3": (
        "Punkty układają się na dwóch gładkich krzywych. Mokre dno przyrasta łagodnie, gdy "
        "zwierciadło się podnosi; otwarta woda pozostaje bliska zeru, dopóki woda nie zbliży się "
        "do powierzchni, a potem rośnie stromo. Te krzywe zamieniają zwierciadło filmu na hektary "
        "w jego tytule."),
    "m3_p4": (
        "Dopasowano je między {lo_s} m a {hi_s} m, w zakresie, który widziały zdjęcia. Powyżej "
        "film mówi POZA ZAPISEM."),
    "m4_title": "Sprawdzian: model wobec satelity",
    "m4_p1": (
        "Zanim krzywym powierzy się model, są z nim testowane. Tutaj krzywe są sterowane "
        "zwierciadłem modelu zamiast piezometrami, a przewidywana przez nie powierzchnia jest "
        "porównywana, miesiąc po miesiącu, z powierzchnią faktycznie zmierzoną przez satelitę."),
    "m4_p2": (
        "Satelita nie bierze udziału w modelu, więc jest to niezależny test samego zwierciadła, a "
        "nie tylko krzywych. Te same cztery zdjęcia w bliskiej podczerwieni są poniżej; każda "
        "linia prowadzi do swojego miesiąca na górnym panelu i nazywa szczyt lub minimum, do "
        "którego należy."),
    "m4_p3": (
        "Mokre dno jest odtwarzane blisko. Otwarta woda, która pojawia się nagle, gdy woda sięga "
        "powierzchni, jest odtwarzana gorzej: mały błąd zwierciadła daje duży błąd powierzchni "
        "rozlewisk. Dlatego niebieski jest w filmie barwą mniej pewną."),
    "m5_title": "3.  Dokąd idzie woda: druga kalibracja",
    "m5_p1": (
        "Krzywe mówią, jak duża część dna jest mokra; nie mówią gdzie. Do tego służy własna "
        "historia każdego kwadratu 10 m na zdjęciach: poziom zwierciadła, przy którym po raz "
        "pierwszy odczytano mokre dno (a, mapa górna) i po raz pierwszy otwartą wodę (b, mapa dolna)."),
    "m5_p2": (
        "Najniższe zagłębienia przełączają się pierwsze, wyższe brzegi ostatnie. Szare kwadraty "
        "nigdy nie przełączyły się w zakresie, który widziały zdjęcia, a las pominięto, bo pod "
        "drzewami satelita widzi korony, nie grunt."),
    "m5_p3": (
        "Film zapala każdy kwadrat, gdy zwierciadło modelu sięga jego poziomu. GDZIE pojawiają się "
        "barwy, nauczono się z satelity; KIEDY — to model."),
    "m6_title": "Jak wydmy wyglądają z kosmosu",
    "m6_p1": (
        "Najsuchsze i najmokrzejsze z tych czterech zdjęć, każde obok własnej mapy filmu z tego "
        "samego miesiąca."),
    "m6_p2": (
        "Na zdjęciach zalane dna obniżeń to ciemne plamy między jasnymi wydmami. Film zapala swój "
        "żółty i niebieski w tych samych zagłębieniach, gdy jego zwierciadło się podnosi."),
    "m6_p3": (
        "To ilustracja, nie test. Gdzie pojawiają się barwy, nauczono się z tych samych zdjęć, "
        "więc część podobieństwa jest wbudowana. Niezależnym testem jest sprawdzian dwa slajdy "
        "wcześniej, w którym satelita nie bierze udziału w modelu."),
    "m6_foot": "{cop} {y0}, {y1}",

    # ---- slajdy przed filmem ----------------------------------------------------------------
    "about_title": "O tym filmie",
    "about_p1": (
        "Film o tym, jak mokre byłyby obniżenia międzywydmowe, miesiąc po miesiącu, od 1930 do "
        "2026 roku — gdyby rezerwat w dzisiejszym kształcie przeżył pogodę każdego z tych lat."),
    "about_p2": (
        "Newborough Warren to rezerwat wydmowy na wyspie Anglesey. Między wydmami leżą setki "
        "niskich zagłębień zwanych obniżeniami międzywydmowymi. W mokrą zimę zwierciadło wód "
        "gruntowych podnosi się do nich: grunt wilgotnieje, pojawiają się rozlewiska, a w bardzo "
        "mokrą wiosnę całe obniżenia stoją pod wodą."),
    "about_p3": (
        "Modelowane są tylko wydmy, nie las. Wszystko tutaj dotyczy otwartych obniżeń "
        "międzywydmowych Newborough Warren — obszaru badań obrysowanego na mapie. Posadzony obok "
        "las nie jest częścią modelu i nie jest oceniany; brak żółtych i niebieskich komórek nie "
        "oznacza braku zalania, lecz to, że nie zostało zamodelowane."),
    "howto_title": "Jak czytać film",
    "howto_p1": "ŻÓŁTY to mokre dno: grunt nasycony wodą albo cienka warstwa wody ukryta w trawie.",
    "howto_p2": "NIEBIESKI to otwarta woda: rozlewiska widoczne z powietrza.",
    "howto_p3": (
        "Obrys na mapie to obszar badań — {floor_ha:.0f} hektarów dna obniżeń w obrębie wydm. "
        "Wszystko, co mówi film, dotyczy gruntu wewnątrz niego. Pustego gruntu poza obrysem nie "
        "oceniano; to nie jest twierdzenie, że był suchy."),
    "howto_p4": (
        "Tytuł podaje sumę każdej z nich na obszarze badań, w hektarach (hektar jest nieco większy "
        "od boiska do rugby)."),
    "howto_p5": (
        "Linia u dołu to zwierciadło wód gruntowych — jak głęboko pod gruntem lub jak wysoko nad "
        "nim stoi woda gruntowa, uśrednione po piezometrach rezerwatu. Czerwony znacznik pokazuje, "
        "dokąd film doszedł. Zegar biegnie trzy sekundy na rok; między odczytem jednego miesiąca a "
        "następnego mapa jest rysowana dla poziomów pośrednich, więc woda podnosi się i opada "
        "płynnie, ale odczytami są miesiące."),
    "howto_p6": (
        "Kolejne slajdy pokazują, jak go zrobiono: model wód gruntowych, zdjęcia satelitarne i "
        "mapa tego, dokąd idzie woda, połączone razem, każdy obok rycin z raportu, które go "
        "kalibrują i testują."),
    "hear_title": "Co słychać",
    "hear_p1": "Dźwięk jest zrobiony z wody, miesiąc po miesiącu. Nic w nim nie jest nagrane.",
    "hear_p2": (
        "Przez cały czas brzmi miękki akord. Gdy grają miesiące, jeden z jego głosów nabrzmiewa z "
        "opadem każdego miesiąca, drugi z jego parowaniem, a najwyższy otwiera się, gdy zwierciadło "
        "się podnosi; w miesiącach poza zapisem drży."),
    "hear_p3": (
        "Stały akord narasta ze zwierciadłem, od ciszy w najsuchszych miesiącach do pełni u szczytu "
        "zapisu; powyżej żółtej linii dołącza do niego septyma, a akord się napina, gdy wydmy "
        "zalewa woda, przechylając się tam, gdzie ona jest: w prawo dla wschodu wydm, w lewo dla "
        "zachodu."),
    "hear_p4": (
        "Przeciągnięte dźwięki brzmią, gdy zwierciadło jest powyżej linii na wykresie u dołu: "
        "jeden powyżej żółtej linii, gdzie pojawia się mokre dno; wyższy powyżej niebieskiej, "
        "gdzie pojawia się otwarta woda; i najwyższy powyżej powodzi 2021 roku."),
    "hear_p5": (
        "Pod spodem oddech: jeden cichy dźwięk przez zimową połowę każdego roku, cisza przez lato, "
        "tak że rok trwa trzy sekundy."),
    "read_title": "Przeczytaj to przed obejrzeniem",
    "read_p1": (
        "To dzisiejsze wydmy, nie wydmy tamtych czasów. Reguł nauczono się na latach 2005–2026, a "
        "grunt pochodzi z pomiarów z 2023 roku, z lasem Newborough w obecnym rozmiarze. Las "
        "posadzono dopiero w latach 1947–1965, a las obniża wokół siebie zwierciadło wód "
        "gruntowych. W 1939 roku lasu nie było. Film odpowiada na pytanie „co by było, gdyby” — "
        "co zrobiłby rezerwat taki, jaki jest teraz, pod tamtą pogodą — a nie na pytanie, co "
        "naprawdę się stało."),
    "read_p2": (
        "Mapa obejmuje tylko obszar badań na wydmach; puste miejsce poza nim znaczy „nieoceniane”, "
        "nie „suche”."),
    "read_p3": (
        "Zdjęcia satelitarne: {cop_years}. Ryciny raportu pochodzą ze studium hydrologicznego "
        "Newborough Warren."),
    "big_title": "Największe powodzie wykraczają poza wszystko, co zmierzono",
    "big_p1": (
        "Najmokrzejszą wiosną w zapisie była wiosna 2021 roku. W niektórych miesiącach — 1939, "
        "1959, 1961–62 i 2000–01 — model wypycha zwierciadło wyżej, powyżej {hmax:+.2f} m, do "
        "których dopasowano krzywe."),
    "big_p2": (
        "Żadne zdjęcie nie widziało wydm w takim stanie. Dlatego te miesiące są oznaczone POZA "
        "ZAPISEM, sumy to krzywe przedłużone poza koniec danych, a reszta dna obniżeń przybiera "
        "BLADY POMARAŃCZ: mokrzej niż cokolwiek w zapisie, gdzie dokładnie — nie umiemy powiedzieć."),
    "big_p3": "Uczciwe twierdzenie o tych zimach brzmi: były większe niż 2021, nic ponadto.",

    # ---- slajdy po filmie ------------------------------------------------------------------
    "says_title": "Co mówi film, z zastrzeżeniami",
    "says_p1": (
        "Lata 60. były mokrą dekadą, z mniej więcej dwukrotnie większą otwartą wodą niż w przeciętnej "
        "zimie pozostałych dekad."),
    "says_p2": (
        "Zimy 1961–62 i 2000–01 wyróżniają się jako dwie wielkie powodzie stulecia, za nimi "
        "1938–39 i 1958–59; zima 2015–16 była najmokrzejszą ery satelitarnej po 2021 roku."),
    "says_p3": (
        "Lata 70. i 90. były suchymi dekadami, z prawie żadną otwartą wodą w przeciętnej zimie."),
    "says_p4": (
        "Wszystko to jest relacją modelu o tym, co pogoda zrobiłaby z rezerwatem w jego dzisiejszym "
        "kształcie."),
    "more_title": "I jeszcze trochę",
    "more_p1": (
        "To nie jest mapa powodziowa. Kwadraty mają 10 m boku; wąskie brzegi, małe rozlewiska i "
        "cienkie warstwy wody nad trawą są w tej skali niewidoczne — mniej więcej jedna trzecia "
        "wody w dużej powodzi. Moment, w którym kwadrat się zapala, znany jest tylko z dokładnością "
        "do pięciu–dziesięciu centymetrów zwierciadła."),
    "more_p2": (
        "Błędy modelu przenoszą się dalej. Nawet skorygowany do piezometrów odtwarza zmierzone "
        "zwierciadło z dokładnością do około dwudziestu centymetrów i w najmokrzejszych miesiącach "
        "wciąż biegnie około dziesięciu centymetrów za nisko. Błąd dziesięciu centymetrów zmienia "
        "powierzchnię otwartej wody mniej więcej o połowę, bo rozlewiska pojawiają się nagle, gdy "
        "woda zbliża się do powierzchni. Żółty jest barwą stabilniejszą, dobrą do około "
        "{wf_pct:.0f} %; niebieski jest trafny z dokładnością do czynnika {s_ow:.1f}. Pierwsze dwa "
        "lata to model dochodzący do siebie po początkowym zgadywaniu."),
    "more_p3": (
        "Zima rządzi przez cały rok. Krzywe pochodzą ze zdjęć z listopada–marca; miesiące letnie "
        "pokazują to, co wynikałoby ze zwierciadła, a nie to, co pokazałoby letnie zdjęcie."),
    "credits_title": "Podziękowania i źródła",
    "credits_p1": "Studium hydrologiczne Newborough Warren, 2026 — Martin Hollingham.",
    "credits_p2": (
        "Pogoda: miesięczny zapis RAF Valley, 1930–2026. Zwierciadło wód gruntowych: sieć "
        "piezometrów rezerwatu, 2005–2026. Grunt: pomiary z 2023 roku."),
    "credits_p3": (
        "Zobrazowania: Copernicus Sentinel-2, 2016–2026, bezpłatne i otwarte na licencji "
        "Copernicus. {cop_years}."),
    "credits_p4": (
        "Model, kod i dane: github.com/newbroman/Newborough_Hydrology. Metoda jest zapisana jako "
        "decyzja D-178; pełny pisemny przewodnik towarzyszy temu filmowi."),
    "credits_p5": (
        "Dźwięk: zsyntezowany przez własny kod filmu z modelowanego zwierciadła i powierzchni; bez "
        "nagrań."),
}
