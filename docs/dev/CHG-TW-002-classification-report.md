# CHG-TW-002 DEV classification report

Environment: **DEV** (local box only). Private repository only. Nothing was pushed, sent or published.
Run: 2026-11-17 17:28 SAST (Africa/Johannesburg). Input: the 291 City of Cape Town award-supplier rows of the CHG-TW-001 DEV run
(OCDS SHA-256 `a2849a632148ca1eb59c0ceabeb45de16be0698a1804a485cf93417542435225`, PublicFunds pin `de37f666c12d1d6b7a815860894af0372514ba7f`, read-only) and the
508 City register rows from the same run. No new network fetch.

## 1. Source-field check (done before building)

| Source | Field that carries the supplier name | Rows | Trailing legal suffix | Any legal-form word |
|---|---|---|---|---|
| eTenders OCDS (OCP mirror) | `awards[].suppliers[].name` (same string as `parties[].name` / `parties[].identifier.legalName`) | 291 | **2** | 2 |
| City of Cape Town monthly award register (PDF) | `Vendor` column, parsed to `supplier_name` | 507 named of 508 | **400** | 460 |

Checked in the raw pinned file: 291 supplier `parties[]` entries; `parties[].identifier.legalName` equals `parties[].name` (ignoring case) on 291 of them, and carries a trailing legal suffix on 2.

Plain reading:

* **The OCDS supplier name almost never carries a legal suffix** (2 of 291); 267 of the names are in capitals, and the raw `legalName` field is the same string, so it adds nothing. The OCDS name alone cannot confirm a legal form.
* **The City register `Vendor` column usually does carry a suffix** (400 of 507 rows end the legal name, i.e. the part before any `t/a`, with a suffix; the other rows with a legal word have it inside a multi-vendor line or on a wrapped PDF line).
* **But the two sources cover different periods.** The City register PDFs cover 2026-02, 2026-03, 2026-04, 2026-05, 2026-06, 2026-07, 2026-08, 2026-09, 2026-10; the OCDS Cape Town awards are from award years {2021: 35, 2022: 84, 2023: 52, 2024: 76, 2025: 44}. A City name can be used only where the two-detail rule links it to the award *with the normalised name agreeing*, which is why method 1 reaches only a minority of suppliers.
* Result: method 1 cannot reach high coverage on this data. The two-person queue is large. This is stated, not fudged.

## 2. Counts

| Status | Rows |
|---|---|
| `confirmed_juristic` | 66 |
| `check_queue` | 225 |
| **Total classified** | **291** of 291 input rows (no row unclassified, none hidden) |

Before (CHG-TW-001 rule): {'unknown': 289, 'juristic': 2}. After: {'unknown': 201, 'juristic': 66, 'natural_person': 24}.

### By method

| Method | Rows |
|---|---|
| `city_register_suffix` | 64 |
| `ocds_suffix` | 2 |

`city_register_suffix`: the City register name linked on name + buyer carries the suffix. `ocds_suffix`: the OCDS name itself carries it. `*_before_trading_as`: the suffix is on the legal name before `t/a`.
How the legal form was linked to the award (CHG-TW-001 §19: only a shared tender reference is a tight link):
| `same_record` | 2 |
| `tender_ref` | 5 |
| `name_and_buyer_only` | 59 |

Legal-form fact label: {'Reported': 59, 'Confirmed': 7}. A suffix taken from a City name linked on name + buyer only is labelled
**Reported**, not Confirmed: the City printed that suffix, but the link to the older OCDS award is a name-only match within one buyer.

Confirmed rows where some City spellings of the same name lacked a suffix (noted, not queued): 0.

### By sub-type

| Sub-type | Rows |
|---|---|
| `company` | 56 |
| `close_corporation` | 8 |
| `npc` | 0 |
| `soc` | 0 |
| `trust` | 0 |
| `jv` | 1 |
| `other_juristic` | 1 |

### Queue by reason

| Reason | Rows |
|---|---|
| `looks_like_personal_name` | 24 |
| `name_mismatch_between_sources` | 7 |
| `ambiguous_suffix` | 0 |
| `no_suffix` | 194 |
| `empty_name` | 0 |

Distinct supplier names in the queue: 191.

### POPIA hold

`popia_hold` = true on **29** rows ({'check_queue': 24, 'confirmed_juristic': 5}). The rule is deliberately over-inclusive:
`t/a` without a legal suffix on the legal name, initials plus surname, a title, a trust with a family or person-style stem,
or a bare two-to-four-word name with no business word, digit or legal word. Many held names will turn out to be businesses;
the two-person check releases them. Held names are not written to this report or to any public file.
Of the confirmed rows, 5 are held because one of their source names looks personal; their status stays `confirmed_juristic` but the name is withheld until checked.

### Age indicator

Confirmed rows with a sourced CIPC registration year: **0**. Confirming a legal form does not supply a year,
so the indicator stays Unknown. Indicator counts: {'unknown': 291}; age bands: {'unknown': 291}.
A trust is registered with the Master of the High Court, not CIPC: its CIPC indicator stays Unknown unless a sourced year exists.

### Local public export (DEV, git-ignored)

291 rows written (= input, no silent hide); 61 carry a name (confirmed and not held).
Queued rows keep their row, status and reason, with the name withheld until the two-person check.

## 3. Remaining list for the two-person check (225 rows)

Row ids are internal (`R<n>` is the row position in the DEV warehouse; the OCID and award id locate the source record).
The two checkers read held names from the local DEV warehouse by row id, never from this file.

### `looks_like_personal_name` (24)

