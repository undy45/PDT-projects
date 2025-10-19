# 2. Zadanie: Indexy, plánovač a výkon dotazov v PostgreSQL

Ste dátový inžinier v tíme, ktorý analyzuje historické tweety a profily používateľov. V produkcii sa vám práve spúšťa
ťažký report a dashboardy sú pomalé. Máte podozrenie, že bez indexov plánovač siaha po sekvenčných scanoch a
paralelizácia sa správa „záhadne“. Vašou misiou je preto prejsť sériu experimentov na tabuľkách users a tweets,
pozorovať plány vykonania, vytvárať vhodné indexy a zdokumentovať dopady na čas vykonania a vyťaženie systémových
zdrojov.

## 1. Presné vyhľadanie screen_name

### Vyhľadajte v users screen_name s presnou hodnotou realDonaldTrump a analyzujte daný select. Akú metódu vám vybral plánovač?

```sql
EXPLAIN ANALYZE
SELECT *
FROM users
WHERE screen_name = 'realDonaldTrump';
```

```
Gather  (cost=1000.00..86800.83 rows=1 width=163) (actual time=274.449..279.592 rows=1.00 loops=1)
  Workers Planned: 2
  Workers Launched: 2
  Buffers: shared hit=2860 read=67356
  ->  Parallel Seq Scan on users  (cost=0.00..85800.73 rows=1 width=163) (actual time=133.522..185.257 rows=0.33 loops=3)
        Filter: (screen_name = 'realDonaldTrump'::text)
        Rows Removed by Filter: 997422
        Buffers: shared hit=2860 read=67356
Planning:
  Buffers: shared hit=5 dirtied=1
Planning Time: 0.732 ms
Execution Time: 279.615 ms
```

Planovac zvolil paralelny sekvencny scan, pretoze na stlpci screen_name nie je ziadny index.
Bez indexu toto trvalo `0.732 | 279.615 ms` a ked vytvorime index na stlpec `screen_name`

## 2. Počet workerov a vplyv na čas

### Koľko workerov pracovalo na danom selecte? Zdvihnite počet workerov a povedzte, ako to ovplyvňuje čas. Je tam nejaký strop?

Na dotaze sa podielali 2 workeri. Zvysenie poctu workerov na 3 vsak cas vykonania nezlepsilo.

```
Gather  (cost=1000.00..83281.70 rows=1 width=163) (actual time=258.739..265.299 rows=1.00 loops=1)
  Workers Planned: 3
  Workers Launched: 3
  Buffers: shared hit=12076 read=58140
  ->  Parallel Seq Scan on users  (cost=0.00..82281.60 rows=1 width=163) (actual time=131.708..166.959 rows=0.25 loops=4)
        Filter: (screen_name = 'realDonaldTrump'::text)
        Rows Removed by Filter: 748067
        Buffers: shared hit=12076 read=58140
Planning Time: 0.095 ms
Execution Time: 265.322 ms
```

Toto je koli tomu lebo realne sa hlada iba jeden riadok a zvysenie poctu workerov uz viac nepomaha.
Moze to taktiez byt sposobene vysokym overheadom koordinacie, zdielanych I/O alebo zdielany buffer a contention.
Toto neni generalizovatelne a zalezi to od konkretnej situacie. V tomto pripade to nepomohlo ale moze zvyseny pocet
workerov pomoct pri inych queries.

Pocet workerov moze byt zvyseny nastavenim parametrov `max_parallel_workers`, `max_parallel_workers_per_gather` a
`max_worker_processes` a limit je pocet jadier CPU.

## 3. Index nad screen_name

### Vytvorte index nad screen_name a porovnajte výstup oproti požiadavke bez indexu. Potrebuje plánovač v tejto požiadavke viac workerov? Bol tu aplikovaný nejaký filter na riadky? Prečo?

```sql
CREATE INDEX idx_users_screen_name ON users (screen_name);
```

Spustime dotaz znovu tak nam dotaz bude trvat `1.798 | 0.180 ms`, lebo moze pouzit vytvoreny index
`idx_users_screen_name`

```
Index Scan using idx_users_screen_name on users  (cost=0.43..8.45 rows=1 width=163) (actual time=0.155..0.157 rows=1.00 loops=1)
  Index Cond: (screen_name = 'realDonaldTrump'::text)
  Index Searches: 1
  Buffers: shared hit=1 read=3
Planning:
  Buffers: shared hit=15 read=1
Planning Time: 1.798 ms
Execution Time: 0.180 ms
```

