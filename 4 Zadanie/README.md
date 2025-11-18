# 4.1 Elastic - práca s indexom a mapovanie

Enkh-Undral EnkhBayar

## Cieľ úlohy

- Preukázať schopnosť pracovať s indexami v elasticu
- Preukázať schopnosť čítať a interpretovať technickú dokumentáciu a mapovať ich s reálnymi dátami, zároveň ich
  importovať
- Prakticky si vyskúšať definíciu vlastných textových analyzátorov v Elasticsearch.
- Vytvoriť striktné a produkčne pripravené mapovanie pre komplexné JSON dáta.
- Aplikovať rôzne techniky analýzy (stemming, n-gramy, shingles) na špecifické textové polia.
- Pre toto zadanie budete vychádzať z nasledujúcich zdrojov:
    - Oficiálny dátový slovník objektu Tweet (primárny
      zdroj): https://web.archive.org/web/20200501162440/https://developer.twitter.com/en/docs/tweets/data-dictionary/overview/tweet-object
    - Ukážkový JSON dokument (pre overenie štruktúry v praxi):
        - Pre overenie, či vaša schéma zodpovedá reálnym dátam, použite jeden príklad JSON dokumentu, ktorý zahŕňa
          retweet aj citovaný tweet.

## Úlohy:

### Predispozícia:

**Rozbehajte si 3 inštancie Elasticsearch-u**

