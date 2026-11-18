# Service-owned WEPPpy JSON profile v1

Status: authored contract before API/client implementation. This is not a capture
of live SDA behavior. Profile identifier: `wepppy-json-v1`. The initial request is
form-urlencoded POST `/Tabular/post.rest` with `query` and
`format=JSON+COLUMNNAME`; encode the plus as `%2B`. Supported query families and
column order come from contracts/wepppy-queries.json. Unsupported queries fail
explicitly under the existing error contract.

## Wire values and release identity

Success is HTTP 200, application/json, with the body defined by
contracts/wepppy-json.schema.json. `Table[0]` always contains the selected column
names in query order, including empty results; subsequent entries are equal-width
data rows. No metadata row, column reordering, padding, or dropped columns.
The header must match the expected family exactly. Preserve every raw row and
its response order; the API does not perform WEPPpy's extraction deduplication.

All non-null cells are JSON strings. SQL numbers use finite decimal strings;
identifiers use exact base-10 integer strings without scientific notation or
floating-point conversion. Preserve numeric precision; reject unrepresentable
non-finite values explicitly. SQL NULL is JSON null. Empty text is the distinct
JSON string "". Unicode and JSON escaping preserve the underlying text.

Required success headers: `X-Soil-Profile: wepppy-json-v1` and `X-Soil-Release`
containing the immutable active release identifier used for that request. The
client selects the endpoint/profile explicitly and verifies the expected release
before writing cache records. A profile/release change fails the current build;
never merge releases or silently switch endpoints. These headers are service-owned,
not claims about USDA headers. Metadata discovery remains GET `/v1/metadata`.

## Legacy WEPPpy extraction contract

The compatibility adapter checks the complete response/header/row shape before
producing records. Reject numeric JSON cells, booleans, extra/missing columns,
wrong headers, malformed JSON, and HTML errors. Fail rather than return empty data.

To match the existing XML path, convert null and empty text to None, then apply
the pinned WEPPpy `try_parse` conversion to every nonempty string. XML's empty
element has no text, so collapsing empty text is an explicitly scoped legacy-client
rule; the API itself keeps empty text distinct from NULL. Whitespace-only text
remains text unless `try_parse` accepts it as numeric. Do not otherwise trim text.

For component and horizon results, keep the first record for each normalized pair
of the first two columns. For fragment, texture, and restriction results, keep the
first record for each normalized first-column key. Do not sort to change which row
wins. These are the current `_extract_table` and `_extract_unique` behaviors.
Raw row tie-order parity on independent official imports remains a separate gate;
authored ordered examples do not prove an upstream ordering guarantee.

contracts/wepppy-json-examples.json records authored wire examples, synthetic XML
for the legacy extractor, and expected parsed rows. Empty, null, empty-text,
Unicode, decimal, large-identifier and first-row-wins cases are deliberately
represented. Synthetic XML must never be relabeled as captured SDA evidence.

The exact column/extraction/order mapping is contracts/wepppy-query-profiles.json.
For the component join, resolve the existing ambiguous `ORDER BY mukey` to the
selected `component.mukey`, consistent with the retained source audit. Do not
invent secondary sort columns to choose a different duplicate winner.
