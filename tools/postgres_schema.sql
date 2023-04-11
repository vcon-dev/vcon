--
-- PostgreSQL database dump
--

-- Dumped from database version 14.5
-- Dumped by pg_dump version 15.2

-- Started on 2023-03-28 15:02:00 JST

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
-- TOC entry 210 (class 1259 OID 53471)
-- Name: analysis; Type: TABLE; Schema: public; Owner: thomashowe
--

CREATE TABLE public.analysis (
    id integer NOT NULL,
    type text NOT NULL,
    dialog integer NOT NULL,
    mimetype text,
    filename text,
    vendor text NOT NULL,
    schema text,
    body text,
    encoding text,
    url text,
    alg text,
    signature text,
    vcon_uuid uuid NOT NULL
);


ALTER TABLE public.analysis OWNER TO thomashowe;

--
-- TOC entry 209 (class 1259 OID 53470)
-- Name: analysis_id_seq; Type: SEQUENCE; Schema: public; Owner: thomashowe
--

CREATE SEQUENCE public.analysis_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.analysis_id_seq OWNER TO thomashowe;

--
-- TOC entry 3620 (class 0 OID 0)
-- Dependencies: 209
-- Name: analysis_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: thomashowe
--

ALTER SEQUENCE public.analysis_id_seq OWNED BY public.analysis.id;


--
-- TOC entry 212 (class 1259 OID 53480)
-- Name: attachment; Type: TABLE; Schema: public; Owner: thomashowe
--

CREATE TABLE public.attachment (
    id integer NOT NULL,
    type text NOT NULL,
    party integer,
    mimetype text,
    filename text,
    body text,
    encoding text,
    url text,
    alg text,
    signature text,
    vcon_uuid uuid NOT NULL
);


ALTER TABLE public.attachment OWNER TO thomashowe;

--
-- TOC entry 211 (class 1259 OID 53479)
-- Name: attachment_id_seq; Type: SEQUENCE; Schema: public; Owner: thomashowe
--

CREATE SEQUENCE public.attachment_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.attachment_id_seq OWNER TO thomashowe;

--
-- TOC entry 3621 (class 0 OID 0)
-- Dependencies: 211
-- Name: attachment_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: thomashowe
--

ALTER SEQUENCE public.attachment_id_seq OWNED BY public.attachment.id;


--
-- TOC entry 214 (class 1259 OID 53489)
-- Name: dialog; Type: TABLE; Schema: public; Owner: thomashowe
--

CREATE TABLE public.dialog (
    id integer NOT NULL,
    type text NOT NULL,
    start timestamp without time zone,
    duration numeric(10,5),
    parties integer[] NOT NULL,
    mimetype text,
    filename text,
    body text,
    url text,
    encoding text,
    alg text,
    signature text,
    vcon_uuid uuid NOT NULL
);


ALTER TABLE public.dialog OWNER TO thomashowe;

--
-- TOC entry 213 (class 1259 OID 53488)
-- Name: dialog_id_seq; Type: SEQUENCE; Schema: public; Owner: thomashowe
--

CREATE SEQUENCE public.dialog_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.dialog_id_seq OWNER TO thomashowe;

--
-- TOC entry 3622 (class 0 OID 0)
-- Dependencies: 213
-- Name: dialog_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: thomashowe
--

ALTER SEQUENCE public.dialog_id_seq OWNED BY public.dialog.id;


--
-- TOC entry 216 (class 1259 OID 53499)
-- Name: group; Type: TABLE; Schema: public; Owner: thomashowe
--

CREATE TABLE public."group" (
    id integer NOT NULL,
    uuid uuid NOT NULL,
    body json,
    encoding text,
    url text,
    alg text,
    signature text,
    vcon_uuid uuid NOT NULL
);


ALTER TABLE public."group" OWNER TO thomashowe;

--
-- TOC entry 215 (class 1259 OID 53498)
-- Name: group_id_seq; Type: SEQUENCE; Schema: public; Owner: thomashowe
--

CREATE SEQUENCE public.group_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.group_id_seq OWNER TO thomashowe;

--
-- TOC entry 3623 (class 0 OID 0)
-- Dependencies: 215
-- Name: group_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: thomashowe
--

ALTER SEQUENCE public.group_id_seq OWNED BY public."group".id;


--
-- TOC entry 218 (class 1259 OID 53508)
-- Name: party; Type: TABLE; Schema: public; Owner: thomashowe
--

CREATE TABLE public.party (
    id integer NOT NULL,
    tel text,
    stir text,
    mailto text,
    name text,
    validation text,
    jcard json,
    gmlpos text,
    civicaddress text,
    timezone text,
    vcon_uuid uuid NOT NULL
);


ALTER TABLE public.party OWNER TO thomashowe;

