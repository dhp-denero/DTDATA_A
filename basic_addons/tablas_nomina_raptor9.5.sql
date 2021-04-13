--
-- PostgreSQL database dump
--

-- Dumped from database version 9.5.4
-- Dumped by pg_dump version 9.5.4

-- Started on 2018-11-02 20:01:54

SET statement_timeout = 0;
SET lock_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;
SET row_security = off;

SET search_path = public, pg_catalog;

--
-- TOC entry 6177 (class 0 OID 47623)
-- Dependencies: 1440
-- Data for Name: hr_payroll_structure; Type: TABLE DATA; Schema: public; Owner: openpg
--

SET SESSION AUTHORIZATION DEFAULT;

ALTER TABLE hr_payroll_structure DISABLE TRIGGER ALL;

INSERT INTO hr_payroll_structure (id, create_uid, code, name, company_id, write_uid, note, parent_id, write_date, create_date) VALUES (2, 1, 'ESTRU1', 'Estructura Base', 1, 1, NULL, NULL, '2018-11-02 15:03:33.264716', '2018-10-29 14:36:00.119193');


ALTER TABLE hr_payroll_structure ENABLE TRIGGER ALL;

--
-- TOC entry 6201 (class 0 OID 0)
-- Dependencies: 1439
-- Name: hr_payroll_structure_id_seq; Type: SEQUENCE SET; Schema: public; Owner: openpg
--

SELECT pg_catalog.setval('hr_payroll_structure_id_seq', 2, true);


--
-- TOC entry 6180 (class 0 OID 47653)
-- Dependencies: 1445
-- Data for Name: hr_salary_rule_category; Type: TABLE DATA; Schema: public; Owner: openpg
--

ALTER TABLE hr_salary_rule_category DISABLE TRIGGER ALL;

INSERT INTO hr_salary_rule_category (id, create_uid, code, name, company_id, write_uid, note, parent_id, write_date, create_date, aparece_en_nomina, secuencia, is_ing_or_desc) VALUES (15, 1, 'ING', 'INGRESOS', 1, 1, NULL, NULL, '2018-10-29 14:15:41.311494', '2018-10-29 14:15:41.311494', true, 1, 'ingreso');
INSERT INTO hr_salary_rule_category (id, create_uid, code, name, company_id, write_uid, note, parent_id, write_date, create_date, aparece_en_nomina, secuencia, is_ing_or_desc) VALUES (16, 1, 'APOR_TRA', 'APORTES TRABAJADOR', 1, 1, NULL, NULL, '2018-10-29 14:15:41.311494', '2018-10-29 14:15:41.311494', true, 2, 'descuento');
INSERT INTO hr_salary_rule_category (id, create_uid, code, name, company_id, write_uid, note, parent_id, write_date, create_date, aparece_en_nomina, secuencia, is_ing_or_desc) VALUES (17, 1, 'DES_NET', 'DESCUENTOS AL NETO', 1, 1, NULL, NULL, '2018-10-29 14:15:41.311494', '2018-10-29 14:15:41.311494', true, 3, 'descuento');
INSERT INTO hr_salary_rule_category (id, create_uid, code, name, company_id, write_uid, note, parent_id, write_date, create_date, aparece_en_nomina, secuencia, is_ing_or_desc) VALUES (18, 1, 'DES_AFE', 'DESCUENTOS AFECTOS', 1, 1, NULL, NULL, '2018-10-29 14:15:41.311494', '2018-10-29 14:15:41.311494', true, 4, 'descuento');
INSERT INTO hr_salary_rule_category (id, create_uid, code, name, company_id, write_uid, note, parent_id, write_date, create_date, aparece_en_nomina, secuencia, is_ing_or_desc) VALUES (20, 1, 'SUB', 'SUBTOTALES', 1, 1, NULL, NULL, '2018-10-29 14:15:41.311494', '2018-10-29 14:15:41.311494', true, 6, 'descuento');
INSERT INTO hr_salary_rule_category (id, create_uid, code, name, company_id, write_uid, note, parent_id, write_date, create_date, aparece_en_nomina, secuencia, is_ing_or_desc) VALUES (21, 1, 'APOR_EMP', 'APORTES EMPLEADOR', 1, 1, NULL, NULL, '2018-10-29 14:15:41.311494', '2018-10-29 14:15:41.311494', true, 7, 'descuento');
INSERT INTO hr_salary_rule_category (id, create_uid, code, name, company_id, write_uid, note, parent_id, write_date, create_date, aparece_en_nomina, secuencia, is_ing_or_desc) VALUES (19, 1, 'POR', 'PORCENTAJES', 1, 1, NULL, NULL, '2018-10-29 14:15:58.226008', '2018-10-29 14:15:41.311494', false, 5, 'descuento');


ALTER TABLE hr_salary_rule_category ENABLE TRIGGER ALL;

--
-- TOC entry 6182 (class 0 OID 47714)
-- Dependencies: 1455
-- Data for Name: hr_salary_rule; Type: TABLE DATA; Schema: public; Owner: openpg
--

ALTER TABLE hr_salary_rule DISABLE TRIGGER ALL;