| Row id | Award year | Supplier name (OCDS) | POPIA hold | Notes |
|---|---|---|---|---|
| R010 ocds-9t57fa-104508/award 59845 | 2024 | [POPIA hold: name withheld until checked] | yes |  |
| R013 ocds-9t57fa-105268/award 47422 | 2024 | [POPIA hold: name withheld until checked] | yes |  |
| R022 ocds-9t57fa-110367/award 50028 | 2024 | [POPIA hold: name withheld until checked] | yes |  |
| R025 ocds-9t57fa-111886/award 57741 | 2025 | [POPIA hold: name withheld until checked] | yes |  |
| R027 ocds-9t57fa-113274/award 67181 | 2025 | [POPIA hold: name withheld until checked] | yes |  |
| R042 ocds-9t57fa-121240/award 57060 | 2025 | [POPIA hold: name withheld until checked] | yes |  |
| R052 ocds-9t57fa-128776/award 61428 | 2025 | [POPIA hold: name withheld until checked] | yes |  |
| R090 ocds-9t57fa-18670/award 6136 | 2022 | [POPIA hold: name withheld until checked] | yes |  |
| R095 ocds-9t57fa-17979/award 4657 | 2022 | [POPIA hold: name withheld until checked] | yes |  |
| R096 ocds-9t57fa-20662/award 8986 | 2022 | [POPIA hold: name withheld until checked] | yes |  |
| R098 ocds-9t57fa-19643/award 6884 | 2022 | [POPIA hold: name withheld until checked] | yes |  |
| R119 ocds-9t57fa-25884/award 8237 | 2022 | [POPIA hold: name withheld until checked] | yes |  |
| R124 ocds-9t57fa-25901/award 12652 | 2022 | [POPIA hold: name withheld until checked] | yes |  |
| R130 ocds-9t57fa-31018/award 8729 | 2022 | [POPIA hold: name withheld until checked] | yes |  |
| R166 ocds-9t57fa-50062/award 17483 | 2023 | [POPIA hold: name withheld until checked] | yes |  |
| R173 ocds-9t57fa-51855/award 17482 | 2023 | [POPIA hold: name withheld until checked] | yes |  |
| R184 ocds-9t57fa-63040/award 67569 | 2023 | [POPIA hold: name withheld until checked] | yes |  |
| R186 ocds-9t57fa-62996/award 27243 | 2023 | [POPIA hold: name withheld until checked] | yes |  |
| R198 ocds-9t57fa-65662/award 25593 | 2023 | [POPIA hold: name withheld until checked] | yes |  |
| R208 ocds-9t57fa-69549/award 24754 | 2023 | [POPIA hold: name withheld until checked] | yes |  |
| R233 ocds-9t57fa-82641/award 32220 | 2024 | [POPIA hold: name withheld until checked] | yes |  |
| R247 ocds-9t57fa-86709/award 69742 | 2024 | [POPIA hold: name withheld until checked] | yes |  |
| R248 ocds-9t57fa-86716/award 58373 | 2024 | [POPIA hold: name withheld until checked] | yes |  |
| R291 ocds-9t57fa-99404/award 67167 | 2024 | [POPIA hold: name withheld until checked] | yes |  |

### `name_mismatch_between_sources` (7)

| Row id | Award year | Supplier name (OCDS) | POPIA hold | Notes |
|---|---|---|---|---|
| R041 ocds-9t57fa-120846/award 72772 | 2025 | IX ENGINEERS | no | city_names_same_tender_differ |
| R045 ocds-9t57fa-123130/award 59698 | 2025 | NEXTEC SECURITY AND BUILDING TECHNOLOGIES _IOCO SBT | no | city_names_same_tender_differ |
| R048 ocds-9t57fa-124392/award 68694 | 2025 | CT CONTROL SYSTEMS | no | city_names_same_tender_differ |
| R070 ocds-9t57fa-139501/award 72691 | 2025 | LUBOCON CIVILS | no | city_names_same_tender_differ |
| R196 ocds-9t57fa-67264/award 38006 | 2023 | (AR PROJECTS AND DEVELOPMENTS) | no | city_names_same_tender_differ |
| R211 ocds-9t57fa-73435/award 36579 | 2023 | (TRIPLE C MAINTENANCE AND SERVICES) | no | city_names_same_tender_differ |
| R212 ocds-9t57fa-75269/award 37088 | 2023 | (R MAHANGE AND ASSOCIATES) | no | city_names_same_tender_differ |

### `no_suffix` (194)

