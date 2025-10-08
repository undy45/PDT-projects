# 1. Uloha import datasetu

## 1. Opis algoritmu

Na import do databaze sme pouzili nasledujuci postup:

1. Vytvorenie tabuliek a indexov v databazi
2. Import datasetu z jsonl.gz suboru do pamate
3. Preformatovanie dat do tried objektov v zlozke `models`
4. Upratanie hashtagov aby boli unikatne
5. Vytvorenie in memory CSV subora z daneho batchu pre kazdu tabulku
6. Pouzitie `COPY` príkazu na import dat z CSV suboru do tmp tabulky
7. `INSERT` s `ON CONFLICT DO NOTHING` na import dat z tmp tabulky do cielovej tabulky

Kazdu danu cast algoritmu si blizsie popiseme

### 1.1. Vytvorenie tabuliek a indexov v databazi

Mame prikladovy subor `create_tables.sql` ktory obsahuje prikazy na vytvorenie tabuliek a indexov. Tento subor sme
pustali rucne do cielovej databazy.

### 1.2. Import datasetu z jsonl.gz suboru do pamate

Zakladne citanie dat z jsonl.gz suboru sme realizovali pomocou kniznice `gzip` a `json` v jazyku Python. Samozrejme sme
citali po riadkoch a citali sme do tej doby pokym sme nemali pocet ziskanych tweets vacsi ako konstantu `BATCH_SIZE`.
Tento pristup nam umoznil spracovat aj velmi velke subory bez toho aby sme narazili na nedostatok pamate. Konstanta
`BATCH_SIZE` bola pre moj pocitac nastavena na hodnotu 10^7, coz malo za ucinok ze sme boli schopny vzdy nacitat cely
subor do pamate a nasledne ho davat do db cely.

### 1.3. Preformatovanie dat do tried objektov v zlozke `models`

Na to aby sme mohli normalne pracovat s datami tak sme vytvorili metodu `parse_json` ktora parsovala jeden riadok
precitaneho suboru. Tato metoda rozparsuje kazdy potrebny objekt podla specifikacie a vrati instanciu danej
potrebnej triedy. Zaroven je tato metoda rekurzivna, pretoze chceme prechadzat quoted_status a retweet_status.

### 1.4. Upratanie hashtagov aby boli unikatne

Kedze hashtagy v json objekte nemaju sami o sebe unikatne ID ale maju iba tag, tak musime im vytvorit unikatne ID. Toto
id je obycajne incrimentovane cislo, treba len vyriesit aby neexistovali duplikaty na id a ani na tag. Najprv pozerame
na
hashtagy ktore mame v pamati a poriesime spravne aby tweet_hashtags mali spravne hashtag_id. Nasledne si selectneme
vsetky
hashtagy z databazy podla tagu a vymazeme z pamate tie ktore uz v databaze su. Nakoniec zase nastavime spravne
hashtag_id
pre tweet_hashtags.

### 1.5. Vytvorenie in memory CSV subora z daneho batchu pre kazdu tabulku

Pouzivame kniznicu `io.StringIO` na vytvorenie in memory CSV suboru. Do tohto suboru zapisujeme pomocou kniznice
`csv.DictWriter` vsetky data z daneho batchu. Toto robime pre kazdu tabulku zvlast. Kazda trieda ma metodu
`get_dict_representation` ktora spravi z triedy dictionary, ktora je vhodna na zapis do CSV suboru.

### 1.6. Pouzitie `COPY` príkazu na import dat z CSV suboru do tmp tabulky

Pre vacsinu tabuliek pouzijeme prikaz
`CREATE TEMP TABLE IF NOT EXISTS {temp_table_name} (LIKE {row_object.get_table_name()} INCLUDING DEFAULTS) ON COMMIT DROP;`
ktory vytvori prazdnu temporary tabulku ktora bude existovat iba do commitu. Schvalne robime aby nemala ziadne
constraints, aby sme mohli importovat cez `COPY`. Následne pouzijeme prikaz
`COPY {row_object.get_table_name()} ({', '.join(row_object.get_field_names())}) FROM STDIN CSV HEADER`
ktory importuje data z CSV suboru do temporary tabulky.

