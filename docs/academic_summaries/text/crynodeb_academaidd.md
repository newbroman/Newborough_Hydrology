<!-- GENERATED MIRROR of docs/academic_summaries/crynodeb_academaidd_v1_25.odt — do not edit. source-sha256=b008568f2668a90a pandoc=3.1.3 -->
<!--      Regenerate with: python3 tools/refresh_mirrors.py -->

Astudiaeth Dŵr Daear Cwningar Niwbwrch

Crynodeb Tystiolaeth --- Dynameg Hydroddaearegol, Clystyru Ymddygiadol a Dadansoddi Ymyriadau Rheoli

Hollingham, M. (2026) \| Drafft \| Crynhowyd ar gyfer ymchwilwyr, adolygwyr tystiolaeth a rheolwyr systemau twyni

Full report, methods supplement and data: github.com/newbroman/Newborough_Hydrology \| Contact: martin.hollingham+nrg@gmail.com \| ORCID: 0000-0003-0253-9301

Cynllun a dulliau\'r astudiaeth

Dadansoddwyd set ddata monitro ffynhonnau (dipwell) 21 mlynedd (2005--2026) yn cwmpasu 88 ffynnon (66 cyfeirnod, 22 estynedig) ar draws ACA Cwningar Niwbwrch gan ddefnyddio piblinell Python ailadroddadwy 60-cam. Cyfunwyd lefelau dŵr misol â data hinsawdd RAF Valley (glawiad, PET Thornthwaite). Yr offeryn dadansoddol craidd yw model gofod-cyflwr (SSM) a ffitiwyd yn annibynnol i bob ffynnon, gan amcangyfrif tri chyfernod ffisegol: sensitifrwydd ailwefru (β₁), tynfa atmosfferig (β₂) a draenio (β₃). Meincnodwyd perfformiad yr SSM yn erbyn model llinol traddodiadol (TLM) heb y term draenio; cyflawnodd yr SSM effeithlonrwydd Nash--Sutcliffe positif mewn modd rhagolygu ailadroddol mewn 65 o\'r 66 ffynnon gyfeirnod (o\'i gymharu â 55 o 66 ar gyfer y model llinol traddodiadol).

Rhannodd dadansoddiad clystyru (Ward hierarchaidd, k=5) y rhwydwaith cyfeirnod yn bum parth hydroddaearegol. Aseswyd ymyriadau rheoli trwy ANCOVA-BACI gyda chynllun arbrofol pum haen a thri grŵp rheoli annibynnol. Defnyddiodd rhagamcanion hinsawdd orfodaeth ganradd-50 UKCP18 RCP8.5. Mae trothwyon ecolegol yn dilyn Curreli et al. (2013): isafswm haf llaciau gwlyb −0.61 m, llaciau sych −0.98 m. Aseswyd newid sylfaenol y gwanwyn gan ddefnyddio metrig MSL5 van Willegen et al. (2025).

![](Pictures/10000000000007600000065963A870F2.png){width="14cm" height="10.714cm"}

Ffigur 1. Y pum parth hydroddaearegol a nodwyd gan ddadansoddiad clystyru (Ward hierarchaidd, k=5): C1 Ymyl y Llyn (glas, n=7), C2 Twyn (gwyrdd, n=19), C3 Gweddilliol Gorllewinol (coch, n=26), C4 Prif Goedwig (porffor, n=9), C5 Coedwig Arfordirol (brown, n=5). Ffin y goedwig yn fagenta; parth clirdorri 2017 yn oren.

Nodweddu\'r dyfrhaen