| Row id | Award year | Supplier name (OCDS) | POPIA hold | Notes |
|---|---|---|---|---|
| R001 ocds-9t57fa-100167/award 47680 | 2024 | CAPE AUTOMATION SYSTEMS | no |  |
| R003 ocds-9t57fa-100172/award 72120 | 2024 | F L O SPECIALIZED PRODUCT SOLUTIONS | no |  |
| R004 ocds-9t57fa-100174/award 57205 | 2024 | BVI CONSULTING ENGINEERS WESTERN CAPE | no |  |
| R005 ocds-9t57fa-100177/award 62894 | 2024 | MOTOROLA SOLUTIONS SOUTH AFRICA | no |  |
| R006 ocds-9t57fa-100946/award 55833 | 2024 | BUSINESS CONNEXION | no |  |
| R007 ocds-9t57fa-100947/award 58827 | 2024 | 4JEN SERVICES | no |  |
| R011 ocds-9t57fa-104508/award 59857 | 2024 | NGCOKOTO GENERAL TRADING | no |  |
| R012 ocds-9t57fa-105263/award 66406 | 2024 | ILISO CONSULTING | no |  |
| R014 ocds-9t57fa-105313/award 58141 | 2024 | F AND A CIVILS | no |  |
| R015 ocds-9t57fa-105313/award 58205 | 2024 | F AND A CIVILS | no |  |
| R016 ocds-9t57fa-106023/award 52960 | 2024 | TGOOD SOUTH AFRICA | no |  |
| R017 ocds-9t57fa-106761/award 68385 | 2024 | CALANDRIA 159 | no |  |
| R018 ocds-9t57fa-107454/award 57743 | 2024 | FS SYSTEMS | no |  |
| R020 ocds-9t57fa-108328/award 48246 | 2024 | FLY BROTHER SA MOBILITY | no |  |
| R021 ocds-9t57fa-108342/award 58732 | 2024 | BONGANI TELECOM | no |  |
| R026 ocds-9t57fa-113266/award 69268 | 2025 | CLAREMART AUCTIONEERS | no |  |
| R031 ocds-9t57fa-11460/award 8082 | 2021 | DELTA FACILITIES MANAGEMENT | no |  |
| R032 ocds-9t57fa-11568/award 2654 | 2021 | KFC PIPES AND FITTINGS | no |  |
| R033 ocds-9t57fa-11570/award 2924 | 2021 | CAPE WINDS OUTSOURCE SOLUTIONS | no |  |
| R034 ocds-9t57fa-116083/award 58419 | 2025 | LAST SAMURAI PROPERTY HOLDINGS 2 | no |  |
| R035 ocds-9t57fa-11661/award 3619 | 2021 | Ramashu Supply and Services | no |  |
| R037 ocds-9t57fa-116840/award 68409 | 2025 | INTEGRATORS OF SYSTEMS TECHNOLOGY | no |  |
| R039 ocds-9t57fa-119908/award 68402 | 2025 | UDAH SOLUTIONS | no |  |
| R040 ocds-9t57fa-119914/award 73195 | 2025 | ONE STOP DRIVING SCHOOL | no |  |
| R043 ocds-9t57fa-121752/award 59699 | 2025 | NEXTEC SECURITY AND BUILDING TECHNOLOGIES | no |  |
| R046 ocds-9t57fa-124376/award 66341 | 2025 | ASLA KONSTRUKSIE | no |  |
| R047 ocds-9t57fa-124381/award 63434 | 2025 | IN2IT | no |  |
| R049 ocds-9t57fa-125170/award 68898 | 2025 | SERVEST | no |  |
| R055 ocds-9t57fa-129380/award 73398 | 2025 | TSHIRELETSO MULTI-SKILLS AND TRAINING | no |  |
| R057 ocds-9t57fa-130083/award 68346 | 2025 | INNOVATIVE TRANSPORT SOLUTIONS | no |  |
| R059 ocds-9t57fa-131547/award 67276 | 2025 | SOUTHERN AFRICA FAULT LOCATION | no |  |
| R061 ocds-9t57fa-132947/award 73973 | 2025 | CORNERSTONE INFRASTRUCTURE ADVISORS | no |  |
| R062 ocds-9t57fa-133699/award 66280 | 2025 | ASLA KONSTRUKSIE | no |  |
| R064 ocds-9t57fa-136453/award 71014 | 2025 | UMTHA STRATEGY PLANNING AND DEVELOPMENT CONSULTANCY | no |  |
| R072 ocds-9t57fa-15926/award 3094 | 2022 | YMS Medical Supplies | no |  |
| R073 ocds-9t57fa-15928/award 3556 | 2022 | PUBLIC DISCIPLINE AND INTEGRATION OF TECHNOLOGY CAPE TOWN | no |  |
| R075 ocds-9t57fa-15930/award 2723 | 2022 | ZIMELE ERP IT SERVICES | no |  |
| R076 ocds-9t57fa-15931/award 3511 | 2022 | Dalag Creations | no |  |
| R077 ocds-9t57fa-15941/award 5715 | 2022 | SP PRACTICE CONSULTING SERVICES | no |  |
| R079 ocds-9t57fa-15994/award 5154 | 2022 | ZIMELE ERP IT SERVICES | no |  |
| R080 ocds-9t57fa-16582/award 3657 | 2022 | EXEO KHOKELA CIVIL ENGINEERING CONSTRUCTION | no |  |
| R081 ocds-9t57fa-16583/award 3353 | 2022 | AVTS ROADWORTHY STATIONS | no |  |
| R082 ocds-9t57fa-16596/award 3908 | 2022 | BARLOWORLD SOUTH AFRICA | no |  |
| R083 ocds-9t57fa-16605/award 6647 | 2022 | RADS INVESTMENTS | no |  |
| R084 ocds-9t57fa-16552/award 3347 | 2022 | BEA S PRINT AND FINISH SOLUTIONS | no |  |
| R085 ocds-9t57fa-17165/award 4559 | 2022 | HE AND SHE DRIVER TRAINING CENTRE | no |  |
| R087 ocds-9t57fa-17174/award 3771 | 2022 | INNOVO NETWORKS | no |  |
| R088 ocds-9t57fa-18649/award 3921 | 2022 | Uhambo Procurement and Distribution | no |  |
| R089 ocds-9t57fa-18670/award 6134 | 2022 | TAKE NOTE TRADING 245 | no |  |
| R091 ocds-9t57fa-17914/award 3340 | 2022 | Dimension Data | no |  |
| R097 ocds-9t57fa-19452/award 6120 | 2022 | SHAR CIVILS | no |  |
| R099 ocds-9t57fa-19645/award 5608 | 2022 | MD CIVILS | no |  |
| R101 ocds-9t57fa-19674/award 12770 | 2022 | BERGSTAN SOUTH AFRICA CONSULTING AND DEVELOPMENT ENGINEERS | no |  |
| R102 ocds-9t57fa-19890/award 4557 | 2022 | K AND A MARKETING | no |  |
| R103 ocds-9t57fa-20180/award 19984 | 2022 | INNOVATIVE TRANSPORT SOLUTIONS | no |  |
| R104 ocds-9t57fa-20188/award 4608 | 2022 | TEDD CUTTER ENTERPRISES | no |  |
| R105 ocds-9t57fa-20226/award 8843 | 2022 | Newfil Consultancy | no |  |
| R106 ocds-9t57fa-20227/award 16356 | 2022 | STELLENBOSCH PREMIER MANUFACTURERS | no |  |
| R107 ocds-9t57fa-21266/award 18826 | 2022 | DIMENSION DATA | no |  |
| R108 ocds-9t57fa-21266/award 18828 | 2022 | IT NALEDI SOLUTIONS | no |  |
| R109 ocds-9t57fa-21270/award 6872 | 2022 | ACTOM | no |  |
| R110 ocds-9t57fa-22978/award 5883 | 2022 | MASSAMATIC | no |  |
| R111 ocds-9t57fa-22987/award 8629 | 2022 | SOUTHERN AFRICA FAULT LOCATION | no |  |
| R112 ocds-9t57fa-22061/award 5603 | 2022 | DATACENTRIX | no |  |
| R114 ocds-9t57fa-22068/award 10549 | 2022 | GREYSTONE TRADING 389 | no |  |
| R115 ocds-9t57fa-22072/award 6513 | 2022 | AAM GEOMATICS | no |  |
| R116 ocds-9t57fa-22078/award 16692 | 2022 | GEONOPLIS AND ASSOCIATES | no |  |
| R117 ocds-9t57fa-24150/award 7304 | 2022 | PDT IRONMONGERY SUPPLIERS | no |  |
| R118 ocds-9t57fa-25863/award 17335 | 2022 | SAKH'IKHAYA SUPPLIERS | no |  |
| R120 ocds-9t57fa-25885/award 13219 | 2022 | LAST SAMURAI PROPERTY HOLDINGS 2 | no |  |
| R121 ocds-9t57fa-25892/award 20418 | 2022 | SYNTELL | no |  |
| R122 ocds-9t57fa-25893/award 9524 | 2022 | SAFAZ CONSTRUCTION R A C | no |  |
| R123 ocds-9t57fa-25896/award 5000 | 2022 | OPTRON | no |  |
| R125 ocds-9t57fa-25964/award 13562 | 2022 | ENVIROSERV WASTE MANAGEMENT | no |  |
| R126 ocds-9t57fa-30040/award 10825 | 2022 | TOPEND TRADING 159 | no |  |
| R128 ocds-9t57fa-30901/award 12298 | 2022 | CIVIL ELEMENT | no |  |
| R132 ocds-9t57fa-31778/award 13926 | 2022 | CEMEX TRADING ENTERPRISE | no |  |
| R134 ocds-9t57fa-31784/award 15317 | 2022 | INTER-WASTE | no |  |
| R135 ocds-9t57fa-31987/award 9260 | 2022 | ALIJAC HIRING SERVICES | no |  |
| R136 ocds-9t57fa-31998/award 14278 | 2022 | UMDLA CIVILS | no |  |
| R137 ocds-9t57fa-32574/award 9364 | 2022 | ENERGYSYSTEMSSA | no |  |
| R138 ocds-9t57fa-32591/award 8247 | 2022 | CALANDRIA 159 | no |  |
| R139 ocds-9t57fa-32632/award 8990 | 2022 | CSV CONSTRUCTION | no |  |
| R140 ocds-9t57fa-32648/award 15556 | 2022 | KAI MA SERVICES | no |  |
| R142 ocds-9t57fa-32694/award 23019 | 2022 | MOBILE TELEPHONE NETWORKS | no |  |
| R144 ocds-9t57fa-35138/award 18487 | 2022 | ONE STOP DRIVING SCHOOL | no |  |
| R145 ocds-9t57fa-35146/award 74879 | 2022 | EPI-USE AFRICA | no |  |
| R146 ocds-9t57fa-38240/award 13939 | 2022 | ASLA KONSTRUKSIE | no |  |
| R147 ocds-9t57fa-37504/award 13818 | 2022 | INDUSTRIES EDUCATION AND TRAINING INSTITUTE | no |  |
| R148 ocds-9t57fa-38445/award 13784 | 2022 | GEONOPLIS AND ASSOCIATES | no |  |
| R149 ocds-9t57fa-41869/award 34519 | 2022 | (GEONOPLIS AND ASSOCIATES) | no |  |
| R150 ocds-9t57fa-41891/award 20583 | 2022 | DIMENSION DATA | no |  |
| R152 ocds-9t57fa-43114/award 17582 | 2022 | TEFLA GROUP | no |  |
| R153 ocds-9t57fa-43132/award 13253 | 2022 | IDTEK Solutions | no |  |
| R155 ocds-9t57fa-42510/award 20179 | 2022 | KAI MA SERVICES | no |  |
| R156 ocds-9t57fa-47399/award 18206 | 2023 | Ryan cris Trading | no |  |
| R157 ocds-9t57fa-47400/award 20562 | 2023 | Urban Status Rentals | no |  |
| R159 ocds-9t57fa-48053/award 18328 | 2023 | Take Note Trading 661 | no |  |
| R160 ocds-9t57fa-48060/award 18440 | 2023 | DIMENSION DATA | no |  |
| R161 ocds-9t57fa-48064/award 32109 | 2023 | (CAPE AUTOMATION SYSTEMS) | no |  |
| R162 ocds-9t57fa-48069/award 25594 | 2023 | (DIMENSION DATA) | no |  |
| R163 ocds-9t57fa-48243/award 13550 | 2023 | JOAT SALES AND SERVICES | no |  |
| R164 ocds-9t57fa-50883/award 15433 | 2023 | Sigma Lifts and Escalators | no |  |
| R165 ocds-9t57fa-50886/award 15435 | 2023 | Sharon Rose Trading | no |  |
| R167 ocds-9t57fa-50961/award 20570 | 2023 | ALUTE SA | no |  |
| R168 ocds-9t57fa-50962/award 18479 | 2023 | MMS COMMUNICATIONS SOUTH AFRICA | no |  |
| R170 ocds-9t57fa-50047/award 28846 | 2023 | (IMPOLO TRADING SOLUTIONS) | no |  |
| R172 ocds-9t57fa-51854/award 36250 | 2023 | (MPAMOT AFRICA) | no |  |
| R174 ocds-9t57fa-52463/award 15454 | 2023 | NJONGO HOLDINGS | no |  |
| R175 ocds-9t57fa-52476/award 35865 | 2023 | (IKAPA RETICULATION AND FLOW) | no |  |
| R177 ocds-9t57fa-5254/award 4074 | 2021 | LAST SAMURAI PROPERTY HOLDINGS 2 | no |  |
| R178 ocds-9t57fa-5254/award 4076 | 2021 | XIGWILI PROJECT MANAGEMENT | no |  |
| R179 ocds-9t57fa-53476/award 20316 | 2023 | FURIPOINT | no |  |
| R181 ocds-9t57fa-52895/award 25586 | 2023 | (ZIMELE ERP IT SERVICES) | no |  |
| R182 ocds-9t57fa-52907/award 20573 | 2023 | NCC Environmental Services | no |  |
| R183 ocds-9t57fa-61645/award 28841 | 2023 | (DE KOCK AND CRONJE) | no |  |
| R185 ocds-9t57fa-62995/award 28847 | 2023 | (KADER TECHNOLOGIES) | no |  |
| R187 ocds-9t57fa-62392/award 20986 | 2023 | FALCODOR 119 | no |  |
| R189 ocds-9t57fa-64727/award 32001 | 2023 | (AERIOS GLOBAL AVIATION) | no |  |
| R190 ocds-9t57fa-64733/award 70377 | 2023 | KADER TECHNOLOGIES | no |  |
| R191 ocds-9t57fa-6613/award 2953 | 2021 | EASYPAY | no |  |
| R193 ocds-9t57fa-6621/award 2186 | 2021 | COMPASS MEDICAL WASTE SERVICES | no |  |
| R194 ocds-9t57fa-6624/award 2729 | 2021 | Motorola Solutions South Africa | no |  |
| R195 ocds-9t57fa-6659/award 2656 | 2021 | QSK ENGINEERING | no |  |
| R199 ocds-9t57fa-68081/award 32262 | 2023 | (BLACK ECONOMIC EMPOWERMENT VERIFICATION AGENCY) | no |  |
| R200 ocds-9t57fa-68089/award 68348 | 2023 | NEW RECRUITMENT TRANSPORT | no |  |
| R201 ocds-9t57fa-68109/award 36331 | 2023 | (INDUSTRIES EDUCATION AND TRAINING INSTITUTE) | no |  |
| R203 ocds-9t57fa-68199/award 27824 | 2023 | (SOARING SUMMITS GROUP) | no |  |
| R204 ocds-9t57fa-67430/award 20695 | 2023 | Kouga Development Company | no |  |
| R205 ocds-9t57fa-68727/award 49105 | 2023 | RESOURCE INNOVATIONS AFRICA | no |  |
| R206 ocds-9t57fa-69497/award 48932 | 2023 | NJONGO HOLDINGS | no |  |
| R207 ocds-9t57fa-69506/award 31020 | 2023 | (CHLORCAPE) | no |  |
| R209 ocds-9t57fa-71216/award 67347 | 2023 | CONCOR CONSTRUCTION | no |  |
| R213 ocds-9t57fa-76062/award 38498 | 2023 | SIBANYE OFFICE SOLUTIONS | no |  |
| R215 ocds-9t57fa-79292/award 66653 | 2024 | GUERRINI MARINE CONSTRUCTION | no |  |
| R216 ocds-9t57fa-79293/award 36488 | 2024 | (TRIPLE C MAINTENANCE AND SERVICES) | no |  |
| R217 ocds-9t57fa-79304/award 38857 | 2024 | (TRIPLE C MAINTENANCE AND SERVICES) | no |  |
| R218 ocds-9t57fa-79305/award 39685 | 2024 | (AL SUPPLIES GROUP) | no |  |
| R219 ocds-9t57fa-7662/award 2155 | 2021 | MPULUZANA TRADING | no |  |
| R220 ocds-9t57fa-8121/award 3330 | 2021 | SP Practice Consulting Services | no |  |
| R221 ocds-9t57fa-8124/award 1521 | 2021 | Managed Integrity Evaluation | no |  |
| R222 ocds-9t57fa-8160/award 4068 | 2021 | CAPE ARMATURE WINDERS | no |  |
| R223 ocds-9t57fa-8163/award 3639 | 2021 | Ngcokoto General Trading | no |  |
| R224 ocds-9t57fa-8175/award 3157 | 2021 | ENERGY MANAGEMENT AND VALIDATION SERVICES | no |  |
| R226 ocds-9t57fa-80925/award 68334 | 2024 | DEMOLITION TECHNOLOGIES | no |  |
| R228 ocds-9t57fa-80925/award 68337 | 2024 | IAN DICKIE AND COMPANY | no |  |
| R229 ocds-9t57fa-80925/award 68338 | 2024 | PHILTECH PROJECTS | no |  |
| R231 ocds-9t57fa-81809/award 46318 | 2024 | LIQUID TELECOMMUNICATIONS SOUTH AFRICA | no |  |
| R232 ocds-9t57fa-8219/award 4821 | 2021 | RONWIC MOTORS | no |  |
| R235 ocds-9t57fa-85670/award 39316 | 2024 | (GLS CONSULTING) | no |  |
| R236 ocds-9t57fa-8721/award 2950 | 2021 | ONLAB SPECIALIST ELECTRO-TECHNOLOGY | no |  |
| R237 ocds-9t57fa-8724/award 2133 | 2021 | TELKOM SA | no |  |
| R238 ocds-9t57fa-87362/award 39317 | 2024 | (GLS CONSULTING) | no |  |
| R239 ocds-9t57fa-87366/award 66567 | 2024 | IDTEK SOLUTIONS | no |  |
| R240 ocds-9t57fa-87419/award 38954 | 2024 | (SUSTAINABLE ENERGY AFRICA) | no |  |
| R242 ocds-9t57fa-88485/award 36005 | 2024 | (UHAMBO SAFETY WEAR AND EQUIPMENT) | no |  |
| R243 ocds-9t57fa-88494/award 66636 | 2024 | ASLA KONSTRUKSIE | no |  |
| R245 ocds-9t57fa-86703/award 39697 | 2024 | (GUERRINI MARINE CONSTRUCTION) | no |  |
| R246 ocds-9t57fa-86708/award 43658 | 2024 | ZANA MANZ'I SERVICES | no |  |
| R249 ocds-9t57fa-90381/award 43978 | 2024 | VOLVO GROUP SOUTHERN AFRICA | no |  |
| R250 ocds-9t57fa-90383/award 55821 | 2024 | S A FIRE AND MEDICAL ACADEMY | no |  |
| R251 ocds-9t57fa-90384/award 67169 | 2024 | TOPENG CONSULTING | no |  |
| R252 ocds-9t57fa-90398/award 67314 | 2024 | MMS COMMUNICATIONS SOUTH AFRICA | no |  |
| R253 ocds-9t57fa-90405/award 72899 | 2024 | INDUSTRIES EDUCATION AND TRAINING INSTITUTE | no |  |
| R254 ocds-9t57fa-88900/award 68107 | 2024 | OPENSOURCE INTELLIGENT SOLUTIONS | no |  |
| R255 ocds-9t57fa-88900/award 68108 | 2024 | SP PRACTICE CONSULTING SERVICES | no |  |
| R256 ocds-9t57fa-89699/award 51806 | 2024 | LINAMANDLA BUSINESS ENTERPRISE | no |  |
| R257 ocds-9t57fa-91552/award 69753 | 2024 | SCHWEITZER ENGINEERING LABORATORIES | no |  |
| R258 ocds-9t57fa-91553/award 68231 | 2024 | STOCKLOG | no |  |
| R260 ocds-9t57fa-92882/award 54614 | 2024 | ABEC ADVANCED INFRASTRUCTURE | no |  |
| R261 ocds-9t57fa-9311/award 14049 | 2021 | ERNST AND YOUNG ADVISORY SERVICES | no |  |
| R262 ocds-9t57fa-9312/award 3335 | 2021 | Marce Projects | no |  |
| R263 ocds-9t57fa-9315/award 3503 | 2021 | Integrum Global Solutions | no |  |
| R264 ocds-9t57fa-9320/award 3333 | 2021 | SGT Solutions | no |  |
| R265 ocds-9t57fa-93378/award 66879 | 2024 | KHABOKEDI WASTE MANAGEMENT | no |  |
| R266 ocds-9t57fa-93380/award 51786 | 2024 | GUNNING CONSTRUCTION AND CIVILS | no |  |
| R269 ocds-9t57fa-93969/award 67324 | 2024 | LEGENDS INFORMATION AND COMMUNICATION TECHNOLOGY | no |  |
| R270 ocds-9t57fa-95071/award 67095 | 2024 | MBELE ELECTRICAL | no |  |
| R271 ocds-9t57fa-95075/award 47984 | 2024 | TEBKHAN INVESTMENTS | no |  |
| R272 ocds-9t57fa-95096/award 54924 | 2024 | PRECISION METERS | no |  |
| R273 ocds-9t57fa-9302/award 9434 | 2021 | EMPA STRUCTURES | no |  |
| R274 ocds-9t57fa-95744/award 73626 | 2024 | KTP PROCUREMENT AND LOGISTICS | no |  |
| R277 ocds-9t57fa-95758/award 49417 | 2024 | FRONTLINE OCCUPATIONAL SAFETY CONSULTANCY AND SERVICES | no |  |
| R278 ocds-9t57fa-9687/award 4058 | 2021 | ESOR CONSTRUCTION | no |  |
| R279 ocds-9t57fa-96521/award 59527 | 2024 | CSX CUSTOMER SERVICES | no |  |
| R280 ocds-9t57fa-96522/award 42404 | 2024 | (CENTREMARK ROADMARKING) | no |  |
| R281 ocds-9t57fa-96524/award 68227 | 2024 | TELKOM SA | no |  |
| R282 ocds-9t57fa-96524/award 68228 | 2024 | CALMEX MOBILE | no |  |
| R284 ocds-9t57fa-96532/award 53492 | 2024 | MALESELA TAIHAN ELECTRIC CABLE | no |  |
| R285 ocds-9t57fa-9815/award 2684 | 2021 | UHLAZA GROUP | no |  |
| R286 ocds-9t57fa-9817/award 3635 | 2021 | DIMENSION DATA | no |  |
| R288 ocds-9t57fa-9896/award 3387 | 2021 | SRK CONSULTING (SOUTH AFRICA) | no |  |
| R289 ocds-9t57fa-9926/award 3500 | 2021 | Eli Marketing | no |  |
| R290 ocds-9t57fa-9927/award 3617 | 2021 | Phakamile Industries | no |  |