Pre tabulky ktore nemaju ziadne constraints tak nepouzivame temp tabulku ale rovno importujeme do cielovej tabulky.
Priklad takejto tabulky je `tweet_urls`, kedze podla specifikacie nema ziadne constrains.

### 1.7. `INSERT` s `ON CONFLICT DO NOTHING` na import dat z tmp tabulky do cielovej tabulky

Na poriesenie duplikatov pouzijeme prikaz

```sql
INSERT INTO {row_object.get_table_name()} ({', '.join(row_object.get_field_names())})
SELECT {', '.join(row_object.get_field_names())}
FROM {temp_table_name}
ON CONFLICT ({pk_cols})
DO NOTHING;
```

Ktora ak na nejakej kolizii narazi na problem tak to jednoducho preskoci. Ako je vidno v celom protokole tak classy v
packagi `models` mali definovane potrebne informacie cez staticke metody. Meno tabulky, nazvy stlpcov a stlpce na
ktorych moze
vzniknut konflikt.

Ako bolo napisane v bode 1.6 tak pre niektore tabulky toto nebolo treba robit. Dalsia tabulka pre ktoru sme mohli
spravit
rovno copy bola `hashtags`, pretoze sme si poriesili unikatnost hashtagov v pamati. Toto sme ale nespravili koli dovodom
debugu lebo to dava pri inserte lepsiu chybovu hlasku. Neni ale preto normalny dovod a v kode je to zmena iba v metode
`get_conflict_columns` kde by sme vratili prazdny zoznam namiesto iba `tag`.

## 2. Meranie casu a priepustnost

| Description                 | Time    |
|-----------------------------|---------|
| Total                       | 1:42:59 |
| Total preprocessing         | 0:21:45 |
| Total make Hash tags unique | 0:01:20 |
| Total COPY and Insert to db | 1:21:14 |
| Average time per file       | 0:02:34 |
| Throughput tweet/time       | 1149,49 |

## 3. Pocty zaznamov v tabulkach

| Table Name          | Record Count |
|---------------------|--------------|
| hashtags            | 316047       |
| places              | 13988        |
| tweet_hashtag       | 2992745      |
| tweet_media         | 435570       |
| tweet_urls          | 4314901      |
| tweet_user_mentions | 9083962      |
| tweets              | 7102727      |
| users               | 3199757      |

## 4. Popis systemu

OS je windows 10 Pro

Verzia databazy: `PostgreSQL 18.0 on x86_64-windows, compiled by msvc-19.44.35215, 64-bit`

### CPU

	Intel(R) Core(TM) i5-7400 CPU @ 3.00GHz
	Base speed:	3,00 GHz
	Sockets:	1
	Cores:	4
	Logical processors:	4

### Memory

Realne ale pycharm cez ktory sme to spustali mal moznost pouzit iba 4GiB

	20,0 GB

	Speed:	2400 MHz
	Form factor:	DIMM
	Hardware reserved:	42,0 MB

### Disk 1 (D:)

Speed je brany z Task manageru pocas bezania skriptu ako presne to bolo v ten dany moment. Skace to ale

	WDC WD20EZRZ-00Z5HB0

	Capacity:	1,8 TB
	Formatted:	1,8 TB
	System disk:	No
	Page file:	Yes
	Type:	HDD
	Read speed	488 KB/s
	Write speed	3,8 MB/s

## 5. Nenaviazane vztahy

| Nenaviazeny stlpec (kolko ich je null) | Record Count |
|----------------------------------------|--------------|
| in_reply_to_status_id                  | 6496356      |
| quoted_status_id                       | 13988        |
| retweeted_status_id                    | 2992745      |


