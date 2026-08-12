DO $$
DECLARE
    layer_name text[];
    i int;
    geom_type text;
    srid_check int;
BEGIN
    layer_name := ARRAY['distribution', 'lek_sites', 'predictions', 'roads', 'state_boundary', 'towns'];

    FOR i IN 1..array_length(layer_name, 1) LOOP
        EXECUTE format('SELECT ST_SRID(geom) FROM %I LIMIT 1', layer_name[i]) INTO srid_check;

        IF srid_check != 26911 THEN
            EXECUTE format('SELECT GeometryType(geom) FROM %I LIMIT 1', layer_name[i]) INTO geom_type;
            EXECUTE format('ALTER TABLE %I ALTER COLUMN geom TYPE geometry(%s, 26911) USING ST_Transform(geom, 26911)', layer_name[i], geom_type);
        END IF;
    END LOOP;
END;
$$;