## 4. Confirmed rows (66)

| Row id | Method | Link | Label | Sub-type | Suffix | Name shown | Notes |
|---|---|---|---|---|---|---|---|
| R002 ocds-9t57fa-100171/award 50470 | `city_register_suffix` | `name_and_buyer_only` | Reported | `company` | (Pty) Ltd | Bloemhof Electrical (Pty) Ltd |  |
| R008 ocds-9t57fa-100960/award 48928 | `city_register_suffix` | `name_and_buyer_only` | Reported | `company` | (Pty) Ltd | Waste Carriers (Pty) Ltd |  |
| R009 ocds-9t57fa-10364/award 2181 | `city_register_suffix` | `name_and_buyer_only` | Reported | `close_corporation` | CC | Cyberfox CC |  |
| R019 ocds-9t57fa-107458/award 52226 | `city_register_suffix` | `name_and_buyer_only` | Reported | `company` | (Pty) Ltd | H & I Construction (Pty) Ltd |  |
| R023 ocds-9t57fa-110381/award 68233 | `city_register_suffix` | `tender_ref` | Confirmed | `company` | (Pty) Ltd | Martin and East (Pty) Ltd |  |
| R024 ocds-9t57fa-111866/award 52086 | `city_register_suffix` | `name_and_buyer_only` | Reported | `company` | (Pty) Ltd | Civils 2000 (Pty) Ltd |  |
| R028 ocds-9t57fa-113274/award 68608 | `city_register_suffix` | `name_and_buyer_only` | Reported | `company` | (Pty) Ltd | [POPIA hold: name withheld until checked] |  |
| R029 ocds-9t57fa-113283/award 61913 | `city_register_suffix` | `name_and_buyer_only` | Reported | `company` | (Pty) Ltd | Isuzu Truck Centre (Pty) Ltd |  |
| R030 ocds-9t57fa-113992/award 55844 | `ocds_suffix` | `same_record` | Confirmed | `other_juristic` | RF | NEIL LYNERS AND ASSOCIATES (RF) |  |
| R036 ocds-9t57fa-116820/award 58709 | `city_register_suffix` | `name_and_buyer_only` | Reported | `company` | (Pty) Ltd | Tuboseal Services (Pty) Ltd |  |
| R038 ocds-9t57fa-119250/award 58706 | `city_register_suffix` | `name_and_buyer_only` | Reported | `company` | (Pty) Ltd | Construction Materials Technologies (Pty) Ltd |  |
| R044 ocds-9t57fa-123040/award 68048 | `city_register_suffix` | `name_and_buyer_only` | Reported | `company` | (Pty) Ltd | Umzali Civils (Pty) Ltd |  |
| R050 ocds-9t57fa-126219/award 71314 | `city_register_suffix` | `tender_ref` | Confirmed | `company` | (Pty) Ltd | Cocopan (Pty) Ltd |  |
| R051 ocds-9t57fa-128103/award 67214 | `city_register_suffix` | `name_and_buyer_only` | Reported | `company` | (Pty) Ltd | Nammic Western Cape (Pty) Ltd |  |
| R053 ocds-9t57fa-129370/award 67691 | `city_register_suffix` | `name_and_buyer_only` | Reported | `company` | (Pty) Ltd | [POPIA hold: name withheld until checked] |  |
| R054 ocds-9t57fa-129371/award 68584 | `city_register_suffix` | `name_and_buyer_only` | Reported | `company` | (Pty) Ltd | On Point On Time Solutions (Pty) Ltd |  |
| R056 ocds-9t57fa-130082/award 68311 | `city_register_suffix` | `name_and_buyer_only` | Reported | `company` | (Pty) Ltd | Nammic Western Cape (Pty) Ltd |  |
| R058 ocds-9t57fa-130844/award 65462 | `city_register_suffix` | `name_and_buyer_only` | Reported | `company` | (Pty) Ltd | Evolution Technology Group (Pty) Ltd |  |
| R060 ocds-9t57fa-132945/award 70571 | `city_register_suffix` | `name_and_buyer_only` | Reported | `company` | (Pty) Ltd | Civils 2000 (Pty) Ltd |  |
| R063 ocds-9t57fa-133689/award 75759 | `city_register_suffix` | `name_and_buyer_only` | Reported | `company` | (Pty) Ltd | Transtruct (Pty) Ltd |  |
| R065 ocds-9t57fa-135728/award 70085 | `city_register_suffix` | `name_and_buyer_only` | Reported | `company` | (Pty) Ltd | Civils 2000 (Pty) Ltd |  |
| R066 ocds-9t57fa-137906/award 75784 | `city_register_suffix` | `name_and_buyer_only` | Reported | `close_corporation` | CC | Pyramid Electrical Contractors CC |  |
| R067 ocds-9t57fa-137150/award 69125 | `city_register_suffix` | `name_and_buyer_only` | Reported | `close_corporation` | CC | Bridge Jointing CC |  |
| R068 ocds-9t57fa-137155/award 73334 | `city_register_suffix` | `tender_ref` | Confirmed | `company` | (Pty) Ltd | Verotest Holdings (Pty) Ltd |  |
| R069 ocds-9t57fa-139499/award 64996 | `city_register_suffix` | `tender_ref` | Confirmed | `company` | (Pty) Ltd | VE Reticulation (Pty) Ltd |  |
| R071 ocds-9t57fa-139507/award 70554 | `city_register_suffix` | `tender_ref` | Confirmed | `company` | (Pty) Ltd | Hypower Heavy Current Maintenance (Pty) Ltd |  |
| R074 ocds-9t57fa-15929/award 5881 | `city_register_suffix` | `name_and_buyer_only` | Reported | `company` | (Pty) Ltd | Waste Carriers (Pty) Ltd |  |
| R078 ocds-9t57fa-15956/award 9391 | `city_register_suffix` | `name_and_buyer_only` | Reported | `company` | (Pty) Ltd | EAS Infrastructure Engineers (Pty) Ltd |  |
| R086 ocds-9t57fa-17166/award 9353 | `city_register_suffix` | `name_and_buyer_only` | Reported | `company` | (Pty) Ltd | Martin & East (Pty) Ltd |  |
| R092 ocds-9t57fa-17934/award 6930 | `city_register_suffix` | `name_and_buyer_only` | Reported | `company` | (Pty) Ltd | Waste Mart (Pty) Ltd |  |
| R093 ocds-9t57fa-17936/award 9683 | `city_register_suffix` | `name_and_buyer_only` | Reported | `company` | (Pty) Ltd | Martin & East (Pty) Ltd |  |
| R094 ocds-9t57fa-17940/award 6145 | `city_register_suffix` | `name_and_buyer_only` | Reported | `company` | (Pty) Ltd | Lazar (Pty) Ltd |  |
| R100 ocds-9t57fa-19659/award 6116 | `city_register_suffix` | `name_and_buyer_only` | Reported | `company` | (Pty) Ltd | Tolplan (Pty) Ltd |  |
| R113 ocds-9t57fa-22063/award 19493 | `city_register_suffix` | `name_and_buyer_only` | Reported | `company` | (Pty) Ltd | Civils 2000 (Pty) Ltd |  |
| R127 ocds-9t57fa-30042/award 27528 | `city_register_suffix` | `name_and_buyer_only` | Reported | `company` | (Pty) Ltd | ABB South Africa (Pty) Ltd |  |
| R129 ocds-9t57fa-30901/award 12299 | `city_register_suffix` | `name_and_buyer_only` | Reported | `close_corporation` | CC | AmandlaGCF Construction CC; |  |
| R131 ocds-9t57fa-31772/award 19456 | `city_register_suffix` | `name_and_buyer_only` | Reported | `close_corporation` | CC | San Building Maintenance CC |  |
| R133 ocds-9t57fa-31778/award 13929 | `city_register_suffix` | `name_and_buyer_only` | Reported | `company` | (Pty) Ltd | Waste Carriers (Pty) Ltd |  |
| R141 ocds-9t57fa-32654/award 20306 | `city_register_suffix` | `name_and_buyer_only` | Reported | `company` | (Pty) Ltd | Martin & East (Pty) Ltd |  |
| R143 ocds-9t57fa-35931/award 13114 | `city_register_suffix` | `name_and_buyer_only` | Reported | `close_corporation` | CC | JT Maritz Electrical CC |  |
| R151 ocds-9t57fa-42083/award 13918 | `city_register_suffix` | `name_and_buyer_only` | Reported | `company` | (Pty) Ltd | Hidro-Tech Systems (Pty) Ltd |  |
| R154 ocds-9t57fa-43190/award 15198 | `city_register_suffix` | `name_and_buyer_only` | Reported | `close_corporation` | CC | AmandlaGCF Construction CC; |  |
| R158 ocds-9t57fa-48037/award 35538 | `city_register_suffix` | `name_and_buyer_only` | Reported | `company` | (Pty) Ltd | [POPIA hold: name withheld until checked] |  |
| R169 ocds-9t57fa-50043/award 14266 | `city_register_suffix` | `name_and_buyer_only` | Reported | `company` | (Pty) Ltd | Taurus Energy Services (Pty) Ltd |  |
| R171 ocds-9t57fa-51839/award 25583 | `city_register_suffix` | `name_and_buyer_only` | Reported | `company` | (Pty) Ltd | [POPIA hold: name withheld until checked] |  |
| R176 ocds-9t57fa-52490/award 13559 | `city_register_suffix` | `name_and_buyer_only` | Reported | `company` | (Pty) Ltd | Chemtoll (Pty) Ltd |  |
| R180 ocds-9t57fa-52883/award 18474 | `city_register_suffix` | `name_and_buyer_only` | Reported | `company` | (Pty) Ltd | Powercomm Solutions (Pty) Ltd |  |
| R188 ocds-9t57fa-62410/award 28838 | `city_register_suffix` | `name_and_buyer_only` | Reported | `company` | (Pty) Ltd | Succido Enterprises (Pty) Ltd |  |
| R192 ocds-9t57fa-6620/award 3938 | `city_register_suffix` | `name_and_buyer_only` | Reported | `company` | (Pty) Ltd | Alexander Forbes Financial Services (Pty) Ltd |  |
| R197 ocds-9t57fa-67265/award 39000 | `city_register_suffix` | `name_and_buyer_only` | Reported | `company` | (Pty) Ltd | Bohlabela Systems (Pty) Ltd |  |
| R202 ocds-9t57fa-68148/award 37628 | `city_register_suffix` | `name_and_buyer_only` | Reported | `company` | (Pty) Ltd | Civils 2000 (Pty) Ltd |  |
| R210 ocds-9t57fa-73431/award 67263 | `city_register_suffix` | `name_and_buyer_only` | Reported | `company` | (Pty) Ltd | Regend Services (Pty) Ltd |  |
| R214 ocds-9t57fa-76101/award 49260 | `city_register_suffix` | `name_and_buyer_only` | Reported | `close_corporation` | CC | FG Jacobs Transport CC |  |
| R225 ocds-9t57fa-8044/award 8852 | `city_register_suffix` | `name_and_buyer_only` | Reported | `company` | (Pty) Ltd | Tuboseal Services (Pty) Ltd |  |
| R227 ocds-9t57fa-80925/award 68335 | `city_register_suffix` | `name_and_buyer_only` | Reported | `company` | (Pty) Ltd | Juno Corp (Pty) Ltd |  |
| R230 ocds-9t57fa-81796/award 50146 | `city_register_suffix` | `name_and_buyer_only` | Reported | `company` | (Pty) Ltd | SEM Solutions (Pty) Ltd |  |
| R234 ocds-9t57fa-85661/award 46560 | `ocds_suffix` | `same_record` | Confirmed | `jv` | JV | QUBEKELA PROJECTS MIS JV |  |
| R241 ocds-9t57fa-87947/award 38493 | `city_register_suffix` | `name_and_buyer_only` | Reported | `company` | Inc | [POPIA hold: name withheld until checked] |  |
| R244 ocds-9t57fa-88499/award 68310 | `city_register_suffix` | `name_and_buyer_only` | Reported | `company` | (Pty) Ltd | Waste Carriers (Pty) Ltd |  |
| R259 ocds-9t57fa-9251/award 3116 | `city_register_suffix` | `name_and_buyer_only` | Reported | `company` | (Pty) Ltd | Ruwacon (Pty) Ltd., |  |
| R267 ocds-9t57fa-93381/award 66283 | `city_register_suffix` | `name_and_buyer_only` | Reported | `company` | (Pty) Ltd | Afriline Civils (Pty) Ltd |  |
| R268 ocds-9t57fa-93968/award 65930 | `city_register_suffix` | `name_and_buyer_only` | Reported | `company` | (Pty) Ltd | Regend Services (Pty) Ltd |  |
| R275 ocds-9t57fa-95754/award 54828 | `city_register_suffix` | `name_and_buyer_only` | Reported | `company` | (Pty) Ltd | Umzali Civils (Pty) Ltd |  |
| R276 ocds-9t57fa-95756/award 54611 | `city_register_suffix` | `name_and_buyer_only` | Reported | `company` | (Pty) Ltd | TMT Services and Supplies (Pty) Ltd |  |
| R283 ocds-9t57fa-96526/award 53491 | `city_register_suffix` | `name_and_buyer_only` | Reported | `company` | (Pty) Ltd | Landis & Gyr (Pty) Ltd |  |
| R287 ocds-9t57fa-9849/award 4055 | `city_register_suffix` | `name_and_buyer_only` | Reported | `company` | (Pty) Ltd | Tuboseal Services (Pty) Ltd |  |

Fact labels: award rows **Confirmed** as published by the source. Legal form **Confirmed** where the suffix is in the OCDS record itself or in a
City row that shares the tender reference; **Reported** where the City row is linked on name + buyer only. No link uses a registry number.
Registration year: **Unknown** unless sourced. `Right of reply: pending` on every row.
