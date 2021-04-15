-- FUNCTION: public.make_stock_picking(integer, integer, date, date, character varying, integer, integer, integer, date, character varying, integer, character varying)

-- DROP FUNCTION public.make_stock_picking(integer, integer, date, date, character varying, integer, integer, integer, date, character varying, integer, character varying);

CREATE OR REPLACE FUNCTION public.make_stock_picking(
	picking_type_id integer,
	partner_id integer,
	date_picking date,
	min_date date,
	origin character varying,
	location_dest_id integer,
	location_id integer,
	company_id integer,
	fecha_kardex date,
	name_picking character varying,
	einvoice12 integer,
	state character varying)
    RETURNS integer
    LANGUAGE 'plpgsql'

    COST 100
    VOLATILE 
AS $BODY$
DECLARE
   v_id integer;
BEGIN
	insert into stock_picking(
		picking_type_id,partner_id,date,min_date,origin,
		location_dest_id,location_id,company_id,fecha_kardex,name,einvoice_12,state,move_type,
		max_date,weight_uom_id
	)
	values (
		$1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,'direct',$3,3
	) RETURNING id INTO v_id;
	RETURN v_id;
END;
$BODY$;

ALTER FUNCTION public.make_stock_picking(integer, integer, date, date, character varying, integer, integer, integer, date, character varying, integer, character varying)
    OWNER TO openpg;



-- FUNCTION: public.make_stock_move(character varying, integer, integer, numeric, date, integer, integer, character varying, integer, integer, integer, integer, integer, integer, integer)

-- DROP FUNCTION public.make_stock_move(character varying, integer, integer, numeric, date, integer, integer, character varying, integer, integer, integer, integer, integer, integer, integer);

CREATE OR REPLACE FUNCTION public.make_stock_move(
	name_move character varying,
	product_id integer,
	product_uom integer,
	product_uom_qty numeric,
	date_move date,
	company_id integer,
	inventory_id integer,
	state_move character varying,
	restrict_lot_id integer,
	restrict_partner_id integer,
	location_id integer,
	location_dest_id integer,
	picking_id integer,
	picking_type_id integer,
	warehouse_id integer)
    RETURNS integer
    LANGUAGE 'plpgsql'

    COST 100
    VOLATILE 
AS $BODY$
	DECLARE
   		v_id integer;
	BEGIN
	insert into stock_move(
		name,
		product_id,
		product_uom,
		product_uom_qty,
		date,
		company_id,
		inventory_id,
		state,
		restrict_lot_id,
		restrict_partner_id,
		location_id,
		location_dest_id,
		picking_id,
		picking_type_id,
		warehouse_id,
		priority,
		create_date,
		date_expected,
		product_qty,
		procure_method,
		invoice_state,
		weight_uom_id)
	values(
		$1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,1,$5,$5,$4,'make_to_stock','none',3
	) RETURNING id INTO v_id;
	RETURN v_id;
	END;
	$BODY$;

ALTER FUNCTION public.make_stock_move(character varying, integer, integer, numeric, date, integer, integer, character varying, integer, integer, integer, integer, integer, integer, integer)
    OWNER TO openpg;