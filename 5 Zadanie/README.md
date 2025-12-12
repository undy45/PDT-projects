# 5. Dátové modelovanie v MongoDB

Enkh-Undral EnkhBayar

Navrhnite dátový model v MongoDB pre sociálnu sieť typu Instagram / Twitter Lite, ktorá umožňuje publikovanie obsahu a
sociálne interakcie.

Úlohy:

## 1. Navrhnite dátový model s využitím minimálne 3 rôznych design patterns (napr. Subset, Polymorphic Pattern, Outlier Patter, Bucket…).

Vysvetlite Váš návrh: ktoré polia a entity budú embedované a ktoré budú referencované s odôvodnením. Zdôvodnite výber
použitých design patterns.
JSON-like examples pre Vami navrhné štruktúry dokumentov
{
_id: ObjectId,
username: string,
…

Systém obsahuje tieto hlavné entity:

Users
Profil, základné informácie, nastavenia, počty followerov/following, histórie aktivít.
Posts
Rôzne typy obsahu (text, obrázok, video, externý link), metaúdaje (timestamp, autor, tagy, location).
Comments
Krátke textové reakcie používateľov, pri populárnych príspevkoch ich môžu byť tisíce.
Likes/Reactions
Reakcie používateľov na príspevok alebo komentár.
Follows
Informácia o tom, kto koho sleduje.

Typické používateľské scenáre a interakcie:

Feed používateľa (hlavná obrazovka aplikácie) ~ 35 % všetkých dotazov

Používateľ otvorí aplikáciu → systém musí čo najrýchlejšie načítať:

posledné príspevky od používateľov, ktorých sleduje,
základné metaúdaje o autoroch (avatar, username),
malú vzorku komentárov (napr. 3 najnovšie),
počty likes, reactions.

2. Detail príspevku (post detail view) ~ 20 % dotazov

Zobrazí sa diskusia:

po stránkach komentáre (paginated)
všetkých reakcií,
full profile informácií autora príspevku.

3. Reakcia na príspevok alebo komentár ~ 15 % dotazov

Likes a iné reakcie.

Patrí medzi najfrekventovanejšie akcie. Tieto operácie musia byť veľmi rýchle a ľahko škálovateľné.

4. Pridanie nového komentára k príspevku ~ 10 % dotazov

Používateľ vloží komentár, vytvorí sa nový dokument v kolekcii comments, aktualizujú sa:

počty komentárov v Posts,
embedované "preview" komentáre v príspevku (ak používame subset pattern).   
Publikovanie nového príspevku  ~ 5 % dotazov

Používateľ zdieľa nový text/obrázok/video: zápis príspevku, update počtu posts v profile autora.

Relatívne málo dotazov v porovnaní s čítaním feedu.

Prehliadanie profilu používateľa  ~ 8 % dotazov

Používateľ klikne na profil a načítajú sa:

základné dáta o používateľovi
posledné príspevky autora,
counters (followers, following, posts).
Tieto dotazy sú časté, ale menej než feed.

Follow / Unfollow < 5%

Pridanie alebo zmazanie vzťahu, update counters pri používateľovi. Menej časté.

Vyhľadávanie používateľov alebo hashtagov < 5%

Full-text a autocomplete dotazy.

## Riesenie

Rozhodol som sa vytvorit 5 kolekcii: Users, Posts, Comments, Reactions, Follows (tak isto ako je popisane v zadani).
Pojdem kolekciu po kolekcii a vysvetlim design patterns a rozhodnutia.

### Users Collection

```json
{
  "_id": "196377029",
  "username": "Macarena",
  "display_name": "maquialifraco",
  "avatar_url": "https://example.com/nejaka_fotka.jpg",
  "description": "⚖️ Abogada | 📖 Inducción Legislativa UBA.",
  "created_at": "2020-06-15T18:47:25.000Z",
  "settings": {
    "is_private": false,
    "language": "es",
    "notifications": {
      "likes": true,
      "comments": true,
      "follows": true
    }
  },
  "counters": {
    "followers": 486,
    "following": 778,
    "posts": 120
  },
  "recent_activity": [
    {
      "type": "post",
      "ref_id": "7452781",
      "created_at": "2025-12-12T10:00:00.000Z"
    },
    {
      "type": "comment",
      "ref_id": "785273782",
      "created_at": "2025-12-12T10:05:00.000Z"
    }
  ]
}
```

Zakladna kolekcia userov. Mame zakladne udaje ako profil, countery, nastavenia a embedovane lahke veci typu avatar,
username. Vsetko ostatne je cez referencie. Zaroven tu je pouzity subset pattern pre recent_activity, kde mame len
referenciu na post alebo comment a cas vytvorenia.

### Posts Collection

```json
{
  "_id": "7451732678",
  "author_id": "71732782",
  "created_at": "2025-12-12T10:05:00.000Z",
  "type": "text",
  "content": {
    "text": "Toto je random text"
  },
  "tags": [
    "31Jul"
  ],
  "location": {
    "name": "Córdoba, Argentina",
    "lat": -31.4201,
    "lon": -64.1888
  },
  "stats": {
    "likes_count": 30452,
    "comments_count": 3,
    "reactions_count": 30452
  },
  "comments_preview": [
    {
      "comment_id": "656547856",
      "author_id": "65489747816",
      "author_username": "juli",
      "author_avatar": "https://example.com/nejaka_fotka.jpg",
      "text": "kdjfbv jkdfbhviufrdsbvi",
      "created_at": "2025-12-12T00:00:00.000Z"
    },
    {
      "comment_id": "745271781",
      "author_id": "785278235871",
      "author_username": "maca",
      "author_avatar": "https://example.com/nejaka_fotka.jpg",
      "text": "ewrujhvckujwsecnksdnc",
      "created_at": "2025-12-12T00:00:00.000Z"
    },
    {
      "comment_id": "727172",
      "author_id": "7782785217867893",
      "author_username": "user123",
      "author_avatar": "https://example.com/nejaka_fotka.jpg",
      "text": "dkfjhvkjsdhcvoisoilcmsedpolc",
      "created_at": "2025-12-12T00:00:00.000Z"
    }
  ],
  "is_outlier": true,
  "outlier_meta": {
    "peak_likes": 30000,
    "peak_comments": 1500
  }
}
```

Toto je kolekacia postov. Pouzil som tu Subset Pattern pre embedovanie preview komentárov. Zaroven som pouzil Outlier
Pattern pre polia is_outlier a outlier_meta, kde ak post je velmi popoularny a aby sa nemuselo vzdy ratat s interakciami
tak sa pouzije outlier meta data. Zaroven tu je pouzity Polymorphic Pattern pre content, kde moze byt text, obrazok,
video alebo externy link. Nasledne policko type by nam povedalo ze co za typ to je.

Subset pattern na komentare je pouzity pretoze v feed view potrebujeme len par komentárov a nie vsetky. Taktiez
potrebujeme aj par udajov o autorovi komentaru (username, avatar) takze je efektivnejsie mat to embedovane ako robit
join cez referenciu.

Polymorphic pattern je pouzity pretoze posty mozu mat rozne typy obsahu a je efektivnejsie mat to v jednom poli
ako robit rozne kolekcie pre kazdy typ. Tieto rozne typy by mali toho vela spolocneho a rozdiel realne by bol iba v
content.

Outlier pattern je pouzity pretoze velmi popularne posty by mohli mat extremne mnozstvo interakcii a by to mohlo
spomalit operacie. Takze pre tieto posty mame specialne pole na rychle ziskanie tychto udajov.

### Comments Collection

```json
{
  "_id": "727172",
  "post_id": "7451732678",
  "parent_comment_id": null,
  "author_id": "52415641756451",
  "text": "Totalmente de acuerdo.",
  "created_at": "2025-12-12T00:00:00.000Z"
}
```

Samostatna kolekcia komentarov. Mame tu referenciu na autora a zaroven parent_comment_id pre pripadne reply na komentar.
Toto je jednoduche a efektivne riesenie. Je tu aj samostatne post id, aby sme mohli rychlo ziskat vsetky komentare pre
dany post. Je tu aj parent_comment_id pre pripadne reply na komentar. Tento reply komentar taktiez bude mat post_id
daneho postu pod ktorym je parent komentar. Tuto dokazem robit jednoduchy pagination a aj sort podla created_at.

Pri vytvoreni noveho komentara sa do tejto kolekcie vlozi novy dokument a nasledne sa update-uje stats.comments_count v Posts kolekcii.
Taktiez sa update-uje comments_preview v Posts kolekcii, kde sa prida novy komentar na zaciatok pola a ak je dlzka pola
vacsia ako 3, tak sa odstrani posledny komentar z pola.

### Reactions Collection

```json
{
  "_id": "9827817827",
  "user_id": "752171732789",
  "target_type": "post",
  "target_id": "727541725872",
  "type": "like",
  "created_at": "2025-12-12T00:00:00.000Z"
}
```

Jedonoducha kolekcia pre reakcie. Pouzil som tu Polymorphic Pattern pre target_type a target_id, kde reakcia moze
byť na post alebo komentar. Zaroven tu je policko type pre typ reakcie (like, love, haha, sad, angry atd.). Toto
riesenie je flexibilne a jednoduche na rozsirovanie.

### Follows Collection

```json
{
  "_id": "654651616",
  "follower_id": "752171732789",
  "followee_id": "52415641756451",
  "created_at": "2025-12-12T00:00:00.000Z"
}
```

Jednoducha kolekcia pre sledovanie vztahov medzi usermi. Kazdy dokument reprezentuje jeden follow vztah.

