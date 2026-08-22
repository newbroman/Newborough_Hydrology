<!-- GENERATED MIRROR of docs/academic_summaries/crynodeb_academaidd_v1_7.odt — do not edit.
     Regenerate with: python3 tools/refresh_mirrors.py -->

Astudiaeth Dŵr Daear Cwningar Niwbwrch

Crynodeb Tystiolaeth --- Dynameg Hydroddaearegol, Clystyru Ymddygiadol a Dadansoddi Ymyriadau Rheoli

Hollingham, M. (2026) \| Drafft \| Crynhowyd ar gyfer ymchwilwyr, adolygwyr tystiolaeth a rheolwyr systemau twyni

Full report, methods supplement and data: github.com/newbroman/Newborough_Hydrology \| Contact: martin.hollingham+nrg@gmail.com \| ORCID: 0000-0003-0253-9301

Cynllun a dulliau\'r astudiaeth

Dadansoddwyd set ddata monitro ffynhonnau (dipwell) 21 mlynedd (2005--2026) yn cwmpasu 88 ffynnon (66 cyfeirnod, 22 estynedig) ar draws ACA Cwningar Niwbwrch gan ddefnyddio piblinell Python ailadroddadwy 43-cam. Cyfunwyd lefelau dŵr misol â data hinsawdd RAF Valley (glawiad, PET Thornthwaite). Yr offeryn dadansoddol craidd yw model gofod-cyflwr (SSM) a ffitiwyd yn annibynnol i bob ffynnon, gan amcangyfrif tri chyfernod ffisegol: sensitifrwydd ailwefru (β₁), tynfa atmosfferig (β₂) a draenio (β₃). Meincnodwyd perfformiad yr SSM yn erbyn ffwythiant trosglwyddo heb y term draenio; cyflawnodd yr SSM effeithlonrwydd Nash--Sutcliffe positif mewn modd rhagolygu ailadroddol mewn 65 o\'r 66 ffynnon gyfeirnod (o\'i gymharu â 44 o 66 ar gyfer y ffwythiant trosglwyddo).

Rhannodd dadansoddiad clystyru (Ward hierarchaidd, k=5) y rhwydwaith cyfeirnod yn bum parth hydroddaearegol. Aseswyd ymyriadau rheoli trwy ANCOVA-BACI gyda chynllun arbrofol pum haen a thri grŵp rheoli annibynnol. Defnyddiodd rhagamcanion hinsawdd orfodaeth ganradd-50 UKCP18 RCP8.5. Mae trothwyon ecolegol yn dilyn Curreli et al. (2013): isafswm haf llaciau gwlyb −0.61 m, llaciau sych −0.98 m. Aseswyd newid sylfaenol y gwanwyn gan ddefnyddio metrig MSL5 van Willegen et al. (2025).

![](Pictures/10000000000007600000065963A870F2.png){width="14cm" height="10.714cm"}

Ffigur 1. Y pum parth hydroddaearegol a nodwyd gan ddadansoddiad clystyru (Ward hierarchaidd, k=5): C1 Ymyl y Llyn (glas, n=7), C2 Twyn (gwyrdd, n=24), C3 Gweddilliol Gorllewinol (coch, n=21), C4 Prif Goedwig (porffor, n=9), C5 Coedwig Arfordirol (brown, n=5). Ffin y goedwig yn fagenta; parth clirdorri 2017 yn oren.

Nodweddu\'r dyfrhaen

