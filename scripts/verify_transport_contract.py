#!/usr/bin/env python3
"""Validate authored wire examples; this is not a deployed WEPPpy client."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def validate_table(body, columns):
    if not isinstance(body,dict) or set(body)!={'Table'}:
        raise ValueError('Expected only the Table response property')
    rows=body['Table']
    if not isinstance(rows,list) or not rows or rows[0]!=columns:
        raise ValueError('Missing or incorrect query header')
    if len(set(columns))!=len(columns) or not all(isinstance(v,str) and v for v in columns):
        raise ValueError('Invalid expected column names')
    for row in rows[1:]:
        if not isinstance(row,list) or len(row)!=len(columns):
            raise ValueError('Data row width differs from query header')
        if any(v is not None and not isinstance(v,str) for v in row):
            raise ValueError('Cells must be strings or null')
    return rows[1:]


def verify(ssurgo=None):
    schema=json.loads((ROOT/'contracts/wepppy-cache-schema.json').read_text())
    examples=json.loads((ROOT/'contracts/wepppy-json-examples.json').read_text())
    if examples['evidence_kind']!='authored_contract_and_synthetic_xml_not_live_sda':
        raise ValueError('Authored examples must not claim live provenance')
    results=[]
    for case in examples['cases']:
        columns=[c[0] for c in schema['tables'][case['query_family']]['columns']]
        validate_table(case['response'],columns)
        if ssurgo is not None:
            rows=[list(r) for r in getattr(ssurgo,case['extractor'])(case['synthetic_xml'])]
            if rows!=case['expected_rows']:
                raise ValueError('Legacy extractor differs from authored expectations: '+case['id'])
        results.append({'id':case['id'],'shape':'passed','legacy_extraction':'passed' if ssurgo is not None else 'not_executed'})
    return results


if __name__=='__main__':print(json.dumps(verify(),indent=2))
