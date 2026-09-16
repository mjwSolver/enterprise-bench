# 2. Snowflake Infrastructure DDL & Staging Layer

## 2.1 Virtual Warehouse Topology

Compute resources are separated by operational domain to isolate ETL ingestion spikes from executive reporting workloads:

| Warehouse Name | Size | Min Clusters | Max Clusters | Auto-Suspend | Intended Workload |
|:---|:---|:---|:---|:---|:---|
| `WH_INGEST_XS` | X-Small | 1 | 2 | 60 sec | Snowpipe, batch micro-loader, and stage file loading |
| `WH_TRANSFORM_M` | Medium | 1 | 3 | 120 sec | dbt transformation models, daily aggregations, and dimensional builds |
| `WH_REPORTING_S` | Small | 1 | 4 | 60 sec | Power BI DirectQuery dashboards and ad-hoc analyst queries |
| `WH_ADMIN_XS` | X-Small | 1 | 1 | 60 sec | DBA maintenance, access audit queries, and permission management |

---

## 2.2 Database & Schema Organization

The Snowflake instance contains three distinct database layers enforcing medallion data hygiene:

* `NGL_RAW_DB`: Immutable raw staging database ingested directly from source systems.
  * `STG_SAP`: SAP ECC ERP staging tables.
  * `STG_LOGISTICS`: Operational shipment and warehouse tables.
* `NGL_ANALYTICS_DB`: Cleaned, modeled enterprise data warehouse.
  * `SILVER`: Conformed enterprise dimensions and deduplicated transactions.
  * `GOLD_SALES`: Executive sales performance metrics, gross profit mart, and customer KPIs.
  * `GOLD_FINANCE`: Balance sheet aggregations, revenue realization, and margin analytics.
* `NGL_GOVERNANCE_DB`: Security, audit logging, and metadata management.

---

## 2.3 Staging DDL & External Storage Definitions

```sql
-- Provision External Storage Integration with AWS S3 Jakarta
CREATE OR REPLACE STORAGE INTEGRATION S3_INTEGRATION_NGL
  TYPE = EXTERNAL_STAGE
  STORAGE_PROVIDER = 'S3'
  ENABLED = TRUE
  STORAGE_AWS_ROLE_ARN = 'arn:aws:iam::123456789012:role/SnowflakeS3AccessRole'
  STORAGE_ALLOWED_LOCATIONS = ('s3://ngl-enterprise-data-lake-prod-jkt/');

-- Define Parquet File Format
CREATE OR REPLACE FILE FORMAT NGL_RAW_DB.STG_SAP.FF_PARQUET_SNAPPY
  TYPE = 'PARQUET'
  COMPRESSION = 'SNAPPY';

-- Define External Stage for Sales Ingestion
CREATE OR REPLACE STAGE NGL_RAW_DB.STG_SAP.STAGE_SALES_TRANSACTIONS
  STORAGE_INTEGRATION = S3_INTEGRATION_NGL
  URL = 's3://ngl-enterprise-data-lake-prod-jkt/sap_ecc/sales/'
  FILE_FORMAT = NGL_RAW_DB.STG_SAP.FF_PARQUET_SNAPPY;
```

---

## 2.4 Raw Staging Table Schemas

The following DDL establishes the raw immutable staging table for sales transaction line items:

```sql
CREATE OR REPLACE TABLE NGL_RAW_DB.STG_SAP.RAW_SALES_ORDER_ITEMS (
    SALES_DOC_NUMBER    VARCHAR(10) NOT NULL,
    ITEM_NUMBER         VARCHAR(6) NOT NULL,
    MATERIAL_NUMBER     VARCHAR(18),
    SALES_ORG           VARCHAR(4),
    DIST_CHANNEL        VARCHAR(2),
    DIVISION            VARCHAR(2),
    ORDER_QUANTITY      NUMBER(15, 3),
    NET_VALUE_IDR       NUMBER(18, 2),
    TAX_AMOUNT_IDR      NUMBER(18, 2),
    CURRENCY            VARCHAR(3) DEFAULT 'IDR',
    CREATED_ON          DATE,
    ETL_LOADED_AT       TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP(),
    ETL_BATCH_ID        VARCHAR(64),
    CONSTRAINT PK_RAW_SALES PRIMARY KEY (SALES_DOC_NUMBER, ITEM_NUMBER)
);
```

> [!WARNING]
> Do NOT apply transformation or business logic inside `NGL_RAW_DB`. All raw fields must mirror the source extract schema exactly to enable audit backtracking and reprocessing.