Mae\'r rhaniad k=5 yn cynhyrchu pum parth â phroffiliau cyfernod SSM gwahanol (Tabl 1). Mae\'r Prif Goedwig (C4) yn arddangos y sensitifrwydd ailwefru isaf a\'r dynfa atmosfferig uchaf, wedi\'i yrru gan ryng-gipiad pinwydd a swbstrad tenau dros graigwely afreolaidd. Mae gan Ymyl y Llyn (C1) y sensitifrwydd ailwefru uchaf a\'r draenio cyflymaf, wedi\'i fyffro gan y llyn cyfagos. Mae\'r Goedwig Arfordirol (C5) yn dangos y dirywiad isafswm haf serthaf o\'r holl barthau. Mae drychiad y tir yn esbonio 98% o\'r amrywiant yn β₂ o fewn yr ardal goediog, gan gadarnhau mai trwch y swbstrad yn hytrach na gorchudd canopi yw\'r prif reolaeth ar ddwysedd tynfa\'r haf.

  ----------------------- ---- ------------- --------------- ------------ -------
  Parth                   n    β₁ ailwefru   β₂ tynfa atm.   β₃ draenio   LCSC
  C1 Ymyl y Llyn          7    4.578         0.911           0.09         0.218
  C2 Twyn                 24   3.896         1.666           0.06         0.257
  C3 Gweddilliol Gorll.   21   3.758         1.778           0.06         0.28
  C4 Prif Goedwig         9    2.476         2.570           0.018        0.4
  C5 Coedwig Arfordirol   5    2.412         1.248           0.04         0.415
  ----------------------- ---- ------------- --------------- ------------ -------

Tabl 1. Cyfernodau mecanistig SSM fesul clwstwr (ffitiau canol-clwstwr). β₁, β₂ heb ddimensiwn; β₃ mis⁻¹. LCSC = Cyfernod Storfa Dalgylch Cyfun (Lumped Catchment Storage Coefficient, 100/β₁), gwrthdro\'r sensitifrwydd ailwefru.

Gorfodaeth hinsawdd a dadansoddi trothwyon

Mae tymheredd uchafswm yr haf yn RAF Valley wedi tueddu i fyny ar +0.014°C y flwyddyn⁻¹ (p \< 0.001) dros y cofnod llawn (1931--2025), gyda chynnydd cam o +0.94°C uwchlaw\'r llinell sylfaen ers 2013. Mae dadansoddiad tuedd o ddyfnder isafswm haf y lefel ddŵr yn cynhyrchu tueddiadau gostwng arwyddocaol yn ystadegol dros y cofnod llawn yn C1, C2, C3 ac C5 (p = 0.024, 0.033, 0.028 a 0.004); nid yw C4 yn arwyddocaol (p = 0.36). Mae\'r gostyngiad wedi\'i grynhoi cyn 2011: o\'u hail-ffitio o 2011, nid oes tuedd arwyddocaol mewn unrhyw glwstwr. Mae isafswm haf C1 Ymyl y Llyn wedi bod yn ddyfnach na throthwy llaciau gwlyb (SD15b, −0.61 m) ym mhob blwyddyn o\'r cofnod; mae bootstrap o\'i duedd isafswm haf yn gosod canolrif croesi trothwy llaciau sych (SD16, −0.98 m) yn 2027 (CI 90% 2021--2046), ac mae tri o\'r wyth isafswm haf diweddaraf eisoes y tu hwnt iddo.

Mae canfyddiad van Willegen et al. (2025) mai lefel gwanwyn gymedrig pum mlynedd (MSL5) sy\'n esbonio ymateb llystyfiant llaciau twyni orau yn adlewyrchu trosglwyddiad ecolegol: mae cymunedau planhigion yn integreiddio amodau hydrolegol dros tua phum mlynedd. Mae a yw\'r pum darlleniad gwanwyn o fewn ffenestr MSL5 yn annibynnol yn dibynnu ar ba mor gyflym y mae\'r lefel ddŵr yn dychwelyd i\'w chymedr ei hun. Nid hanner-oes draenio t½ = ln(2)/β₃ y model cyhoeddedig heb ryngdoriad yw hynny; cysonyn enciliad y term draenio ar ddatwm 3.7 m yw hwnnw, ac mae\'n newid gyda\'r datwm. Fe\'i mesurir drwy ail-ffitio\'r un model gyda rhyngdoriad rhydd, nad yw ei gyfernod draenio\'n dibynnu ar y datwm, ac mae\'n fyr: tua hanner blwyddyn yw\'r amser e-blygu (canolrif 6.5 mis, o\'i gymharu â 5.1 mis o hunangydberthyniad arsylwedig y lefel wedi\'i dad-dymoreiddio), o tua 2 fis yn C1 Ymyl y Llyn i tua 13 mis yn C5 Coedwig Arfordirol. Bach yw\'r parhad gwanwyn o flwyddyn i flwyddyn y mae hyn yn ei awgrymu, o 0.01 yn C1 i 0.28 yn C5 (canolrif 0.15 ar draws y ffynhonnau), ac mae hunangydberthyniad lag-1 arsylwedig lefel flynyddol y gwanwyn bron yn sero ym mhob clwstwr (canolrif −0.11). Felly mae\'r darlleniadau o fewn ffenestr MSL5 yn agos at fod yn annibynnol ar draws y rhwydwaith, ac mae MSL5 yn ymddwyn fel gwir gyfartaledd pum mlynedd. Mae sensitifrwydd y ffenestr yn real ac yn raddedig, ond fel mater o osgled yn hytrach na pharhad: mae ar ei fwyaf yn C4 Prif Goedwig, lle mae lefelau\'r gwanwyn yn siglo bellaf, ac mae gwasgariad rhyngflynyddol lefel y gwanwyn yn dilyn y cyfernod tynnu atmosfferig β₂ yn hytrach na β₃. Ni ellir adnabod cyfernod draenio rhyngdoriad-rhydd C4 o\'r cofnod.