Pouzil som navod
z [stranky](https://www.elastic.co/docs/deploy-manage/deploy/self-managed/install-elasticsearch-docker-compose)
elasticu, kde su rozbehane rovno rozbehane 3 instancie zaroven s Kibanou.
![img.png](img.png)

Na to ale aby som to rozbehal som musel zvacsit memory pre wsl takze som do Home pridal subor `.wslconfig` s obsahom:

```
[wsl2]
memory=8GB
kernelCommandLine = "sysctl.vm.max_map_count=262144"
```

**Vytvorte index pre tweets, ktorý bude mať “optimálny“ počet shardov a replík pre 3 nody (aby tam bola distribúcia
dotazov vo vyhľadávaní, aj distribúcia uložených dát). Vysvetlite prečo ste zvolili daný počet.**

Pre tri nody som zvolil 3 primarne shardy a 1 repliku. Dovod je ten, ze kazdy shard moze byt na inom node a tak sa
zabezpeci rovnomerne rozlozenie dat a dotazov. Replika zabezpeci dostupnost dat v pripade vypadku nodu.

<details>
<summary>Request and response</summary>

```
PUT /tweets
Host: localhost:9200
```
Request Body:
```json
{
  "settings": {
    "number_of_shards": 3,
    "number_of_replicas": 1
  }
}
```
Response:
```json
{
    "acknowledged": true,
    "shards_acknowledged": true,
    "index": "tweets"
}
```

</details>

### Časť 1: Vlastné analyzátory (v sekcii settings.analysis)

**Definujte tri vlastné analyzátory a k nim potrebné komponenty**

Pred kazdym vytvorenim analyzatora musim zatvorit index s nasledujucim requestom:

<details>
<summary>Request and response</summary>

```
POST /tweets/_close
Host: localhost:9200
```
Response:
```json
{
  "acknowledged": true,
  "shards_acknowledged": true,
  "indices": {
    "tweets": {
      "closed": true
    }
  }
}
```

</details>

#### 1.1 Analyzátor englando

- Analyzátor englando: Určený na analýzu bežného anglického textu.
    - Tokenizer: standard
    - Char Filter: html_strip
    - Token Filtre: english_possessive_stemmer, lowercase, english_stop, english_stemmer.

<details>
<summary>Request and response</summary>

```
POST /tweets/_settings
Host: localhost:9200
```
Request Body:
```json
{
  "settings": {
    "analysis": {
      "analyzer": {
        "englando": {
          "type": "custom",
          "tokenizer": "standard",
          "char_filter": [
            "html_strip"
          ],
          "filter": [
            "english_possessive_stemmer",
            "lowercase",
            "english_stop",
            "english_stemmer"
          ]
        }
      },
      "filter": {
        "english_stop": {
          "type": "stop",
          "stopwords": "_english_"
        },
        "english_stemmer": {
          "type": "stemmer",
          "language": "english"
        },
        "english_possessive_stemmer": {
          "type": "stemmer",
          "language": "possessive_english"
        }
      }
    }
  }
}
```
Response:
```json
{
  "acknowledged": true
}
```

</details>

#### 1.2 Analyzátor custom_ngram
- Analyzátor custom_ngram: Určený na "type-ahead" vyhľadávanie po častiach slova.
    - Tokenizer: standard
    - Char Filter: html_strip
    - Filtre: lowercase, asciifolding a vlastný filter filter_ngrams.
    - Vami definovaný filter filter_ngrams musí byť typu ngram a generovať tokeny s dĺžkou od 3 do 6 znakov.

Tuto som zaroven musel zvacsit max_ngram_diff na 3, pretoze defaultne je 1 a rozdiel medzi min_gram a max_gram je 3
`(6-3=3)`.

<details>
<summary>Request and response</summary>

```
POST /tweets/_settings
Host: localhost:9200
```
Request Body:
```json
{
  "settings": {
    "index": {
      "max_ngram_diff": 3
    },
    "analysis": {
      "analyzer": {
        "custom_ngram": {
          "type": "custom",
          "tokenizer": "standard",
          "char_filter": [
            "html_strip"
          ],
          "filter": [
            "asciifolding",
            "lowercase",
            "filter_ngrams"
          ]
        }
      },
      "filter": {
        "filter_ngrams": {
          "type": "ngram",
          "min_gram": 3,
          "max_gram": 6
        }
      }
    }
  }
}
```
Response:
```json
{
  "acknowledged": true
}
```

</details>

#### 1.3 Analyzátor custom_shingles
- Analyzátor custom_shingles: Určený na vytváranie spojených tokenov pre lepšie frázové vyhľadávanie.
    - Tokenizer: standard
    - Char Filter: html_strip
    - Filtre: lowercase, asciifolding a vlastný filter filter_shingles.
    - Vami definovaný filter filter_shingles musí byť typu shingle a spájať tokeny bez medzery (token_separator: "").

### Časť 2: Tvorba striktného mapovania (v sekcii mappings)

Na základe poskytnutej dokumentácie a ukážkového JSON súboru vytvorte kompletné a striktné mapovanie.

#### Striktnosť a úplnosť:

Mapovanie musí byť striktne definované ("dynamic": "strict"). Musíte zmapovať všetky polia, ktoré sa nachádzajú v
dokumentácii a v ukážkovom JSON, vrátane rekurzívnych objektov ako retweeted_status a quoted_status. Pre polia, ktorých
obsah nechcete indexovať (napr. niektoré URL obrázkov alebo farby profilu), použite index: false. Pre vnorené objekty s
nepredvídateľnou štruktúrou (napr. place.attributes) použite "dynamic": "false".

#### Aplikácia analyzátorov:

Každý anglický text (text tweetu full_text, popis používateľa, ..) analyzujte pomocou analyzátora englando.
Priraďte analyzátory pomocou multi-fields, aby sa zachoval aj pôvodný typ poľa:
pre všetky mená: pridajte mapovania pre custom_ngram alebo / alebo aj custom_shingles - opíšte prečo
pre všetky textové polia kde to má zmysel: okrem hlavného englando analyzátora pridajte mapovanie pre custom_shingles.
Názvy miest, krajín a URL adresy (v objekte place a entities.urls) musia mať pridané mapovanie pre custom_ngram.
Hashtagy: Text hashtagov (entities.hashtags.text) indexujte ako keyword, ale zabezpečte, aby vyhľadávanie bolo nezávislé
od veľkosti písmen (case-insensitive). Použite na to normalizer.
Dátové typy: Zvoľte najvhodnejšie dátové typy (geo_point, geo_shape, nested, date atď.). Dátumové polia musia byť
schopné spracovať formát z Twitter API.

### Zdôvodníte tieto rozhodnutia:

Prečo a pre ktoré objekty v poli ste zvolili typ nested.
Prečo je dôležité definovať rekurzívnu štruktúru pre retweeted_status a aké by boli dôsledky, keby ste ho v striktnej
schéme nedefinovali.
Vysvetlite rozdiel v použití medzi analyzátorom custom_ngram a custom_shingles na poli user.name. Kedy by ste použili
jeden a kedy druhý?

### Časť 3: Naimportujte dáta

### Časť 4: Experimentovanie s indexom

Experimentujte s nódami, a zistite koľko nódov musí bežať (a ktoré) aby vám Elasticsearch vedel pridávať dokumenty,
mazať dokumenty, prezerať dokumenty a vyhľadávať nad nimi? Dá sa nastaviť Elastic tak, aby mu stačil jeden nód?
Upravujte ľubovolný tweets.friends_count pomocou vášho jednoduchého skriptu (v rámci Elasticsearchu) a sledujte ako sa
mení _seq_no a _primary_term pri tom ako zabíjate a spúšťate nódy. Čo sa deje s dokumentami
Výstup: Výstup zadania je realizovaný formou protokolu, kde odpovedáte na jednotlivé otázky. Všetky úlohy musia
obsahovať príklady vstupu aj výstup vo formáte JSON.

Záver: Záver, kde zhodnotíte najväčšie úskalia a čo sa podarilo/nepodarilo realizovať.