Planovac nepotrebuje viac workerov pretoze dotaz je velmi rychly a nema vyznam paralelizovat ho.
Bol aplikovany filter na riadky `Index Cond: (screen_name = 'realDonaldTrump'::text)`, pretoze sa nasiel iba jeden.

## 4. Filter na followers_count (100–200)

### Vyberte používateľov, ktorí majú followers_count väčší alebo rovný 100 a zároveň menší alebo rovný 200. Je správanie rovnaké ako v prvej úlohe? Je správanie rovnaké ako v druhej úlohe? Prečo?

```
Seq Scan on users  (cost=0.00..115100.02 rows=414992 width=163) (actual time=0.040..467.029 rows=410767.00 loops=1)
  Filter: ((100 <= followers_count) AND (followers_count <= 200))
  Rows Removed by Filter: 2581501
  Buffers: shared hit=15820 read=54396
Planning:
  Buffers: shared hit=136
Planning Time: 1.729 ms
Execution Time: 479.655 ms
```

Planovac zvolil sekvencny scan, pretoze na stlpci `followers_count` nie je ziadny index.
Spravanie je uplne rovnake ako v prvej a druhej ulohe kde viac workerov moc nepomoha pre zrychlenie dotazu.

## 5. Index pre úlohu 4 a bitmapy

### Vytvorte index nad podmienkou z úlohy 4 a popíšte prácu s indexom. Čo je to Bitmap Index Scan a prečo je tam Bitmap Heap Scan? Prečo je tam recheck condition?

`CREATE INDEX idx_follower_count ON users (followers_count) completed in 1 s 486 ms`

```
Bitmap Heap Scan on users  (cost=5758.10..82198.98 rows=414992 width=163) (actual time=45.645..353.383 rows=410767.00 loops=1)
  Recheck Cond: ((100 <= followers_count) AND (followers_count <= 200))
  Heap Blocks: exact=70027
  Buffers: shared hit=16931 read=53450
  ->  Bitmap Index Scan on idx_follower_count  (cost=0.00..5654.35 rows=414992 width=0) (actual time=33.369..33.369 rows=410767.00 loops=1)
        Index Cond: ((followers_count >= 100) AND (followers_count <= 200))
        Index Searches: 1
        Buffers: shared read=354
Planning:
  Buffers: shared hit=19 read=1
Planning Time: 1.312 ms
Execution Time: 365.981 ms
```

#### Čo je to Bitmap Index Scan?

Skenuje index a neziska priamo riadky, ale vytvori bitmapu. Tato struktura oznaci umiestnenie riadkov (tuple
identifiers) vyhovujucich podmienke.

Tato bitmapa predstavuje mnozinu riadkov v tabulke, ktore su potencialne zaujimave.

#### prečo je tam Bitmap Heap Scan?

Pouzije bitmapu na efektivne nacitanie potrebnych stranok z pamate.

#### Prečo je tam recheck condition?

Je tam pretoze bitmapa moze obsahovat false positives. Toto je koli tomu lebo je mozne ze bitmapa oznaci stranku ako
releventnu aj ked neni.

## 6. Širší interval followers_count (100–1000) | vplyv ďalších indexov

### Vyberte používateľov, ktorí majú followers_count väčší alebo rovný 100 a zároveň menší alebo rovný 1000. V čom je rozdiel, prečo?

### Potom:

### - Vytvorte ďalšie 3 indexy na name, friends_count a description.

### - Vložte svojho používateľa (ľubovoľné dáta) do users. Koľko to trvalo?

### - Dropnite vytvorené indexy a spravte vloženie ešte raz. Prečo je tu rozdiel?

```
Bitmap Heap Scan on users  (cost=20029.02..111904.42 rows=1443960 width=163) (actual time=99.936..360.514 rows=1449697.00 loops=1)
  Recheck Cond: ((100 <= followers_count) AND (followers_count <= 1000))
  Heap Blocks: exact=70205
  Buffers: shared hit=70411 read=1054
  ->  Bitmap Index Scan on idx_follower_count  (cost=0.00..19668.03 rows=1443960 width=0) (actual time=87.939..87.939 rows=1449697.00 loops=1)
        Index Cond: ((followers_count >= 100) AND (followers_count <= 1000))
        Index Searches: 1
        Buffers: shared hit=354 read=906
Planning Time: 0.127 ms
Execution Time: 402.776 ms

```