Gwerthuswyd rhagamcanion canradd-50 UKCP18 RCP8.5 fel y newid parhaus yn y lefel ddŵr, fesul ffynnon ar gyfernodau ffurf rhyngdoriad y model (nad yw ei gyfernod draenio\'n dibynnu ar y datwm draenio); ni ragamcanir C4 Prif Goedwig, gan na ellir adnabod ei gyfernod draenio o\'r cofnod. Mae lefel flynyddol gymedrig y safle\'n gostwng 0.159 m erbyn y 2050au a 0.286 m erbyn y 2080au. Yr haf sy\'n cario\'r rhan fwyaf o\'r newid: mae lefelau\'r haf yn gostwng 0.213 a 0.387 m ar draws y safle, gan gyrraedd 0.440 m yn C3 erbyn y 2080au, ac mae lefelau\'r gaeaf yn gostwng hefyd (0.103 a 0.180 m) ym mhobman ac eithrio C1. Mae sylfaen y gwanwyn yn symud llawer llai yn y twyni agored: erbyn y 2080au mae MSL5 yn newid +52 mm yn C1 a −22 mm yn C2, o\'i gymharu â gostyngiadau haf o 315 a 359 mm. Yn C3 ac C5 mae\'n gostwng tua hanner cymaint â lefel yr haf (−150 o\'i gymharu â −440 mm, a −141 o\'i gymharu â −319 mm), gan fod yr amser dychwelyd i\'r cymedr hirach yno\'n cario diffyg yr haf i\'r gwanwyn canlynol. Mae lluosyddion glaw critigol (m_P) yn dosbarthu 58 o 64 ffynnon twyni agored fel cyraeddadwy (m_P \< 1.5) a 5 o 24 ffynnon parth-coedwig fel rhai na ellir eu cyrraedd yn strwythurol (m_P ≥ 2.5).

![](Pictures/100000000000076200000446097E6DF6.png){width="14cm" height="8.1cm"}

Ffigur 2. Llwybr isafswm haf rhagamcanol ar gyfer y pum parth yn erbyn trothwyon ecolegol Curreli et al. (2013). Ffenestr ymyrraeth critigol 2030--2039 wedi\'i chysgodi.

![](Pictures/10000000000006B2000004D245961E36.png){width="14cm" height="10.090cm"}

Ffigur 3. Symudiad parhaus rhagamcanol yn lefel ddŵr gymedrig pum mlynedd y gwanwyn (MSL5, glas) ac yn lefel ddŵr yr haf (oren), fesul parth, o dan orfodaeth UKCP18 RCP8.5 ar gyfer y 2050au a\'r 2080au, ar gyfernodau\'r ffurf rhyngdoriad. Ni ragamcanir C4 (ni ellir adnabod ei gyfernod draenio). Negatif yw dyfnach. Mae metrig y gwanwyn yn symud llawer llai na lefel yr haf yn y twyni agored (C1, C2), a thua hanner cymaint yn C3 ac C5.

Dadansoddi ymyriadau rheoli

Crafu twyni --- CEH36 (Ebrill 2015) a CEH18/CEH21 (Hydref 2023)

CEH36: Mae tri amcangyfrifwr annibynnol yn cynhyrchu effeithiau crafu cyson --- BACI pâr crai +128 mm, rheolydd synthetig +141 mm, gweddill-ymlaen SSM +100 mm. Y ffigur pennawd yw\'r symudiad BACI isafswm haf pâr: +195 mm (p = 0.004) o\'i gymharu â\'r rheolydd heb ei grafu CEH4. Mae hyn yn cynrychioli budd geometrig parhaol: mae wyneb y tir yn agosach at y lefel ddŵr, felly mae dyfnder cymharol y lefel ddŵr yn fwy bas waeth beth fo\'r lefel absoliwt. Mae CEH36 yn rhagflaenu ffenestri cymharu MSL5 (2013--2017 yn erbyn 2019--2023); nid yw ei godiad cychwynnol yn ymddangos yn Ffigur 4.

CEH18/CEH21 (Hydref 2023): Cofnod ôl-ymyrraeth annigonol (\<2 flynedd) ar gyfer casgliad ystadegol. Mae\'r ddau safle mewn safleoedd mwy tua\'r môr lle mae graddiant cilio\'r arfordir yn ffactor cymysglyd. Nid oes signal ôl-grafu arwyddocaol yn ganfyddadwy yn y naill ffynnon na\'r llall yn erbyn cefndir amrywioldeb o flwyddyn i flwyddyn.

BACI clirdorri --- Rhagfyr 2017 (4.2 ha)

Cynllun ANCOVA-BACI pum haen: 17 ffynnon, tri diffiniad rheoli annibynnol (Coedwig, Hinsawdd, Cyfunol). Prif ganlyniad (rheolydd Coedwig, ffynnon effaith WMC3): cam clirdorri +0.108 m (p = 0.003, CI \[0.037, 0.180\]). Ymyl y Goedwig: +0.031 m (p = 0.23), heb fod yn arwyddocaol. Estyniad synthetig (10h, centroid WMC3 + FE2): +0.094 m (p = 0.002). ANCOVA haf yn unig (is-set Meh--Medi): −0.001 m (p = 0.99) --- heb fod yn arwyddocaol. Mae\'r di-ganlyniad haf yn gadarn ar draws pob diffiniad rheoli.

Nid yw\'r ffynnon a gwympwyd ei hun yn dangos cynnydd yn y sensitifrwydd ailwefru ar ôl y cwympo (β₁ 0.98 o\'i werth cyn y cwympo, net o\'r rheolyddion hinsawdd), ac mae\'r dynfa atmosfferig wedi gostwng 4.8% y tu hwnt i\'r rheolyddion hinsawdd, heb golli cysgodi haf y canopi (tynfa misoedd y canopi −1.7% net). Mae\'r cam yn y lefel fisol gymedrig, nid yn lefel yr haf. Mae gostyngiad cymedrig rhwydwaith yn y sensitifrwydd ailwefru (β₁ −4.6% ar draws y 17 ffynnon BACI) yn fecanwaith posibl ar gyfer dirywiad yr isafswm haf, ond prin y mae haen y Rheolydd Hinsawdd heb ei chwympo yn ei ddangos (−0.3%), felly nid yw ei annibyniaeth ar reolaeth wedi\'i sefydlu.

Mae\'r senarios coedwigaeth (D-239) wedi\'u hangori i\'r hyn a fesurodd cwympo Rhagfyr 2017 yn WMC3: gostyngiad yn y dynfa atmosfferig a dim cynnydd mewn ailwefru. Fel newidiadau parhaus yn y lefel, mae clirdorri\'n codi\'r lefel ddŵr +0.038 m (Model B) i +0.066 m (Model A) yn C5 a +0.217 m yn C4 (Model A); yn y ffynnon a gwympwyd mae\'n rhoi +0.060 a +0.135 m, o boptu\'r +0.108 m a fesurwyd yno. Mae teneuo\'n rhoi hanner pob un ar y mwyaf. Mae trosi i goed llydanddail yn amrywio o ostyngiad bach (−0.037 m yn C5 a −0.121 m yn C4, Model A) heb enill rhyng-gipiad i gynnydd (+0.308 a +0.506 m) gydag un. Pen isaf ystod y clirdorri yw\'r rhain: mae\'r adran 4.2 ha yn gulach na chyrhaeddiad y gostyngiad (tua 220 m), felly byddai enill ailwefru yno\'n lledaenu i\'r goedwig o\'i hamgylch; mae\'r ffurf rhyng-gipiad yn nodi\'r pen uchaf ar gyfer cwympo ehangach, wedi\'i ffinio gan gyflwr terfynol twyni agored o 0.5--0.9 m. Gwerthusir y senarios ffynnon wrth ffynnon ac ni allant ddangos a yw newid yn y goedwig yn cyrraedd y twyni agored. Erbyn y 2080au mae\'r lefel flynyddol yn C5 yn gostwng 0.27 m (Model B) i 0.49 m (Model A) o dan UKCP18, mwy nag y mae pen isaf unrhyw senario coedwigaeth yn ei chodi.

Newid sylfaenol y gwanwyn a arsylwyd a\'r strwythur gofodol

Cymhariaeth MSL5 (diwedd-ffenestr 2017 yn erbyn diwedd-ffenestr 2023): dyfnhau cymedrig y safle −105 mm (cymedr y rhwydwaith −467 i −572 mm). O 59 ffynnon â data dilys yn y ddwy ffenestr, dyfnhaodd 58 \>25 mm; aeth 0 yn fwy bas \>25 mm. Y gostyngiadau mwyaf ar ymyl arfordirol y de-orllewin (CEH22: −233 mm); y lleiaf ar Ymyl y Llyn dwyreiniol. Nid yw parth y clirdorri\'n dangos signal gwahaniaethadwy.

![](Pictures/10000001000009EE00000967C79BE1C0.png){width="13cm" height="9.377cm"}

Ffigur 4. Newid MSL5 2017→2023. n=59 ffynnon; dyfnhaodd 58 \>25 mm, 0 yn fwy bas \>25 mm. Ffynhonnell: 20_msl5_change_2017_2023.png; Ffigur 72 yr adroddiad.

Mae dadansoddiad symudiad gwanwyn gwahaniaethol (Sgript 32, 2011--2025) yn datgelu tueddiadau dargyfeiriol o fewn y rhwydwaith. Mae C4 Prif Goedwig yn unffurf bositif (+6.9 i +18.9 mm y flwyddyn⁻¹ o\'i gymharu â chymedr y safle, cymedr y clwstwr +13.7 mm y flwyddyn⁻¹); nid oes yr un yn arwyddocaol yn unigol ar ôl cywiriad AR(1). Mae hyn yn adlewyrchu dau fecanwaith atgyfnerthol: (1) mae\'r goedwig yn meddiannu uchafbwynt hydrolig y dyfrhaen, bellaf o unrhyw ffin pen-cyson (llyn i\'r dwyrain, Afon Menai i\'r de-ddwyrain, arfordir i\'r de-orllewin), gan roi\'r rhyddid mwyaf i\'r lefel ddŵr godi mewn blynyddoedd gwlyb a gostwng mewn rhai sych; (2) mae\'r swbstrad cynnyrch-penodol isel (tywod tenau dros graigwely) yn crynhoi ailwefru\'n newidiadau pen mwy. Mae gwanwynau gwlyb diweddar (2021, 2024) wedi mwyhau C4 o\'i gymharu â\'r rhwydwaith. Mae C1 Ymyl y Llyn yn gostwng −5.6 mm y flwyddyn⁻¹ (CEH11 yn arwyddocaol) ac C5 Coedwig Arfordirol −8.5 mm y flwyddyn⁻¹ (NW9, CEH17 a CEH19 yn arwyddocaol), wedi\'u gyrru gan signal ffin cilio\'r arfordir. Mae C2 Twyn tua\'n niwtral ar gyfartaledd.

![](Pictures/100000010000075D0000047A9BEF99AE.png){width="14.986cm" height="10.811cm"}

Ffigur 5. Symudiad gwanwyn gwahaniaethol 2011--2025. C4 yn unffurf bositif (ymateb blwyddyn-wlyb wedi\'i fwyhau + safle uchafbwynt hydrolig); C5 yn unffurf negatif ac C1 yn negatif gan mwyaf (effaith ffin arfordirol). C2/C3 yn niwtral yn fras. Wedi\'i lenwi = arwyddocaol (p wedi\'i gywiro gan AR \< 0.05).

Signal cilio\'r arfordir

Mae atchweliad ar raddfa rhwydwaith o dueddiadau fesul ffynnon yn erbyn y pellter i\'r draethlin sy\'n erydu yn datrys graddiant cilio arfordirol go iawn sy\'n effeithio ar yr ymyl orllewinol. Yn annibynnol, mae trawslun dwy-ffynnon o ffynhonnau rheoli arfordirol yn dirywio mewn patrwm sy\'n gyson ag isel-hau amod-ffin cynyddol. Mae graddiant cilio\'r arfordir yn cyfrif am tua hanner dirywiad eithriadol C5 (53% ar y sail gytbwys), gan adael −17.6 mm y flwyddyn⁻¹ heb ei esbonio; mae\'r gyfran yn sensitif i ba ffynhonnau sydd yn y clwstwr. Mae oediadau lledaeniad dŵr daear yn golygu bod data cyfredol yn rhannol adlewyrchu erydiad hanesyddol; os yw erydiad yn cyflymu, nid yw\'r effeithiau gwaethaf wedi cyrraedd y ffynhonnau mewnol eto. Mae CEH22 (y tu allan i\'r rhwydwaith cyfeirnod, ymyl arfordirol de-orllewinol) yn dirywio ar −27.8 mm y flwyddyn⁻¹ (p \< 0.001), y cyflymaf yn y rhwydwaith.

Graddfa\'r newid a arsylwyd yn ei gyd-destun

Mae\'r ymyriadau rheoli a astudiwyd hyd yma wedi cynhyrchu effeithiau mesuradwy ar y raddfa leol: mae budd y crafu yn CEH36 yn gadarn yn ystadegol ac yn arwyddocaol yn ecolegol, a chynhyrchodd y clirdorri welliant canfyddadwy mewn lefelau dŵr misol cymedrig yn erbyn rheolyddion coedwig. Fodd bynnag, dyfnhaodd sylfaen gwanwyn y safle cyfan 105 mm rhwng ffenestri cymharu 2017 a 2023 --- newid sy\'n effeithio ar 58 o 59 ffynnon a fonitrwyd ar yr un pryd ac wedi\'i yrru gan rymoedd sy\'n gweithredu ar raddfa\'r dyfrhaen gyfan. Mae tymheredd yr haf wedi tueddu i fyny ar +0.014°C y flwyddyn⁻¹ ers 1931, gyda chynnydd cam o +0.94°C uwchlaw\'r llinell sylfaen ers 2013. Mae signal cilio\'r arfordir yn cyfrif am tua hanner dirywiad eithriadol parth y Goedwig Arfordirol, ac mae\'n ymestyn sawl can metr i mewn i\'r tir. Yn erbyn y signalau hyn, mae budd y crafu mewn un ffynnon (+195 mm) a gwelliant misol-cymedrig y clirdorri (+108 mm o\'i gymharu â choedwig heb ei chwympo) yn cynrychioli ymatebion lleol nad ydynt yn newid cyfeiriad y duedd ar draws y rhwydwaith. Mae rhagamcanion UKCP18 yn dangos gostyngiad pellach yn lefel ddŵr yr haf o tua 0.39 m ar draws y safle erbyn y 2080au (0.32 i 0.44 m ar draws y parthau a ragamcanwyd; ni ragamcanir C4), ar ben y 105 mm o ddyfnhau yn sylfaen y gwanwyn a fesurwyd eisoes rhwng ffenestri cymharu 2017 a 2023, gan ragori\'n sylweddol ar unrhyw effaith reoli a arsylwyd yn y cofnod hwn.

Prif ganfyddiadau meintiol

  ------------------------------------------------------------------------- ------------------------------- ----------------
  Canfyddiad                                                                Gwerth                          Ffynhonnell
  Cam crafu CEH36 (BACI pâr)                                                \+ 195 mm p = 0.004             Script 09c
  Cam clirdorri yn erbyn rheolydd Coedwig (cymedr misol)                    \+ 108 mm p = 0.003             Script 10a
  Cam clirdorri yn erbyn rheolydd Coedwig (haf yn unig)                     − 1 mm p = 0.99 (n.s.)          Script 10a
  Newid MSL5 2017→2023 (cymedr y safle)                                     − 105 mm                        Script 26 / 20
  Ffynhonnau a ddyfnhaodd \>25 mm (o 59 dilys)                              58 (98%)                        Script 20
  Tuedd wahaniaethol C4 2011--2025                                          \+ 13.7 mm/yr (cymedr)          Script 32
  Tuedd wahaniaethol C5 2011--2025                                          − 8.5 mm/yr (cymedr)            Script 32
  Cyfernod mwyhau C4 (canonaidd)                                            1.66× cymedr y safle            Script 33/35
  Cyfernod mwyhau C1                                                        0.64× cymedr y safle            Script 33/35
  Tuedd CEH22 (ymyl arfordirol)                                             − 27.8 mm/yr p \< 0.001         Script 32
  Croesiad SD16 C1 (isafswm haf, canolrif bootstrap)                        2027 (CI 90% 2021--2046)        Script 14
  Gostyngiad lefel haf UKCP18 2080au, ar draws y safle (ni ragamcanir C4)   387 mm (319--440 fesul parth)   Script 19
  Newid MSL5 UKCP18 2080au, C1 / C2 / C3 / C5                               +52 / −22 / −150 / −141 mm      Script 19
  ------------------------------------------------------------------------- ------------------------------- ----------------

Tabl 2. Prif ganlyniadau meintiol. Daw\'r holl ffigurau o CSVs y biblinell a ymrwymwyd ar gangen main GitHub.

Casgliadau

> • Y lefel ddŵr isafswm haf yw\'r newidyn sy\'n rhwymo\'n ecolegol. Mae MSL5 yn ddirprwy a fesurir yn well sy\'n olrhain drifft arafach y system ond sy\'n tanamcangyfrif osgled y risg ecolegol, yn enwedig yn y twyni agored (C1, C2), lle mae lefelau rhagamcanol y gwanwyn prin yn symud tra bo lefelau\'r haf yn gostwng mwy na 0.3 m erbyn y 2080au.

> • Crafu twyni mewn safleoedd mewndirol a ddewiswyd yn dda yw\'r ymyrraeth uniongyrchol fwyaf effeithiol sydd ar gael, ond nid yw\'n mynd i\'r afael â\'r gyrwyr sylfaenol. Mae\'r buddion yn erydu yn erbyn tuedd hinsawdd y cefndir.

> • Mae clirdorri yn codi lefelau cymedrig y dŵr ym mharth y goedwig o\'i gymharu â rheolyddion heb eu cwympo ond nid yw\'n cynhyrchu gwelliant isafswm haf canfyddadwy, mae\'r cam ar ei fwyaf yn gynnar (+152 mm hyd at Ragfyr 2020, +39 mm wedi hynny) ac mae\'r ffynnon a gwympwyd yn dangos gostyngiad yn y dynfa heb gynnydd mewn ailwefru (D-239).

> • Mae gostyngiad ar draws y rhwydwaith yn y sensitifrwydd ailwefru yn fecanwaith posibl ar gyfer dirywiad yr isafswm haf; nid yw ei annibyniaeth ar reolaeth wedi\'i sefydlu.

> • Mae signal ffin cilio\'r arfordir yn fygythiad gwahanol, oediog, ac ar hyn o bryd na ellir ei reoli, i\'r ymyl orllewinol. Nid yw\'r ffynhonnau mewnol wedi profi effaith lawn yr erydiad cyflymedig diweddar eto.

> • Mae safle hydrolig y goedwig (uchafbwynt topograffig a dyfrhaen, heb ffin pen-cyson gerllaw) yn ei wneud yn fwyhadur cryf o amrywioldeb hinsawdd o flwyddyn i flwyddyn, nid signal adfer.

> • Mae grymoedd hinsawdd ac arfordirol yn gweithredu ar faint sy\'n gorlifo\'r ymyriadau rheoli lleol a arsylwyd hyd yma.

DRAFFT --- cyfieithiad drafft awtomataidd; rhaid ei wirio gan adolygydd Cymraeg cyn ei ddefnyddio. Cedwir rhifau, symbolau ac enwau sgriptiau yn union fel yn y gwreiddiol Saesneg; mae testun o fewn y ffigurau'n aros yn Saesneg. (Draft --- automated draft translation; must be checked by a Welsh-language reviewer before use. Numbers, symbols and script names are kept exactly as the English original; text inside the figures remains in English.)
