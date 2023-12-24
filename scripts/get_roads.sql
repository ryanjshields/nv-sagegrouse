WITH NVboundary AS (
    SELECT geom
    FROM state_boundary
), FilteredLeks AS (
    SELECT ST_Buffer(geom, 5000) AS geom
    FROM lek_sites
    WHERE state = 'NV' AND lek_status = 'Active'
    AND ST_Intersects(geom, (SELECT geom FROM NVboundary))
), FilteredDistribution AS (
    SELECT geom
    FROM distribution
    WHERE ST_Intersects(geom, (SELECT geom FROM NVboundary))
), Combined AS (
    SELECT ST_Union(geom) AS geom FROM (
        SELECT geom FROM FilteredLeks
        UNION ALL
        SELECT geom FROM FilteredDistribution
    ) AS Sub
), StudyArea AS (
    SELECT ST_Intersection(Combined.geom, NVboundary.geom) AS geom
    FROM Combined, NVboundary
)
SELECT roads.*, cfcc_descriptions.description
FROM roads
JOIN cfcc_descriptions ON roads."FCC" = cfcc_descriptions.cfcc
WHERE ST_Within(roads.geom, (SELECT geom FROM StudyArea));