Je tam omnoho viac vysledkov coz znamena ze sa vytvara vacsia bitmapa a zaroven nacitava aj viac stranok. Strategia je
ale rovnaka.

#### Vytvorte ďalšie 3 indexy na name, friends_count a description.

```sql
CREATE INDEX idx_name ON users (name) completed in 19 s 157 ms
CREATE INDEX idx_friends_count ON users (friends_count) completed in 1 s 447 ms
CREATE INDEX idx_description ON users (description) completed in 21 s 826 ms
```

#### Vložte svojho používateľa (ľubovoľné dáta) do users. Koľko to trvalo?

```sql
INSERT INTO users (id, screen_name, name, followers_count, friends_count, description)
values (1, 'undy', 'undy', 0, 0, 'dkjfhvikusewhfiuoesw') 1 row affected in 13 ms
```

#### Dropnite vytvorené indexy a spravte vloženie ešte raz. Prečo je tu rozdiel?

```sql
drop INDEX idx_description, idx_friends_count, idx_name, idx_follower_count, idx_users_screen_name completed in 49 ms
INSERT INTO users (id, screen_name, name, followers_count, friends_count, description)
values (3, 'undy', 'undy', 0, 0, 'dkjfhvikusewhfiuoesw') 1 row affected in 2 ms
```

Bolo to rychlejsie lebo pri insertovani sa uz nemuseli aktualizovat vsetky indexy, co zabera cas.

## 7. Indexy v tweets pre retweet_count a full_text

### Vytvorte index nad retweet_count a nad full_text. Porovnajte dĺžku vytvárania. Prečo je tu taký rozdiel?

```sql
CREATE INDEX idx_retweet_count ON tweets (retweet_count) completed in 13 s 215 ms
CREATE INDEX idx_full_text ON tweets (full_text) completed in 53 s 362 ms
```

retweet_count je ciselny stlpec coz umoznuje efektivnejsie usporiadanie a hladanie v indexe.
full_text je textovy stlpec ktory je vacsi a zlozitejsi.

## 8. Porovnanie indexov (stručne)

### Porovnajte indexy pre retweet_count, full_text, followers_count, screen_name, … v čom sa líšia a prečo

`idx_retweet_count`, `idx_follower_count` a `idx_friends_count` su velmi podobne kde maju avg_item_size ~ 729 B. Toto
poukazuje na specificke nastavenia ukladania. Su ale relativne male a efektivne. Textove indexy ako
`idx_users_screen_name` a `idx_name` maju mensie velkosti avg_item_size ~ 25 B lebo ide o kratsie texty. `idx_full_text`
je oproti tomu vyrazne vacsi, koli vacsej priemernej velkosti polozky ~ 149 B, velkom pocte poloziek.

## 9. Hľadanie „Gates“ kdekoľvek vo tweets.full_text

### Vyhľadajte v tweets.full_text meno „Gates“ na ľubovoľnom mieste a porovnajte výsledok po tom, ako full_text naindexujete. V čom je rozdiel a prečo?

```sql
select *
from tweets
where full_text LIKE '%Gates%';
```

S a bez indexu neni ziadny rozdiel lebo obycajny B-tree index ktory sme vytvorili aj tak neni pre tento search pouzity.

## 10. Tweet začínajúci na „DANGER: WARNING:“

### Vyhľadajte tweet, ktorý začína DANGER: WARNING:. Použil sa index?

```sql
select *
from tweets
where full_text LIKE 'DANGER: WARNING:%';
```

Index sa nepouzil.

## 11. Indexovanie full_text pre použitie indexu

### Teraz naindexujte full_text tak, aby sa použil index a zhodnoťte, prečo sa predtým nad DANGER: WARNING: nepoužil. Použije sa teraz na „Gates“ na ľubovoľnom mieste?

```sql
CREATE INDEX idx_full_text_start ON tweets (full_text text_pattern_ops);
```

Nepouzil sa lebo obycajny obycajny B-tree index nie je vhodny pre full text vyhladavanie. Teraz

```sql
select *
from tweets
where full_text LIKE 'DANGER: WARNING:%';
```