--
-- TOC entry 217 (class 1259 OID 53507)
-- Name: party_id_seq; Type: SEQUENCE; Schema: public; Owner: thomashowe
--

CREATE SEQUENCE public.party_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.party_id_seq OWNER TO thomashowe;

--
-- TOC entry 3624 (class 0 OID 0)
-- Dependencies: 217
-- Name: party_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: thomashowe
--

ALTER SEQUENCE public.party_id_seq OWNED BY public.party.id;


--
-- TOC entry 219 (class 1259 OID 53516)
-- Name: vcons; Type: TABLE; Schema: public; Owner: thomashowe
--

CREATE TABLE public.vcons (
    id uuid NOT NULL,
    vcon text NOT NULL,
    uuid uuid NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone,
    subject text
);


ALTER TABLE public.vcons OWNER TO thomashowe;

--
-- TOC entry 3457 (class 2604 OID 53474)
-- Name: analysis id; Type: DEFAULT; Schema: public; Owner: thomashowe
--

ALTER TABLE ONLY public.analysis ALTER COLUMN id SET DEFAULT nextval('public.analysis_id_seq'::regclass);


--
-- TOC entry 3458 (class 2604 OID 53483)
-- Name: attachment id; Type: DEFAULT; Schema: public; Owner: thomashowe
--

ALTER TABLE ONLY public.attachment ALTER COLUMN id SET DEFAULT nextval('public.attachment_id_seq'::regclass);


--
-- TOC entry 3459 (class 2604 OID 53492)
-- Name: dialog id; Type: DEFAULT; Schema: public; Owner: thomashowe
--

ALTER TABLE ONLY public.dialog ALTER COLUMN id SET DEFAULT nextval('public.dialog_id_seq'::regclass);


--
-- TOC entry 3460 (class 2604 OID 53502)
-- Name: group id; Type: DEFAULT; Schema: public; Owner: thomashowe
--

ALTER TABLE ONLY public."group" ALTER COLUMN id SET DEFAULT nextval('public.group_id_seq'::regclass);


--
-- TOC entry 3461 (class 2604 OID 53511)
-- Name: party id; Type: DEFAULT; Schema: public; Owner: thomashowe
--

ALTER TABLE ONLY public.party ALTER COLUMN id SET DEFAULT nextval('public.party_id_seq'::regclass);


--
-- TOC entry 3463 (class 2606 OID 53478)
-- Name: analysis analysis_pkey; Type: CONSTRAINT; Schema: public; Owner: thomashowe
--

ALTER TABLE ONLY public.analysis
    ADD CONSTRAINT analysis_pkey PRIMARY KEY (id);


--
-- TOC entry 3465 (class 2606 OID 53487)
-- Name: attachment attachment_pkey; Type: CONSTRAINT; Schema: public; Owner: thomashowe
--

ALTER TABLE ONLY public.attachment
    ADD CONSTRAINT attachment_pkey PRIMARY KEY (id);


--
-- TOC entry 3468 (class 2606 OID 53496)
-- Name: dialog dialog_pkey; Type: CONSTRAINT; Schema: public; Owner: thomashowe
--

ALTER TABLE ONLY public.dialog
    ADD CONSTRAINT dialog_pkey PRIMARY KEY (id);


--
-- TOC entry 3470 (class 2606 OID 53506)
-- Name: group group_pkey; Type: CONSTRAINT; Schema: public; Owner: thomashowe
--

ALTER TABLE ONLY public."group"
    ADD CONSTRAINT group_pkey PRIMARY KEY (id);


--
-- TOC entry 3472 (class 2606 OID 53515)
-- Name: party party_pkey; Type: CONSTRAINT; Schema: public; Owner: thomashowe
--

ALTER TABLE ONLY public.party
    ADD CONSTRAINT party_pkey PRIMARY KEY (id);


--
-- TOC entry 3474 (class 2606 OID 53522)
-- Name: vcons vcons_pkey; Type: CONSTRAINT; Schema: public; Owner: thomashowe
--

ALTER TABLE ONLY public.vcons
    ADD CONSTRAINT vcons_pkey PRIMARY KEY (id);


--
-- TOC entry 3466 (class 1259 OID 53497)
-- Name: dialog_parties; Type: INDEX; Schema: public; Owner: thomashowe
--

CREATE INDEX dialog_parties ON public.dialog USING gin (parties);


--
-- TOC entry 3619 (class 0 OID 0)
-- Dependencies: 5
-- Name: SCHEMA public; Type: ACL; Schema: -; Owner: thomashowe
--

REVOKE USAGE ON SCHEMA public FROM PUBLIC;
GRANT ALL ON SCHEMA public TO PUBLIC;


-- Completed on 2023-03-28 15:02:00 JST

--
-- PostgreSQL database dump complete
--