Mae\'r rhaniad k=5 yn cynhyrchu pum parth â phroffiliau cyfernod SSM gwahanol (Tabl 1). Mae\'r Prif Goedwig (C4) yn arddangos y sensitifrwydd ailwefru isaf a\'r dynfa atmosfferig uchaf, wedi\'i yrru gan ryng-gipiad pinwydd a swbstrad tenau dros graigwely afreolaidd. Mae gan Ymyl y Llyn (C1) y sensitifrwydd ailwefru uchaf a\'r draenio cyflymaf, wedi\'i fyffro gan y llyn cyfagos. Mae\'r Goedwig Arfordirol (C5) yn dangos y dirywiad isafswm haf serthaf o\'r holl barthau. Mae drychiad y tir yn esbonio tua 95% o\'r amrywiant yn β₂ o fewn yr ardal goediog, gan gadarnhau mai trwch y swbstrad yn hytrach na gorchudd canopi yw\'r prif reolaeth ar ddwysedd tynfa\'r haf.

  ----------------------- ---- ------------- --------------- ------------ ------
  Parth                   n    β₁ ailwefru   β₂ tynfa atm.   β₃ draenio   LCSC
  C1 Ymyl y Llyn          7    4.58          0.92            0.09         0.22
  C2 Twyn                 24   3.97          1.74            0.06         0.25
  C3 Gweddilliol Gorll.   21   3.57          1.81            0.06         0.28
  C4 Prif Goedwig         9    2.48          2.56            0.02         0.4
  C5 Coedwig Arfordirol   5    2.43          1.27            0.04         0.41
  ----------------------- ---- ------------- --------------- ------------ ------

Tabl 1. Cyfernodau mecanistig SSM fesul clwstwr (canolrifau). β₁, β₂ heb ddimensiwn; β₃ mis⁻¹. LCSC = cyfraniad hinsawdd-storfa cyfun (100/β₁), gwrthdro\'r sensitifrwydd ailwefru.

Gorfodaeth hinsawdd a dadansoddi trothwyon

Mae tymheredd uchafswm yr haf yn RAF Valley wedi tueddu i fyny ar +0.014°C y flwyddyn⁻¹ (p \< 0.001) dros y cofnod llawn (1931--2025), gyda chynnydd cam o +0.94°C uwchlaw\'r llinell sylfaen ers 2013. Mae dadansoddiad tuedd o ddyfnder isafswm haf y lefel ddŵr yn cynhyrchu tueddiadau gostwng arwyddocaol yn ystadegol yn C1 (p \< 0.05) ac C5 (p \< 0.05); mae C2 yn ymylol; nid yw C3 ac C4 yn arwyddocaol ar eu pen eu hunain. Mae allosod tueddiadau canolrif-clwstwr yn dangos bod C1 Ymyl y Llyn yn croesi trothwy hyfywedd llaciau gwlyb (SD15b, −0.61 m) tua 2030--2032 dan y llwybr presennol.

Mae canfyddiad van Willegen et al. (2025) mai lefel gwanwyn gymedrig pum mlynedd (MSL5) sy\'n esbonio ymateb llystyfiant llaciau twyni orau yn adlewyrchu trosglwyddiad ecolegol: mae cymunedau planhigion yn integreiddio amodau hydrolegol dros tua phum mlynedd. Mae hanner-oes dadfeiliad draenio t½ = ln(2)/β₃ yn rheoli trosglwyddiad gwahanol, i fyny\'r afon --- pa mor hir y mae\'r dyfrhaen ei hun yn cadw aflonyddwch, ac felly pa mor annibynnol y mae\'r pum darlleniad gwanwyn o fewn ffenestr MSL5 mewn gwirionedd. Yn y clystyrau twyni agored mae hyn yn amrywio digon i fod o bwys wrth ddehongli MSL5. Mae C1 Ymyl y Llyn (t½ cymedrig ≈ 7 mis) yn cadw dim ond tua 28% o anomaledd gwanwyn flwyddyn yn ddiweddarach, felly mae ei bum darlleniad o fewn y ffenestr yn agos at fod yn annibynnol ac mae MSL5 yn ymddwyn fel gwir gyfartaledd aml-flwyddyn. Mae C2 Twyn (≈ 10 mis) yn debyg. Mae gan C3 Gweddilliol Gorllewinol, fodd bynnag, t½ cymedrig o 14 mis yn codi i 22 mis yn ei ffynhonnau arafaf, gan gadw 42--52% o anomaledd ar ôl blwyddyn: mae un gwanwyn gwlyb neu sych yn lledaenu i ddarlleniadau dilynol, felly mae gwerth MSL5 yn y ffynhonnau hyn yn pwyso tuag at safle unrhyw wanwyn eithafol o fewn ei ffenestr yn hytrach na bod yn gyfartaledd glân pum mlynedd. Mae hyn yn golygu bod yr un dyfnhau MSL5 a fesurwyd yn cario gwybodaeth wahanol ar draws y rhwydwaith twyni --- signal aml-flwyddyn cadarn yn C1 ac C2, ond un a allai fod wedi\'i halogi gan anomaledd yn y ffynhonnau C3 arafach, y dylid eu gwirio yn erbyn lleoliad y ffenestr cyn priodoli newid i reolaeth neu hinsawdd. Mae tu mewn y goedwig ymhell y tu allan i\'r ystod hon (C4 t½ cymedrig ≈ 40 mis) ac nid yw\'n gartref i\'r cymunedau llaciau y cynlluniwyd MSL5 ar eu cyfer, ond mae ei gof hir yn cadarnhau\'r mecanwaith yn ddefnyddiol: lle mae draenio\'n araf, mae darlleniadau\'r gwanwyn wedi\'u hunangydberthyn yn drwm ac mae MSL5 yn colli ei ddehongliad fel cyfartaledd.