pouzije index

```
Index Scan using idx_full_text_start on tweets  (cost=0.68..8.70 rows=587 width=310) (actual time=0.021..0.022 rows=1.00 loops=1)
  Index Cond: ((full_text ~>=~ 'DANGER: WARNING:'::text) AND (full_text ~<~ 'DANGER: WARNING;'::text))
  Filter: (full_text ~~ 'DANGER: WARNING:%'::text)
  Index Searches: 1
  Buffers: shared hit=6
Planning Time: 0.228 ms
Execution Time: 0.037 ms
```

lebo som text_pattern_ops moze index efektivne vyhladavat na zaciatku retazca.

## 12. Vyhľadanie sufixu „LUCIFERASE“ (case-insensitive)

### Vytvorte nový index tak, aby ste vedeli vyhľadať tweet, ktorý končí reťazcom „LUCIFERASE“ a nezáleží na tom, ako to napíšete.

```sql
CREATE INDEX idx_full_text_end ON tweets (reverse(full_text) text_pattern_ops);
select *
from tweets
where reverse(full_text) LIKE reverse('%LUCIFERASE');
```

```
Bitmap Heap Scan on tweets  (cost=1634.22..89986.27 rows=31760 width=310) (actual time=0.048..0.048 rows=0.00 loops=1)
  Filter: (reverse(full_text) ~~ 'ESAREFICUL%'::text)
  Buffers: shared hit=5
  ->  Bitmap Index Scan on idx_full_text_end  (cost=0.00..1626.28 rows=31760 width=0) (actual time=0.032..0.032 rows=0.00 loops=1)
        Index Cond: ((reverse(full_text) ~>=~ 'ESAREFICUL'::text) AND (reverse(full_text) ~<~ 'ESAREFICUM'::text))
        Index Searches: 1
        Buffers: shared hit=5
Planning Time: 0.165 ms
Execution Time: 0.071 ms
```

## 13. Kombinované filtre a triedenie v users

### Nájdite účty, ktoré majú follower_count < 10 a friends_count > 1000, a výsledok zoraďte podľa statuses_count. Následne spravte jednoduché indexy tak, aby to malo

```sql
select *
from users
where followers_count < 10
  and friends_count > 1000
order by statuses_count
```

```
Sort  (cost=77269.54..77374.30 rows=41904 width=163) (actual time=71.782..71.789 rows=167.00 loops=1)
  Sort Key: statuses_count
  Sort Method: quicksort  Memory: 49kB
  Buffers: shared hit=997
  ->  Bitmap Heap Scan on users  (cost=9969.93..74052.40 rows=41904 width=163) (actual time=71.631..71.739 rows=167.00 loops=1)
        Recheck Cond: ((followers_count < 10) AND (friends_count > 1000))
        Heap Blocks: exact=165
        Buffers: shared hit=997
        ->  BitmapAnd  (cost=9969.93..9969.93 rows=41904 width=0) (actual time=71.218..71.219 rows=0.00 loops=1)
              Buffers: shared hit=832
              ->  Bitmap Index Scan on idx_follower_count  (cost=0.00..1922.64 rows=172562 width=0) (actual time=21.496..21.496 rows=169773.00 loops=1)
                    Index Cond: (followers_count < 10)
                    Index Searches: 1
                    Buffers: shared hit=146
              ->  Bitmap Index Scan on idx_friends_count  (cost=0.00..8026.09 rows=726621 width=0) (actual time=46.839..46.839 rows=731822.00 loops=1)
                    Index Cond: (friends_count > 1000)
                    Index Searches: 1
                    Buffers: shared hit=686
Planning:
  Buffers: shared hit=4
Planning Time: 0.147 ms
Execution Time: 72.397 ms
```

Krasne to pouzilo indexy ktore som vytvoril a nasledne to pouzilo quick sort na zoradenie

## 14. Zložený index vs. separátne indexy

### Na predošlú query spravte zložený index a porovnajte výsledok s tým, keď sú indexy separátne.

```sql
CREATE INDEX idx_combined ON users (followers_count, friends_count);
```

