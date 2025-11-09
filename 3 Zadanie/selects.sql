DROP DATABASE osm_slovakia;
CREATE DATABASE osm_slovakia;
CREATE EXTENSION postgis;
CREATE EXTENSION hstore;

SELECT name,
       ST_AsText(ST_Centroid(way)) AS tazisko
FROM planet_osm_polygon
WHERE admin_level = '4';

SELECT name,
       st_area(st_transform(way, 5514)) / 1000000 AS area_km2
FROM planet_osm_polygon
WHERE admin_level = '4'
order by area_km2;

select max(osm_id)
from planet_osm_polygon;

INSERT INTO planet_osm_polygon (osm_id, name, building, way)
VALUES (1448060469,
        'Mlynska 7394',
        'yes',
        ST_GeomFromText('POLYGON((' ||
                        '16.972821505617702 48.21818066130518, ' ||
                        '16.972770543649517 48.218232935264, ' ||
                        '16.97290733630096 48.218290570592586, ' ||
                        '16.972957627716934 48.218242317763746,' ||
                        '16.972821505617702 48.21818066130518' ||
                        '))',
                        4326));

SELECT name, way
FROM planet_osm_polygon
WHERE name = 'Mlynska 7394';

SELECT kraj.name
FROM planet_osm_polygon AS kraj,
     planet_osm_polygon AS dom
WHERE kraj.admin_level = '4'
  AND dom.name = 'Mlynska 7394'
  AND ST_Contains(kraj.way, dom.way);

select max(osm_id)
from planet_osm_point;


INSERT INTO planet_osm_point (osm_id, name, way)
VALUES (13286091436,
        'Moja poloha',
        ST_GeomFromText('POINT(16.97287545382493 48.2182570729315)', 4326));

SELECT name, way
FROM planet_osm_point
WHERE name = 'Moja poloha';

SELECT ST_Contains(dom.way, poloha.way)
FROM planet_osm_polygon AS dom,
     planet_osm_point AS poloha
WHERE dom.name = 'Mlynska 7394'
  AND poloha.name = 'Moja poloha';

SELECT ST_Distance(
               poloha.way::geography,
               fiit.way::geography
       ) AS vzdialenost_v_metroch
FROM planet_osm_point AS poloha,
     planet_osm_polygon AS fiit
WHERE poloha.name = 'Moja poloha'
  AND fiit.name = 'Fakulta informatiky a informačných technológií STU';


SELECT name,
       ST_AsText(ST_Centroid(way))                          AS centroid_coordinates,
       ST_Area(ST_Transform(way, 5514)::geometry) / 1000000 AS area_km2,
       'EPSG:4326'                                          AS srid
FROM planet_osm_polygon okres
WHERE admin_level = '8'
  and lower(name) like 'okres%'
order by area_km2
limit 1;

DROP TABLE IF EXISTS cesty_v_okoli_hranice;
DROP TABLE IF EXISTS cesty_pretinajuce_hranicu;
DROP TABLE IF EXISTS hranica_okresov;
DROP TABLE IF EXISTS buffer_hranice;

-- Vytvorenie docasnej tabulky hranice okresov Malacky a Pezinok
SELECT ST_Intersection(ma.way, pk.way) AS geom
into hranica_okresov
FROM planet_osm_polygon AS ma,
     planet_osm_polygon AS pk
WHERE ma.name = 'okres Malacky'
  AND ma.admin_level = '8'
  AND pk.name = 'okres Pezinok'
  AND pk.admin_level = '8';

-- Vytvorenie docasnej tabulky buffer s okruhom 10 km okolo hranice
SELECT ST_Buffer(hranica_okresov.geom::geography, 10000)::geometry AS geom
into buffer_hranice
FROM hranica_okresov;

-- 1. Cast
SELECT cesta.*
INTO cesty_v_okoli_hranice
FROM planet_osm_roads AS cesta,
     buffer_hranice
WHERE ST_Within(cesta.way, buffer_hranice.geom);

-- 2. Cast
SELECT cesta.*
INTO cesty_pretinajuce_hranicu
FROM planet_osm_roads AS cesta,
     hranica_okresov
WHERE ST_Intersects(cesta.way, hranica_okresov.geom);

SELECT a.way, a.name
FROM planet_osm_polygon as a
WHERE 1 = 1
  and a.admin_level = '6'
  and lower(a.name) like 'bratislava%';

DROP TABLE IF EXISTS bratislava_okolie;

SELECT st_difference(st_intersection(
                             slovensko.way,
                             ST_Buffer(
                                     bratislava.way::geography,
                                     20000
                             )::geometry),
                     bratislava.way) as way
INTO bratislava_okolie
from planet_osm_polygon slovensko,
     planet_osm_polygon bratislava
where 1 = 1
  and slovensko.admin_level = '2'
  and slovensko.name = 'Slovensko'
  and bratislava.admin_level = '6'
  and bratislava.name = 'Bratislava';

select ST_Area(ST_Transform(a.way, 4326)::geography) / 1000000 as area_km2
from bratislava_okolie a;