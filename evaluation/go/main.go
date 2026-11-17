package main

import (
	"encoding/json"
	"fmt"
	"github.com/ajitpratap0/GoSQLX/pkg/gosqlx"
	"github.com/ajitpratap0/GoSQLX/pkg/sql/ast"
	"github.com/ajitpratap0/GoSQLX/pkg/sql/keywords"
	"github.com/ajitpratap0/GoSQLX/pkg/transform"
	"os"
)

type Case struct {
	ID       string `json:"id"`
	SQL      string `json:"sql"`
	Category string `json:"category"`
}

func run() error {
	if len(os.Args) != 2 {
		return fmt.Errorf("expected corpus path")
	}
	data, err := os.ReadFile(os.Args[1])
	if err != nil {
		return err
	}
	var cases []Case
	if err = json.Unmarshal(data, &cases); err != nil {
		return err
	}
	results := []map[string]any{}
	for _, c := range cases {
		tree, parseErr := gosqlx.ParseWithDialect(c.SQL, keywords.DialectSQLServer)
		row := map[string]any{"id": c.ID, "category": c.Category, "parsed": parseErr == nil}
		if parseErr != nil {
			row["error"] = parseErr.Error()
		} else {
			row["statement_count"] = len(tree.Statements)
			rendered := []string{}
			for _, statement := range tree.Statements {
				sql, formatErr := transform.FormatSQLWithDialectChecked(statement, keywords.DialectSQLServer)
				if formatErr != nil {
					row["render_error"] = formatErr.Error()
				} else {
					rendered = append(rendered, sql)
				}
			}
			row["rendered"] = rendered
			ast.ReleaseAST(tree)
		}
		results = append(results, row)
	}
	encoder := json.NewEncoder(os.Stdout)
	encoder.SetIndent("", "  ")
	return encoder.Encode(results)
}
func main() {
	if err := run(); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
