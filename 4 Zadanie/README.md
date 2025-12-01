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

Nasledne pred kazdym testom som to znova musel otvorit:

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
  "shards_acknowledged": true
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

<details>
<summary>Testing</summary>

```
POST /tweets/_analyze
Host: localhost:9200
```

Request Body:

```json
{
  "analyzer": "englando",
  "text": "If this doctor, who so recklessly flew into New York from West Africa,has Ebola,then Obama should apologize to the American people &amp; resign!"
}
```

Response:

```json
{
  "tokens": [
    {
      "token": "doctor",
      "start_offset": 8,
      "end_offset": 14,
      "type": "<ALPHANUM>",
      "position": 2
    },
    {
      "token": "who",
      "start_offset": 16,
      "end_offset": 19,
      "type": "<ALPHANUM>",
      "position": 3
    },
    {
      "token": "so",
      "start_offset": 20,
      "end_offset": 22,
      "type": "<ALPHANUM>",
      "position": 4
    },
    {
      "token": "recklessli",
      "start_offset": 23,
      "end_offset": 33,
      "type": "<ALPHANUM>",
      "position": 5
    },
    {
      "token": "flew",
      "start_offset": 34,
      "end_offset": 38,
      "type": "<ALPHANUM>",
      "position": 6
    },
    {
      "token": "new",
      "start_offset": 44,
      "end_offset": 47,
      "type": "<ALPHANUM>",
      "position": 8
    },
    {
      "token": "york",
      "start_offset": 48,
      "end_offset": 52,
      "type": "<ALPHANUM>",
      "position": 9
    },
    {
      "token": "from",
      "start_offset": 53,
      "end_offset": 57,
      "type": "<ALPHANUM>",
      "position": 10
    },
    {
      "token": "west",
      "start_offset": 58,
      "end_offset": 62,
      "type": "<ALPHANUM>",
      "position": 11
    },
    {
      "token": "africa",
      "start_offset": 63,
      "end_offset": 69,
      "type": "<ALPHANUM>",
      "position": 12
    },
    {
      "token": "ha",
      "start_offset": 70,
      "end_offset": 73,
      "type": "<ALPHANUM>",
      "position": 13
    },
    {
      "token": "ebola",
      "start_offset": 74,
      "end_offset": 79,
      "type": "<ALPHANUM>",
      "position": 14
    },
    {
      "token": "obama",
      "start_offset": 85,
      "end_offset": 90,
      "type": "<ALPHANUM>",
      "position": 16
    },
    {
      "token": "should",
      "start_offset": 91,
      "end_offset": 97,
      "type": "<ALPHANUM>",
      "position": 17
    },
    {
      "token": "apolog",
      "start_offset": 98,
      "end_offset": 107,
      "type": "<ALPHANUM>",
      "position": 18
    },
    {
      "token": "american",
      "start_offset": 115,
      "end_offset": 123,
      "type": "<ALPHANUM>",
      "position": 21
    },
    {
      "token": "peopl",
      "start_offset": 124,
      "end_offset": 130,
      "type": "<ALPHANUM>",
      "position": 22
    },
    {
      "token": "resign",
      "start_offset": 137,
      "end_offset": 143,
      "type": "<ALPHANUM>",
      "position": 23
    }
  ]
}
```

Response vyzera byt ok len niektore slova su trochu inak ako by som cakal. Po researchi to vyzera byt ok.

