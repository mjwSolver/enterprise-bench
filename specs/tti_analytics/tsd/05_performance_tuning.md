# 5. Performance Tuning & Cost Optimization

## 5.1 Micro-Partitioning & Clustering Strategy

Snowflake partitions data automatically based on ingestion sequence. For high-cardinality fact tables exceeding 50 million rows, explicit clustering keys guarantee efficient partition pruning:

```sql
-- Apply Clustering to High-Volume Sales Fact Table
ALTER TABLE NGL_ANALYTICS_DB.GOLD_SALES.FCT_SALES_AGG 
  CLUSTER BY (TRANSACTION_DATE, SALES_ORG);

-- Monitor Clustering Depth & Overlap
SELECT SYSTEM$CLUSTERING_INFORMATION('NGL_ANALYTICS_DB.GOLD_SALES.FCT_SALES_AGG', '(TRANSACTION_DATE, SALES_ORG)');
```

The target clustering depth metric must remain below **3.0** to ensure that analytical dashboard queries scan fewer than 5% of total table micro-partitions.

---

## 5.2 Query Acceleration & Search Optimization

To accelerate point lookups on large transaction histories without provisioning larger virtual warehouses:
1. **Search Optimization Service (SOS):** Enabled for `SALES_DOC_NUMBER` lookups in customer inquiry portals.
2. **Result Caching (24-Hour Persistence):** DirectQuery dashboards leverage Snowflake's in-memory result cache, answering repeated queries in **< 150 milliseconds** with **zero warehouse credit consumption**.
3. **Multi-Cluster Auto-Scaling:** `WH_REPORTING_S` scales from 1 to 4 clusters automatically in `Standard` scaling mode when queue time exceeds 8 seconds during monthend financial close.

| Optimization Technique | Target Workload | Performance Impact | Cost Impact |
|:---|:---|:---|:---|
| **Explicit Clustering Keys** | Large Fact Tables (`FCT_*`) | 8x faster range scans | Low (Automated Background Reclustering) |
| **Result Caching** | Power BI Executive Dashboards | Sub-second response (<200ms) | Zero credit cost |
| **Warehouse Auto-Suspend (60s)** | Ad-hoc Analyst Exploration | Eliminates idle runtime | Up to 40% monthly credit savings |
| **Search Optimization (SOS)** | Customer Service Document Search | 20x faster equality lookups | Moderate storage credit add-on |

---

## 5.3 Maintenance & Housekeeping Procedures

* **Time Travel Retention Period:**
  * Staging tables (`NGL_RAW_DB`): `1 day` (Transient tables).
  * Production conformed tables (`NGL_ANALYTICS_DB`): `30 days` (Fail-safe enabled).
* **Automated Weekly Vacuum & Sizing Review:** Every Sunday at 02:00 WIB, an automated script inspects unused tables and logs recommendations to `NGL_GOVERNANCE_DB.AUDIT.PERFORMANCE_LOG`.

> [!NOTE]
> All maintenance routines are scheduled during off-peak weekend hours to ensure zero interference with weekday analytical workflows.
