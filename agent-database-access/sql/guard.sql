-- A blast-radius guard: refuse any single UPDATE or DELETE on orders that
-- touches more than 1,000 rows, whoever runs it. Statement-level triggers
-- with transition tables (PostgreSQL 10+).
CREATE FUNCTION refuse_mass_change() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE n bigint;
BEGIN
  SELECT count(*) INTO n FROM changed;
  IF n > 1000 THEN
    RAISE EXCEPTION 'refusing to % % rows in % (limit 1000)', TG_OP, n, TG_TABLE_NAME;
  END IF;
  RETURN NULL;
END $$;
CREATE TRIGGER orders_guard_update AFTER UPDATE ON orders
  REFERENCING NEW TABLE AS changed FOR EACH STATEMENT EXECUTE FUNCTION refuse_mass_change();
CREATE TRIGGER orders_guard_delete AFTER DELETE ON orders
  REFERENCING OLD TABLE AS changed FOR EACH STATEMENT EXECUTE FUNCTION refuse_mass_change();