- slova `who` a `so` by som tu necakal koli stop words ale vyzera to byt ok podla
  Lucene [Kod](https://github.com/apache/lucene-solr/blob/branch_7x/lucene/core/src/java/org/apache/lucene/analysis/standard/StandardAnalyzer.java#L47-L53)
- slovo `recklessli` by som cakal `reckless` ale toto je iba detail a je to podla mna podla ocakavani.

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

<details>
<summary>Testing</summary>

```
POST /tweets/_analyze
Host: localhost:9200
```

Request Body:

```json
{
  "analyzer": "custom_ngram",
  "text": "If this doctor, who so recklessly flew into New York from West Africà,has Ebolà,then Obama should apologize to the Americàn people &amp; resign!"
}
```

Response:

```json
{
  "tokens": [
    {
      "token": "thi",
      "start_offset": 3,
      "end_offset": 7,
      "type": "<ALPHANUM>",
      "position": 1
    },
    {
      "token": "this",
      "start_offset": 3,
      "end_offset": 7,
      "type": "<ALPHANUM>",
      "position": 1
    },
    {
      "token": "his",
      "start_offset": 3,
      "end_offset": 7,
      "type": "<ALPHANUM>",
      "position": 1
    },
    {
      "token": "doc",
      "start_offset": 8,
      "end_offset": 14,
      "type": "<ALPHANUM>",
      "position": 2
    },
    {
      "token": "doct",
      "start_offset": 8,
      "end_offset": 14,
      "type": "<ALPHANUM>",
      "position": 2
    },
    {
      "token": "docto",
      "start_offset": 8,
      "end_offset": 14,
      "type": "<ALPHANUM>",
      "position": 2
    },
    {
      "token": "doctor",
      "start_offset": 8,
      "end_offset": 14,
      "type": "<ALPHANUM>",
      "position": 2
    },
    {
      "token": "oct",
      "start_offset": 8,
      "end_offset": 14,
      "type": "<ALPHANUM>",
      "position": 2
    },
    {
      "token": "octo",
      "start_offset": 8,
      "end_offset": 14,
      "type": "<ALPHANUM>",
      "position": 2
    },
    {
      "token": "octor",
      "start_offset": 8,
      "end_offset": 14,
      "type": "<ALPHANUM>",
      "position": 2
    },
    {
      "token": "cto",
      "start_offset": 8,
      "end_offset": 14,
      "type": "<ALPHANUM>",
      "position": 2
    },
    {
      "token": "ctor",
      "start_offset": 8,
      "end_offset": 14,
      "type": "<ALPHANUM>",
      "position": 2
    },
    {
      "token": "tor",
      "start_offset": 8,
      "end_offset": 14,
      "type": "<ALPHANUM>",
      "position": 2
    },
    {
      "token": "who",
      "start_offset": 16,
      "end_offset": 19,
      "type": "<ALPHANUM>",
      "position": 3
    },
    {
      "token": "rec",
      "start_offset": 23,
      "end_offset": 33,
      "type": "<ALPHANUM>",
      "position": 5
    },
    {
      "token": "reck",
      "start_offset": 23,
      "end_offset": 33,
      "type": "<ALPHANUM>",
      "position": 5
    },
    {
      "token": "reckl",
      "start_offset": 23,
      "end_offset": 33,
      "type": "<ALPHANUM>",
      "position": 5
    },
    {
      "token": "reckle",
      "start_offset": 23,
      "end_offset": 33,
      "type": "<ALPHANUM>",
      "position": 5
    },
    {
      "token": "eck",
      "start_offset": 23,
      "end_offset": 33,
      "type": "<ALPHANUM>",
      "position": 5
    },
    {
      "token": "eckl",
      "start_offset": 23,
      "end_offset": 33,
      "type": "<ALPHANUM>",
      "position": 5
    },
    {
      "token": "eckle",
      "start_offset": 23,
      "end_offset": 33,
      "type": "<ALPHANUM>",
      "position": 5
    },
    {
      "token": "eckles",
      "start_offset": 23,
      "end_offset": 33,
      "type": "<ALPHANUM>",
      "position": 5
    },
    {
      "token": "ckl",
      "start_offset": 23,
      "end_offset": 33,
      "type": "<ALPHANUM>",
      "position": 5
    },
    {
      "token": "ckle",
      "start_offset": 23,
      "end_offset": 33,
      "type": "<ALPHANUM>",
      "position": 5
    },
    {
      "token": "ckles",
      "start_offset": 23,
      "end_offset": 33,
      "type": "<ALPHANUM>",
      "position": 5
    },
    {
      "token": "ckless",
      "start_offset": 23,
      "end_offset": 33,
      "type": "<ALPHANUM>",
      "position": 5
    },
    {
      "token": "kle",
      "start_offset": 23,
      "end_offset": 33,
      "type": "<ALPHANUM>",
      "position": 5
    },
    {
      "token": "kles",
      "start_offset": 23,
      "end_offset": 33,
      "type": "<ALPHANUM>",
      "position": 5
    },
    {
      "token": "kless",
      "start_offset": 23,
      "end_offset": 33,
      "type": "<ALPHANUM>",
      "position": 5
    },
    {
      "token": "klessl",
      "start_offset": 23,
      "end_offset": 33,
      "type": "<ALPHANUM>",
      "position": 5
    },
    {
      "token": "les",
      "start_offset": 23,
      "end_offset": 33,
      "type": "<ALPHANUM>",
      "position": 5
    },
    {
      "token": "less",
      "start_offset": 23,
      "end_offset": 33,
      "type": "<ALPHANUM>",
      "position": 5
    },
    {
      "token": "lessl",
      "start_offset": 23,
      "end_offset": 33,
      "type": "<ALPHANUM>",
      "position": 5
    },
    {
      "token": "lessly",
      "start_offset": 23,
      "end_offset": 33,
      "type": "<ALPHANUM>",
      "position": 5
    },
    {
      "token": "ess",
      "start_offset": 23,
      "end_offset": 33,
      "type": "<ALPHANUM>",
      "position": 5
    },
    {
      "token": "essl",
      "start_offset": 23,
      "end_offset": 33,
      "type": "<ALPHANUM>",
      "position": 5
    },
    {
      "token": "essly",
      "start_offset": 23,
      "end_offset": 33,
      "type": "<ALPHANUM>",
      "position": 5
    },
    {
      "token": "ssl",
      "start_offset": 23,
      "end_offset": 33,
      "type": "<ALPHANUM>",
      "position": 5
    },
    {
      "token": "ssly",
      "start_offset": 23,
      "end_offset": 33,
      "type": "<ALPHANUM>",
      "position": 5
    },
    {
      "token": "sly",
      "start_offset": 23,
      "end_offset": 33,
      "type": "<ALPHANUM>",
      "position": 5
    },
    {
      "token": "fle",
      "start_offset": 34,
      "end_offset": 38,
      "type": "<ALPHANUM>",
      "position": 6
    },
    {
      "token": "flew",
      "start_offset": 34,
      "end_offset": 38,
      "type": "<ALPHANUM>",
      "position": 6
    },
    {
      "token": "lew",
      "start_offset": 34,
      "end_offset": 38,
      "type": "<ALPHANUM>",
      "position": 6
    },
    {
      "token": "int",
      "start_offset": 39,
      "end_offset": 43,
      "type": "<ALPHANUM>",
      "position": 7
    },
    {
      "token": "into",
      "start_offset": 39,
      "end_offset": 43,
      "type": "<ALPHANUM>",
      "position": 7
    },
    {
      "token": "nto",
      "start_offset": 39,
      "end_offset": 43,
      "type": "<ALPHANUM>",
      "position": 7
    },
    {
      "token": "new",
      "start_offset": 44,
      "end_offset": 47,
      "type": "<ALPHANUM>",
      "position": 8
    },
    {
      "token": "yor",
      "start_offset": 48,
      "end_offset": 52,
      "type": "<ALPHANUM>",
      "position": 9
    },
    {
      "token": "york",
      "start_offset": 48,
      "end_offset": 52,
      "type": "<ALPHANUM>",
      "position": 9
    },
    {
      "token": "ork",
      "start_offset": 48,
      "end_offset": 52,
      "type": "<ALPHANUM>",
      "position": 9
    },
    {
      "token": "fro",
      "start_offset": 53,
      "end_offset": 57,
      "type": "<ALPHANUM>",
      "position": 10
    },
    {
      "token": "from",
      "start_offset": 53,
      "end_offset": 57,
      "type": "<ALPHANUM>",
      "position": 10
    },
    {
      "token": "rom",
      "start_offset": 53,
      "end_offset": 57,
      "type": "<ALPHANUM>",
      "position": 10
    },
    {
      "token": "wes",
      "start_offset": 58,
      "end_offset": 62,
      "type": "<ALPHANUM>",
      "position": 11
    },
    {
      "token": "west",
      "start_offset": 58,
      "end_offset": 62,
      "type": "<ALPHANUM>",
      "position": 11
    },
    {
      "token": "est",
      "start_offset": 58,
      "end_offset": 62,
      "type": "<ALPHANUM>",
      "position": 11
    },
    {
      "token": "afr",
      "start_offset": 63,
      "end_offset": 69,
      "type": "<ALPHANUM>",
      "position": 12
    },
    {
      "token": "afri",
      "start_offset": 63,
      "end_offset": 69,
      "type": "<ALPHANUM>",
      "position": 12
    },
    {
      "token": "afric",
      "start_offset": 63,
      "end_offset": 69,
      "type": "<ALPHANUM>",
      "position": 12
    },
    {
      "token": "africa",
      "start_offset": 63,
      "end_offset": 69,
      "type": "<ALPHANUM>",
      "position": 12
    },
    {
      "token": "fri",
      "start_offset": 63,
      "end_offset": 69,
      "type": "<ALPHANUM>",
      "position": 12
    },
    {
      "token": "fric",
      "start_offset": 63,
      "end_offset": 69,
      "type": "<ALPHANUM>",
      "position": 12
    },
    {
      "token": "frica",
      "start_offset": 63,
      "end_offset": 69,
      "type": "<ALPHANUM>",
      "position": 12
    },
    {
      "token": "ric",
      "start_offset": 63,
      "end_offset": 69,
      "type": "<ALPHANUM>",
      "position": 12
    },
    {
      "token": "rica",
      "start_offset": 63,
      "end_offset": 69,
      "type": "<ALPHANUM>",
      "position": 12
    },
    {
      "token": "ica",
      "start_offset": 63,
      "end_offset": 69,
      "type": "<ALPHANUM>",
      "position": 12
    },
    {
      "token": "has",
      "start_offset": 70,
      "end_offset": 73,
      "type": "<ALPHANUM>",
      "position": 13
    },
    {
      "token": "ebo",
      "start_offset": 74,
      "end_offset": 79,
      "type": "<ALPHANUM>",
      "position": 14
    },
    {
      "token": "ebol",
      "start_offset": 74,
      "end_offset": 79,
      "type": "<ALPHANUM>",
      "position": 14
    },
    {
      "token": "ebola",
      "start_offset": 74,
      "end_offset": 79,
      "type": "<ALPHANUM>",
      "position": 14
    },
    {
      "token": "bol",
      "start_offset": 74,
      "end_offset": 79,
      "type": "<ALPHANUM>",
      "position": 14
    },
    {
      "token": "bola",
      "start_offset": 74,
      "end_offset": 79,
      "type": "<ALPHANUM>",
      "position": 14
    },
    {
      "token": "ola",
      "start_offset": 74,
      "end_offset": 79,
      "type": "<ALPHANUM>",
      "position": 14
    },
    {
      "token": "the",
      "start_offset": 80,
      "end_offset": 84,
      "type": "<ALPHANUM>",
      "position": 15
    },
    {
      "token": "then",
      "start_offset": 80,
      "end_offset": 84,
      "type": "<ALPHANUM>",
      "position": 15
    },
    {
      "token": "hen",
      "start_offset": 80,
      "end_offset": 84,
      "type": "<ALPHANUM>",
      "position": 15
    },
    {
      "token": "oba",
      "start_offset": 85,
      "end_offset": 90,
      "type": "<ALPHANUM>",
      "position": 16
    },
    {
      "token": "obam",
      "start_offset": 85,
      "end_offset": 90,
      "type": "<ALPHANUM>",
      "position": 16
    },
    {
      "token": "obama",
      "start_offset": 85,
      "end_offset": 90,
      "type": "<ALPHANUM>",
      "position": 16
    },
    {
      "token": "bam",
      "start_offset": 85,
      "end_offset": 90,
      "type": "<ALPHANUM>",
      "position": 16
    },
    {
      "token": "bama",
      "start_offset": 85,
      "end_offset": 90,
      "type": "<ALPHANUM>",
      "position": 16
    },
    {
      "token": "ama",
      "start_offset": 85,
      "end_offset": 90,
      "type": "<ALPHANUM>",
      "position": 16
    },
    {
      "token": "sho",
      "start_offset": 91,
      "end_offset": 97,
      "type": "<ALPHANUM>",
      "position": 17
    },
    {
      "token": "shou",
      "start_offset": 91,
      "end_offset": 97,
      "type": "<ALPHANUM>",
      "position": 17
    },
    {
      "token": "shoul",
      "start_offset": 91,
      "end_offset": 97,
      "type": "<ALPHANUM>",
      "position": 17
    },
    {
      "token": "should",
      "start_offset": 91,
      "end_offset": 97,
      "type": "<ALPHANUM>",
      "position": 17
    },
    {
      "token": "hou",
      "start_offset": 91,
      "end_offset": 97,
      "type": "<ALPHANUM>",
      "position": 17
    },
    {
      "token": "houl",
      "start_offset": 91,
      "end_offset": 97,
      "type": "<ALPHANUM>",
      "position": 17
    },
    {
      "token": "hould",
      "start_offset": 91,
      "end_offset": 97,
      "type": "<ALPHANUM>",
      "position": 17
    },
    {
      "token": "oul",
      "start_offset": 91,
      "end_offset": 97,
      "type": "<ALPHANUM>",
      "position": 17
    },
    {
      "token": "ould",
      "start_offset": 91,
      "end_offset": 97,
      "type": "<ALPHANUM>",
      "position": 17
    },
    {
      "token": "uld",
      "start_offset": 91,
      "end_offset": 97,
      "type": "<ALPHANUM>",
      "position": 17
    },
    {
      "token": "apo",
      "start_offset": 98,
      "end_offset": 107,
      "type": "<ALPHANUM>",
      "position": 18
    },
    {
      "token": "apol",
      "start_offset": 98,
      "end_offset": 107,
      "type": "<ALPHANUM>",
      "position": 18
    },
    {
      "token": "apolo",
      "start_offset": 98,
      "end_offset": 107,
      "type": "<ALPHANUM>",
      "position": 18
    },
    {
      "token": "apolog",
      "start_offset": 98,
      "end_offset": 107,
      "type": "<ALPHANUM>",
      "position": 18
    },
    {
      "token": "pol",
      "start_offset": 98,
      "end_offset": 107,
      "type": "<ALPHANUM>",
      "position": 18
    },
    {
      "token": "polo",
      "start_offset": 98,
      "end_offset": 107,
      "type": "<ALPHANUM>",
      "position": 18
    },
    {
      "token": "polog",
      "start_offset": 98,
      "end_offset": 107,
      "type": "<ALPHANUM>",
      "position": 18
    },
    {
      "token": "pologi",
      "start_offset": 98,
      "end_offset": 107,
      "type": "<ALPHANUM>",
      "position": 18
    },
    {
      "token": "olo",
      "start_offset": 98,
      "end_offset": 107,
      "type": "<ALPHANUM>",
      "position": 18
    },
    {
      "token": "olog",
      "start_offset": 98,
      "end_offset": 107,
      "type": "<ALPHANUM>",
      "position": 18
    },
    {
      "token": "ologi",
      "start_offset": 98,
      "end_offset": 107,
      "type": "<ALPHANUM>",
      "position": 18
    },
    {
      "token": "ologiz",
      "start_offset": 98,
      "end_offset": 107,
      "type": "<ALPHANUM>",
      "position": 18
    },
    {
      "token": "log",
      "start_offset": 98,
      "end_offset": 107,
      "type": "<ALPHANUM>",
      "position": 18
    },
    {
      "token": "logi",
      "start_offset": 98,
      "end_offset": 107,
      "type": "<ALPHANUM>",
      "position": 18
    },
    {
      "token": "logiz",
      "start_offset": 98,
      "end_offset": 107,
      "type": "<ALPHANUM>",
      "position": 18
    },
    {
      "token": "logize",
      "start_offset": 98,
      "end_offset": 107,
      "type": "<ALPHANUM>",
      "position": 18
    },
    {
      "token": "ogi",
      "start_offset": 98,
      "end_offset": 107,
      "type": "<ALPHANUM>",
      "position": 18
    },
    {
      "token": "ogiz",
      "start_offset": 98,
      "end_offset": 107,
      "type": "<ALPHANUM>",
      "position": 18
    },
    {
      "token": "ogize",
      "start_offset": 98,
      "end_offset": 107,
      "type": "<ALPHANUM>",
      "position": 18
    },
    {
      "token": "giz",
      "start_offset": 98,
      "end_offset": 107,
      "type": "<ALPHANUM>",
      "position": 18
    },
    {
      "token": "gize",
      "start_offset": 98,
      "end_offset": 107,
      "type": "<ALPHANUM>",
      "position": 18
    },
    {
      "token": "ize",
      "start_offset": 98,
      "end_offset": 107,
      "type": "<ALPHANUM>",
      "position": 18
    },
    {
      "token": "the",
      "start_offset": 111,
      "end_offset": 114,
      "type": "<ALPHANUM>",
      "position": 20
    },
    {
      "token": "ame",
      "start_offset": 115,
      "end_offset": 123,
      "type": "<ALPHANUM>",
      "position": 21
    },
    {
      "token": "amer",
      "start_offset": 115,
      "end_offset": 123,
      "type": "<ALPHANUM>",
      "position": 21
    },
    {
      "token": "ameri",
      "start_offset": 115,
      "end_offset": 123,
      "type": "<ALPHANUM>",
      "position": 21
    },
    {
      "token": "americ",
      "start_offset": 115,
      "end_offset": 123,
      "type": "<ALPHANUM>",
      "position": 21
    },
    {
      "token": "mer",
      "start_offset": 115,
      "end_offset": 123,
      "type": "<ALPHANUM>",
      "position": 21
    },
    {
      "token": "meri",
      "start_offset": 115,
      "end_offset": 123,
      "type": "<ALPHANUM>",
      "position": 21
    },
    {
      "token": "meric",
      "start_offset": 115,
      "end_offset": 123,
      "type": "<ALPHANUM>",
      "position": 21
    },
    {
      "token": "merica",
      "start_offset": 115,
      "end_offset": 123,
      "type": "<ALPHANUM>",
      "position": 21
    },
    {
      "token": "eri",
      "start_offset": 115,
      "end_offset": 123,
      "type": "<ALPHANUM>",
      "position": 21
    },
    {
      "token": "eric",
      "start_offset": 115,
      "end_offset": 123,
      "type": "<ALPHANUM>",
      "position": 21
    },
    {
      "token": "erica",
      "start_offset": 115,
      "end_offset": 123,
      "type": "<ALPHANUM>",
      "position": 21
    },
    {
      "token": "erican",
      "start_offset": 115,
      "end_offset": 123,
      "type": "<ALPHANUM>",
      "position": 21
    },
    {
      "token": "ric",
      "start_offset": 115,
      "end_offset": 123,
      "type": "<ALPHANUM>",
      "position": 21
    },
    {
      "token": "rica",
      "start_offset": 115,
      "end_offset": 123,
      "type": "<ALPHANUM>",
      "position": 21
    },
    {
      "token": "rican",
      "start_offset": 115,
      "end_offset": 123,
      "type": "<ALPHANUM>",
      "position": 21
    },
    {
      "token": "ica",
      "start_offset": 115,
      "end_offset": 123,
      "type": "<ALPHANUM>",
      "position": 21
    },
    {
      "token": "ican",
      "start_offset": 115,
      "end_offset": 123,
      "type": "<ALPHANUM>",
      "position": 21
    },
    {
      "token": "can",
      "start_offset": 115,
      "end_offset": 123,
      "type": "<ALPHANUM>",
      "position": 21
    },
    {
      "token": "peo",
      "start_offset": 124,
      "end_offset": 130,
      "type": "<ALPHANUM>",
      "position": 22
    },
    {
      "token": "peop",
      "start_offset": 124,
      "end_offset": 130,
      "type": "<ALPHANUM>",
      "position": 22
    },
    {
      "token": "peopl",
      "start_offset": 124,
      "end_offset": 130,
      "type": "<ALPHANUM>",
      "position": 22
    },
    {
      "token": "people",
      "start_offset": 124,
      "end_offset": 130,
      "type": "<ALPHANUM>",
      "position": 22
    },
    {
      "token": "eop",
      "start_offset": 124,
      "end_offset": 130,
      "type": "<ALPHANUM>",
      "position": 22
    },
    {
      "token": "eopl",
      "start_offset": 124,
      "end_offset": 130,
      "type": "<ALPHANUM>",
      "position": 22
    },
    {
      "token": "eople",
      "start_offset": 124,
      "end_offset": 130,
      "type": "<ALPHANUM>",
      "position": 22
    },
    {
      "token": "opl",
      "start_offset": 124,
      "end_offset": 130,
      "type": "<ALPHANUM>",
      "position": 22
    },
    {
      "token": "ople",
      "start_offset": 124,
      "end_offset": 130,
      "type": "<ALPHANUM>",
      "position": 22
    },
    {
      "token": "ple",
      "start_offset": 124,
      "end_offset": 130,
      "type": "<ALPHANUM>",
      "position": 22
    },
    {
      "token": "res",
      "start_offset": 137,
      "end_offset": 143,
      "type": "<ALPHANUM>",
      "position": 23
    },
    {
      "token": "resi",
      "start_offset": 137,
      "end_offset": 143,
      "type": "<ALPHANUM>",
      "position": 23
    },
    {
      "token": "resig",
      "start_offset": 137,
      "end_offset": 143,
      "type": "<ALPHANUM>",
      "position": 23
    },
    {
      "token": "resign",
      "start_offset": 137,
      "end_offset": 143,
      "type": "<ALPHANUM>",
      "position": 23
    },
    {
      "token": "esi",
      "start_offset": 137,
      "end_offset": 143,
      "type": "<ALPHANUM>",
      "position": 23
    },
    {
      "token": "esig",
      "start_offset": 137,
      "end_offset": 143,
      "type": "<ALPHANUM>",
      "position": 23
    },
    {
      "token": "esign",
      "start_offset": 137,
      "end_offset": 143,
      "type": "<ALPHANUM>",
      "position": 23
    },
    {
      "token": "sig",
      "start_offset": 137,
      "end_offset": 143,
      "type": "<ALPHANUM>",
      "position": 23
    },
    {
      "token": "sign",
      "start_offset": 137,
      "end_offset": 143,
      "type": "<ALPHANUM>",
      "position": 23
    },
    {
      "token": "ign",
      "start_offset": 137,
      "end_offset": 143,
      "type": "<ALPHANUM>",
      "position": 23
    }
  ]
}
```

Response vyzera tak isto ok. Schvalne som do vety vymenil niektora `a` za `à` aby som testol asciifolding a vidim ze
nikde neni znak `à`. Zaroven mame iba tokeny ktore maju dlzku 3 az 6 znakov a vsetky po sebe iduce kombinacie. Taktiez
vsetko je lowercase.

</details>

#### 1.3 Analyzátor custom_shingles

- Analyzátor custom_shingles: Určený na vytváranie spojených tokenov pre lepšie frázové vyhľadávanie.
    - Tokenizer: standard
    - Char Filter: html_strip
    - Filtre: lowercase, asciifolding a vlastný filter filter_shingles.
    - Vami definovaný filter filter_shingles musí byť typu shingle a spájať tokeny bez medzery (token_separator: "").

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
      "filter": {
        "filter_shingles": {
          "type": "shingle",
          "token_separator": ""
        }
      },
      "analyzer": {
        "custom_shingles": {
          "type": "custom",
          "tokenizer": "standard",
          "char_filter": [
            "html_strip"
          ],
          "filter": [
            "lowercase",
            "asciifolding",
            "filter_shingles"
          ]
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


<details>
<summary>Testing</summary>

```
POST /tweets/_analyze
Host: localhost:9200
```

Request Body:

```json
{
  "analyzer": "custom_shingles",
  "text": "If this doctor, who so recklessly flew into New York from West Africà,has Ebolà,then Obama should apologize to the Americàn people &amp; resign!"
}
```

Response:

```json
{
  "tokens": [
    {
      "token": "if",
      "start_offset": 0,
      "end_offset": 2,
      "type": "<ALPHANUM>",
      "position": 0
    },
    {
      "token": "ifthis",
      "start_offset": 0,
      "end_offset": 7,
      "type": "shingle",
      "position": 0,
      "positionLength": 2
    },
    {
      "token": "this",
      "start_offset": 3,
      "end_offset": 7,
      "type": "<ALPHANUM>",
      "position": 1
    },
    {
      "token": "thisdoctor",
      "start_offset": 3,
      "end_offset": 14,
      "type": "shingle",
      "position": 1,
      "positionLength": 2
    },
    {
      "token": "doctor",
      "start_offset": 8,
      "end_offset": 14,
      "type": "<ALPHANUM>",
      "position": 2
    },
    {
      "token": "doctorwho",
      "start_offset": 8,
      "end_offset": 19,
      "type": "shingle",
      "position": 2,
      "positionLength": 2
    },
    {
      "token": "who",
      "start_offset": 16,
      "end_offset": 19,
      "type": "<ALPHANUM>",
      "position": 3
    },
    {
      "token": "whoso",
      "start_offset": 16,
      "end_offset": 22,
      "type": "shingle",
      "position": 3,
      "positionLength": 2
    },
    {
      "token": "so",
      "start_offset": 20,
      "end_offset": 22,
      "type": "<ALPHANUM>",
      "position": 4
    },
    {
      "token": "sorecklessly",
      "start_offset": 20,
      "end_offset": 33,
      "type": "shingle",
      "position": 4,
      "positionLength": 2
    },
    {
      "token": "recklessly",
      "start_offset": 23,
      "end_offset": 33,
      "type": "<ALPHANUM>",
      "position": 5
    },
    {
      "token": "recklesslyflew",
      "start_offset": 23,
      "end_offset": 38,
      "type": "shingle",
      "position": 5,
      "positionLength": 2
    },
    {
      "token": "flew",
      "start_offset": 34,
      "end_offset": 38,
      "type": "<ALPHANUM>",
      "position": 6
    },
    {
      "token": "flewinto",
      "start_offset": 34,
      "end_offset": 43,
      "type": "shingle",
      "position": 6,
      "positionLength": 2
    },
    {
      "token": "into",
      "start_offset": 39,
      "end_offset": 43,
      "type": "<ALPHANUM>",
      "position": 7
    },
    {
      "token": "intonew",
      "start_offset": 39,
      "end_offset": 47,
      "type": "shingle",
      "position": 7,
      "positionLength": 2
    },
    {
      "token": "new",
      "start_offset": 44,
      "end_offset": 47,
      "type": "<ALPHANUM>",
      "position": 8
    },
    {
      "token": "newyork",
      "start_offset": 44,
      "end_offset": 52,
      "type": "shingle",
      "position": 8,
      "positionLength": 2
    },
    {
      "token": "york",
      "start_offset": 48,
      "end_offset": 52,
      "type": "<ALPHANUM>",
      "position": 9
    },
    {
      "token": "yorkfrom",
      "start_offset": 48,
      "end_offset": 57,
      "type": "shingle",
      "position": 9,
      "positionLength": 2
    },
    {
      "token": "from",
      "start_offset": 53,
      "end_offset": 57,
      "type": "<ALPHANUM>",
      "position": 10
    },
    {
      "token": "fromwest",
      "start_offset": 53,
      "end_offset": 62,
      "type": "shingle",
      "position": 10,
      "positionLength": 2
    },
    {
      "token": "west",
      "start_offset": 58,
      "end_offset": 62,
      "type": "<ALPHANUM>",
      "position": 11
    },
    {
      "token": "westafrica",
      "start_offset": 58,
      "end_offset": 69,
      "type": "shingle",
      "position": 11,
      "positionLength": 2
    },
    {
      "token": "africa",
      "start_offset": 63,
      "end_offset": 69,
      "type": "<ALPHANUM>",
      "position": 12
    },
    {
      "token": "africahas",
      "start_offset": 63,
      "end_offset": 73,
      "type": "shingle",
      "position": 12,
      "positionLength": 2
    },
    {
      "token": "has",
      "start_offset": 70,
      "end_offset": 73,
      "type": "<ALPHANUM>",
      "position": 13
    },
    {
      "token": "hasebola",
      "start_offset": 70,
      "end_offset": 79,
      "type": "shingle",
      "position": 13,
      "positionLength": 2
    },
    {
      "token": "ebola",
      "start_offset": 74,
      "end_offset": 79,
      "type": "<ALPHANUM>",
      "position": 14
    },
    {
      "token": "ebolathen",
      "start_offset": 74,
      "end_offset": 84,
      "type": "shingle",
      "position": 14,
      "positionLength": 2
    },
    {
      "token": "then",
      "start_offset": 80,
      "end_offset": 84,
      "type": "<ALPHANUM>",
      "position": 15
    },
    {
      "token": "thenobama",
      "start_offset": 80,
      "end_offset": 90,
      "type": "shingle",
      "position": 15,
      "positionLength": 2
    },
    {
      "token": "obama",
      "start_offset": 85,
      "end_offset": 90,
      "type": "<ALPHANUM>",
      "position": 16
    },
    {
      "token": "obamashould",
      "start_offset": 85,
      "end_offset": 97,
      "type": "shingle",
      "position": 16,
      "positionLength": 2
    },
    {
      "token": "should",
      "start_offset": 91,
      "end_offset": 97,
      "type": "<ALPHANUM>",
      "position": 17
    },
    {
      "token": "shouldapologize",
      "start_offset": 91,
      "end_offset": 107,
      "type": "shingle",
      "position": 17,
      "positionLength": 2
    },
    {
      "token": "apologize",
      "start_offset": 98,
      "end_offset": 107,
      "type": "<ALPHANUM>",
      "position": 18
    },
    {
      "token": "apologizeto",
      "start_offset": 98,
      "end_offset": 110,
      "type": "shingle",
      "position": 18,
      "positionLength": 2
    },
    {
      "token": "to",
      "start_offset": 108,
      "end_offset": 110,
      "type": "<ALPHANUM>",
      "position": 19
    },
    {
      "token": "tothe",
      "start_offset": 108,
      "end_offset": 114,
      "type": "shingle",
      "position": 19,
      "positionLength": 2
    },
    {
      "token": "the",
      "start_offset": 111,
      "end_offset": 114,
      "type": "<ALPHANUM>",
      "position": 20
    },
    {
      "token": "theamerican",
      "start_offset": 111,
      "end_offset": 123,
      "type": "shingle",
      "position": 20,
      "positionLength": 2
    },
    {
      "token": "american",
      "start_offset": 115,
      "end_offset": 123,
      "type": "<ALPHANUM>",
      "position": 21
    },
    {
      "token": "americanpeople",
      "start_offset": 115,
      "end_offset": 130,
      "type": "shingle",
      "position": 21,
      "positionLength": 2
    },
    {
      "token": "people",
      "start_offset": 124,
      "end_offset": 130,
      "type": "<ALPHANUM>",
      "position": 22
    },
    {
      "token": "peopleresign",
      "start_offset": 124,
      "end_offset": 143,
      "type": "shingle",
      "position": 22,
      "positionLength": 2
    },
    {
      "token": "resign",
      "start_offset": 137,
      "end_offset": 143,
      "type": "<ALPHANUM>",
      "position": 23
    }
  ]
}
```

Odpoved vyzera spravne. Dava to lowercase, meni to specialne znaky a spaja to 2 slova dokopy bez medzery. 2 koli tomu
lebo min a max maju default 2.

</details>

### Časť 2: Tvorba striktného mapovania (v sekcii mappings)

Na základe poskytnutej dokumentácie a ukážkového JSON súboru vytvorte kompletné a striktné mapovanie.

#### Striktnosť a úplnosť:

Mapovanie musí byť striktne definované ("dynamic": "strict"). Musíte zmapovať všetky polia, ktoré sa nachádzajú v
dokumentácii a v ukážkovom JSON, vrátane rekurzívnych objektov ako retweeted_status a quoted_status. Pre polia, ktorých
obsah nechcete indexovať (napr. niektoré URL obrázkov alebo farby profilu), použite index: false. Pre vnorené objekty s
nepredvídateľnou štruktúrou (napr. place.attributes) použite "dynamic": "false".

#### Aplikácia analyzátorov:

- Každý anglický text (text tweetu full_text, popis používateľa, ..) analyzujte pomocou analyzátora englando.
- Priraďte analyzátory pomocou multi-fields, aby sa zachoval aj pôvodný typ poľa.
- pre všetky mená: pridajte mapovania pre custom_ngram alebo / alebo aj custom_shingles - opíšte prečo
  pre všetky textové polia kde to má zmysel.
- okrem hlavného englando analyzátora pridajte mapovanie pre custom_shingles.
- Názvy miest, krajín a URL adresy (v objekte place a entities.urls) musia mať pridané mapovanie pre custom_ngram.
- Hashtagy: Text hashtagov (entities.hashtags.text) indexujte ako keyword, ale zabezpečte, aby vyhľadávanie bolo
  nezávislé
  od veľkosti písmen (case-insensitive). Použite na to normalizer.
- Dátové typy: Zvoľte najvhodnejšie dátové typy (geo_point, geo_shape, nested, date atď.). Dátumové polia musia byť
  schopné spracovať formát z Twitter API.

<details>
<summary>Implementacia</summary>

```
POST /tweets/_settings
Host: localhost:9200
```

Request Body:

```json
{
  "dynamic": "strict",
  "properties": {
    "created_at": {
      "type": "date",
      "format": "EEE MMM dd HH:mm:ss Z yyyy"
    },
    "id": {
      "type": "keyword"
    },
    "id_str": {
      "type": "keyword"
    },
    "full_text": {
      "type": "text",
      "fields": {
        "englando": {
          "type": "text",
          "analyzer": "englando"
        }
      }
    },
    "truncated": {
      "type": "boolean"
    },
    "display_text_range": {
      "type": "integer"
    },
    "entities": {
      "properties": {
        "hashtags": {
          "type": "nested",
          "properties": {
            "text": {
              "type": "keyword",
              "normalizer": "lowercase_normalizer"
            },
            "indices": {
              "type": "integer"
            }
          }
        },
        "symbols": {
          "type": "nested",
          "properties": {
            "text": {
              "type": "keyword",
              "normalizer": "lowercase_normalizer"
            },
            "indices": {
              "type": "integer"
            }
          }
        },
        "user_mentions": {
          "type": "nested",
          "properties": {
            "screen_name": {
              "type": "text",
              "analyzer": "englando",
              "fields": {
                "ngram": {
                  "type": "text",
                  "analyzer": "custom_ngram"
                },
                "shingles": {
                  "type": "text",
                  "analyzer": "custom_shingles"
                }
              }
            },
            "name": {
              "type": "text",
              "analyzer": "englando",
              "fields": {
                "ngram": {
                  "type": "text",
                  "analyzer": "custom_ngram"
                },
                "shingles": {
                  "type": "text",
                  "analyzer": "custom_shingles"
                }
              }
            },
            "id": {
              "type": "keyword"
            },
            "id_str": {
              "type": "keyword"
            },
            "indices": {
              "type": "integer"
            }
          }
        },
        "urls": {
          "type": "nested",
          "properties": {
            "url": {
              "type": "text",
              "fields": {
                "ngram": {
                  "type": "text",
                  "analyzer": "custom_ngram"
                }
              }
            },
            "expanded_url": {
              "type": "text",
              "fields": {
                "ngram": {
                  "type": "text",
                  "analyzer": "custom_ngram"
                }
              }
            },
            "display_url": {
              "type": "text",
              "fields": {
                "ngram": {
                  "type": "text",
                  "analyzer": "custom_ngram"
                }
              }
            },
            "indices": {
              "type": "integer"
            }
          }
        }
      }
    },
    "source": {
      "type": "text",
      "fields": {
        "ngram": {
          "type": "text",
          "analyzer": "custom_ngram"
        }
      }
    },
    "in_reply_to_status_id": {
      "type": "keyword"
    },
    "in_reply_to_status_id_str": {
      "type": "keyword"
    },
    "in_reply_to_user_id": {
      "type": "keyword"
    },
    "in_reply_to_user_id_str": {
      "type": "keyword"
    },
    "in_reply_to_screen_name": {
      "type": "text",
      "analyzer": "englando",
      "fields": {
        "ngram": {
          "type": "text",
          "analyzer": "custom_ngram"
        },
        "shingles": {
          "type": "text",
          "analyzer": "custom_shingles"
        }
      }
    },
    "user": {
      "properties": {
        "id": {
          "type": "keyword"
        },
        "id_str": {
          "type": "keyword"
        },
        "name": {
          "type": "text",
          "analyzer": "englando",
          "fields": {
            "ngram": {
              "type": "text",
              "analyzer": "custom_ngram"
            },
            "shingles": {
              "type": "text",
              "analyzer": "custom_shingles"
            }
          }
        },
        "screen_name": {
          "type": "text",
          "analyzer": "englando",
          "fields": {
            "ngram": {
              "type": "text",
              "analyzer": "custom_ngram"
            },
            "shingles": {
              "type": "text",
              "analyzer": "custom_shingles"
            }
          }
        },
        "location": {
          "type": "text",
          "fields": {
            "ngram": {
              "type": "text",
              "analyzer": "custom_ngram"
            }
          }
        },
        "description": {
          "type": "text",
          "fields": {
            "englando": {
              "type": "text",
              "analyzer": "englando"
            }
          }
        },
        "url": {
          "type": "text",
          "fields": {
            "ngram": {
              "type": "text",
              "analyzer": "custom_ngram"
            }
          }
        },
        "entities": {
          "properties": {
            "url": {
              "properties": {
                "urls": {
                  "type": "nested",
                  "properties": {
                    "url": {
                      "type": "text",
                      "fields": {
                        "ngram": {
                          "type": "text",
                          "analyzer": "custom_ngram"
                        }
                      }
                    },
                    "expanded_url": {
                      "type": "text",
                      "fields": {
                        "ngram": {
                          "type": "text",
                          "analyzer": "custom_ngram"
                        }
                      }
                    },
                    "display_url": {
                      "type": "text",
                      "fields": {
                        "ngram": {
                          "type": "text",
                          "analyzer": "custom_ngram"
                        }
                      }
                    },
                    "indices": {
                      "type": "integer"
                    }
                  }
                }
              }
            },
            "description": {
              "properties": {
                "urls": {
                  "type": "nested",
                  "properties": {
                    "url": {
                      "type": "text",
                      "fields": {
                        "ngram": {
                          "type": "text",
                          "analyzer": "custom_ngram"
                        }
                      }
                    },
                    "expanded_url": {
                      "type": "text",
                      "fields": {
                        "ngram": {
                          "type": "text",
                          "analyzer": "custom_ngram"
                        }
                      }
                    },
                    "display_url": {
                      "type": "text",
                      "fields": {
                        "ngram": {
                          "type": "text",
                          "analyzer": "custom_ngram"
                        }
                      }
                    },
                    "indices": {
                      "type": "integer"
                    }
                  }
                }
              }
            }
          }
        },
        "protected": {
          "type": "boolean"
        },
        "followers_count": {
          "type": "integer"
        },
        "friends_count": {
          "type": "integer"
        },
        "listed_count": {
          "type": "integer"
        },
        "created_at": {
          "type": "date",
          "format": "EEE MMM dd HH:mm:ss Z yyyy"
        },
        "favourites_count": {
          "type": "integer"
        },
        "verified": {
          "type": "boolean"
        },
        "statuses_count": {
          "type": "integer"
        },
        "profile_background_color": {
          "type": "keyword"
        },
        "profile_background_image_url": {
          "type": "text",
          "fields": {
            "ngram": {
              "type": "text",
              "analyzer": "custom_ngram"
            }
          }
        },
        "profile_background_image_url_https": {
          "type": "text",
          "fields": {
            "ngram": {
              "type": "text",
              "analyzer": "custom_ngram"
            }
          }
        },
        "profile_image_url": {
          "type": "text",
          "fields": {
            "ngram": {
              "type": "text",
              "analyzer": "custom_ngram"
            }
          }
        },
        "profile_image_url_https": {
          "type": "text",
          "fields": {
            "ngram": {
              "type": "text",
              "analyzer": "custom_ngram"
            }
          }
        },
        "profile_link_color": {
          "type": "keyword"
        },
        "profile_sidebar_border_color": {
          "type": "keyword"
        },
        "profile_sidebar_fill_color": {
          "type": "keyword"
        },
        "profile_text_color": {
          "type": "keyword"
        },
        "profile_use_background_image": {
          "type": "boolean"
        },
        "has_extended_profile": {
          "type": "boolean"
        },
        "default_profile": {
          "type": "boolean"
        },
        "default_profile_image": {
          "type": "boolean"
        },
        "following": {
          "type": "boolean"
        },
        "follow_request_sent": {
          "type": "boolean"
        },
        "notifications": {
          "type": "boolean"
        },
        "translator_type": {
          "type": "keyword"
        }
      }
    },
    "coordinates": {
      "type": "geo_point"
    },
    "place": {
      "properties": {
        "attributes": {
          "type": "object",
          "dynamic": false
        },
        "bounding_box": {
          "type": "geo_shape"
        },
        "country": {
          "type": "text",
          "fields": {
            "ngram": {
              "type": "text",
              "analyzer": "custom_ngram"
            }
          }
        },
        "country_code": {
          "type": "text",
          "fields": {
            "ngram": {
              "type": "text",
              "analyzer": "custom_ngram"
            }
          }
        },
        "full_name": {
          "type": "text",
          "fields": {
            "ngram": {
              "type": "text",
              "analyzer": "custom_ngram"
            }
          }
        },
        "id": {
          "type": "keyword"
        },
        "name": {
          "type": "text",
          "fields": {
            "ngram": {
              "type": "text",
              "analyzer": "custom_ngram"
            }
          }
        },
        "place_type": {
          "type": "keyword"
        },
        "url": {
          "type": "text",
          "fields": {
            "ngram": {
              "type": "text",
              "analyzer": "custom_ngram"
            }
          }
        }
      }
    },
    "is_quote_status": {
      "type": "boolean"
    },
    "quoted_status_id": {
      "type": "keyword"
    },
    "quoted_status_id_str": {
      "type": "keyword"
    },
    "quoted_status_permalink": {
      "properties": {
        "url": {
          "type": "text",
          "fields": {
            "ngram": {
              "type": "text",
              "analyzer": "custom_ngram"
            }
          }
        },
        "expanded": {
          "type": "text",
          "fields": {
            "ngram": {
              "type": "text",
              "analyzer": "custom_ngram"
            }
          }
        },
        "display": {
          "type": "text",
          "fields": {
            "ngram": {
              "type": "text",
              "analyzer": "custom_ngram"
            }
          }
        }
      }
    },
    "retweet_count": {
      "type": "integer"
    },
    "favorite_count": {
      "type": "integer"
    },
    "favorited": {
      "type": "boolean"
    },
    "retweeted": {
      "type": "boolean"
    },
    "lang": {
      "type": "keyword"
    },
    "quoted_status": {
      "properties": {
        "created_at": {
          "type": "date",
          "format": "EEE MMM dd HH:mm:ss Z yyyy"
        },
        "id": {
          "type": "keyword"
        },
        "id_str": {
          "type": "keyword"
        },
        "full_text": {
          "type": "text",
          "fields": {
            "englando": {
              "type": "text",
              "analyzer": "englando"
            }
          }
        },
        "truncated": {
          "type": "boolean"
        },
        "display_text_range": {
          "type": "integer"
        },
        "entities": {
          "properties": {
            "hashtags": {
              "type": "nested",
              "properties": {
                "text": {
                  "type": "keyword",
                  "normalizer": "lowercase_normalizer"
                },
                "indices": {
                  "type": "integer"
                }
              }
            },
            "symbols": {
              "type": "nested",
              "properties": {
                "text": {
                  "type": "keyword",
                  "normalizer": "lowercase_normalizer"
                },
                "indices": {
                  "type": "integer"
                }
              }
            },
            "user_mentions": {
              "type": "nested",
              "properties": {
                "screen_name": {
                  "type": "text",
                  "analyzer": "englando",
                  "fields": {
                    "ngram": {
                      "type": "text",
                      "analyzer": "custom_ngram"
                    },
                    "shingles": {
                      "type": "text",
                      "analyzer": "custom_shingles"
                    }
                  }
                },
                "name": {
                  "type": "text",
                  "analyzer": "englando",
                  "fields": {
                    "ngram": {
                      "type": "text",
                      "analyzer": "custom_ngram"
                    },
                    "shingles": {
                      "type": "text",
                      "analyzer": "custom_shingles"
                    }
                  }
                },
                "id": {
                  "type": "keyword"
                },
                "id_str": {
                  "type": "keyword"
                },
                "indices": {
                  "type": "integer"
                }
              }
            },
            "urls": {
              "type": "nested",
              "properties": {
                "url": {
                  "type": "text",
                  "fields": {
                    "ngram": {
                      "type": "text",
                      "analyzer": "custom_ngram"
                    }
                  }
                },
                "expanded_url": {
                  "type": "text",
                  "fields": {
                    "ngram": {
                      "type": "text",
                      "analyzer": "custom_ngram"
                    }
                  }
                },
                "display_url": {
                  "type": "text",
                  "fields": {
                    "ngram": {
                      "type": "text",
                      "analyzer": "custom_ngram"
                    }
                  }
                },
                "indices": {
                  "type": "integer"
                }
              }
            }
          }
        },
        "source": {
          "type": "text",
          "fields": {
            "ngram": {
              "type": "text",
              "analyzer": "custom_ngram"
            }
          }
        },
        "in_reply_to_status_id": {
          "type": "keyword"
        },
        "in_reply_to_status_id_str": {
          "type": "keyword"
        },
        "in_reply_to_user_id": {
          "type": "keyword"
        },
        "in_reply_to_user_id_str": {
          "type": "keyword"
        },
        "in_reply_to_screen_name": {
          "type": "text",
          "analyzer": "englando",
          "fields": {
            "ngram": {
              "type": "text",
              "analyzer": "custom_ngram"
            },
            "shingles": {
              "type": "text",
              "analyzer": "custom_shingles"
            }
          }
        },
        "user": {
          "properties": {
            "id": {
              "type": "keyword"
            },
            "id_str": {
              "type": "keyword"
            },
            "name": {
              "type": "text",
              "analyzer": "englando",
              "fields": {
                "ngram": {
                  "type": "text",
                  "analyzer": "custom_ngram"
                },
                "shingles": {
                  "type": "text",
                  "analyzer": "custom_shingles"
                }
              }
            },
            "screen_name": {
              "type": "text",
              "analyzer": "englando",
              "fields": {
                "ngram": {
                  "type": "text",
                  "analyzer": "custom_ngram"
                },
                "shingles": {
                  "type": "text",
                  "analyzer": "custom_shingles"
                }
              }
            },
            "location": {
              "type": "text",
              "fields": {
                "ngram": {
                  "type": "text",
                  "analyzer": "custom_ngram"
                }
              }
            },
            "description": {
              "type": "text",
              "fields": {
                "englando": {
                  "type": "text",
                  "analyzer": "englando"
                }
              }
            },
            "url": {
              "type": "text",
              "fields": {
                "ngram": {
                  "type": "text",
                  "analyzer": "custom_ngram"
                }
              }
            },
            "entities": {
              "properties": {
                "url": {
                  "properties": {
                    "urls": {
                      "type": "nested",
                      "properties": {
                        "url": {
                          "type": "text",
                          "fields": {
                            "ngram": {
                              "type": "text",
                              "analyzer": "custom_ngram"
                            }
                          }
                        },
                        "expanded_url": {
                          "type": "text",
                          "fields": {
                            "ngram": {
                              "type": "text",
                              "analyzer": "custom_ngram"
                            }
                          }
                        },
                        "display_url": {
                          "type": "text",
                          "fields": {
                            "ngram": {
                              "type": "text",
                              "analyzer": "custom_ngram"
                            }
                          }
                        },
                        "indices": {
                          "type": "integer"
                        }
                      }
                    }
                  }
                },
                "description": {
                  "properties": {
                    "urls": {
                      "type": "nested",
                      "properties": {
                        "url": {
                          "type": "text",
                          "fields": {
                            "ngram": {
                              "type": "text",
                              "analyzer": "custom_ngram"
                            }
                          }
                        },
                        "expanded_url": {
                          "type": "text",
                          "fields": {
                            "ngram": {
                              "type": "text",
                              "analyzer": "custom_ngram"
                            }
                          }
                        },
                        "display_url": {
                          "type": "text",
                          "fields": {
                            "ngram": {
                              "type": "text",
                              "analyzer": "custom_ngram"
                            }
                          }
                        },
                        "indices": {
                          "type": "integer"
                        }
                      }
                    }
                  }
                }
              }
            },
            "protected": {
              "type": "boolean"
            },
            "followers_count": {
              "type": "integer"
            },
            "friends_count": {
              "type": "integer"
            },
            "listed_count": {
              "type": "integer"
            },
            "created_at": {
              "type": "date",
              "format": "EEE MMM dd HH:mm:ss Z yyyy"
            },
            "favourites_count": {
              "type": "integer"
            },
            "verified": {
              "type": "boolean"
            },
            "statuses_count": {
              "type": "integer"
            },
            "profile_background_color": {
              "type": "keyword"
            },
            "profile_background_image_url": {
              "type": "text",
              "fields": {
                "ngram": {
                  "type": "text",
                  "analyzer": "custom_ngram"
                }
              }
            },
            "profile_background_image_url_https": {
              "type": "text",
              "fields": {
                "ngram": {
                  "type": "text",
                  "analyzer": "custom_ngram"
                }
              }
            },
            "profile_image_url": {
              "type": "text",
              "fields": {
                "ngram": {
                  "type": "text",
                  "analyzer": "custom_ngram"
                }
              }
            },
            "profile_image_url_https": {
              "type": "text",
              "fields": {
                "ngram": {
                  "type": "text",
                  "analyzer": "custom_ngram"
                }
              }
            },
            "profile_link_color": {
              "type": "keyword"
            },
            "profile_sidebar_border_color": {
              "type": "keyword"
            },
            "profile_sidebar_fill_color": {
              "type": "keyword"
            },
            "profile_text_color": {
              "type": "keyword"
            },
            "profile_use_background_image": {
              "type": "boolean"
            },
            "has_extended_profile": {
              "type": "boolean"
            },
            "default_profile": {
              "type": "boolean"
            },
            "default_profile_image": {
              "type": "boolean"
            },
            "following": {
              "type": "boolean"
            },
            "follow_request_sent": {
              "type": "boolean"
            },
            "notifications": {
              "type": "boolean"
            },
            "translator_type": {
              "type": "keyword"
            }
          }
        },
        "coordinates": {
          "type": "geo_point"
        },
        "place": {
          "properties": {
            "attributes": {
              "type": "object",
              "dynamic": false
            },
            "bounding_box": {
              "type": "geo_shape"
            },
            "country": {
              "type": "text",
              "fields": {
                "ngram": {
                  "type": "text",
                  "analyzer": "custom_ngram"
                }
              }
            },
            "country_code": {
              "type": "text",
              "fields": {
                "ngram": {
                  "type": "text",
                  "analyzer": "custom_ngram"
                }
              }
            },
            "full_name": {
              "type": "text",
              "fields": {
                "ngram": {
                  "type": "text",
                  "analyzer": "custom_ngram"
                }
              }
            },
            "id": {
              "type": "keyword"
            },
            "name": {
              "type": "text",
              "fields": {
                "ngram": {
                  "type": "text",
                  "analyzer": "custom_ngram"
                }
              }
            },
            "place_type": {
              "type": "keyword"
            },
            "url": {
              "type": "text",
              "fields": {
                "ngram": {
                  "type": "text",
                  "analyzer": "custom_ngram"
                }
              }
            }
          }
        },
        "is_quote_status": {
          "type": "boolean"
        },
        "quoted_status_id": {
          "type": "keyword"
        },
        "quoted_status_id_str": {
          "type": "keyword"
        },
        "quoted_status_permalink": {
          "properties": {
            "url": {
              "type": "text",
              "fields": {
                "ngram": {
                  "type": "text",
                  "analyzer": "custom_ngram"
                }
              }
            },
            "expanded": {
              "type": "text",
              "fields": {
                "ngram": {
                  "type": "text",
                  "analyzer": "custom_ngram"
                }
              }
            },
            "display": {
              "type": "text",
              "fields": {
                "ngram": {
                  "type": "text",
                  "analyzer": "custom_ngram"
                }
              }
            }
          }
        },
        "retweet_count": {
          "type": "integer"
        },
        "favorite_count": {
          "type": "integer"
        },
        "favorited": {
          "type": "boolean"
        },
        "retweeted": {
          "type": "boolean"
        },
        "lang": {
          "type": "keyword"
        },
        "quoted_status": {
          "type": "object",
          "dynamic": false
        },
        "retweeted_status": {
          "type": "object",
          "dynamic": false
        }
      }
    },
    "retweeted_status": {
      "properties": {
        "created_at": {
          "type": "date",
          "format": "EEE MMM dd HH:mm:ss Z yyyy"
        },
        "id": {
          "type": "keyword"
        },
        "id_str": {
          "type": "keyword"
        },
        "full_text": {
          "type": "text",
          "fields": {
            "englando": {
              "type": "text",
              "analyzer": "englando"
            }
          }
        },
        "truncated": {
          "type": "boolean"
        },
        "display_text_range": {
          "type": "integer"
        },
        "entities": {
          "properties": {
            "hashtags": {
              "type": "nested",
              "properties": {
                "text": {
                  "type": "keyword",
                  "normalizer": "lowercase_normalizer"
                },
                "indices": {
                  "type": "integer"
                }
              }
            },
            "symbols": {
              "type": "nested",
              "properties": {
                "text": {
                  "type": "keyword",
                  "normalizer": "lowercase_normalizer"
                },
                "indices": {
                  "type": "integer"
                }
              }
            },
            "user_mentions": {
              "type": "nested",
              "properties": {
                "screen_name": {
                  "type": "text",
                  "analyzer": "englando",
                  "fields": {
                    "ngram": {
                      "type": "text",
                      "analyzer": "custom_ngram"
                    },
                    "shingles": {
                      "type": "text",
                      "analyzer": "custom_shingles"
                    }
                  }
                },
                "name": {
                  "type": "text",
                  "analyzer": "englando",
                  "fields": {
                    "ngram": {
                      "type": "text",
                      "analyzer": "custom_ngram"
                    },
                    "shingles": {
                      "type": "text",
                      "analyzer": "custom_shingles"
                    }
                  }
                },
                "id": {
                  "type": "keyword"
                },
                "id_str": {
                  "type": "keyword"
                },
                "indices": {
                  "type": "integer"
                }
              }
            },
            "urls": {
              "type": "nested",
              "properties": {
                "url": {
                  "type": "text",
                  "fields": {
                    "ngram": {
                      "type": "text",
                      "analyzer": "custom_ngram"
                    }
                  }
                },
                "expanded_url": {
                  "type": "text",
                  "fields": {
                    "ngram": {
                      "type": "text",
                      "analyzer": "custom_ngram"
                    }
                  }
                },
                "display_url": {
                  "type": "text",
                  "fields": {
                    "ngram": {
                      "type": "text",
                      "analyzer": "custom_ngram"
                    }
                  }
                },
                "indices": {
                  "type": "integer"
                }
              }
            }
          }
        },
        "source": {
          "type": "text",
          "fields": {
            "ngram": {
              "type": "text",
              "analyzer": "custom_ngram"
            }
          }
        },
        "in_reply_to_status_id": {
          "type": "keyword"
        },
        "in_reply_to_status_id_str": {
          "type": "keyword"
        },
        "in_reply_to_user_id": {
          "type": "keyword"
        },
        "in_reply_to_user_id_str": {
          "type": "keyword"
        },
        "in_reply_to_screen_name": {
          "type": "text",
          "analyzer": "englando",
          "fields": {
            "ngram": {
              "type": "text",
              "analyzer": "custom_ngram"
            },
            "shingles": {
              "type": "text",
              "analyzer": "custom_shingles"
            }
          }
        },
        "user": {
          "properties": {
            "id": {
              "type": "keyword"
            },
            "id_str": {
              "type": "keyword"
            },
            "name": {
              "type": "text",
              "analyzer": "englando",
              "fields": {
                "ngram": {
                  "type": "text",
                  "analyzer": "custom_ngram"
                },
                "shingles": {
                  "type": "text",
                  "analyzer": "custom_shingles"
                }
              }
            },
            "screen_name": {
              "type": "text",
              "analyzer": "englando",
              "fields": {
                "ngram": {
                  "type": "text",
                  "analyzer": "custom_ngram"
                },
                "shingles": {
                  "type": "text",
                  "analyzer": "custom_shingles"
                }
              }
            },
            "location": {
              "type": "text",
              "fields": {
                "ngram": {
                  "type": "text",
                  "analyzer": "custom_ngram"
                }
              }
            },
            "description": {
              "type": "text",
              "fields": {
                "englando": {
                  "type": "text",
                  "analyzer": "englando"
                }
              }
            },
            "url": {
              "type": "text",
              "fields": {
                "ngram": {
                  "type": "text",
                  "analyzer": "custom_ngram"
                }
              }
            },
            "entities": {
              "properties": {
                "url": {
                  "properties": {
                    "urls": {
                      "type": "nested",
                      "properties": {
                        "url": {
                          "type": "text",
                          "fields": {
                            "ngram": {
                              "type": "text",
                              "analyzer": "custom_ngram"
                            }
                          }
                        },
                        "expanded_url": {
                          "type": "text",
                          "fields": {
                            "ngram": {
                              "type": "text",
                              "analyzer": "custom_ngram"
                            }
                          }
                        },
                        "display_url": {
                          "type": "text",
                          "fields": {
                            "ngram": {
                              "type": "text",
                              "analyzer": "custom_ngram"
                            }
                          }
                        },
                        "indices": {
                          "type": "integer"
                        }
                      }
                    }
                  }
                },
                "description": {
                  "properties": {
                    "urls": {
                      "type": "nested",
                      "properties": {
                        "url": {
                          "type": "text",
                          "fields": {
                            "ngram": {
                              "type": "text",
                              "analyzer": "custom_ngram"
                            }
                          }
                        },
                        "expanded_url": {
                          "type": "text",
                          "fields": {
                            "ngram": {
                              "type": "text",
                              "analyzer": "custom_ngram"
                            }
                          }
                        },
                        "display_url": {
                          "type": "text",
                          "fields": {
                            "ngram": {
                              "type": "text",
                              "analyzer": "custom_ngram"
                            }
                          }
                        },
                        "indices": {
                          "type": "integer"
                        }
                      }
                    }
                  }
                }
              }
            },
            "protected": {
              "type": "boolean"
            },
            "followers_count": {
              "type": "integer"
            },
            "friends_count": {
              "type": "integer"
            },
            "listed_count": {
              "type": "integer"
            },
            "created_at": {
              "type": "date",
              "format": "EEE MMM dd HH:mm:ss Z yyyy"
            },
            "favourites_count": {
              "type": "integer"
            },
            "verified": {
              "type": "boolean"
            },
            "statuses_count": {
              "type": "integer"
            },
            "profile_background_color": {
              "type": "keyword"
            },
            "profile_background_image_url": {
              "type": "text",
              "fields": {
                "ngram": {
                  "type": "text",
                  "analyzer": "custom_ngram"
                }
              }
            },
            "profile_background_image_url_https": {
              "type": "text",
              "fields": {
                "ngram": {
                  "type": "text",
                  "analyzer": "custom_ngram"
                }
              }
            },
            "profile_image_url": {
              "type": "text",
              "fields": {
                "ngram": {
                  "type": "text",
                  "analyzer": "custom_ngram"
                }
              }
            },
            "profile_image_url_https": {
              "type": "text",
              "fields": {
                "ngram": {
                  "type": "text",
                  "analyzer": "custom_ngram"
                }
              }
            },
            "profile_link_color": {
              "type": "keyword"
            },
            "profile_sidebar_border_color": {
              "type": "keyword"
            },
            "profile_sidebar_fill_color": {
              "type": "keyword"
            },
            "profile_text_color": {
              "type": "keyword"
            },
            "profile_use_background_image": {
              "type": "boolean"
            },
            "has_extended_profile": {
              "type": "boolean"
            },
            "default_profile": {
              "type": "boolean"
            },
            "default_profile_image": {
              "type": "boolean"
            },
            "following": {
              "type": "boolean"
            },
            "follow_request_sent": {
              "type": "boolean"
            },
            "notifications": {
              "type": "boolean"
            },
            "translator_type": {
              "type": "keyword"
            }
          }
        },
        "coordinates": {
          "type": "geo_point"
        },
        "place": {
          "properties": {
            "attributes": {
              "type": "object",
              "dynamic": false
            },
            "bounding_box": {
              "type": "geo_shape"
            },
            "country": {
              "type": "text",
              "fields": {
                "ngram": {
                  "type": "text",
                  "analyzer": "custom_ngram"
                }
              }
            },
            "country_code": {
              "type": "text",
              "fields": {
                "ngram": {
                  "type": "text",
                  "analyzer": "custom_ngram"
                }
              }
            },
            "full_name": {
              "type": "text",
              "fields": {
                "ngram": {
                  "type": "text",
                  "analyzer": "custom_ngram"
                }
              }
            },
            "id": {
              "type": "keyword"
            },
            "name": {
              "type": "text",
              "fields": {
                "ngram": {
                  "type": "text",
                  "analyzer": "custom_ngram"
                }
              }
            },
            "place_type": {
              "type": "keyword"
            },
            "url": {
              "type": "text",
              "fields": {
                "ngram": {
                  "type": "text",
                  "analyzer": "custom_ngram"
                }
              }
            }
          }
        },
        "is_quote_status": {
          "type": "boolean"
        },
        "quoted_status_id": {
          "type": "keyword"
        },
        "quoted_status_id_str": {
          "type": "keyword"
        },
        "quoted_status_permalink": {
          "properties": {
            "url": {
              "type": "text",
              "fields": {
                "ngram": {
                  "type": "text",
                  "analyzer": "custom_ngram"
                }
              }
            },
            "expanded": {
              "type": "text",
              "fields": {
                "ngram": {
                  "type": "text",
                  "analyzer": "custom_ngram"
                }
              }
            },
            "display": {
              "type": "text",
              "fields": {
                "ngram": {
                  "type": "text",
                  "analyzer": "custom_ngram"
                }
              }
            }
          }
        },
        "retweet_count": {
          "type": "integer"
        },
        "favorite_count": {
          "type": "integer"
        },
        "favorited": {
          "type": "boolean"
        },
        "retweeted": {
          "type": "boolean"
        },
        "lang": {
          "type": "keyword"
        },
        "quoted_status": {
          "type": "object",
          "dynamic": false
        },
        "retweeted_status": {
          "type": "object",
          "dynamic": false
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

#### Zdôvodníte tieto rozhodnutia:

- Prečo a pre ktoré objekty v poli ste zvolili typ nested.
    - Zvolil som nested pre nasledujuce fieldy
        - Hashtags
        - symbols
        - user_mentions
        - urls
    - Pre vsetky tieto fieldy som tak zvolil lebo drzia v sebe zoznam
- Prečo je dôležité definovať rekurzívnu štruktúru pre retweeted_status a aké by boli dôsledky, keby ste ho v striktnej
  schéme nedefinovali.
    - Spravil som to tak ze som skopiroval strukturu pola tweet do pola retweeted_status a quoted status. Nasledne v
      nich som som dal nech sa to neindexuje dalej
- Vysvetlite rozdiel v použití medzi analyzátorom custom_ngram a custom_shingles na poli user.name. Kedy by ste použili
  jeden a kedy druhý?
  - Custom_ngrm sa pouziva hlavne na vyhladavanie na urovni znakom. Takze pre prikladove meno `Juli Forcato` by tam boli
    ngrami `jul`, `uli` atd. shingles funguje na urovni fraz takze by to spojilo `juliforcato`.

### Časť 3: Naimportujte dáta

### Časť 4: Experimentovanie s indexom

Experimentujte s nódami, a zistite koľko nódov musí bežať (a ktoré) aby vám Elasticsearch vedel pridávať dokumenty,
mazať dokumenty, prezerať dokumenty a vyhľadávať nad nimi? Dá sa nastaviť Elastic tak, aby mu stačil jeden nód?
Upravujte ľubovolný tweets.friends_count pomocou vášho jednoduchého skriptu (v rámci Elasticsearchu) a sledujte ako sa
mení _seq_no a _primary_term pri tom ako zabíjate a spúšťate nódy. Čo sa deje s dokumentami
Výstup: Výstup zadania je realizovaný formou protokolu, kde odpovedáte na jednotlivé otázky. Všetky úlohy musia
obsahovať príklady vstupu aj výstup vo formáte JSON.

Záver: Záver, kde zhodnotíte najväčšie úskalia a čo sa podarilo/nepodarilo realizovať.