```
Sort  (cost=69100.83..69205.59 rows=41904 width=163) (actual time=0.270..0.278 rows=167.00 loops=1)
  Sort Key: statuses_count
  Sort Method: quicksort  Memory: 49kB
  Buffers: shared hit=200
  ->  Bitmap Heap Scan on users  (cost=1801.23..65883.70 rows=41904 width=163) (actual time=0.109..0.223 rows=167.00 loops=1)
        Recheck Cond: ((followers_count < 10) AND (friends_count > 1000))
        Heap Blocks: exact=165
        Buffers: shared hit=200
        ->  Bitmap Index Scan on idx_combined  (cost=0.00..1790.75 rows=41904 width=0) (actual time=0.060..0.060 rows=167.00 loops=1)
              Index Cond: ((followers_count < 10) AND (friends_count > 1000))
              Index Searches: 11
              Buffers: shared hit=35
Planning:
  Buffers: shared hit=39 read=4
Planning Time: 2.235 ms
Execution Time: 0.310 ms
```

Nerobili sme 2 index scany ale iba jeden co je efektivnejsie. Cas vykonania sa znizil z `72.397 ms` na `0.310 ms`.

## 15. Zmena hranice follower_coun

### Upravte query tak, aby bol follower_count < 1000 a friends_count > 1000. V čom je rozdiel a prečo?

```
Gather Merge  (cost=94038.67..160911.79 rows=558511 width=163) (actual time=468.350..553.793 rows=263297.00 loops=1)
  Workers Planned: 4
  Workers Launched: 3
  Buffers: shared hit=3513 read=67459
  ->  Sort  (cost=93038.61..93387.68 rows=139628 width=163) (actual time=330.784..338.769 rows=65824.25 loops=4)
        Sort Key: statuses_count
        Sort Method: quicksort  Memory: 23869kB
        Buffers: shared hit=3513 read=67459
        Worker 0:  Sort Method: quicksort  Memory: 12635kB
        Worker 1:  Sort Method: quicksort  Memory: 10723kB
        Worker 2:  Sort Method: quicksort  Memory: 10224kB
        ->  Parallel Bitmap Heap Scan on users  (cost=8165.72..81106.54 rows=139628 width=163) (actual time=23.990..308.388 rows=65824.25 loops=4)
              Recheck Cond: (friends_count > 1000)
              Filter: (followers_count < 1000)
              Rows Removed by Filter: 117131
              Heap Blocks: exact=28757
              Buffers: shared hit=3492 read=67459
              Worker 0:  Heap Blocks: exact=15783
              Worker 1:  Heap Blocks: exact=13130
              Worker 2:  Heap Blocks: exact=12535
              ->  Bitmap Index Scan on idx_friends_count  (cost=0.00..8026.09 rows=726621 width=0) (actual time=75.153..75.153 rows=731822.00 loops=1)
                    Index Cond: (friends_count > 1000)
                    Index Searches: 1
                    Buffers: shared hit=686
Planning Time: 0.176 ms
Execution Time: 563.988 ms
```

Kedze bolo viac vysledkov tak planovac rozhodol pouzit paralelizaciu co zlepsilo vykonanie. Spravil tak pre bithmap heap
scan nasledne si rozdelil vysledok a po sortoval si bloky s quick sortom a nasledne to spojil s merge sort.

## Komplexný dotaz nad tweets a users

### Vyhľadajte všetky tweety (full_text), ktoré spomenul autor, ktorý obsahuje v popise (description) reťazec „comedian” (case-insensitive), tweety musia obsahovať reťazec „conspiracy“ (case-insensitive), tweety nesmú mať priradený hashtag a počet retweetov (retweet_count) je buď menší alebo rovný 10, alebo väčší ako 50. Zobrazte len rozdielne záznamy a zoraďte ich podľa počtu followerov DESC a pobavte sa. Následne nad tým spravte analýzu a popíšte do protokolu, čo všetko sa tam deje (EXPLAIN ANALYZE).

```sql
select distinct t.*, u.followers_count
from tweets t
         join users u on t.user_id = u.id
where 1 = 1
  and u.description LIKE '%comedian%'
  and t.full_text LIKE '%conspiracy%'
  and (t.retweet_count <= 10 or t.retweet_count >= 50)
  and NOT EXISTS (SELECT 1
                  FROM tweet_hashtag th
                  WHERE th.tweet_id = t.id)
order by u.followers_count DESC;
```