Mae rhagamcanion canradd-50 UKCP18 RCP8.5 a ledaenwyd trwy\'r SSM yn cynhyrchu dyfnhau isafswm haf rhagamcanol o 71--134 mm erbyn y 2080au a dyfnhau sylfaen y gwanwyn (MSL5) o 21--39 mm. Mae\'r anghymesuredd (mae\'r isafswm haf yn dyfnhau 3--5× yn gyflymach na MSL5) yn adlewyrchu rôl aflinol PET ym misoedd yr haf. Mae lluosyddion glaw critigol (λ) yn dosbarthu 57 o 65 ffynnon twyni agored fel cyraeddadwy (λ \< 1.5) a 5 o 23 ffynnon parth-coedwig fel rhai na ellir eu cyrraedd yn strwythurol (λ ≥ 2.5).

![](Pictures/100000000000076200000446097E6DF6.png){width="14cm" height="8.1cm"}

Ffigur 2. Llwybr isafswm haf rhagamcanol ar gyfer y pum parth yn erbyn trothwyon ecolegol Curreli et al. (2013). Ffenestr ymyrraeth critigol 2030--2039 wedi\'i chysgodi.

![](Pictures/10000000000006B2000004D245961E36.png){width="14cm" height="10.081cm"}

Ffigur 3. Rhagamcanion UKCP18 RCP8.5 o MSL5 (glas) ac isafswm haf (oren) erbyn y 2050au a\'r 2080au. Mae\'r isafswm haf yn dyfnhau 3--5× yn gyflymach na sylfaen y gwanwyn ym mhob parth.

Dadansoddi ymyriadau rheoli

Crafu twyni --- CEH36 (Ebrill 2015) a CEH18/CEH21 (Hydref 2023)

CEH36: Mae tri amcangyfrifwr annibynnol yn cynhyrchu effeithiau crafu cyson --- BACI pâr crai +130 mm, rheolydd synthetig +137 mm, gweddill-ymlaen SSM +81 mm. Y ffigur pennawd yw\'r symudiad BACI isafswm haf pâr: +195 mm (p = 0.004) o\'i gymharu â\'r rheolydd heb ei grafu CEH4. Mae hyn yn cynrychioli budd geometrig parhaol: mae wyneb y tir yn agosach at y lefel ddŵr, felly mae dyfnder cymharol y lefel ddŵr yn fwy bas waeth beth fo\'r lefel absoliwt. Mae CEH36 yn rhagflaenu ffenestri cymharu MSL5 (2013--2017 yn erbyn 2019--2023); nid yw ei godiad cychwynnol yn ymddangos yn Ffigur 4.

CEH18/CEH21 (Hydref 2023): Cofnod ôl-ymyrraeth annigonol (\<2 flynedd) ar gyfer casgliad ystadegol. Mae\'r ddau safle mewn safleoedd mwy tua\'r môr lle mae graddiant cilio\'r arfordir yn ffactor cymysglyd. Nid oes signal ôl-grafu arwyddocaol yn ganfyddadwy yn y naill ffynnon na\'r llall yn erbyn cefndir amrywioldeb o flwyddyn i flwyddyn.

BACI clirdorri --- Rhagfyr 2017 (8.4 ha)

