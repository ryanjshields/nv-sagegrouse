CREATE INDEX lek_sites_geom_idx ON lek_sites USING GIST (geom);
CREATE INDEX distribution_geom_idx ON distribution USING GIST (geom);
CREATE INDEX state_boundary_geom_idx ON state_boundary USING GIST (geom);
CREATE INDEX roads_geom_idx ON roads USING GIST (geom);