--
-- PostgreSQL database dump
--

-- Dumped from database version 14.5
-- Dumped by pg_dump version 15.2

-- Started on 2023-03-27 17:02:16 JST

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- TOC entry 5 (class 2615 OID 2200)
-- Name: public; Type: SCHEMA; Schema: -; Owner: thomashowe
--

-- *not* creating schema, since initdb creates it


ALTER SCHEMA public OWNER TO thomashowe;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- TOC entry 209 (class 1259 OID 16384)
-- Name: analysis; Type: TABLE; Schema: public; Owner: thomashowe
--

CREATE TABLE public.analysis (
    id uuid NOT NULL,
    vcon_uuid uuid,
    vendor text,
    type text,
    body jsonb
);


ALTER TABLE public.analysis OWNER TO thomashowe;

--
-- TOC entry 215 (class 1259 OID 52848)
-- Name: appended; Type: TABLE; Schema: public; Owner: thomashowe
--

CREATE TABLE public.appended (
    id uuid NOT NULL,
    vcon_uuid uuid,
    body text,
    encoding text,
    url text,
    alg text,
    signature text
);


ALTER TABLE public.appended OWNER TO thomashowe;

--
-- TOC entry 210 (class 1259 OID 16389)
-- Name: attachments; Type: TABLE; Schema: public; Owner: thomashowe
--

CREATE TABLE public.attachments (
    id uuid NOT NULL,
    vcon_uuid uuid,
    body jsonb,
    vendor text,
    type text
);


ALTER TABLE public.attachments OWNER TO thomashowe;

--
-- TOC entry 211 (class 1259 OID 16394)
-- Name: dialogs; Type: TABLE; Schema: public; Owner: thomashowe
--

CREATE TABLE public.dialogs (
    type text,
    start timestamp with time zone,
    duration integer,
    disposition text,
    direction text,
    parties integer[],
    url text,
    mimetype text,
    filename text,
    id uuid NOT NULL,
    vcon_uuid uuid,
    signature text,
    alg text,
    encoding text,
    body text,
    originator integer,
    transferee integer,
    transferor integer,
    "transfer-target" integer,
    original integer,
    consultation integer,
    "target-dialog" integer
);


ALTER TABLE public.dialogs OWNER TO thomashowe;

--
-- TOC entry 216 (class 1259 OID 52860)
-- Name: groups; Type: TABLE; Schema: public; Owner: thomashowe
--

CREATE TABLE public.groups (
    id uuid NOT NULL,
    vcon_uuid uuid,
    group_uuid uuid,
    body text,
    alg text,
    signature text
);


ALTER TABLE public.groups OWNER TO thomashowe;

--
-- TOC entry 212 (class 1259 OID 16399)
-- Name: parties; Type: TABLE; Schema: public; Owner: thomashowe
--

CREATE TABLE public.parties (
    id uuid NOT NULL,
    tel text,
    role text,
    mailto text,
    name text,
    extension text,
    vcon_uuid uuid,
    stir text,
    validation text,
    gmlpos text,
    jcard json,
    timezone text
);


ALTER TABLE public.parties OWNER TO thomashowe;

--
-- TOC entry 214 (class 1259 OID 52841)
-- Name: redacted; Type: TABLE; Schema: public; Owner: thomashowe
--

CREATE TABLE public.redacted (
    id uuid NOT NULL,
    vcon_uuid uuid,
    original_uuid uuid,
    body text,
    alg text,
    signature text
);


ALTER TABLE public.redacted OWNER TO thomashowe;

--
-- TOC entry 213 (class 1259 OID 16404)
-- Name: vcons; Type: TABLE; Schema: public; Owner: thomashowe
--

CREATE TABLE public.vcons (
    id uuid NOT NULL,
    created_at timestamp with time zone,
    updated_at timestamp with time zone,
    uuid uuid,
    subject text
);


ALTER TABLE public.vcons OWNER TO thomashowe;

--
-- TOC entry 3461 (class 2606 OID 32770)
-- Name: analysis analysis_pkey; Type: CONSTRAINT; Schema: public; Owner: thomashowe
--

ALTER TABLE ONLY public.analysis
    ADD CONSTRAINT analysis_pkey PRIMARY KEY (id);


--
-- TOC entry 3473 (class 2606 OID 52854)
-- Name: appended appended_pkey; Type: CONSTRAINT; Schema: public; Owner: thomashowe
--

ALTER TABLE ONLY public.appended
    ADD CONSTRAINT appended_pkey PRIMARY KEY (id);


--
-- TOC entry 3463 (class 2606 OID 31300)
-- Name: attachments attachments_pkey; Type: CONSTRAINT; Schema: public; Owner: thomashowe
--

ALTER TABLE ONLY public.attachments
    ADD CONSTRAINT attachments_pkey PRIMARY KEY (id);


--
-- TOC entry 3465 (class 2606 OID 52838)
-- Name: dialogs dialogs_pkey; Type: CONSTRAINT; Schema: public; Owner: thomashowe
--

ALTER TABLE ONLY public.dialogs
    ADD CONSTRAINT dialogs_pkey PRIMARY KEY (id);


--
-- TOC entry 3475 (class 2606 OID 52866)
-- Name: groups groups_pkey; Type: CONSTRAINT; Schema: public; Owner: thomashowe
--

ALTER TABLE ONLY public.groups
    ADD CONSTRAINT groups_pkey PRIMARY KEY (id);


--
-- TOC entry 3467 (class 2606 OID 31302)
-- Name: parties parties_pkey; Type: CONSTRAINT; Schema: public; Owner: thomashowe
--

ALTER TABLE ONLY public.parties
    ADD CONSTRAINT parties_pkey PRIMARY KEY (id);


--
-- TOC entry 3471 (class 2606 OID 52847)
-- Name: redacted redacted_pkey; Type: CONSTRAINT; Schema: public; Owner: thomashowe
--

ALTER TABLE ONLY public.redacted
    ADD CONSTRAINT redacted_pkey PRIMARY KEY (id);


--
-- TOC entry 3469 (class 2606 OID 31304)
-- Name: vcons vcons_pkey; Type: CONSTRAINT; Schema: public; Owner: thomashowe
--

ALTER TABLE ONLY public.vcons
    ADD CONSTRAINT vcons_pkey PRIMARY KEY (id);


--
-- TOC entry 3620 (class 0 OID 0)
-- Dependencies: 5
-- Name: SCHEMA public; Type: ACL; Schema: -; Owner: thomashowe
--

REVOKE USAGE ON SCHEMA public FROM PUBLIC;
GRANT ALL ON SCHEMA public TO PUBLIC;


-- Completed on 2023-03-27 17:02:16 JST

--
-- PostgreSQL database dump complete
--