Cynllun ANCOVA-BACI pum haen: 17 ffynnon, tri diffiniad rheoli annibynnol (Coedwig, Hinsawdd, Cyfunol). Prif ganlyniad (rheolydd Coedwig, ffynnon effaith WMC3): cam clirdorri +0.113 m (p \< 0.001, CI \[0.050, 0.189\]). Ymyl y Goedwig: +0.033 m (p = 0.193). Estyniad synthetig (10h, centroid WMC3+FE1+FE2): +0.085 m (p \< 0.001). ANCOVA haf yn unig (is-set Meh--Medi): +0.046 m (p = 0.436) --- heb fod yn arwyddocaol. Mae\'r di-ganlyniad haf yn gadarn ar draws pob diffiniad rheoli.

Mae\'r di-ganlyniad haf yn gyson â rôl ddeuol i\'r canopi: mae tynnu rhyng-gipiad yn cynyddu ailwefru\'r gaeaf ond mae dinoethiad yn cynyddu anwedddrydarthiad haf uniongyrchol o\'r pridd sydd bellach heb ei gysgodi. Mae\'r effeithiau hyn tua\'n canslo ei gilydd yn ffenestr Mehefin--Medi. Nodir gostyngiad ar draws y safle mewn effeithlonrwydd ailwefru (β₁ yn gostwng dros amser ar draws pob clwstwr) fel prif yrrwr dirywiad yr isafswm haf, gan weithredu\'n annibynnol ar reoli\'r canopi.

Newid sylfaenol y gwanwyn a arsylwyd a\'r strwythur gofodol

Cymhariaeth MSL5 (diwedd-ffenestr 2017 yn erbyn diwedd-ffenestr 2023): dyfnhau cymedrig y safle −97 mm (cymedr y rhwydwaith −492 i −589 mm). O 59 ffynnon â data dilys yn y ddwy ffenestr, dyfnhaodd 56 \>25 mm; aeth 0 yn fwy bas \>25 mm. Y gostyngiadau mwyaf ar ymyl arfordirol y de-orllewin (CEH22: −229 mm); y lleiaf ar Ymyl y Llyn dwyreiniol. Nid yw parth y clirdorri\'n dangos signal gwahaniaethadwy.

![](Pictures/10000001000009EE00000967C79BE1C0.png){width="13cm" height="9.377cm"}

Ffigur 4. Newid MSL5 2017→2023. n=59 ffynnon; dyfnhaodd 56 \>25 mm, 0 yn fwy bas \>25 mm. Ffynhonnell: 20_msl5_change_2017_2023.png; Ffigur 58 yr adroddiad.

