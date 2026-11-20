# Forest latency comparison with USDA SDA

This benchmark measures the elapsed time a forest WEPPpy worker sees when
requesting soil data. The worker reaches the mirror over local Compose HTTP and
USDA over public HTTPS. The numbers include the respective connection, network,
endpoint processing, and response transfer costs.

## Method

- **Matched HTTP requests.** Send the same form-encoded SQL and
  `JSON+COLUMNNAME` format to both endpoints. Cover the five WEPPpy query
  families for the retained Guam SSURGO and Virgin Islands STATSGO2 samples.
  Include the 100-map-unit SSURGO component query from the national mirror
  qualification. Record seven paired samples per query, with the source that
  goes first alternating. Send one request at a time, with USDA request starts
  at least 1.25 seconds apart. The timer ends when the response body is read,
  before JSON parsing.
- **WEPPpy acquisition.** Open a fresh SQLite cache for the same eight
  SSURGO map units and measure through completion of
  `SurgoSoilCollection`. Use the mirror JSON client or the bounded USDA
  XML client. The mirror time includes its metadata request. Reopen each cache
  immediately to measure the warm path, and verify that it makes no new
  acquisition calls. Take five pairs and space USDA collection starts by
  at least ten seconds.
- **Checks.** Record response status, length and hash, row counts, and exact
  numeric and text row multiset comparisons. Record equivalence after the
  previously observed empty-`geomdesc` representation difference separately.
  Treat differing result sets as different work even when the SQL is identical.
  Check the active mirror release throughout. The report retains individual
  readings, medians and observed ranges.

Run the comparison script in a forest WEPPpy worker environment, with the
checkout's scripts, contracts and national parity receipt available.

```bash
python scripts/benchmark_live_sda.py --output /tmp/forest-sda-latency
```

## Results

Collected November 20, 2026 UTC from a forest worker on a dual-socket Xeon
E5-2697 v2 host. The mirror served the pinned national release
`forest-us-ssurgo-20261001-statsgo2-20161013-v1`. The
[measurement receipt](../artifacts/assessment/forest-sda-latency.json)
includes container images, client source hashes, release checksums, and
each timing.

| JSON request | Rows per response | USDA median | Mirror median | USDA ÷ mirror |
| --- | ---: | ---: | ---: | ---: |
| SSURGO components | 5 | 460.7 ms | 28.9 ms | 15.9× |
| SSURGO horizons | 16 | 444.9 ms | 25.5 ms | 17.4× |
| SSURGO fragments | 0 | 444.6 ms | 28.3 ms | 15.7× |
| SSURGO textures | 19 | 435.7 ms | 25.6 ms | 17.0× |
| SSURGO restrictions | 4 | 447.0 ms | 24.2 ms | 18.5× |
| STATSGO2 components | 26 | 447.8 ms | 28.0 ms | 16.0× |
| STATSGO2 horizons | 104 | 451.7 ms | 30.0 ms | 15.1× |
| STATSGO2 fragments | 179 | 452.3 ms | 26.4 ms | 17.1× |
| STATSGO2 textures | 172 | 456.8 ms | 29.4 ms | 15.5× |
| STATSGO2 restrictions | 25 | 435.0 ms | 25.0 ms | 17.4× |
| SSURGO components for 100 map units | 354 | 700.0 ms | 37.0 ms | 18.9× |

All 77 paired HTTP trials completed successfully. Row counts matched for
every pair. Nine workloads had exact value multisets after numeric parsing.
All eleven matched when the empty-string and null representations of
`geomdesc` were treated as equivalent.

| WEPPpy cache acquisition | USDA median (range) | Mirror median (range) |
| --- | ---: | ---: |
| Fresh cache, eight SSURGO map units | 3.09 s (2.96–4.21 s) | 257 ms (213–263 ms) |
| Populated cache, same map units | 5.6 ms (4.6–8.8 ms) | 7.9 ms (3.9–9.7 ms) |

Fresh acquisition took 12.0× as long through live USDA as through the
mirror. Warm measurements overlapped and recorded no additional retrievals.
These results describe serial client latency on forest. Server-only
execution times and public-service capacity remain unmeasured.

## Connection timing

Three follow-up requests used the same zero-row SSURGO fragment query from the
same worker. The [receipt](../artifacts/assessment/forest-sda-latency.json)
preserves curl's cumulative timings. The USDA public HTTPS path took 317–607 ms
to reach the start of request transfer, including DNS, TCP and TLS setup.
Another 148–262 ms elapsed before the first byte, including the public
network round trip and server work. The mirror took 21–27 ms for the complete
response. These timings leave USDA's internal query execution time unknown.
