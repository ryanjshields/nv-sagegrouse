WITH ActiveLeks AS (
    SELECT ST_Buffer(ST_Transform(geom, 26911), 5000) AS geom
    FROM lek_sites
    WHERE state = 'NV' AND lek_status = 'Active'
), Combined AS (
    SELECT ST_Union(geom) AS geom FROM (
        SELECT geom FROM ActiveLeks
        UNION ALL
        SELECT ST_Transform(geom, 26911) FROM distribution
    ) AS Sub
), NVboundary AS (
    SELECT ST_Transform(geom, 26911) AS geom
    FROM state_boundary
), StudyArea AS (
    SELECT ST_Intersection(Combined.geom, NVboundary.geom) AS geom
    FROM Combined
    JOIN NVboundary ON ST_Intersects(Combined.geom, NVboundary.geom)
)
SELECT roads.*
FROM roads
JOIN StudyArea ON ST_Within(ST_Transform(roads.geom, 26911), StudyArea.geom);