Mae dadansoddiad symudiad gwanwyn gwahaniaethol (Sgript 32, 2011--2025) yn datgelu tueddiadau dargyfeiriol o fewn y rhwydwaith. Mae C4 Prif Goedwig yn unffurf bositif (+8.4 i +20.5 mm y flwyddyn⁻¹ o\'i gymharu â chymedr y safle, cymedr y clwstwr +14.9 mm y flwyddyn⁻¹); nid oes yr un yn arwyddocaol yn unigol ar ôl cywiriad AR(1). Mae hyn yn adlewyrchu dau fecanwaith atgyfnerthol: (1) mae\'r goedwig yn meddiannu uchafbwynt hydrolig y dyfrhaen, bellaf o unrhyw ffin pen-cyson (llyn i\'r dwyrain, Afon Menai i\'r de-ddwyrain, arfordir i\'r de-orllewin), gan roi\'r rhyddid mwyaf i\'r lefel ddŵr godi mewn blynyddoedd gwlyb a gostwng mewn rhai sych; (2) mae\'r swbstrad cynnyrch-penodol isel (tywod tenau dros graigwely) yn crynhoi ailwefru\'n newidiadau pen mwy. Mae gwanwynau gwlyb diweddar (2021, 2024) wedi mwyhau C4 o\'i gymharu â\'r rhwydwaith. Mae C1 Ymyl y Llyn ac C5 Coedwig Arfordirol yn unffurf negatif (−8.0 a −6.8 mm y flwyddyn⁻¹ yn y drefn honno), wedi\'u gyrru gan signal ffin cilio\'r arfordir. Mae C2 Twyn tua\'n niwtral ar gyfartaledd.

![](Pictures/100000010000075D0000047A9BEF99AE.png){width="14.986cm" height="10.811cm"}

Ffigur 5. Symudiad gwanwyn gwahaniaethol 2011--2025. C4 yn unffurf bositif (ymateb blwyddyn-wlyb wedi\'i fwyhau + safle uchafbwynt hydrolig); C1 ac C5 yn unffurf negatif (effaith ffin arfordirol). C2/C3 yn niwtral yn fras. Wedi\'i lenwi = arwyddocaol (p wedi\'i gywiro gan AR \< 0.05).

Signal cilio\'r arfordir

Mae cyd-newidyn dwyreinio×amser ar raddfa rhwydwaith yn ANCOVA\'r clirdorri yn dal graddiant cilio arfordirol go iawn sy\'n effeithio ar yr ymyl orllewinol. Yn annibynnol, mae trawslun dwy-ffynnon o ffynhonnau rheoli arfordirol yn dirywio mewn patrwm sy\'n gyson ag isel-hau amod-ffin cynyddol. Mae signal cilio\'r arfordir yn cyfrif, o fewn ansicrwydd, am ddirywiad eithriadol C5 yn ei gyfanrwydd. Mae oediadau lledaeniad dŵr daear yn golygu bod data cyfredol yn rhannol adlewyrchu erydiad hanesyddol; os yw erydiad yn cyflymu, nid yw\'r effeithiau gwaethaf wedi cyrraedd y ffynhonnau mewnol eto. Mae CEH22 (y tu allan i\'r rhwydwaith cyfeirnod, ymyl arfordirol de-orllewinol) yn dirywio ar −26.5 mm y flwyddyn⁻¹ (p \< 0.001), y cyflymaf yn y rhwydwaith.

Graddfa\'r newid a arsylwyd yn ei gyd-destun

Mae\'r ymyriadau rheoli a astudiwyd hyd yma wedi cynhyrchu effeithiau mesuradwy ar y raddfa leol: mae budd y crafu yn CEH36 yn gadarn yn ystadegol ac yn arwyddocaol yn ecolegol, a chynhyrchodd y clirdorri welliant canfyddadwy mewn lefelau dŵr misol cymedrig yn erbyn rheolyddion coedwig. Fodd bynnag, dyfnhaodd sylfaen gwanwyn y safle cyfan 97 mm rhwng ffenestri cymharu 2017 a 2023 --- newid sy\'n effeithio ar 56 o 59 ffynnon a fonitrwyd ar yr un pryd ac wedi\'i yrru gan rymoedd sy\'n gweithredu ar raddfa\'r dyfrhaen gyfan. Mae tymheredd yr haf wedi tueddu i fyny ar +0.014°C y flwyddyn⁻¹ ers 1931, gyda chynnydd cam o +0.94°C uwchlaw\'r llinell sylfaen ers 2013. Mae signal cilio\'r arfordir yn cyfrif, o fewn ansicrwydd, am ddirywiad eithriadol parth y Goedwig Arfordirol yn ei gyfanrwydd, ac mae\'n ymestyn sawl can metr i mewn i\'r tir. Yn erbyn y signalau hyn, mae budd y crafu mewn un ffynnon (+195 mm) a gwelliant misol-cymedrig y clirdorri (+113 mm o\'i gymharu â choedwig heb ei chwympo) yn cynrychioli ymatebion lleol nad ydynt yn newid cyfeiriad y duedd ar draws y rhwydwaith. Mae rhagamcanion UKCP18 yn dangos dyfnhau isafswm haf pellach o 71--134 mm erbyn y 2080au --- sydd, o\'i ychwanegu at y 97 mm a gollwyd eisoes rhwng ffenestri cymharu 2017 a 2023, yn gosod colledion cronnus o\'r llinell sylfaen cyn-clirdorri yn yr ystod 170--230 mm, gan ragori\'n sylweddol ar unrhyw effaith reoli a arsylwyd yn y cofnod hwn.

Prif ganfyddiadau meintiol

  -------------------------------------------------------- -------------------------- ----------------
  Canfyddiad                                               Gwerth                     Ffynhonnell
  Cam crafu CEH36 (BACI pâr)                               \+ 195 mm p = 0.004        Script 09c
  Cam clirdorri yn erbyn rheolydd Coedwig (cymedr misol)   \+ 113 mm p \< 0.001       Script 10a
  Cam clirdorri yn erbyn rheolydd Coedwig (haf yn unig)    \+ 46 mm p = 0.44 (n.s.)   Script 10a
  Newid MSL5 2017→2023 (cymedr y safle)                    − 97 mm                    Script 26 / 20
  Ffynhonnau a ddyfnhaodd \>25 mm (o 59 dilys)             56 (95%)                   Script 20
  Tuedd wahaniaethol C4 2011--2025                         \+ 14.9 mm/yr (cymedr)     Script 32
  Tuedd wahaniaethol C5 2011--2025                         − 6.8 mm/yr (cymedr)       Script 32
  Cyfernod mwyhau C4 (canonaidd)                           1.72× cymedr y safle       Script 33/35
  Cyfernod mwyhau C1                                       0.61× cymedr y safle       Script 33/35
  Tuedd CEH22 (ymyl arfordirol)                            − 26.5 mm/yr p \< 0.001    Script 32
  Croesiad trothwy C1 (isafswm haf)                        \~2030--2032               Script 14
  Dyfnhau isafswm haf UKCP18 2080au                        71--134 mm                 Script 14/26b
  Dyfnhau MSL5 UKCP18 2080au                               21--39 mm                  Script 26b
  -------------------------------------------------------- -------------------------- ----------------

Tabl 2. Prif ganlyniadau meintiol. Daw\'r holl ffigurau o CSVs y biblinell a ymrwymwyd ar gangen main GitHub.

Casgliadau

> • Y lefel ddŵr isafswm haf yw\'r newidyn sy\'n rhwymo\'n ecolegol. Mae MSL5 yn ddirprwy a fesurir yn well sy\'n olrhain drifft arafach y system ond sy\'n tanamcangyfrif osgled y risg ecolegol.

> • Crafu twyni mewn safleoedd mewndirol a ddewiswyd yn dda yw\'r ymyrraeth uniongyrchol fwyaf effeithiol sydd ar gael, ond nid yw\'n mynd i\'r afael â\'r gyrwyr sylfaenol. Mae\'r buddion yn erydu yn erbyn tuedd hinsawdd y cefndir.

> • Mae clirdorri yn codi lefelau cymedrig y dŵr ym mharth y goedwig o\'i gymharu â rheolyddion heb eu cwympo ond nid yw\'n cynhyrchu gwelliant isafswm haf canfyddadwy, sy\'n gyson ag effeithiau deuol tynnu\'r canopi yn canslo ei gilydd yn yr haf.

> • Gostyngiad ar draws y safle mewn effeithlonrwydd ailwefru, sy\'n gweithredu\'n annibynnol ar reoli\'r wyneb, yw prif yrrwr dirywiad yr isafswm haf.

> • Mae signal ffin cilio\'r arfordir yn fygythiad gwahanol, oediog, ac ar hyn o bryd na ellir ei reoli, i\'r ymyl orllewinol. Nid yw\'r ffynhonnau mewnol wedi profi effaith lawn yr erydiad cyflymedig diweddar eto.

> • Mae safle hydrolig y goedwig (uchafbwynt topograffig a dyfrhaen, heb ffin pen-cyson gerllaw) yn ei wneud yn fwyhadur cryf o amrywioldeb hinsawdd o flwyddyn i flwyddyn, nid signal adfer.

> • Mae grymoedd hinsawdd ac arfordirol yn gweithredu ar faint sy\'n gorlifo\'r ymyriadau rheoli lleol a arsylwyd hyd yma.

DRAFFT --- cyfieithiad drafft awtomataidd; rhaid ei wirio gan adolygydd Cymraeg cyn ei ddefnyddio. Cedwir rhifau, symbolau ac enwau sgriptiau yn union fel yn y gwreiddiol Saesneg; mae testun o fewn y ffigurau'n aros yn Saesneg. (Draft --- automated draft translation; must be checked by a Welsh-language reviewer before use. Numbers, symbols and script names are kept exactly as the English original; text inside the figures remains in English.)