INSERT INTO hr_salary_rule (id, code, create_date, write_date, sequence, write_uid, appears_on_payslip, condition_range, amount_fix, create_uid, parent_rule_id, company_id, note, amount_percentage, condition_range_min, condition_select, amount_percentage_base, register_id, amount_select, active, condition_range_max, name, condition_python, amount_python_compute, category_id, quantity, analytic_account_id, account_credit, account_tax_id, account_debit, cod_sunat, is_subtotal) VALUES (65, 'FAL', '2018-10-30 16:42:02.861646', '2018-10-31 20:53:39.066758', 2, 6, true, 'contract.wage', NULL, 1, NULL, 1, NULL, NULL, NULL, 'none', NULL, NULL, 'code', true, NULL, 'Faltas', '
                    # Available variables:
                    #----------------------
                    # payslip: object containing the payslips
                    # employee: hr.employee object
                    # contract: hr.contract object
                    # rules: object containing the rules code (previously computed)
                    # categories: object containing the computed salary rule categories (sum of amount of all rules belonging to that category).
                    # worked_days: object containing the computed worked days
                    # inputs: object containing the computed inputs

                    # Note: returned value have to be set in the variable ''result''

                    result = rules.NET > categories.NET * 0.10', 'result=worked_days.FAL.number_of_days*(contract.wage/30)', 15, '1.0', NULL, NULL, NULL, NULL, NULL, false);
INSERT INTO hr_salary_rule (id, code, create_date, write_date, sequence, write_uid, appears_on_payslip, condition_range, amount_fix, create_uid, parent_rule_id, company_id, note, amount_percentage, condition_range_min, condition_select, amount_percentage_base, register_id, amount_select, active, condition_range_max, name, condition_python, amount_python_compute, category_id, quantity, analytic_account_id, account_credit, account_tax_id, account_debit, cod_sunat, is_subtotal) VALUES (64, 'BAS', '2018-10-30 16:42:02.861646', '2018-10-30 16:42:02.861646', 1, 1, true, 'contract.wage', NULL, 1, NULL, 1, NULL, NULL, NULL, 'none', NULL, NULL, 'code', true, NULL, 'Básico', '
                    # Available variables:
                    #----------------------
                    # payslip: object containing the payslips
                    # employee: hr.employee object
                    # contract: hr.contract object
                    # rules: object containing the rules code (previously computed)
                    # categories: object containing the computed salary rule categories (sum of amount of all rules belonging to that category).
                    # worked_days: object containing the computed worked days
                    # inputs: object containing the computed inputs

                    # Note: returned value have to be set in the variable ''result''

                    result = rules.NET > categories.NET * 0.10', 'result = contract.wage', 15, '1.0', NULL, NULL, NULL, NULL, NULL, false);
INSERT INTO hr_salary_rule (id, code, create_date, write_date, sequence, write_uid, appears_on_payslip, condition_range, amount_fix, create_uid, parent_rule_id, company_id, note, amount_percentage, condition_range_min, condition_select, amount_percentage_base, register_id, amount_select, active, condition_range_max, name, condition_python, amount_python_compute, category_id, quantity, analytic_account_id, account_credit, account_tax_id, account_debit, cod_sunat, is_subtotal) VALUES (66, 'TAR', '2018-10-30 16:42:02.861646', '2018-10-30 16:42:02.861646', 3, 1, true, 'contract.wage', NULL, 1, NULL, 1, NULL, NULL, NULL, 'none', NULL, NULL, 'code', true, NULL, 'Tardanzas', '
                    # Available variables:
                    #----------------------
                    # payslip: object containing the payslips
                    # employee: hr.employee object
                    # contract: hr.contract object
                    # rules: object containing the rules code (previously computed)
                    # categories: object containing the computed salary rule categories (sum of amount of all rules belonging to that category).
                    # worked_days: object containing the computed worked days
                    # inputs: object containing the computed inputs

                    # Note: returned value have to be set in the variable ''result''

                    result = rules.NET > categories.NET * 0.10', 'result=worked_days.TAR.number_of_hours*(contract.wage/30/8)', 15, '1.0', NULL, NULL, NULL, NULL, NULL, false);
INSERT INTO hr_salary_rule (id, code, create_date, write_date, sequence, write_uid, appears_on_payslip, condition_range, amount_fix, create_uid, parent_rule_id, company_id, note, amount_percentage, condition_range_min, condition_select, amount_percentage_base, register_id, amount_select, active, condition_range_max, name, condition_python, amount_python_compute, category_id, quantity, analytic_account_id, account_credit, account_tax_id, account_debit, cod_sunat, is_subtotal) VALUES (67, 'BAS_M', '2018-10-30 16:42:02.861646', '2018-10-30 16:42:02.861646', 4, 1, true, 'contract.wage', NULL, 1, NULL, 1, NULL, NULL, NULL, 'none', NULL, NULL, 'code', true, NULL, 'Basico del mes', '
                    # Available variables:
                    #----------------------
                    # payslip: object containing the payslips
                    # employee: hr.employee object
                    # contract: hr.contract object
                    # rules: object containing the rules code (previously computed)
                    # categories: object containing the computed salary rule categories (sum of amount of all rules belonging to that category).
                    # worked_days: object containing the computed worked days
                    # inputs: object containing the computed inputs

                    # Note: returned value have to be set in the variable ''result''

                    result = rules.NET > categories.NET * 0.10', 'result=BAS-FAL-TAR', 20, '1.0', NULL, NULL, NULL, NULL, NULL, false);
INSERT INTO hr_salary_rule (id, code, create_date, write_date, sequence, write_uid, appears_on_payslip, condition_range, amount_fix, create_uid, parent_rule_id, company_id, note, amount_percentage, condition_range_min, condition_select, amount_percentage_base, register_id, amount_select, active, condition_range_max, name, condition_python, amount_python_compute, category_id, quantity, analytic_account_id, account_credit, account_tax_id, account_debit, cod_sunat, is_subtotal) VALUES (68, 'AF', '2018-10-30 16:42:02.861646', '2018-10-30 16:42:02.861646', 5, 1, true, 'contract.wage', NULL, 1, NULL, 1, NULL, NULL, NULL, 'none', NULL, NULL, 'code', true, NULL, 'Asignación Familiar', '
                    # Available variables:
                    #----------------------
                    # payslip: object containing the payslips
                    # employee: hr.employee object
                    # contract: hr.contract object
                    # rules: object containing the rules code (previously computed)
                    # categories: object containing the computed salary rule categories (sum of amount of all rules belonging to that category).
                    # worked_days: object containing the computed worked days
                    # inputs: object containing the computed inputs

                    # Note: returned value have to be set in the variable ''result''

                    result = rules.NET > categories.NET * 0.10', 'if employee.children>0:
 result = 93
else:
 result=0', 15, '1.0', NULL, NULL, NULL, NULL, NULL, false);
INSERT INTO hr_salary_rule (id, code, create_date, write_date, sequence, write_uid, appears_on_payslip, condition_range, amount_fix, create_uid, parent_rule_id, company_id, note, amount_percentage, condition_range_min, condition_select, amount_percentage_base, register_id, amount_select, active, condition_range_max, name, condition_python, amount_python_compute, category_id, quantity, analytic_account_id, account_credit, account_tax_id, account_debit, cod_sunat, is_subtotal) VALUES (69, 'HE25', '2018-10-30 16:42:02.861646', '2018-10-30 16:42:02.861646', 6, 1, true, 'contract.wage', NULL, 1, NULL, 1, NULL, NULL, NULL, 'none', NULL, NULL, 'code', true, NULL, 'Horas extras 25%', '
                    # Available variables:
                    #----------------------
                    # payslip: object containing the payslips
                    # employee: hr.employee object
                    # contract: hr.contract object
                    # rules: object containing the rules code (previously computed)
                    # categories: object containing the computed salary rule categories (sum of amount of all rules belonging to that category).
                    # worked_days: object containing the computed worked days
                    # inputs: object containing the computed inputs

                    # Note: returned value have to be set in the variable ''result''

                    result = rules.NET > categories.NET * 0.10', 'result = ((contract.wage /30 / 8)*(1+worked_days.HE25.tasa/100))*worked_days.HE25.number_of_hours', 15, '1.0', NULL, NULL, NULL, NULL, NULL, false);
INSERT INTO hr_salary_rule (id, code, create_date, write_date, sequence, write_uid, appears_on_payslip, condition_range, amount_fix, create_uid, parent_rule_id, company_id, note, amount_percentage, condition_range_min, condition_select, amount_percentage_base, register_id, amount_select, active, condition_range_max, name, condition_python, amount_python_compute, category_id, quantity, analytic_account_id, account_credit, account_tax_id, account_debit, cod_sunat, is_subtotal) VALUES (70, 'HE35', '2018-10-30 16:42:02.861646', '2018-10-30 16:42:02.861646', 7, 1, true, 'contract.wage', NULL, 1, NULL, 1, NULL, NULL, NULL, 'none', NULL, NULL, 'code', true, NULL, 'Horas extras de 35%', '
                    # Available variables:
                    #----------------------
                    # payslip: object containing the payslips
                    # employee: hr.employee object
                    # contract: hr.contract object
                    # rules: object containing the rules code (previously computed)
                    # categories: object containing the computed salary rule categories (sum of amount of all rules belonging to that category).
                    # worked_days: object containing the computed worked days
                    # inputs: object containing the computed inputs

                    # Note: returned value have to be set in the variable ''result''

                    result = rules.NET > categories.NET * 0.10', 'result = ((contract.wage /30 / 8)*(1+worked_days.HE35.tasa/100))*worked_days.HE35.number_of_hours', 15, '1.0', NULL, NULL, NULL, NULL, NULL, false);
INSERT INTO hr_salary_rule (id, code, create_date, write_date, sequence, write_uid, appears_on_payslip, condition_range, amount_fix, create_uid, parent_rule_id, company_id, note, amount_percentage, condition_range_min, condition_select, amount_percentage_base, register_id, amount_select, active, condition_range_max, name, condition_python, amount_python_compute, category_id, quantity, analytic_account_id, account_credit, account_tax_id, account_debit, cod_sunat, is_subtotal) VALUES (71, 'HE100', '2018-10-30 16:42:02.861646', '2018-10-30 16:42:02.861646', 8, 1, true, 'contract.wage', NULL, 1, NULL, 1, NULL, NULL, NULL, 'none', NULL, NULL, 'code', true, NULL, 'Horas extras 100%', '
                    # Available variables:
                    #----------------------
                    # payslip: object containing the payslips
                    # employee: hr.employee object
                    # contract: hr.contract object
                    # rules: object containing the rules code (previously computed)
                    # categories: object containing the computed salary rule categories (sum of amount of all rules belonging to that category).
                    # worked_days: object containing the computed worked days
                    # inputs: object containing the computed inputs

                    # Note: returned value have to be set in the variable ''result''

                    result = rules.NET > categories.NET * 0.10', 'result = ((contract.wage /30 / 8)*(1+worked_days.HE100.tasa/100))*worked_days.HE100.number_of_hours', 15, '1.0', NULL, NULL, NULL, NULL, NULL, false);
INSERT INTO hr_salary_rule (id, code, create_date, write_date, sequence, write_uid, appears_on_payslip, condition_range, amount_fix, create_uid, parent_rule_id, company_id, note, amount_percentage, condition_range_min, condition_select, amount_percentage_base, register_id, amount_select, active, condition_range_max, name, condition_python, amount_python_compute, category_id, quantity, analytic_account_id, account_credit, account_tax_id, account_debit, cod_sunat, is_subtotal) VALUES (72, 'BONR', '2018-10-30 16:42:02.861646', '2018-10-30 16:42:02.861646', 9, 1, true, 'contract.wage', NULL, 1, NULL, 1, NULL, NULL, NULL, 'none', NULL, NULL, 'code', true, NULL, 'Bonificacion', '
                    # Available variables:
                    #----------------------
                    # payslip: object containing the payslips
                    # employee: hr.employee object
                    # contract: hr.contract object
                    # rules: object containing the rules code (previously computed)
                    # categories: object containing the computed salary rule categories (sum of amount of all rules belonging to that category).
                    # worked_days: object containing the computed worked days
                    # inputs: object containing the computed inputs

                    # Note: returned value have to be set in the variable ''result''

                    result = rules.NET > categories.NET * 0.10', 'result = inputs.BONRER.amount', 15, '1.0', NULL, NULL, NULL, NULL, NULL, false);
INSERT INTO hr_salary_rule (id, code, create_date, write_date, sequence, write_uid, appears_on_payslip, condition_range, amount_fix, create_uid, parent_rule_id, company_id, note, amount_percentage, condition_range_min, condition_select, amount_percentage_base, register_id, amount_select, active, condition_range_max, name, condition_python, amount_python_compute, category_id, quantity, analytic_account_id, account_credit, account_tax_id, account_debit, cod_sunat, is_subtotal) VALUES (73, 'COMI', '2018-10-30 16:42:02.861646', '2018-10-30 16:42:02.861646', 10, 1, true, 'contract.wage', NULL, 1, NULL, 1, NULL, NULL, NULL, 'none', NULL, NULL, 'code', true, NULL, 'COMISIONES', '
                    # Available variables:
                    #----------------------
                    # payslip: object containing the payslips
                    # employee: hr.employee object
                    # contract: hr.contract object
                    # rules: object containing the rules code (previously computed)
                    # categories: object containing the computed salary rule categories (sum of amount of all rules belonging to that category).
                    # worked_days: object containing the computed worked days
                    # inputs: object containing the computed inputs

                    # Note: returned value have to be set in the variable ''result''

                    result = rules.NET > categories.NET * 0.10', 'result = inputs.COMI.amount', 15, '1.0', NULL, NULL, NULL, NULL, NULL, false);
INSERT INTO hr_salary_rule (id, code, create_date, write_date, sequence, write_uid, appears_on_payslip, condition_range, amount_fix, create_uid, parent_rule_id, company_id, note, amount_percentage, condition_range_min, condition_select, amount_percentage_base, register_id, amount_select, active, condition_range_max, name, condition_python, amount_python_compute, category_id, quantity, analytic_account_id, account_credit, account_tax_id, account_debit, cod_sunat, is_subtotal) VALUES (74, 'SMAR', '2018-10-30 16:42:02.861646', '2018-10-30 16:42:02.861646', 11, 1, true, 'contract.wage', NULL, 1, NULL, 1, NULL, NULL, NULL, 'none', NULL, NULL, 'code', true, NULL, 'Subsidio Maternidad', '
                    # Available variables:
                    #----------------------
                    # payslip: object containing the payslips
                    # employee: hr.employee object
                    # contract: hr.contract object
                    # rules: object containing the rules code (previously computed)
                    # categories: object containing the computed salary rule categories (sum of amount of all rules belonging to that category).
                    # worked_days: object containing the computed worked days
                    # inputs: object containing the computed inputs

                    # Note: returned value have to be set in the variable ''result''

                    result = rules.NET > categories.NET * 0.10', 'result=worked_days.DSUBM.number_of_days*(contract.wage/30)
', 15, '1.0', NULL, NULL, NULL, NULL, NULL, false);
INSERT INTO hr_salary_rule (id, code, create_date, write_date, sequence, write_uid, appears_on_payslip, condition_range, amount_fix, create_uid, parent_rule_id, company_id, note, amount_percentage, condition_range_min, condition_select, amount_percentage_base, register_id, amount_select, active, condition_range_max, name, condition_python, amount_python_compute, category_id, quantity, analytic_account_id, account_credit, account_tax_id, account_debit, cod_sunat, is_subtotal) VALUES (75, 'SUBE', '2018-10-30 16:42:02.861646', '2018-10-30 16:42:02.861646', 12, 1, true, 'contract.wage', NULL, 1, NULL, 1, NULL, NULL, NULL, 'none', NULL, NULL, 'code', true, NULL, 'Subsidio por enfermedad', '
                    # Available variables:
                    #----------------------
                    # payslip: object containing the payslips
                    # employee: hr.employee object
                    # contract: hr.contract object
                    # rules: object containing the rules code (previously computed)
                    # categories: object containing the computed salary rule categories (sum of amount of all rules belonging to that category).
                    # worked_days: object containing the computed worked days
                    # inputs: object containing the computed inputs

                    # Note: returned value have to be set in the variable ''result''

                    result = rules.NET > categories.NET * 0.10', 'result=worked_days.DSUBE.number_of_days*(contract.wage/30)', 15, '1.0', NULL, NULL, NULL, NULL, NULL, false);
INSERT INTO hr_salary_rule (id, code, create_date, write_date, sequence, write_uid, appears_on_payslip, condition_range, amount_fix, create_uid, parent_rule_id, company_id, note, amount_percentage, condition_range_min, condition_select, amount_percentage_base, register_id, amount_select, active, condition_range_max, name, condition_python, amount_python_compute, category_id, quantity, analytic_account_id, account_credit, account_tax_id, account_debit, cod_sunat, is_subtotal) VALUES (76, 'VAC', '2018-10-30 16:42:02.861646', '2018-10-30 16:42:02.861646', 13, 1, true, 'contract.wage', NULL, 1, NULL, 1, NULL, NULL, NULL, 'none', NULL, NULL, 'code', true, NULL, 'Vacaciones', '
                    # Available variables:
                    #----------------------
                    # payslip: object containing the payslips
                    # employee: hr.employee object
                    # contract: hr.contract object
                    # rules: object containing the rules code (previously computed)
                    # categories: object containing the computed salary rule categories (sum of amount of all rules belonging to that category).
                    # worked_days: object containing the computed worked days
                    # inputs: object containing the computed inputs

                    # Note: returned value have to be set in the variable ''result''

                    result = rules.NET > categories.NET * 0.10', 'result = inputs.VAC.amount', 15, '1.0', NULL, NULL, NULL, NULL, NULL, false);
INSERT INTO hr_salary_rule (id, code, create_date, write_date, sequence, write_uid, appears_on_payslip, condition_range, amount_fix, create_uid, parent_rule_id, company_id, note, amount_percentage, condition_range_min, condition_select, amount_percentage_base, register_id, amount_select, active, condition_range_max, name, condition_python, amount_python_compute, category_id, quantity, analytic_account_id, account_credit, account_tax_id, account_debit, cod_sunat, is_subtotal) VALUES (77, 'VATRU', '2018-10-30 16:42:02.861646', '2018-10-30 16:42:02.861646', 14, 1, true, 'contract.wage', NULL, 1, NULL, 1, NULL, NULL, NULL, 'none', NULL, NULL, 'code', true, NULL, 'Vacaciones Truncas', '
                    # Available variables:
                    #----------------------
                    # payslip: object containing the payslips
                    # employee: hr.employee object
                    # contract: hr.contract object
                    # rules: object containing the rules code (previously computed)
                    # categories: object containing the computed salary rule categories (sum of amount of all rules belonging to that category).
                    # worked_days: object containing the computed worked days
                    # inputs: object containing the computed inputs

                    # Note: returned value have to be set in the variable ''result''

                    result = rules.NET > categories.NET * 0.10', 'result = inputs.VAC_TRU.amount', 15, '1.0', NULL, NULL, NULL, NULL, NULL, false);
INSERT INTO hr_salary_rule (id, code, create_date, write_date, sequence, write_uid, appears_on_payslip, condition_range, amount_fix, create_uid, parent_rule_id, company_id, note, amount_percentage, condition_range_min, condition_select, amount_percentage_base, register_id, amount_select, active, condition_range_max, name, condition_python, amount_python_compute, category_id, quantity, analytic_account_id, account_credit, account_tax_id, account_debit, cod_sunat, is_subtotal) VALUES (78, 'GRA', '2018-10-30 16:42:02.861646', '2018-10-30 16:42:02.861646', 15, 1, true, 'contract.wage', NULL, 1, NULL, 1, NULL, NULL, NULL, 'none', NULL, NULL, 'code', true, NULL, 'Gratificaciones de fiestas patrias y navidad', '
                    # Available variables:
                    #----------------------
                    # payslip: object containing the payslips
                    # employee: hr.employee object
                    # contract: hr.contract object
                    # rules: object containing the rules code (previously computed)
                    # categories: object containing the computed salary rule categories (sum of amount of all rules belonging to that category).
                    # worked_days: object containing the computed worked days
                    # inputs: object containing the computed inputs

                    # Note: returned value have to be set in the variable ''result''

                    result = rules.NET > categories.NET * 0.10', 'result = inputs.GRA.amount', 15, '1.0', NULL, NULL, NULL, NULL, NULL, false);
INSERT INTO hr_salary_rule (id, code, create_date, write_date, sequence, write_uid, appears_on_payslip, condition_range, amount_fix, create_uid, parent_rule_id, company_id, note, amount_percentage, condition_range_min, condition_select, amount_percentage_base, register_id, amount_select, active, condition_range_max, name, condition_python, amount_python_compute, category_id, quantity, analytic_account_id, account_credit, account_tax_id, account_debit, cod_sunat, is_subtotal) VALUES (79, 'BON9', '2018-10-30 16:42:02.861646', '2018-10-30 16:42:02.861646', 16, 1, true, 'contract.wage', NULL, 1, NULL, 1, NULL, NULL, NULL, 'none', NULL, NULL, 'code', true, NULL, 'Bonificacion 9%', '
                    # Available variables:
                    #----------------------
                    # payslip: object containing the payslips
                    # employee: hr.employee object
                    # contract: hr.contract object
                    # rules: object containing the rules code (previously computed)
                    # categories: object containing the computed salary rule categories (sum of amount of all rules belonging to that category).
                    # worked_days: object containing the computed worked days
                    # inputs: object containing the computed inputs

                    # Note: returned value have to be set in the variable ''result''

                    result = rules.NET > categories.NET * 0.10', 'result = inputs.BON9.amount', 15, '1.0', NULL, NULL, NULL, NULL, NULL, false);
INSERT INTO hr_salary_rule (id, code, create_date, write_date, sequence, write_uid, appears_on_payslip, condition_range, amount_fix, create_uid, parent_rule_id, company_id, note, amount_percentage, condition_range_min, condition_select, amount_percentage_base, register_id, amount_select, active, condition_range_max, name, condition_python, amount_python_compute, category_id, quantity, analytic_account_id, account_credit, account_tax_id, account_debit, cod_sunat, is_subtotal) VALUES (80, 'GRA_TRU', '2018-10-30 16:42:02.861646', '2018-10-30 16:42:02.861646', 17, 1, true, 'contract.wage', NULL, 1, NULL, 1, NULL, NULL, NULL, 'none', NULL, NULL, 'code', true, NULL, 'Gratificación Trunca ', '
                    # Available variables:
                    #----------------------
                    # payslip: object containing the payslips
                    # employee: hr.employee object
                    # contract: hr.contract object
                    # rules: object containing the rules code (previously computed)
                    # categories: object containing the computed salary rule categories (sum of amount of all rules belonging to that category).
                    # worked_days: object containing the computed worked days
                    # inputs: object containing the computed inputs

                    # Note: returned value have to be set in the variable ''result''

                    result = rules.NET > categories.NET * 0.10', 'result = inputs.GRA_TRU.amount', 15, '1.0', NULL, NULL, NULL, NULL, NULL, false);
INSERT INTO hr_salary_rule (id, code, create_date, write_date, sequence, write_uid, appears_on_payslip, condition_range, amount_fix, create_uid, parent_rule_id, company_id, note, amount_percentage, condition_range_min, condition_select, amount_percentage_base, register_id, amount_select, active, condition_range_max, name, condition_python, amount_python_compute, category_id, quantity, analytic_account_id, account_credit, account_tax_id, account_debit, cod_sunat, is_subtotal) VALUES (81, 'BON9_TRU', '2018-10-30 16:42:02.861646', '2018-10-30 16:42:02.861646', 18, 1, true, 'contract.wage', NULL, 1, NULL, 1, NULL, NULL, NULL, 'none', NULL, NULL, 'code', true, NULL, 'BONIFICACION 9% TRUNCA ', '
                    # Available variables:
                    #----------------------
                    # payslip: object containing the payslips
                    # employee: hr.employee object
                    # contract: hr.contract object
                    # rules: object containing the rules code (previously computed)
                    # categories: object containing the computed salary rule categories (sum of amount of all rules belonging to that category).
                    # worked_days: object containing the computed worked days
                    # inputs: object containing the computed inputs

                    # Note: returned value have to be set in the variable ''result''

                    result = rules.NET > categories.NET * 0.10', 'result = inputs.BON9_TRU.amount', 15, '1.0', NULL, NULL, NULL, NULL, NULL, false);
INSERT INTO hr_salary_rule (id, code, create_date, write_date, sequence, write_uid, appears_on_payslip, condition_range, amount_fix, create_uid, parent_rule_id, company_id, note, amount_percentage, condition_range_min, condition_select, amount_percentage_base, register_id, amount_select, active, condition_range_max, name, condition_python, amount_python_compute, category_id, quantity, analytic_account_id, account_credit, account_tax_id, account_debit, cod_sunat, is_subtotal) VALUES (82, 'CTS', '2018-10-30 16:42:02.861646', '2018-10-30 16:42:02.861646', 19, 1, true, 'contract.wage', NULL, 1, NULL, 1, NULL, NULL, NULL, 'none', NULL, NULL, 'code', true, NULL, 'Compensación por tiempo de servicios', '
                    # Available variables:
                    #----------------------
                    # payslip: object containing the payslips
                    # employee: hr.employee object
                    # contract: hr.contract object
                    # rules: object containing the rules code (previously computed)
                    # categories: object containing the computed salary rule categories (sum of amount of all rules belonging to that category).
                    # worked_days: object containing the computed worked days
                    # inputs: object containing the computed inputs

                    # Note: returned value have to be set in the variable ''result''

                    result = rules.NET > categories.NET * 0.10', 'result = inputs.CTS.amount', 15, '1.0', NULL, NULL, NULL, NULL, NULL, false);
INSERT INTO hr_salary_rule (id, code, create_date, write_date, sequence, write_uid, appears_on_payslip, condition_range, amount_fix, create_uid, parent_rule_id, company_id, note, amount_percentage, condition_range_min, condition_select, amount_percentage_base, register_id, amount_select, active, condition_range_max, name, condition_python, amount_python_compute, category_id, quantity, analytic_account_id, account_credit, account_tax_id, account_debit, cod_sunat, is_subtotal) VALUES (83, 'CTS_TRU', '2018-10-30 16:42:02.861646', '2018-10-30 16:42:02.861646', 20, 1, true, 'contract.wage', NULL, 1, NULL, 1, NULL, NULL, NULL, 'none', NULL, NULL, 'code', true, NULL, 'CTS Trunca', '
                    # Available variables:
                    #----------------------
                    # payslip: object containing the payslips
                    # employee: hr.employee object
                    # contract: hr.contract object
                    # rules: object containing the rules code (previously computed)
                    # categories: object containing the computed salary rule categories (sum of amount of all rules belonging to that category).
                    # worked_days: object containing the computed worked days
                    # inputs: object containing the computed inputs

                    # Note: returned value have to be set in the variable ''result''

                    result = rules.NET > categories.NET * 0.10', 'result = inputs.CTS_TRU.amount', 15, '1.0', NULL, NULL, NULL, NULL, NULL, false);
INSERT INTO hr_salary_rule (id, code, create_date, write_date, sequence, write_uid, appears_on_payslip, condition_range, amount_fix, create_uid, parent_rule_id, company_id, note, amount_percentage, condition_range_min, condition_select, amount_percentage_base, register_id, amount_select, active, condition_range_max, name, condition_python, amount_python_compute, category_id, quantity, analytic_account_id, account_credit, account_tax_id, account_debit, cod_sunat, is_subtotal) VALUES (84, 'TINGR', '2018-10-30 16:42:02.861646', '2018-10-30 16:42:02.861646', 21, 1, true, 'contract.wage', NULL, 1, NULL, 1, NULL, NULL, NULL, 'none', NULL, NULL, 'code', true, NULL, 'Total Ingresos ', '
                    # Available variables:
                    #----------------------
                    # payslip: object containing the payslips
                    # employee: hr.employee object
                    # contract: hr.contract object
                    # rules: object containing the rules code (previously computed)
                    # categories: object containing the computed salary rule categories (sum of amount of all rules belonging to that category).
                    # worked_days: object containing the computed worked days
                    # inputs: object containing the computed inputs

                    # Note: returned value have to be set in the variable ''result''

                    result = rules.NET > categories.NET * 0.10', 'result = BAS_M+AF+HE25+HE35+HE100+BONR+COMI+SMAR+SUBE+VAC+VATRU+GRA+BON9+GRA_TRU+BON9_TRU+CTS+CTS_TRU', 20, '1.0', NULL, NULL, NULL, NULL, NULL, false);
INSERT INTO hr_salary_rule (id, code, create_date, write_date, sequence, write_uid, appears_on_payslip, condition_range, amount_fix, create_uid, parent_rule_id, company_id, note, amount_percentage, condition_range_min, condition_select, amount_percentage_base, register_id, amount_select, active, condition_range_max, name, condition_python, amount_python_compute, category_id, quantity, analytic_account_id, account_credit, account_tax_id, account_debit, cod_sunat, is_subtotal) VALUES (85, 'AONP', '2018-10-30 16:42:02.861646', '2018-10-30 16:42:02.861646', 22, 1, true, 'contract.wage', NULL, 1, NULL, 1, NULL, NULL, NULL, 'none', NULL, NULL, 'code', true, NULL, 'Ingresos Afectos ONP', '
                    # Available variables:
                    #----------------------
                    # payslip: object containing the payslips
                    # employee: hr.employee object
                    # contract: hr.contract object
                    # rules: object containing the rules code (previously computed)
                    # categories: object containing the computed salary rule categories (sum of amount of all rules belonging to that category).
                    # worked_days: object containing the computed worked days
                    # inputs: object containing the computed inputs

                    # Note: returned value have to be set in the variable ''result''

                    result = rules.NET > categories.NET * 0.10', 'result = BAS_M+AF+HE25+HE35+HE100+BONR+COMI+VAC+VATRU', 20, '1.0', NULL, NULL, NULL, NULL, NULL, false);
INSERT INTO hr_salary_rule (id, code, create_date, write_date, sequence, write_uid, appears_on_payslip, condition_range, amount_fix, create_uid, parent_rule_id, company_id, note, amount_percentage, condition_range_min, condition_select, amount_percentage_base, register_id, amount_select, active, condition_range_max, name, condition_python, amount_python_compute, category_id, quantity, analytic_account_id, account_credit, account_tax_id, account_debit, cod_sunat, is_subtotal) VALUES (86, 'AAFP', '2018-10-30 16:42:02.861646', '2018-10-30 16:42:02.861646', 23, 1, true, 'contract.wage', NULL, 1, NULL, 1, NULL, NULL, NULL, 'none', NULL, NULL, 'code', true, NULL, 'Ingresos Afectos AFP', '
                    # Available variables:
                    #----------------------
                    # payslip: object containing the payslips
                    # employee: hr.employee object
                    # contract: hr.contract object
                    # rules: object containing the rules code (previously computed)
                    # categories: object containing the computed salary rule categories (sum of amount of all rules belonging to that category).
                    # worked_days: object containing the computed worked days
                    # inputs: object containing the computed inputs

                    # Note: returned value have to be set in the variable ''result''

                    result = rules.NET > categories.NET * 0.10', 'result = BAS_M+AF+HE25+HE35+HE100+BONR+COMI+SMAR+SUBE+VAC+VATRU', 20, '1.0', NULL, NULL, NULL, NULL, NULL, false);
INSERT INTO hr_salary_rule (id, code, create_date, write_date, sequence, write_uid, appears_on_payslip, condition_range, amount_fix, create_uid, parent_rule_id, company_id, note, amount_percentage, condition_range_min, condition_select, amount_percentage_base, register_id, amount_select, active, condition_range_max, name, condition_python, amount_python_compute, category_id, quantity, analytic_account_id, account_credit, account_tax_id, account_debit, cod_sunat, is_subtotal) VALUES (87, 'ONP', '2018-10-30 16:42:02.861646', '2018-10-30 16:42:02.861646', 24, 1, true, 'contract.wage', NULL, 1, NULL, 1, NULL, NULL, NULL, 'none', NULL, NULL, 'code', true, NULL, 'ONP', '
                    # Available variables:
                    #----------------------
                    # payslip: object containing the payslips
                    # employee: hr.employee object
                    # contract: hr.contract object
                    # rules: object containing the rules code (previously computed)
                    # categories: object containing the computed salary rule categories (sum of amount of all rules belonging to that category).
                    # worked_days: object containing the computed worked days
                    # inputs: object containing the computed inputs

                    # Note: returned value have to be set in the variable ''result''

                    result = rules.NET > categories.NET * 0.10', 'if contract.afiliacion_id.entidad==''ONP'':
 result=round((contract.afiliacion_id.fondo_jib/100)*AONP,2)
else:
 result=0', 16, '1.0', NULL, NULL, NULL, NULL, NULL, false);
INSERT INTO hr_salary_rule (id, code, create_date, write_date, sequence, write_uid, appears_on_payslip, condition_range, amount_fix, create_uid, parent_rule_id, company_id, note, amount_percentage, condition_range_min, condition_select, amount_percentage_base, register_id, amount_select, active, condition_range_max, name, condition_python, amount_python_compute, category_id, quantity, analytic_account_id, account_credit, account_tax_id, account_debit, cod_sunat, is_subtotal) VALUES (88, 'A_JUB', '2018-10-30 16:42:02.861646', '2018-10-30 16:42:02.861646', 25, 1, true, 'contract.wage', NULL, 1, NULL, 1, NULL, NULL, NULL, 'none', NULL, NULL, 'code', true, NULL, 'Aporte jubilacion AFP', '
                    # Available variables:
                    #----------------------
                    # payslip: object containing the payslips
                    # employee: hr.employee object
                    # contract: hr.contract object
                    # rules: object containing the rules code (previously computed)
                    # categories: object containing the computed salary rule categories (sum of amount of all rules belonging to that category).
                    # worked_days: object containing the computed worked days
                    # inputs: object containing the computed inputs

                    # Note: returned value have to be set in the variable ''result''

                    result = rules.NET > categories.NET * 0.10', 'if contract.afiliacion_id.entidad==''ONP'':
 result=0
if contract.afiliacion_id.entidad==''HABITAT'':
 result=round((contract.afiliacion_id.fondo_jib/100)*AAFP,2)
if contract.afiliacion_id.entidad==''INTEGRA'':
 result=round((contract.afiliacion_id.fondo_jib/100)*AAFP,2)
if contract.afiliacion_id.entidad==''PRIMA'':
 result=round((contract.afiliacion_id.fondo_jib/100)*AAFP,2)
if contract.afiliacion_id.entidad==''PROFUTURO'':
 result=round((contract.afiliacion_id.fondo_jib/100)*AAFP,2)
if contract.afiliacion_id.entidad==''SIN REGIMEN'':
 result=0
', 16, '1.0', NULL, NULL, NULL, NULL, NULL, false);
INSERT INTO hr_salary_rule (id, code, create_date, write_date, sequence, write_uid, appears_on_payslip, condition_range, amount_fix, create_uid, parent_rule_id, company_id, note, amount_percentage, condition_range_min, condition_select, amount_percentage_base, register_id, amount_select, active, condition_range_max, name, condition_python, amount_python_compute, category_id, quantity, analytic_account_id, account_credit, account_tax_id, account_debit, cod_sunat, is_subtotal) VALUES (89, 'COMFI', '2018-10-30 16:42:02.861646', '2018-10-30 16:42:02.861646', 26, 1, true, 'contract.wage', NULL, 1, NULL, 1, NULL, NULL, NULL, 'none', NULL, NULL, 'code', true, NULL, 'Comisión Fija', '
                    # Available variables:
                    #----------------------
                    # payslip: object containing the payslips
                    # employee: hr.employee object
                    # contract: hr.contract object
                    # rules: object containing the rules code (previously computed)
                    # categories: object containing the computed salary rule categories (sum of amount of all rules belonging to that category).
                    # worked_days: object containing the computed worked days
                    # inputs: object containing the computed inputs

                    # Note: returned value have to be set in the variable ''result''

                    result = rules.NET > categories.NET * 0.10', 'if contract.tipo_comision==1:
 if contract.afiliacion_id.entidad==''ONP'':
  result=0
 if contract.afiliacion_id.entidad==''HABITAT'':
  result=round((contract.afiliacion_id.com_fija/100)*AAFP,2)
 if contract.afiliacion_id.entidad==''INTEGRA'':
  result=round((contract.afiliacion_id.com_fija/100)*AAFP,2)
 if contract.afiliacion_id.entidad==''PRIMA'':
  result=round((contract.afiliacion_id.com_fija/100)*AAFP,2)
 if contract.afiliacion_id.entidad==''PROFUTURO'':
  result=round((contract.afiliacion_id.com_fija/100)*AAFP,2)
 if contract.afiliacion_id.entidad==''SIN REGIMEN'':
  result=0
else:
 result=0
', 16, '1.0', NULL, NULL, NULL, NULL, NULL, false);
INSERT INTO hr_salary_rule (id, code, create_date, write_date, sequence, write_uid, appears_on_payslip, condition_range, amount_fix, create_uid, parent_rule_id, company_id, note, amount_percentage, condition_range_min, condition_select, amount_percentage_base, register_id, amount_select, active, condition_range_max, name, condition_python, amount_python_compute, category_id, quantity, analytic_account_id, account_credit, account_tax_id, account_debit, cod_sunat, is_subtotal) VALUES (90, 'COMMIX', '2018-10-30 16:42:02.861646', '2018-10-30 16:42:02.861646', 27, 1, true, 'contract.wage', NULL, 1, NULL, 1, NULL, NULL, NULL, 'none', NULL, NULL, 'code', true, NULL, 'Comisión Mixta', '
                    # Available variables:
                    #----------------------
                    # payslip: object containing the payslips
                    # employee: hr.employee object
                    # contract: hr.contract object
                    # rules: object containing the rules code (previously computed)
                    # categories: object containing the computed salary rule categories (sum of amount of all rules belonging to that category).
                    # worked_days: object containing the computed worked days
                    # inputs: object containing the computed inputs

                    # Note: returned value have to be set in the variable ''result''

                    result = rules.NET > categories.NET * 0.10', 'if contract.tipo_comision==2:
 result=95
else:
 result=0', 16, '1.0', NULL, NULL, NULL, NULL, NULL, false);
INSERT INTO hr_salary_rule (id, code, create_date, write_date, sequence, write_uid, appears_on_payslip, condition_range, amount_fix, create_uid, parent_rule_id, company_id, note, amount_percentage, condition_range_min, condition_select, amount_percentage_base, register_id, amount_select, active, condition_range_max, name, condition_python, amount_python_compute, category_id, quantity, analytic_account_id, account_credit, account_tax_id, account_debit, cod_sunat, is_subtotal) VALUES (91, 'SEGI', '2018-10-30 16:42:02.861646', '2018-10-30 16:42:02.861646', 28, 1, true, 'contract.wage', NULL, 1, NULL, 1, NULL, NULL, NULL, 'none', NULL, NULL, 'code', true, NULL, 'Seguro de Invalidez', '
                    # Available variables:
                    #----------------------
                    # payslip: object containing the payslips
                    # employee: hr.employee object
                    # contract: hr.contract object
                    # rules: object containing the rules code (previously computed)
                    # categories: object containing the computed salary rule categories (sum of amount of all rules belonging to that category).
                    # worked_days: object containing the computed worked days
                    # inputs: object containing the computed inputs

                    # Note: returned value have to be set in the variable ''result''

                    result = rules.NET > categories.NET * 0.10', 'if contract.afiliacion_id.entidad==''ONP'':
 result=0
if contract.afiliacion_id.entidad==''HABITAT'':
 result=round((contract.afiliacion_id.prima_s/100)*AAFP,2)
if contract.afiliacion_id.entidad==''INTEGRA'':
 result=round((contract.afiliacion_id.prima_s/100)*AAFP,2)
if contract.afiliacion_id.entidad==''PRIMA'':
 result=round((contract.afiliacion_id.prima_s/100)*AAFP,2)
if contract.afiliacion_id.entidad==''PROFUTURO'':
 result=round((contract.afiliacion_id.prima_s/100)*AAFP,2)
if contract.afiliacion_id.entidad==''SIN REGIMEN'':
 result=0
', 16, '1.0', NULL, NULL, NULL, NULL, NULL, false);
INSERT INTO hr_salary_rule (id, code, create_date, write_date, sequence, write_uid, appears_on_payslip, condition_range, amount_fix, create_uid, parent_rule_id, company_id, note, amount_percentage, condition_range_min, condition_select, amount_percentage_base, register_id, amount_select, active, condition_range_max, name, condition_python, amount_python_compute, category_id, quantity, analytic_account_id, account_credit, account_tax_id, account_debit, cod_sunat, is_subtotal) VALUES (92, 'QUINTA', '2018-10-30 16:42:02.861646', '2018-10-30 16:42:02.861646', 29, 1, true, 'contract.wage', NULL, 1, NULL, 1, NULL, NULL, NULL, 'none', NULL, NULL, 'code', true, NULL, 'Quinta Categoría', '
                    # Available variables:
                    #----------------------
                    # payslip: object containing the payslips
                    # employee: hr.employee object
                    # contract: hr.contract object
                    # rules: object containing the rules code (previously computed)
                    # categories: object containing the computed salary rule categories (sum of amount of all rules belonging to that category).
                    # worked_days: object containing the computed worked days
                    # inputs: object containing the computed inputs

                    # Note: returned value have to be set in the variable ''result''

                    result = rules.NET > categories.NET * 0.10', 'result = inputs.QUINTA.amount', 16, '1.0', NULL, NULL, NULL, NULL, NULL, false);
INSERT INTO hr_salary_rule (id, code, create_date, write_date, sequence, write_uid, appears_on_payslip, condition_range, amount_fix, create_uid, parent_rule_id, company_id, note, amount_percentage, condition_range_min, condition_select, amount_percentage_base, register_id, amount_select, active, condition_range_max, name, condition_python, amount_python_compute, category_id, quantity, analytic_account_id, account_credit, account_tax_id, account_debit, cod_sunat, is_subtotal) VALUES (93, 'TDES', '2018-10-30 16:42:02.861646', '2018-10-30 16:42:02.861646', 30, 1, true, 'contract.wage', NULL, 1, NULL, 1, NULL, NULL, NULL, 'none', NULL, NULL, 'code', true, NULL, 'Total descuentos', '
                    # Available variables:
                    #----------------------
                    # payslip: object containing the payslips
                    # employee: hr.employee object
                    # contract: hr.contract object
                    # rules: object containing the rules code (previously computed)
                    # categories: object containing the computed salary rule categories (sum of amount of all rules belonging to that category).
                    # worked_days: object containing the computed worked days
                    # inputs: object containing the computed inputs

                    # Note: returned value have to be set in the variable ''result''

                    result = rules.NET > categories.NET * 0.10', 'result = ONP+A_JUB+COMFI+COMMIX+SEGI+QUINTA', 20, '1.0', NULL, NULL, NULL, NULL, NULL, false);
INSERT INTO hr_salary_rule (id, code, create_date, write_date, sequence, write_uid, appears_on_payslip, condition_range, amount_fix, create_uid, parent_rule_id, company_id, note, amount_percentage, condition_range_min, condition_select, amount_percentage_base, register_id, amount_select, active, condition_range_max, name, condition_python, amount_python_compute, category_id, quantity, analytic_account_id, account_credit, account_tax_id, account_debit, cod_sunat, is_subtotal) VALUES (94, 'NET', '2018-10-30 16:42:02.861646', '2018-10-30 16:42:02.861646', 31, 1, true, 'contract.wage', NULL, 1, NULL, 1, NULL, NULL, NULL, 'none', NULL, NULL, 'code', true, NULL, 'Neto a pagar ', '
                    # Available variables:
                    #----------------------
                    # payslip: object containing the payslips
                    # employee: hr.employee object
                    # contract: hr.contract object
                    # rules: object containing the rules code (previously computed)
                    # categories: object containing the computed salary rule categories (sum of amount of all rules belonging to that category).
                    # worked_days: object containing the computed worked days
                    # inputs: object containing the computed inputs

                    # Note: returned value have to be set in the variable ''result''

                    result = rules.NET > categories.NET * 0.10', 'result= TINGR-TDES', 20, '1.0', NULL, NULL, NULL, NULL, NULL, false);
INSERT INTO hr_salary_rule (id, code, create_date, write_date, sequence, write_uid, appears_on_payslip, condition_range, amount_fix, create_uid, parent_rule_id, company_id, note, amount_percentage, condition_range_min, condition_select, amount_percentage_base, register_id, amount_select, active, condition_range_max, name, condition_python, amount_python_compute, category_id, quantity, analytic_account_id, account_credit, account_tax_id, account_debit, cod_sunat, is_subtotal) VALUES (95, 'AESSALUD', '2018-10-30 16:42:02.861646', '2018-10-30 16:42:02.861646', 32, 1, true, 'contract.wage', NULL, 1, NULL, 1, NULL, NULL, NULL, 'none', NULL, NULL, 'code', true, NULL, 'Afectos Essalud', '
                    # Available variables:
                    #----------------------
                    # payslip: object containing the payslips
                    # employee: hr.employee object
                    # contract: hr.contract object
                    # rules: object containing the rules code (previously computed)
                    # categories: object containing the computed salary rule categories (sum of amount of all rules belonging to that category).
                    # worked_days: object containing the computed worked days
                    # inputs: object containing the computed inputs

                    # Note: returned value have to be set in the variable ''result''

                    result = rules.NET > categories.NET * 0.10', 'result = BAS_M+AF+HE25+HE35+HE100+BONR+COMI+VAC+VATRU', 20, '1.0', NULL, NULL, NULL, NULL, NULL, false);
INSERT INTO hr_salary_rule (id, code, create_date, write_date, sequence, write_uid, appears_on_payslip, condition_range, amount_fix, create_uid, parent_rule_id, company_id, note, amount_percentage, condition_range_min, condition_select, amount_percentage_base, register_id, amount_select, active, condition_range_max, name, condition_python, amount_python_compute, category_id, quantity, analytic_account_id, account_credit, account_tax_id, account_debit, cod_sunat, is_subtotal) VALUES (96, 'ESSALUD', '2018-10-30 16:42:02.861646', '2018-10-30 16:42:02.861646', 33, 1, true, 'contract.wage', NULL, 1, NULL, 1, NULL, NULL, NULL, 'none', NULL, NULL, 'code', true, NULL, 'Aportes ESSALUD', '
                    # Available variables:
                    #----------------------
                    # payslip: object containing the payslips
                    # employee: hr.employee object
                    # contract: hr.contract object
                    # rules: object containing the rules code (previously computed)
                    # categories: object containing the computed salary rule categories (sum of amount of all rules belonging to that category).
                    # worked_days: object containing the computed worked days
                    # inputs: object containing the computed inputs

                    # Note: returned value have to be set in the variable ''result''

                    result = rules.NET > categories.NET * 0.10', 'if AESSALUD>930:
 result=AESSALUD*0.09
else:
 result=930*0.09
', 21, '1.0', NULL, NULL, NULL, NULL, NULL, false);
INSERT INTO hr_salary_rule (id, code, create_date, write_date, sequence, write_uid, appears_on_payslip, condition_range, amount_fix, create_uid, parent_rule_id, company_id, note, amount_percentage, condition_range_min, condition_select, amount_percentage_base, register_id, amount_select, active, condition_range_max, name, condition_python, amount_python_compute, category_id, quantity, analytic_account_id, account_credit, account_tax_id, account_debit, cod_sunat, is_subtotal) VALUES (97, 'REMAFE', '2018-10-30 16:42:02.861646', '2018-10-30 16:42:02.861646', 34, 1, true, 'contract.wage', NULL, 1, NULL, 1, NULL, NULL, NULL, 'none', NULL, NULL, 'code', true, NULL, 'Remuneraciones Afectas', '
                    # Available variables:
                    #----------------------
                    # payslip: object containing the payslips
                    # employee: hr.employee object
                    # contract: hr.contract object
                    # rules: object containing the rules code (previously computed)
                    # categories: object containing the computed salary rule categories (sum of amount of all rules belonging to that category).
                    # worked_days: object containing the computed worked days
                    # inputs: object containing the computed inputs

                    # Note: returned value have to be set in the variable ''result''

                    result = rules.NET > categories.NET * 0.10', 'result = (BAS_M+AF+HE25+HE35+HE100+BONR+COMI+SMAR+SUBE)/(BAS_M+AF+HE25+HE35+HE100+BONR+COMI+SMAR+SUBE+VAC+VATRU)', 20, '1.0', NULL, NULL, NULL, NULL, NULL, false);
INSERT INTO hr_salary_rule (id, code, create_date, write_date, sequence, write_uid, appears_on_payslip, condition_range, amount_fix, create_uid, parent_rule_id, company_id, note, amount_percentage, condition_range_min, condition_select, amount_percentage_base, register_id, amount_select, active, condition_range_max, name, condition_python, amount_python_compute, category_id, quantity, analytic_account_id, account_credit, account_tax_id, account_debit, cod_sunat, is_subtotal) VALUES (98, 'VACAFE', '2018-10-30 16:42:02.861646', '2018-10-30 16:42:02.861646', 35, 1, true, 'contract.wage', NULL, 1, NULL, 1, NULL, NULL, NULL, 'none', NULL, NULL, 'code', true, NULL, 'Vacaciones afectas', '
                    # Available variables:
                    #----------------------
                    # payslip: object containing the payslips
                    # employee: hr.employee object
                    # contract: hr.contract object
                    # rules: object containing the rules code (previously computed)
                    # categories: object containing the computed salary rule categories (sum of amount of all rules belonging to that category).
                    # worked_days: object containing the computed worked days
                    # inputs: object containing the computed inputs

                    # Note: returned value have to be set in the variable ''result''

                    result = rules.NET > categories.NET * 0.10', 'result= (VAC+VATRU)/(BAS_M+AF+HE25+HE35+HE100+BONR+COMI+SMAR+SUBE+VAC+VATRU)', 20, '1.0', NULL, NULL, NULL, NULL, NULL, false);
INSERT INTO hr_salary_rule (id, code, create_date, write_date, sequence, write_uid, appears_on_payslip, condition_range, amount_fix, create_uid, parent_rule_id, company_id, note, amount_percentage, condition_range_min, condition_select, amount_percentage_base, register_id, amount_select, active, condition_range_max, name, condition_python, amount_python_compute, category_id, quantity, analytic_account_id, account_credit, account_tax_id, account_debit, cod_sunat, is_subtotal) VALUES (99, 'NETREMU', '2018-10-30 16:42:02.861646', '2018-10-30 16:42:02.861646', 36, 1, true, 'contract.wage', NULL, 1, NULL, 1, NULL, NULL, NULL, 'none', NULL, NULL, 'code', true, NULL, 'Neto Remuneraciones', '
                    # Available variables:
                    #----------------------
                    # payslip: object containing the payslips
                    # employee: hr.employee object
                    # contract: hr.contract object
                    # rules: object containing the rules code (previously computed)
                    # categories: object containing the computed salary rule categories (sum of amount of all rules belonging to that category).
                    # worked_days: object containing the computed worked days
                    # inputs: object containing the computed inputs

                    # Note: returned value have to be set in the variable ''result''

                    result = rules.NET > categories.NET * 0.10', 'result = NET*REMAFE', 20, '1.0', NULL, NULL, NULL, NULL, NULL, false);
INSERT INTO hr_salary_rule (id, code, create_date, write_date, sequence, write_uid, appears_on_payslip, condition_range, amount_fix, create_uid, parent_rule_id, company_id, note, amount_percentage, condition_range_min, condition_select, amount_percentage_base, register_id, amount_select, active, condition_range_max, name, condition_python, amount_python_compute, category_id, quantity, analytic_account_id, account_credit, account_tax_id, account_debit, cod_sunat, is_subtotal) VALUES (100, 'NETVACA', '2018-10-30 16:42:02.861646', '2018-10-30 16:42:02.861646', 37, 1, true, 'contract.wage', NULL, 1, NULL, 1, NULL, NULL, NULL, 'none', NULL, NULL, 'code', true, NULL, 'Neto Vacaciones', '
                    # Available variables:
                    #----------------------
                    # payslip: object containing the payslips
                    # employee: hr.employee object
                    # contract: hr.contract object
                    # rules: object containing the rules code (previously computed)
                    # categories: object containing the computed salary rule categories (sum of amount of all rules belonging to that category).
                    # worked_days: object containing the computed worked days
                    # inputs: object containing the computed inputs

                    # Note: returned value have to be set in the variable ''result''

                    result = rules.NET > categories.NET * 0.10', 'result = NET*VACAFE', 20, '1.0', NULL, NULL, NULL, NULL, NULL, false);


ALTER TABLE hr_salary_rule ENABLE TRIGGER ALL;

--
-- TOC entry 6202 (class 0 OID 0)
-- Dependencies: 1444
-- Name: hr_salary_rule_category_id_seq; Type: SEQUENCE SET; Schema: public; Owner: openpg
--

SELECT pg_catalog.setval('hr_salary_rule_category_id_seq', 21, true);


--
-- TOC entry 6203 (class 0 OID 0)
-- Dependencies: 1454
-- Name: hr_salary_rule_id_seq; Type: SEQUENCE SET; Schema: public; Owner: openpg
--

SELECT pg_catalog.setval('hr_salary_rule_id_seq', 100, true);


--
-- TOC entry 6178 (class 0 OID 47632)
-- Dependencies: 1441
-- Data for Name: hr_structure_salary_rule_rel; Type: TABLE DATA; Schema: public; Owner: openpg
--

ALTER TABLE hr_structure_salary_rule_rel DISABLE TRIGGER ALL;

INSERT INTO hr_structure_salary_rule_rel (struct_id, rule_id) VALUES (2, 98);
INSERT INTO hr_structure_salary_rule_rel (struct_id, rule_id) VALUES (2, 86);
INSERT INTO hr_structure_salary_rule_rel (struct_id, rule_id) VALUES (2, 100);
INSERT INTO hr_structure_salary_rule_rel (struct_id, rule_id) VALUES (2, 66);
INSERT INTO hr_structure_salary_rule_rel (struct_id, rule_id) VALUES (2, 70);
INSERT INTO hr_structure_salary_rule_rel (struct_id, rule_id) VALUES (2, 80);
INSERT INTO hr_structure_salary_rule_rel (struct_id, rule_id) VALUES (2, 64);
INSERT INTO hr_structure_salary_rule_rel (struct_id, rule_id) VALUES (2, 87);
INSERT INTO hr_structure_salary_rule_rel (struct_id, rule_id) VALUES (2, 97);
INSERT INTO hr_structure_salary_rule_rel (struct_id, rule_id) VALUES (2, 72);
INSERT INTO hr_structure_salary_rule_rel (struct_id, rule_id) VALUES (2, 68);
INSERT INTO hr_structure_salary_rule_rel (struct_id, rule_id) VALUES (2, 65);
INSERT INTO hr_structure_salary_rule_rel (struct_id, rule_id) VALUES (2, 77);
INSERT INTO hr_structure_salary_rule_rel (struct_id, rule_id) VALUES (2, 92);
INSERT INTO hr_structure_salary_rule_rel (struct_id, rule_id) VALUES (2, 99);
INSERT INTO hr_structure_salary_rule_rel (struct_id, rule_id) VALUES (2, 81);
INSERT INTO hr_structure_salary_rule_rel (struct_id, rule_id) VALUES (2, 67);
INSERT INTO hr_structure_salary_rule_rel (struct_id, rule_id) VALUES (2, 85);
INSERT INTO hr_structure_salary_rule_rel (struct_id, rule_id) VALUES (2, 93);
INSERT INTO hr_structure_salary_rule_rel (struct_id, rule_id) VALUES (2, 76);
INSERT INTO hr_structure_salary_rule_rel (struct_id, rule_id) VALUES (2, 78);
INSERT INTO hr_structure_salary_rule_rel (struct_id, rule_id) VALUES (2, 89);
INSERT INTO hr_structure_salary_rule_rel (struct_id, rule_id) VALUES (2, 90);
INSERT INTO hr_structure_salary_rule_rel (struct_id, rule_id) VALUES (2, 75);
INSERT INTO hr_structure_salary_rule_rel (struct_id, rule_id) VALUES (2, 74);
INSERT INTO hr_structure_salary_rule_rel (struct_id, rule_id) VALUES (2, 82);
INSERT INTO hr_structure_salary_rule_rel (struct_id, rule_id) VALUES (2, 79);
INSERT INTO hr_structure_salary_rule_rel (struct_id, rule_id) VALUES (2, 96);
INSERT INTO hr_structure_salary_rule_rel (struct_id, rule_id) VALUES (2, 91);
INSERT INTO hr_structure_salary_rule_rel (struct_id, rule_id) VALUES (2, 73);
INSERT INTO hr_structure_salary_rule_rel (struct_id, rule_id) VALUES (2, 69);
INSERT INTO hr_structure_salary_rule_rel (struct_id, rule_id) VALUES (2, 71);
INSERT INTO hr_structure_salary_rule_rel (struct_id, rule_id) VALUES (2, 84);
INSERT INTO hr_structure_salary_rule_rel (struct_id, rule_id) VALUES (2, 94);
INSERT INTO hr_structure_salary_rule_rel (struct_id, rule_id) VALUES (2, 83);
INSERT INTO hr_structure_salary_rule_rel (struct_id, rule_id) VALUES (2, 88);
INSERT INTO hr_structure_salary_rule_rel (struct_id, rule_id) VALUES (2, 95);


ALTER TABLE hr_structure_salary_rule_rel ENABLE TRIGGER ALL;

--
-- TOC entry 6184 (class 0 OID 48463)
-- Dependencies: 1483
-- Data for Name: planilla_afiliacion; Type: TABLE DATA; Schema: public; Owner: openpg
--

ALTER TABLE planilla_afiliacion DISABLE TRIGGER ALL;

INSERT INTO planilla_afiliacion (id, entidad, create_uid, create_date, write_uid, write_date, prima_s, rem_ase, com_mix, fondo_jib, com_fija) VALUES (6, 'ONP', 1, '2018-10-27 00:18:37.369448', 1, '2018-10-27 00:18:37.369448', 0, 0, 0, 13, 0);
INSERT INTO planilla_afiliacion (id, entidad, create_uid, create_date, write_uid, write_date, prima_s, rem_ase, com_mix, fondo_jib, com_fija) VALUES (7, 'SIN REGIMEN', 1, '2018-10-27 00:18:45.792732', 1, '2018-10-27 00:18:45.792732', 0, 0, 0, 0, 0);
INSERT INTO planilla_afiliacion (id, entidad, create_uid, create_date, write_uid, write_date, prima_s, rem_ase, com_mix, fondo_jib, com_fija) VALUES (2, 'HABITAT', 1, '2018-10-27 00:16:03.391482', 6, '2018-10-31 21:08:38.829015', 1.3600000000000001, 9489.0400000000009, 0.38, 10, 1.47);
INSERT INTO planilla_afiliacion (id, entidad, create_uid, create_date, write_uid, write_date, prima_s, rem_ase, com_mix, fondo_jib, com_fija) VALUES (3, 'INTEGRA', 1, '2018-10-27 00:16:44.462067', 6, '2018-10-31 21:08:42.19884', 1.3600000000000001, 9489.0400000000009, 0.90000000000000002, 10, 1.55);
INSERT INTO planilla_afiliacion (id, entidad, create_uid, create_date, write_uid, write_date, prima_s, rem_ase, com_mix, fondo_jib, com_fija) VALUES (4, 'PRIMA', 1, '2018-10-27 00:17:30.821541', 6, '2018-10-31 21:08:45.809241', 1.3600000000000001, 9489.0400000000009, 0.17999999999999999, 10, 1.6000000000000001);
INSERT INTO planilla_afiliacion (id, entidad, create_uid, create_date, write_uid, write_date, prima_s, rem_ase, com_mix, fondo_jib, com_fija) VALUES (5, 'PROFUTURO', 1, '2018-10-27 00:18:06.189054', 6, '2018-10-31 21:08:54.943207', 1.3600000000000001, 9489.0400000000009, 1.0700000000000001, 10, 1.6899999999999999);


ALTER TABLE planilla_afiliacion ENABLE TRIGGER ALL;

--
-- TOC entry 6204 (class 0 OID 0)
-- Dependencies: 1482
-- Name: planilla_afiliacion_id_seq; Type: SEQUENCE SET; Schema: public; Owner: openpg
--

SELECT pg_catalog.setval('planilla_afiliacion_id_seq', 7, true);


--
-- TOC entry 6186 (class 0 OID 48474)
-- Dependencies: 1485
-- Data for Name: planilla_afiliacion_line; Type: TABLE DATA; Schema: public; Owner: openpg
--

ALTER TABLE planilla_afiliacion_line DISABLE TRIGGER ALL;



ALTER TABLE planilla_afiliacion_line ENABLE TRIGGER ALL;

--
-- TOC entry 6205 (class 0 OID 0)
-- Dependencies: 1484
-- Name: planilla_afiliacion_line_id_seq; Type: SEQUENCE SET; Schema: public; Owner: openpg
--

SELECT pg_catalog.setval('planilla_afiliacion_line_id_seq', 1, false);


--
-- TOC entry 6192 (class 0 OID 48698)
-- Dependencies: 1529
-- Data for Name: planilla_situacion; Type: TABLE DATA; Schema: public; Owner: openpg
--

ALTER TABLE planilla_situacion DISABLE TRIGGER ALL;

INSERT INTO planilla_situacion (id, create_uid, descripcion_abrev, write_uid, write_date, descripcion, create_date, codigo) VALUES (1, 1, 'ACTIVO O SUBSIDIADO', 1, '2018-10-26 23:58:18.200401', 'ACTIVO O SUBSIDIADO', '2018-10-26 00:02:50.724235', '1');
INSERT INTO planilla_situacion (id, create_uid, descripcion_abrev, write_uid, write_date, descripcion, create_date, codigo) VALUES (2, 1, 'BAJA', 1, '2018-10-26 23:58:31.309549', 'BAJA', '2018-10-26 23:58:31.309549', '0');
INSERT INTO planilla_situacion (id, create_uid, descripcion_abrev, write_uid, write_date, descripcion, create_date, codigo) VALUES (3, 1, 'SIN VINC. LAB. CON CONC PEND POR LIQUIDAR', 1, '2018-10-26 23:59:01.913209', 'SIN VÍNCULO LABORAL CON CONCEPTOS PENDIENTE DE LIQUIDAR', '2018-10-26 23:59:01.913209', '2');
INSERT INTO planilla_situacion (id, create_uid, descripcion_abrev, write_uid, write_date, descripcion, create_date, codigo) VALUES (4, 1, 'SUSPENSION PERFECTA DE LABORES', 1, '2018-10-26 23:59:24.169106', 'SUSPENSION PERFECTA DE LABORES', '2018-10-26 23:59:24.169106', '3');


ALTER TABLE planilla_situacion ENABLE TRIGGER ALL;

--
-- TOC entry 6206 (class 0 OID 0)
-- Dependencies: 1528
-- Name: planilla_situacion_id_seq; Type: SEQUENCE SET; Schema: public; Owner: openpg
--

SELECT pg_catalog.setval('planilla_situacion_id_seq', 4, true);


--
-- TOC entry 6190 (class 0 OID 48687)
-- Dependencies: 1527
-- Data for Name: planilla_tipo_documento; Type: TABLE DATA; Schema: public; Owner: openpg
--

ALTER TABLE planilla_tipo_documento DISABLE TRIGGER ALL;

INSERT INTO planilla_tipo_documento (id, create_uid, descripcion_abrev, codigo_afp, codigo_sunat, write_date, descripcion, create_date, write_uid) VALUES (3, 1, 'RUC', NULL, '06', '2018-10-26 23:48:23.3878', 'REG. UNICO DE CONTRIBUYENTES', '2018-10-26 23:48:23.3878', 1);
INSERT INTO planilla_tipo_documento (id, create_uid, descripcion_abrev, codigo_afp, codigo_sunat, write_date, descripcion, create_date, write_uid) VALUES (5, 1, 'CARNE SOLIC REFUGIO', NULL, '09', '2018-10-26 23:49:55.628968', 'CARNE DE SOLICIT DE REFUGIO', '2018-10-26 23:49:55.628968', 1);
INSERT INTO planilla_tipo_documento (id, create_uid, descripcion_abrev, codigo_afp, codigo_sunat, write_date, descripcion, create_date, write_uid) VALUES (6, 1, 'PART. NAC.', NULL, '11', '2018-10-26 23:50:23.968171', 'PARTIDA DE NACIMIENTO', '2018-10-26 23:50:23.968171', 1);
INSERT INTO planilla_tipo_documento (id, create_uid, descripcion_abrev, codigo_afp, codigo_sunat, write_date, descripcion, create_date, write_uid) VALUES (1, 1, 'DNI', '0', '01', '2018-10-26 23:51:55.041836', 'DOCUMENTO NACIONAL DE IDENTIDAD', '2018-10-25 23:57:01.962245', 1);
INSERT INTO planilla_tipo_documento (id, create_uid, descripcion_abrev, codigo_afp, codigo_sunat, write_date, descripcion, create_date, write_uid) VALUES (2, 1, 'CARNE EXT.', '1', '04', '2018-10-26 23:52:03.720779', 'CARNET DE EXTRANJERIA', '2018-10-26 23:47:09.575169', 1);
INSERT INTO planilla_tipo_documento (id, create_uid, descripcion_abrev, codigo_afp, codigo_sunat, write_date, descripcion, create_date, write_uid) VALUES (7, 1, 'CARMP', '2', 'NE', '2018-10-26 23:54:27.958218', 'CARNET MILITAR Y POLICIAL', '2018-10-26 23:54:27.958218', 1);
INSERT INTO planilla_tipo_documento (id, create_uid, descripcion_abrev, codigo_afp, codigo_sunat, write_date, descripcion, create_date, write_uid) VALUES (8, 1, 'LAT', '3', 'NE', '2018-10-26 23:55:36.920884', 'LIBRETA ADOLESCENTES TRABAJADOR', '2018-10-26 23:55:36.920884', 1);
INSERT INTO planilla_tipo_documento (id, create_uid, descripcion_abrev, codigo_afp, codigo_sunat, write_date, descripcion, create_date, write_uid) VALUES (4, 1, 'PASAPORTE', '4', '07', '2018-10-26 23:55:50.082496', 'PASAPORTE', '2018-10-26 23:49:27.000642', 1);
INSERT INTO planilla_tipo_documento (id, create_uid, descripcion_abrev, codigo_afp, codigo_sunat, write_date, descripcion, create_date, write_uid) VALUES (9, 1, 'IA', '5', 'NE', '2018-10-26 23:56:19.017072', 'INEXISTENCIA/AFILIA', '2018-10-26 23:56:19.017072', 1);
INSERT INTO planilla_tipo_documento (id, create_uid, descripcion_abrev, codigo_afp, codigo_sunat, write_date, descripcion, create_date, write_uid) VALUES (10, 1, 'PTP', '6', 'NE', '2018-10-26 23:56:51.275278', 'PERMISO TEMPORAL DE PERMANENCIA', '2018-10-26 23:56:51.275278', 1);


ALTER TABLE planilla_tipo_documento ENABLE TRIGGER ALL;

--
-- TOC entry 6207 (class 0 OID 0)
-- Dependencies: 1526
-- Name: planilla_tipo_documento_id_seq; Type: SEQUENCE SET; Schema: public; Owner: openpg
--

SELECT pg_catalog.setval('planilla_tipo_documento_id_seq', 10, true);


--
-- TOC entry 6196 (class 0 OID 48720)
-- Dependencies: 1533
-- Data for Name: planilla_tipo_suspension; Type: TABLE DATA; Schema: public; Owner: openpg
--

ALTER TABLE planilla_tipo_suspension DISABLE TRIGGER ALL;

INSERT INTO planilla_tipo_suspension (id, create_uid, descripcion_abrev, write_uid, write_date, descripcion, create_date, codigo) VALUES (1, 1, 'S.P. SANCION DISCIPLINARIA', 1, '2018-10-27 00:06:53.887604', 'S.P. SANCION DISCIPLINARIA', '2018-10-27 00:06:53.887604', '01');
INSERT INTO planilla_tipo_suspension (id, create_uid, descripcion_abrev, write_uid, write_date, descripcion, create_date, codigo) VALUES (2, 1, 'S.P. EJERCICIO DERECHO HUELGA', 1, '2018-10-27 00:07:33.982512', 'S.P. EJERCICIO DEL DERECHO DE HUELGA', '2018-10-27 00:07:33.982512', '02');
INSERT INTO planilla_tipo_suspension (id, create_uid, descripcion_abrev, write_uid, write_date, descripcion, create_date, codigo) VALUES (3, 1, 'S.P. DETENCIÓN DEL TRABAJADOR', 1, '2018-10-27 00:07:52.626782', 'S.P. DETENCIÓN DEL TRABAJADOR, SALVO EL CASO DE CONDENA PRIVATIVA DE LA LIBERTAD', '2018-10-27 00:07:52.626782', '03');
INSERT INTO planilla_tipo_suspension (id, create_uid, descripcion_abrev, write_uid, write_date, descripcion, create_date, codigo) VALUES (4, 1, 'S.P. INHAB. ADMINIST., JUDICIAL O PENA PRIVATIVA', 1, '2018-10-27 00:08:11.379957', 'S.P. INHABILITACIÓN ADMINISTRATIVA, JUDICIAL  O PENA PRIVATIVA DE LA LIBERTAD EFECTIVA POR DELITO CULPOSO, POR PERIODO NO SUPERIOR A TRES MESES', '2018-10-27 00:08:11.379957', '04');
INSERT INTO planilla_tipo_suspension (id, create_uid, descripcion_abrev, write_uid, write_date, descripcion, create_date, codigo) VALUES (5, 1, 'S.P. PERMISO, LICENCIA U OTROS SIN GOCE DE HABER', 1, '2018-10-27 00:08:35.71752', 'S.P. PERMISO, LICENCIA U OTROS MOTIVOS SIN GOCE DE HABER
', '2018-10-27 00:08:35.71752', '05');
INSERT INTO planilla_tipo_suspension (id, create_uid, descripcion_abrev, write_uid, write_date, descripcion, create_date, codigo) VALUES (6, 1, 'S.P. CASO FORTUITO O FUERZA MAYOR', 1, '2018-10-27 00:09:00.346893', 'S.P. CASO FORTUITO O FUERZA MAYOR
', '2018-10-27 00:09:00.346893', '06');
INSERT INTO planilla_tipo_suspension (id, create_uid, descripcion_abrev, write_uid, write_date, descripcion, create_date, codigo) VALUES (7, 1, 'S.P. FALTA NO JUSTIFICADA', 1, '2018-10-27 00:09:20.657074', 'S.P. FALTA NO JUSTIFICADA
', '2018-10-27 00:09:20.657074', '07');
INSERT INTO planilla_tipo_suspension (id, create_uid, descripcion_abrev, write_uid, write_date, descripcion, create_date, codigo) VALUES (8, 1, 'S.P. POR TEMPORADA O INTERMITENTE', 1, '2018-10-27 00:09:36.25786', 'S.P. POR TEMPORADA O INTERMITENTE
', '2018-10-27 00:09:36.25786', '08');
INSERT INTO planilla_tipo_suspension (id, create_uid, descripcion_abrev, write_uid, write_date, descripcion, create_date, codigo) VALUES (9, 1, 'S.P. MATERNIDAD - PRE Y POST NATAL', 1, '2018-10-27 00:10:08.267226', 'S.P. MATERNIDAD DURANTE EL DESCANSO PRE Y POST NATAL
', '2018-10-27 00:10:08.267226', '09');
INSERT INTO planilla_tipo_suspension (id, create_uid, descripcion_abrev, write_uid, write_date, descripcion, create_date, codigo) VALUES (10, 1, 'S.P. SENTENCIA TERR, NARC,CORRUP Y VIOLAC.', 1, '2018-10-27 00:10:23.508397', 'S.P. SENTENCIA DE PRIMERA INSTANCIA POR DELITOS DE TERRORISMO, NARCOTRÁFICO, CORRUPCIÓN O VIOLACIÓN DE LA LIBERTAD SEXUAL.
', '2018-10-27 00:10:23.508397', '10');


ALTER TABLE planilla_tipo_suspension ENABLE TRIGGER ALL;

--
-- TOC entry 6208 (class 0 OID 0)
-- Dependencies: 1532
-- Name: planilla_tipo_suspension_id_seq; Type: SEQUENCE SET; Schema: public; Owner: openpg
--

SELECT pg_catalog.setval('planilla_tipo_suspension_id_seq', 10, true);


--
-- TOC entry 6194 (class 0 OID 48709)
-- Dependencies: 1531
-- Data for Name: planilla_tipo_trabajador; Type: TABLE DATA; Schema: public; Owner: openpg
--

ALTER TABLE planilla_tipo_trabajador DISABLE TRIGGER ALL;

INSERT INTO planilla_tipo_trabajador (id, create_uid, descripcion_abrev, write_uid, write_date, descripcion, create_date, codigo) VALUES (1, 1, 'EMPLEADO', 1, '2018-10-27 00:01:09.022698', 'EMPLEADO', '2018-10-25 23:57:51.330242', '21');
INSERT INTO planilla_tipo_trabajador (id, create_uid, descripcion_abrev, write_uid, write_date, descripcion, create_date, codigo) VALUES (2, 1, 'EJECUTIVO', 1, '2018-10-27 00:01:57.170069', 'EJECUTIVO', '2018-10-27 00:01:57.170069', '19');
INSERT INTO planilla_tipo_trabajador (id, create_uid, descripcion_abrev, write_uid, write_date, descripcion, create_date, codigo) VALUES (3, 1, 'OBRERO', 1, '2018-10-27 00:02:11.964805', 'OBRERO', '2018-10-27 00:02:11.964805', '20');
INSERT INTO planilla_tipo_trabajador (id, create_uid, descripcion_abrev, write_uid, write_date, descripcion, create_date, codigo) VALUES (4, 1, 'TRAB.PORTUARIO', 1, '2018-10-27 00:02:48.180508', 'TRABAJADOR PORTUARIO - LEY 27866
', '2018-10-27 00:02:39.923191', '22');
INSERT INTO planilla_tipo_trabajador (id, create_uid, descripcion_abrev, write_uid, write_date, descripcion, create_date, codigo) VALUES (5, 1, 'PRACT. SENATI', 1, '2018-10-27 00:03:14.658857', 'PRACTICANTE SENATI - DEC. LEY 20151', '2018-10-27 00:03:14.658857', '23');
INSERT INTO planilla_tipo_trabajador (id, create_uid, descripcion_abrev, write_uid, write_date, descripcion, create_date, codigo) VALUES (6, 1, 'PENSIONISTA O CESANTE', 1, '2018-10-27 00:03:47.732149', 'PENSIONISTA O CESANTE', '2018-10-27 00:03:47.732149', '24');


ALTER TABLE planilla_tipo_trabajador ENABLE TRIGGER ALL;

--
-- TOC entry 6209 (class 0 OID 0)
-- Dependencies: 1530
-- Name: planilla_tipo_trabajador_id_seq; Type: SEQUENCE SET; Schema: public; Owner: openpg
--

SELECT pg_catalog.setval('planilla_tipo_trabajador_id_seq', 6, true);


--
-- TOC entry 6188 (class 0 OID 48519)
-- Dependencies: 1493
-- Data for Name: planilla_worked_days; Type: TABLE DATA; Schema: public; Owner: openpg
--

ALTER TABLE planilla_worked_days DISABLE TRIGGER ALL;

INSERT INTO planilla_worked_days (id, create_uid, minutos, write_uid, write_date, descripcion, create_date, horas, codigo, dias, tasa_monto) VALUES (9, 1, 0, 1, '2018-10-29 14:29:23.25439', 'TARDANZAS', '2018-10-29 14:29:23.25439', 0, 'TAR', 0, 0);
INSERT INTO planilla_worked_days (id, create_uid, minutos, write_uid, write_date, descripcion, create_date, horas, codigo, dias, tasa_monto) VALUES (10, 1, 0, 1, '2018-10-29 14:29:23.25439', 'FALTAS', '2018-10-29 14:29:23.25439', 0, 'FAL', 0, 0);
INSERT INTO planilla_worked_days (id, create_uid, minutos, write_uid, write_date, descripcion, create_date, horas, codigo, dias, tasa_monto) VALUES (11, 1, 0, 1, '2018-10-29 14:29:23.25439', 'HORAS EXTRAS 25%', '2018-10-29 14:29:23.25439', 0, 'HE25', 0, 25);
INSERT INTO planilla_worked_days (id, create_uid, minutos, write_uid, write_date, descripcion, create_date, horas, codigo, dias, tasa_monto) VALUES (12, 1, 0, 1, '2018-10-29 14:29:23.25439', 'HORAS EXTRAS 35%', '2018-10-29 14:29:23.25439', 0, 'HE35', 0, 35);
INSERT INTO planilla_worked_days (id, create_uid, minutos, write_uid, write_date, descripcion, create_date, horas, codigo, dias, tasa_monto) VALUES (13, 1, 0, 1, '2018-10-29 14:29:23.25439', 'HORAS EXTRAS 100%', '2018-10-29 14:29:23.25439', 0, 'HE100', 0, 100);
INSERT INTO planilla_worked_days (id, create_uid, minutos, write_uid, write_date, descripcion, create_date, horas, codigo, dias, tasa_monto) VALUES (14, 1, 0, 1, '2018-10-29 14:29:23.25439', 'DIAS SUBSIDIADOS POR MATERNIDAD', '2018-10-29 14:29:23.25439', 0, 'DSUBM', 0, 0);
INSERT INTO planilla_worked_days (id, create_uid, minutos, write_uid, write_date, descripcion, create_date, horas, codigo, dias, tasa_monto) VALUES (15, 1, 0, 1, '2018-10-29 14:29:23.25439', 'DIAS SUBSIDIADOS POR ENFERMEDAD', '2018-10-29 14:29:23.25439', 0, 'DSUBE', 0, 0);
INSERT INTO planilla_worked_days (id, create_uid, minutos, write_uid, write_date, descripcion, create_date, horas, codigo, dias, tasa_monto) VALUES (16, 1, 0, 1, '2018-10-29 14:29:23.25439', 'DIAS LABORADOS', '2018-10-29 14:29:23.25439', 0, 'DLAB', 30, 0);


ALTER TABLE planilla_worked_days ENABLE TRIGGER ALL;

--
-- TOC entry 6210 (class 0 OID 0)
-- Dependencies: 1492
-- Name: planilla_worked_days_id_seq; Type: SEQUENCE SET; Schema: public; Owner: openpg
--

SELECT pg_catalog.setval('planilla_worked_days_id_seq', 16, true);


-- Completed on 2018-11-02 20:01:55

--
-- PostgreSQL database dump complete
--



--
-- TOC entry 6107 (class 0 OID 48508)
-- Dependencies: 1491
-- Data for Name: planilla_inputs_nomina; Type: TABLE DATA; Schema: public; Owner: openpg
--

SET SESSION AUTHORIZATION DEFAULT;

ALTER TABLE planilla_inputs_nomina DISABLE TRIGGER ALL;

INSERT INTO planilla_inputs_nomina (id, create_uid, create_date, write_uid, write_date, descripcion, codigo) VALUES (16, 1, '2018-10-29 14:32:14.084544', 1, '2018-10-29 14:32:14.084544', 'GRATIFICACIONES', 'GRA');
INSERT INTO planilla_inputs_nomina (id, create_uid, create_date, write_uid, write_date, descripcion, codigo) VALUES (17, 1, '2018-10-29 14:32:14.084544', 1, '2018-10-29 14:32:14.084544', 'VACACIONES', 'VAC');
INSERT INTO planilla_inputs_nomina (id, create_uid, create_date, write_uid, write_date, descripcion, codigo) VALUES (18, 1, '2018-10-29 14:32:14.084544', 1, '2018-10-29 14:32:14.084544', 'COMPENSACION POR TIEMPO DE SERVICIOS', 'CTS');
INSERT INTO planilla_inputs_nomina (id, create_uid, create_date, write_uid, write_date, descripcion, codigo) VALUES (19, 1, '2018-10-29 14:32:14.084544', 1, '2018-10-29 14:32:14.084544', 'GRATIFICACIONES TRUNCAS', 'GRA_TRU');
INSERT INTO planilla_inputs_nomina (id, create_uid, create_date, write_uid, write_date, descripcion, codigo) VALUES (20, 1, '2018-10-29 14:32:14.084544', 1, '2018-10-29 14:32:14.084544', 'VACACIONES TRUNCAS', 'VAC_TRU');
INSERT INTO planilla_inputs_nomina (id, create_uid, create_date, write_uid, write_date, descripcion, codigo) VALUES (21, 1, '2018-10-29 14:32:14.084544', 1, '2018-10-29 14:32:14.084544', 'CTS TRUNCA', 'CTS_TRU');
INSERT INTO planilla_inputs_nomina (id, create_uid, create_date, write_uid, write_date, descripcion, codigo) VALUES (22, 1, '2018-10-29 14:32:14.084544', 1, '2018-10-29 14:32:14.084544', 'ADELANTOS DE REMUNERACION', 'ADELANTO');
INSERT INTO planilla_inputs_nomina (id, create_uid, create_date, write_uid, write_date, descripcion, codigo) VALUES (23, 1, '2018-10-29 14:32:14.084544', 1, '2018-10-29 14:32:14.084544', 'PRESTAMOS A TRABAJADORES', 'PRESTAMO');
INSERT INTO planilla_inputs_nomina (id, create_uid, create_date, write_uid, write_date, descripcion, codigo) VALUES (24, 1, '2018-10-29 14:32:14.084544', 1, '2018-10-29 14:32:14.084544', 'OTROS DESCUENTOS AL NETO', 'OTROS');
INSERT INTO planilla_inputs_nomina (id, create_uid, create_date, write_uid, write_date, descripcion, codigo) VALUES (25, 1, '2018-10-29 14:32:14.084544', 1, '2018-10-29 14:32:14.084544', 'QUINTA', 'QUINTA');
INSERT INTO planilla_inputs_nomina (id, create_uid, create_date, write_uid, write_date, descripcion, codigo) VALUES (26, 1, '2018-10-29 14:32:14.084544', 1, '2018-10-29 14:32:14.084544', 'COMISIONES', 'COMI');
INSERT INTO planilla_inputs_nomina (id, create_uid, create_date, write_uid, write_date, descripcion, codigo) VALUES (27, 1, '2018-10-29 14:32:14.084544', 1, '2018-10-29 14:32:14.084544', 'BONIFICACIONES REGULARES', 'BONRER');
INSERT INTO planilla_inputs_nomina (id, create_uid, create_date, write_uid, write_date, descripcion, codigo) VALUES (29, 1, '2018-10-29 14:32:14.084544', 1, '2018-10-29 14:32:14.084544', 'BONIFICACION 9%', 'BON9');
INSERT INTO planilla_inputs_nomina (id, create_uid, create_date, write_uid, write_date, descripcion, codigo) VALUES (30, 1, '2018-10-29 14:32:14.084544', 1, '2018-10-29 14:32:14.084544', 'BONIFICACION TRUNCA 9% ', 'BON9_TRU');


ALTER TABLE planilla_inputs_nomina ENABLE TRIGGER ALL;

--
-- TOC entry 6112 (class 0 OID 0)
-- Dependencies: 1490
-- Name: planilla_inputs_nomina_id_seq; Type: SEQUENCE SET; Schema: public; Owner: openpg
--

SELECT pg_catalog.setval('planilla_inputs_nomina_id_seq', 30, true);


-- Completed on 2018-11-02 20:06:53

--
-- PostgreSQL database dump complete
--


