# Elasticsearch Build DB Query Patterns

## Endpoint
`https://gpuwa.nvidia.com/elasticsearch/` — NO AUTH NEEDED

## Common Queries

### Build count and avg duration by month
```bash
curl -s "https://gpuwa.nvidia.com/elasticsearch/df-nvip-build_db-per_build-YYYYMM/_search" \
  -H 'Content-Type: application/json' -d '{
  "size": 0,
  "aggs": {
    "avg_duration": {"avg": {"field": "l_duration"}},
    "total_builds": {"value_count": {"field": "l_duration"}},
    "top_projects": {"terms": {"field": "s_nvprojectname", "size": 10}}
  }
}'
```

### Per-task longpole analysis
```bash
curl -s "https://gpuwa.nvidia.com/elasticsearch/df-nvip-build_db-per_job-YYYYMM/_search" \
  -H 'Content-Type: application/json' -d '{
  "size": 0,
  "query": {"term": {"s_nvprojectname": "PROJECT_NAME"}},
  "aggs": {
    "top_jobs": {"terms": {"field": "s_job_name", "size": 10, "order": {"avg_wall": "desc"}},
      "aggs": {"avg_wall": {"avg": {"field": "stats.d_wall_time"}}}}
  }
}'
```

### Build activity for a team (e.g., hw_mmplex_secip)
```bash
curl -s "https://gpuwa.nvidia.com/elasticsearch/df-nvip-build_db-per_build-YYYYMM/_search" \
  -H 'Content-Type: application/json' -d '{
  "size": 0,
  "query": {"wildcard": {"s_nvprojectname": "*secip*"}},
  "aggs": {"projects": {"terms": {"field": "s_nvprojectname", "size": 20}}}
}'
```

## Available Indices
| Pattern | Content |
|---------|---------|
| `df-nvip-build_db-per_build-YYYYMM` | Per-build: ~143K docs/month |
| `df-nvip-build_db-per_job-YYYYMM` | Per-task: ~47M docs/month |
| `df-nvip-build_db-unified-YYYYMM` | Merged build+job |
| `df-nvip-build_db-overhead-metrics-YYYYMM` | System overhead |
| `df-genie-p4export-nvmobile-YYYY` | P4 sync operations |
| `df-ghw-pmu-nvgpu-to-nvip-integrations` | Cross-project tracking |