```
Unique  (cost=272084.89..272084.94 rows=1 width=314) (actual time=1524.205..1536.641 rows=1.00 loops=1)
  Buffers: shared hit=56331 read=209927
  ->  Sort  (cost=272084.89..272084.90 rows=1 width=314) (actual time=1524.204..1536.639 rows=1.00 loops=1)
"        Sort Key: u.followers_count DESC, t.id, t.created_at, t.full_text, t.display_from, t.display_to, t.lang, t.user_id, t.source, t.in_reply_to_status_id, t.quoted_status_id, t.retweeted_status_id, t.place_id, t.retweet_count, t.favorite_count, t.possibly_sensitive"
        Sort Method: quicksort  Memory: 25kB
        Buffers: shared hit=56331 read=209927
        ->  Nested Loop Anti Join  (cost=1000.86..272084.88 rows=1 width=314) (actual time=1523.845..1536.615 rows=1.00 loops=1)
              Buffers: shared hit=56331 read=209927
              ->  Gather  (cost=1000.43..272081.89 rows=1 width=314) (actual time=778.268..1536.582 rows=2.00 loops=1)
                    Workers Planned: 4
                    Workers Launched: 3
                    Buffers: shared hit=56324 read=209927
                    ->  Nested Loop  (cost=0.43..271081.79 rows=1 width=314) (actual time=1232.110..1437.117 rows=0.50 loops=4)
                          Buffers: shared hit=56324 read=209927
                          ->  Parallel Seq Scan on tweets t  (cost=0.00..270222.37 rows=103 width=310) (actual time=10.119..1403.269 rows=1488.50 loops=4)
                                Filter: ((full_text ~~ '%conspiracy%'::text) AND ((retweet_count <= 10) OR (retweet_count >= 50)))
                                Rows Removed by Filter: 1586533
                                Buffers: shared hit=32505 read=209927
                          ->  Index Scan using users_pkey on users u  (cost=0.43..8.34 rows=1 width=12) (actual time=0.021..0.021 rows=0.00 loops=5954)
                                Index Cond: (id = t.user_id)
                                Filter: (description ~~ '%comedian%'::text)
                                Rows Removed by Filter: 1
                                Index Searches: 5954
                                Buffers: shared hit=23819
              ->  Index Only Scan using tweet_hashtag_pkey on tweet_hashtag th  (cost=0.43..4.44 rows=4 width=8) (actual time=0.012..0.012 rows=0.50 loops=2)
                    Index Cond: (tweet_id = t.id)
                    Heap Fetches: 0
                    Index Searches: 2
                    Buffers: shared hit=7
Planning:
  Buffers: shared hit=33
Planning Time: 2.578 ms
Execution Time: 1536.724 ms
```

Najprv sa spravil Index Scan na useroch kde sa checkla podmienka `description LIKE '%comedian%'` (cez filter) a zaroven
join (index cond). Nasledne sa spravil paralelny sekvencny scan na tweetoch kde sa checkli podmienky
`full_text LIKE '%conspiracy%'` a `retweet_count <= 10 or retweet_count >= 50` (dalo by sa zlepsit indexom). Potom sa to
pozbieralo paralelne dokopy. Spravil sa Anti join na index only scan na tweet_hashtag aby sa vyfiltrovali tweety s
hashtagmi. Ako predposledny krok sa spravil sort podla u.followers_count kde sa pouzil quick sort. Ako posledny krok sa
spravil unique.

Vysledkom je jeden zaznam:

| id                  | created_at                 | full_text | display_from                                                                                                                                 | display_to | lang | user_id | source    | in_reply_to_status_id                                                              | quoted_status_id | retweeted_status_id | place_id | retweet_count | favorite_count | possibly_sensitive | followers_count |
|---------------------|----------------------------|-----------|----------------------------------------------------------------------------------------------------------------------------------------------|------------|------|---------|-----------|------------------------------------------------------------------------------------|------------------|---------------------|----------|---------------|----------------|--------------------|-----------------|
| 1290916763572600840 | 2020-08-05 07:45:15.000000 | 00:00     | RT @ChelseaClinton: Trump is an anti-science, narcissistic, conspiracy-peddling racist leader absent of empathy when we need the opposite t… | null       | null | en      | 266707226 | <a href="http://twitter.com/download/iphone" rel="nofollow">Twitter for iPhone</a> | null             | null                | null     | null          | 2880           | 0                  | null            |3732           |